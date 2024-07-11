"""active

Revision ID: 3d1745433113
Revises: 5ae5b084f01c
Create Date: 2024-07-10 10:37:08.103384

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3d1745433113"
down_revision = "5ae5b084f01c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "agg_profile_e8ae44cba1_meta",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("process_ts", sa.Float(), nullable=True),
        sa.Column("is_success", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.drop_table("datapipe_step_events")
    op.drop_table("datapipe_events")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "datapipe_events",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "event_ts",
            postgresql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("type", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column(
            "event",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="datapipe_events_pkey"),
    )
    op.create_table(
        "datapipe_step_events",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("step", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column(
            "event_ts",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("event", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column(
            "event_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="datapipe_step_events_pkey"),
    )
    op.drop_table("agg_profile_e8ae44cba1_meta")
    # ### end Alembic commands ###
