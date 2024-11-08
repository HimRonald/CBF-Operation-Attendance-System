"""Add attendance_id foreign key to CheckMeal

Revision ID: afb2bd1def76
Revises: 6aa468426966
Create Date: 2024-11-08 00:03:02.967983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afb2bd1def76'
down_revision = '6aa468426966'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('checkmeal', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attendance_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint(None, ['attendance_id'])
        batch_op.create_foreign_key(None, 'attendance', ['attendance_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('checkmeal', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('attendance_id')

    # ### end Alembic commands ###
