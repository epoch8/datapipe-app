"""remove *2 steps

Revision ID: 724c165a90bc
Revises: 72a7da982290
Create Date: 2023-07-12 01:02:32.908177

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '724c165a90bc'
down_revision = '72a7da982290'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('datapipe_step_events',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('step', sa.String(length=100), nullable=True),
    sa.Column('event_ts', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('event', sa.String(length=100), nullable=True),
    sa.Column('event_payload', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('user_lang2')
    op.drop_table('events_meta')
    op.drop_table('user_lang_meta')
    op.drop_table('user_profile_meta')
    op.drop_table('user_profile2_meta')
    op.drop_table('user_lang2_meta')
    op.drop_table('events2_meta')
    op.drop_table('events2')
    op.drop_table('user_profile2')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_profile2',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('offer_clicks', sqlite.JSON(), nullable=True),
    sa.Column('events_count', sa.INTEGER(), nullable=True),
    sa.Column('active', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('events2',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('event_id', sa.INTEGER(), nullable=False),
    sa.Column('event', sqlite.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('events2_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('event_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('user_lang2_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile2_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_lang_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('events_meta',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('event_id', sa.INTEGER(), nullable=False),
    sa.Column('hash', sa.INTEGER(), nullable=True),
    sa.Column('create_ts', sa.FLOAT(), nullable=True),
    sa.Column('update_ts', sa.FLOAT(), nullable=True),
    sa.Column('process_ts', sa.FLOAT(), nullable=True),
    sa.Column('delete_ts', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('user_lang2',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('lang', sa.VARCHAR(length=100), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.drop_table('datapipe_step_events')
    # ### end Alembic commands ###
