"""initial chronos schema

Revision ID: hybrid202606
Revises:
Create Date: 2026-06-27 19:23:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "hybrid202606"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # extraction_run: durable workflow execution context
    # -------------------------------------------------------------------------
    op.create_table(
        "extraction_run",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("attack_id", sa.UUID(as_uuid=True), index=True, nullable=False),
        sa.Column("target_handle", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success", sa.Boolean(), default=False),
        sa.Column("final_gamma", sa.Float(), nullable=True),
        sa.Column("cost_usd", sa.Float(), default=0.0),
        sa.Column("turns_total", sa.Integer(), default=0),
        sa.Column("queries_total", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # -------------------------------------------------------------------------
    # turn: individual probe/response pairs in a CHRONOS workflow
    # -------------------------------------------------------------------------
    op.create_table(
        "turn",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("attack_id", sa.UUID(as_uuid=True), index=True, nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("probe_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("gamma", sa.Float(), nullable=True),
        sa.Column("strategy", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # -------------------------------------------------------------------------
    # gamma_score: per-layer γ scores
    # -------------------------------------------------------------------------
    op.create_table(
        "gamma_score",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("turn_id", sa.UUID(as_uuid=True), index=True, nullable=False),
        sa.Column("layer", sa.Text(), nullable=False),  # lexical | semantic | behavioral
        sa.Column("gamma", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # -------------------------------------------------------------------------
    # leak_fragment: partial disclosures extracted from responses
    # -------------------------------------------------------------------------
    op.create_table(
        "leak_fragment",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("turn_id", sa.UUID(as_uuid=True), index=True, nullable=False),
        sa.Column("leak_type", sa.Text(), nullable=False),  # metadata | hint | partial_disclosure | full_disclosure
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("target_property", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # -------------------------------------------------------------------------
    # behavioral_profile: OCEAN+ profiles per attack
    # -------------------------------------------------------------------------
    op.create_table(
        "behavioral_profile",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("attack_id", sa.UUID(as_uuid=True), index=True, nullable=False, unique=True),
        sa.Column("ocean", sa.JSON(), nullable=False),  # {"O": 3.2, "C": 4.1, ...}
        sa.Column("stir_percentage", sa.Float(), nullable=True),
        sa.Column("profiled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # -------------------------------------------------------------------------
    # technique_burned: feedback loop back to V-Genome
    # -------------------------------------------------------------------------
    op.create_table(
        "technique_burned",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("technique_id", sa.Text(), nullable=False, index=True),
        sa.Column("target_model", sa.Text(), nullable=False, index=True),
        sa.Column("defense_type", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("counters", sa.JSON(), default=list),
        sa.Column("burned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("technique_burned")
    op.drop_table("behavioral_profile")
    op.drop_table("leak_fragment")
    op.drop_table("gamma_score")
    op.drop_table("turn")
    op.drop_table("extraction_run")
