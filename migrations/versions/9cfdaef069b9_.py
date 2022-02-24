"""empty message

Revision ID: 9cfdaef069b9
Revises: 3354fc98102c
Create Date: 2022-02-22 17:41:57.494240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9cfdaef069b9'
down_revision = '3354fc98102c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('movies', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('series', sa.Column('updated_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('series', 'updated_at')
    op.drop_column('movies', 'updated_at')
    # ### end Alembic commands ###