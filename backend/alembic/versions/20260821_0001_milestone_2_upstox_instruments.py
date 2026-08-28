"""milestone 2 upstox instruments

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21 00:00:00
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260821_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_key", sa.String(length=128), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("segment", sa.String(length=32), nullable=False),
        sa.Column("instrument_type", sa.String(length=32), nullable=False),
        sa.Column("isin", sa.String(length=32), nullable=True),
        sa.Column("trading_symbol", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=255), nullable=True),
        sa.Column("lot_size", sa.Integer(), nullable=False),
        sa.Column("freeze_quantity", sa.Numeric(20, 4), nullable=True),
        sa.Column("tick_size", sa.Numeric(12, 4), nullable=False),
        sa.Column("qty_multiplier", sa.Numeric(20, 4), nullable=True),
        sa.Column("security_type", sa.String(length=64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrument_key", name="uq_instruments_instrument_key"),
        sa.UniqueConstraint("isin", name="uq_instruments_isin"),
    )
    op.create_index("ix_instruments_active", "instruments", ["active"])
    op.create_index(
        "ix_instruments_exchange_segment_type",
        "instruments",
        ["exchange", "segment", "instrument_type"],
    )
    op.create_index("ix_instruments_symbol_active", "instruments", ["trading_symbol", "active"])
    op.create_index("ix_instruments_trading_symbol", "instruments", ["trading_symbol"])

    op.create_table(
        "upstox_oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_hash"),
    )
    op.create_index("ix_upstox_oauth_states_state_hash", "upstox_oauth_states", ["state_hash"])

    op.create_table(
        "upstox_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", name="uq_upstox_tokens_provider"),
    )

    op.create_table(
        "data_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("check_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=False),
        sa.Column("accepted_records", sa.Integer(), nullable=False),
        sa.Column("rejected_records", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_health_check_name", "data_health", ["check_name"])
    op.create_index("ix_data_health_source", "data_health", ["source"])
    op.create_index("ix_data_health_status", "data_health", ["status"])


def downgrade() -> None:
    op.drop_index("ix_data_health_status", table_name="data_health")
    op.drop_index("ix_data_health_source", table_name="data_health")
    op.drop_index("ix_data_health_check_name", table_name="data_health")
    op.drop_table("data_health")
    op.drop_table("upstox_tokens")
    op.drop_index("ix_upstox_oauth_states_state_hash", table_name="upstox_oauth_states")
    op.drop_table("upstox_oauth_states")
    op.drop_index("ix_instruments_trading_symbol", table_name="instruments")
    op.drop_index("ix_instruments_symbol_active", table_name="instruments")
    op.drop_index("ix_instruments_exchange_segment_type", table_name="instruments")
    op.drop_index("ix_instruments_active", table_name="instruments")
    op.drop_table("instruments")
