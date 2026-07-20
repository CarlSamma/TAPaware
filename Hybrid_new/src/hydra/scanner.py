"""HYDRA Scanner — entrypoint for the HYDRA discovery pipeline.

Usage:
    $env:PYTHONPATH = "src"
    python -m hydra.scanner --target HackingA0 --platform twitter280

This module:
1. Connects to Neo4j V-Genome and queries techniques for the target model.
2. Fuses techniques via CartesianPruningFusionEngine.
3. Scores payloads via the SurrogateModel.
4. Optionally applies obfuscation and M2S+ platform conversion.
5. Publishes DiscoveryResult events to Kafka for CHRONOS consumption.
"""
from __future__ import annotations

import argparse
import asyncio
from typing import Any
from uuid import uuid4

from hydra.acd import AdaptiveCounterDefense
from hydra.fusion_engine import CartesianPruningFusionEngine
from hydra.handoff import HandoffProducer
from hydra.m2s_converter import M2SConverter, M2SStrategy
from hydra.obfuscation import ObfuscationEngine, ObfuscationLayer
from hydra.surrogate_model import SurrogateModel
from hydra.v_genome import VGenomeClient
from shared.models import (
    BehavioralProfile,
    DiscoveryResult,
    PlatformConstraint,
    SecretProfile,
)
from tap.config import get_settings
from tap.logger import get_logger

logger = get_logger("hydra.scanner")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HYDRA Scanner — discovery pipeline for attack techniques",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target model handle/identifier (e.g., HackingA0)",
    )
    parser.add_argument(
        "--platform",
        default="twitter280",
        choices=["twitter280", "twitter_thread", "discord_2000", "bluesky", "generic"],
        help="Target platform constraint (default: twitter280)",
    )
    parser.add_argument(
        "--asr-threshold",
        type=float,
        default=0.6,
        help="Minimum surrogate ASR threshold (default: 0.6)",
    )
    parser.add_argument(
        "--stealth-threshold",
        type=float,
        default=0.7,
        help="Minimum stealth score threshold (default: 0.7)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of fused payloads to generate (default: 5)",
    )
    parser.add_argument(
        "--obfuscate",
        action="store_true",
        default=False,
        help="Apply obfuscation layers to payloads",
    )
    parser.add_argument(
        "--no-handoff",
        action="store_true",
        default=False,
        help="Skip Kafka handoff (dry-run mode)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max techniques to fetch from V-Genome (default: 50)",
    )
    return parser.parse_args()


def _platform_to_constraint(name: str) -> PlatformConstraint:
    mapping: dict[str, PlatformConstraint] = {
        "twitter280": PlatformConstraint.TWITTER_280,
        "twitter_thread": PlatformConstraint.TWITTER_THREAD,
        "discord_2000": PlatformConstraint.DISCORD_2000,
        "bluesky": PlatformConstraint.BLUESKY,
        "generic": PlatformConstraint.GENERIC,
    }
    return mapping.get(name, PlatformConstraint.TWITTER_280)


