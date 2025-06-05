"""Add codigo_autenticacao to venda

Revision ID: add_codigo_autenticacao_to_venda
Revises: 8edb46cc0a94
Create Date: 2025-06-05 14:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_codigo_autenticacao_to_venda'
down_revision = '8edb46cc0a94'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna codigo_autenticacao à tabela venda
    op.add_column('venda', sa.Column('codigo_autenticacao', sa.String(length=20), nullable=True))
    
    # Cria um índice único para o código de autenticação
    op.create_unique_constraint('uq_venda_codigo_autenticacao', 'venda', ['codigo_autenticacao'])

def downgrade():
    # Remove a restrição de unicidade e a coluna ao reverter a migração
    op.drop_constraint('uq_venda_codigo_autenticacao', 'venda', type_='unique')
    op.drop_column('venda', 'codigo_autenticacao')
