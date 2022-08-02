"""initial

Revision ID: e7716e02d74b
Revises: 
Create Date: 2022-08-02 16:04:28.330850

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7716e02d74b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('datapipe_events',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('event_ts', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('type', sa.String(length=100), nullable=True),
    sa.Column('event', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('events',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('event', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('events_meta',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.Integer(), nullable=True),
    sa.Column('create_ts', sa.Float(), nullable=True),
    sa.Column('update_ts', sa.Float(), nullable=True),
    sa.Column('process_ts', sa.Float(), nullable=True),
    sa.Column('delete_ts', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('user_lang',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('lang', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_lang_meta',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.Integer(), nullable=True),
    sa.Column('create_ts', sa.Float(), nullable=True),
    sa.Column('update_ts', sa.Float(), nullable=True),
    sa.Column('process_ts', sa.Float(), nullable=True),
    sa.Column('delete_ts', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('offer_clicks', sa.JSON(), nullable=True),
    sa.Column('events_count', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile_meta',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.Integer(), nullable=True),
    sa.Column('create_ts', sa.Float(), nullable=True),
    sa.Column('update_ts', sa.Float(), nullable=True),
    sa.Column('process_ts', sa.Float(), nullable=True),
    sa.Column('delete_ts', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_profile_meta')
    op.drop_table('user_profile')
    op.drop_table('user_lang_meta')
    op.drop_table('user_lang')
    op.drop_table('events_meta')
    op.drop_table('events')
    op.drop_table('datapipe_events')
    # ### end Alembic commands ###