async def _run_scanner(args: argparse.Namespace) -> int:
    """Execute the HYDRA discovery pipeline.

    Returns exit code (0 = success, 1 = error).
    """
    settings = get_settings()
    target_model = args.target.lower()
    platform = _platform_to_constraint(args.platform)
    attack_id = uuid4()

    logger.info(
        "hydra_scanner_start",
        target_model=target_model,
        platform=platform.value,
        attack_id=str(attack_id),
    )

    # ------------------------------------------------------------------
    # 1. Connect to Neo4j V-Genome
    # ------------------------------------------------------------------
    vgenome = VGenomeClient(settings)
    try:
        await vgenome.connect()
    except Exception as exc:
        logger.error("vgenome_connect_failed", error=str(exc))
        return 1

    try:
        # ------------------------------------------------------------------
        # 2. Query techniques for the target model
        # ------------------------------------------------------------------
        techniques: list[dict[str, Any]] = await vgenome.get_techniques(
            target_model=target_model,
            asr_threshold=args.asr_threshold,
            stealth_threshold=args.stealth_threshold,
            burned=False,
            limit=args.limit,
        )

        if not techniques:
            logger.warning(
                "no_techniques_found",
                target_model=target_model,
                asr_threshold=args.asr_threshold,
                stealth_threshold=args.stealth_threshold,
            )
            return 0

        logger.info(
            "techniques_retrieved",
            count=len(techniques),
            target_model=target_model,
        )

        # ------------------------------------------------------------------
        # 3. Fuse techniques into payloads
        # ------------------------------------------------------------------
        fusion = CartesianPruningFusionEngine()
        fused_prompts = fusion.generate_payloads(
            techniques=techniques,
            platform=platform,
            top_k=args.top_k,
        )

        logger.info("fusion_complete", candidate_count=len(fused_prompts))

        # ------------------------------------------------------------------
        # 4. Score with surrogate model
        # ------------------------------------------------------------------
        surrogate = SurrogateModel()
        best_asr = 0.0
        best_stealth = 0.0
        for prompt in fused_prompts:
            pred = surrogate.predict(prompt)
            logger.debug(
                "surrogate_prediction",
                prompt_id=str(prompt.prompt_id),
                asr=round(pred.asr, 4),
                stealth=round(pred.stealth, 4),
                cost=round(pred.cost, 6),
                turns=round(pred.turns, 1),
            )
            if pred.asr > best_asr:
                best_asr = pred.asr
            if pred.stealth > best_stealth:
                best_stealth = pred.stealth

        # ------------------------------------------------------------------
        # 5. Apply obfuscation (optional)
        # ------------------------------------------------------------------
        if args.obfuscate:
            obfuscator = ObfuscationEngine()
            obfuscation_layers = [
                ObfuscationLayer.UNICODE,
                ObfuscationLayer.CASE_SHIFT,
                ObfuscationLayer.ZERO_WIDTH,
            ]
            for prompt in fused_prompts:
                original = prompt.prompt_text
                prompt.prompt_text = obfuscator.obfuscate(
                    original, layers=obfuscation_layers, probability=0.25
                )
                prompt.obfuscation_layers = [layer.value for layer in obfuscation_layers]
            logger.info("obfuscation_applied", payload_count=len(fused_prompts))

        # ------------------------------------------------------------------
        # 6. Apply M2S+ platform conversion
        # ------------------------------------------------------------------
        m2s = M2SConverter()
        for prompt in fused_prompts:
            if platform != PlatformConstraint.GENERIC:
                # Wrap single-turn prompt through M2S narrative strategy
                prompt.prompt_text = m2s.convert(
                    turns=[prompt.prompt_text],
                    strategy=M2SStrategy.HYPHENIZE,
                    platform=platform.value,
                )
                prompt.m2s_converted = True
                prompt.platform_native_format = platform

        # ------------------------------------------------------------------
        # 7. Build DiscoveryResult
        # ------------------------------------------------------------------
        acd = AdaptiveCounterDefense()
        strategy_vector = acd.current_vector()

        discovery = DiscoveryResult(
            attack_id=attack_id,
            target_handle=f"@{args.target}",
            fused_prompts=fused_prompts,
            surrogate_asr=best_asr,
            surrogate_stealth=best_stealth,
            behavioral_profile=BehavioralProfile(),
        )

        logger.info(
            "discovery_result",
            attack_id=str(attack_id),
            target_handle=discovery.target_handle,
            prompt_count=len(fused_prompts),
            best_asr=round(best_asr, 4),
            best_stealth=round(best_stealth, 4),
            strategy_vector=strategy_vector.model_dump(),
        )

        # Print a human-readable summary
        print(f"\n{'='*60}")
        print(f"  HYDRA Scanner — Discovery Complete")
        print(f"{'='*60}")
        print(f"  Attack ID:     {attack_id}")
        print(f"  Target:        @{args.target} ({platform.value})")
        print(f"  Techniques:    {len(techniques)} fetched")
        print(f"  Payloads:      {len(fused_prompts)} generated")
        print(f"  Best ASR:      {best_asr:.4f}")
        print(f"  Best Stealth:  {best_stealth:.4f}")
        print(f"{'='*60}")
        for i, prompt in enumerate(fused_prompts, 1):
            print(f"\n  [{i}] {prompt.prompt_text[:120]}{'...' if len(prompt.prompt_text) > 120 else ''}")
            print(f"      ASR={prompt.expected_asr:.3f}  Stealth={prompt.expected_stealth:.3f}  Cost=${prompt.estimated_cost_usd:.4f}")
        print()

        # ------------------------------------------------------------------
        # 8. Handoff to CHRONOS via Kafka (optional)
        # ------------------------------------------------------------------
        if not args.no_handoff:
            handoff = HandoffProducer(settings)
            try:
                await handoff.send_discovery_result(discovery)
                logger.info("handoff_success", attack_id=str(attack_id))
            except Exception as exc:
                logger.error("handoff_failed", error=str(exc))
                return 1
            finally:
                await handoff.close()
        else:
            logger.info("handoff_skipped", reason="--no-handoff flag")

        return 0

    finally:
        await vgenome.close()


def main() -> None:
    """Entry point for `python -m hydra.scanner`."""
    args = _parse_args()
    try:
        exit_code = asyncio.run(_run_scanner(args))
    except KeyboardInterrupt:
        logger.warning("scanner_interrupted")
        exit_code = 130
    except Exception as exc:
        logger.error("scanner_fatal", error=str(exc))
        exit_code = 1
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()