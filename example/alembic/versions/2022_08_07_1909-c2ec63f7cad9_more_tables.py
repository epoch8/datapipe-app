"""more tables

Revision ID: c2ec63f7cad9
Revises: e7716e02d74b
Create Date: 2022-08-07 19:09:12.155709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2ec63f7cad9'
down_revision = 'e7716e02d74b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('events2',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('event', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('events2_meta',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.Integer(), nullable=True),
    sa.Column('create_ts', sa.Float(), nullable=True),
    sa.Column('update_ts', sa.Float(), nullable=True),
    sa.Column('process_ts', sa.Float(), nullable=True),
    sa.Column('delete_ts', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    op.create_table('user_lang2',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('lang', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_lang2_meta',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.Integer(), nullable=True),
    sa.Column('create_ts', sa.Float(), nullable=True),
    sa.Column('update_ts', sa.Float(), nullable=True),
    sa.Column('process_ts', sa.Float(), nullable=True),
    sa.Column('delete_ts', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile2',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('offer_clicks', sa.JSON(), nullable=True),
    sa.Column('events_count', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_profile2_meta',
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
    op.drop_table('user_profile2_meta')
    op.drop_table('user_profile2')
    op.drop_table('user_lang2_meta')
    op.drop_table('user_lang2')
    op.drop_table('events2_meta')
    op.drop_table('events2')
    # ### end Alembic commands ###