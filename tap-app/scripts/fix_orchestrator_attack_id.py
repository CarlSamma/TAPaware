from pathlib import Path

p = Path("d:/PROGETTI/Framework-studio/framework/src/chronos/orchestrator.py")
text = p.read_text()

old = """        extraction_input = ExtractionInput(
            target_handle=target_handle or "",
            secret_profile=payload.get("secret_profile", {}),
            fused_payloads=[],
            behavioral_profile=behavioral_profile,
        )"""

new = """        from uuid import UUID
        extraction_input = ExtractionInput(
            attack_id=UUID(str(attack_id)) if attack_id else None,
            target_handle=target_handle or "",
            secret_profile=payload.get("secret_profile", {}),
            fused_payloads=[],
            behavioral_profile=behavioral_profile,
        )"""

if old in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("FIXED orchestrator attack_id")
else:
    print("pattern not found")
