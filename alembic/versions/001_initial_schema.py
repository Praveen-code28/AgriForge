"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "farms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lon", sa.Float(), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farms_id"), "farms", ["id"], unique=False)
    op.create_index(op.f("ix_farms_user_id"), "farms", ["user_id"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=True),
        sa.Column("image_path", sa.String(length=512), nullable=False),
        sa.Column("primary_plant", sa.String(length=64), nullable=False),
        sa.Column("primary_disease", sa.String(length=64), nullable=False),
        sa.Column("primary_confidence", sa.Float(), nullable=False),
        sa.Column("predictions_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_predictions_farm_id"), "predictions", ["farm_id"], unique=False)
    op.create_index(op.f("ix_predictions_id"), "predictions", ["id"], unique=False)
    op.create_index(op.f("ix_predictions_user_id"), "predictions", ["user_id"], unique=False)

    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("disease_result", sa.Text(), nullable=False),
        sa.Column("treatment_result", sa.Text(), nullable=False),
        sa.Column("weather_result", sa.Text(), nullable=True),
        sa.Column("combined_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prediction_id"),
    )
    op.create_index(op.f("ix_analysis_reports_id"), "analysis_reports", ["id"], unique=False)
    op.create_index(op.f("ix_analysis_reports_user_id"), "analysis_reports", ["user_id"], unique=False)

    op.create_table(
        "weather_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("location_json", sa.Text(), nullable=False),
        sa.Column("weather_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prediction_id"),
    )
    op.create_index(op.f("ix_weather_analyses_id"), "weather_analyses", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_weather_analyses_id"), table_name="weather_analyses")
    op.drop_table("weather_analyses")
    op.drop_index(op.f("ix_analysis_reports_user_id"), table_name="analysis_reports")
    op.drop_index(op.f("ix_analysis_reports_id"), table_name="analysis_reports")
    op.drop_table("analysis_reports")
    op.drop_index(op.f("ix_predictions_user_id"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_id"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_farm_id"), table_name="predictions")
    op.drop_table("predictions")
    op.drop_index(op.f("ix_farms_user_id"), table_name="farms")
    op.drop_index(op.f("ix_farms_id"), table_name="farms")
    op.drop_table("farms")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
