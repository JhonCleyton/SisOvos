"""Initial migration

Revision ID: 8edb46cc0a94
Revises: 
Create Date: 2025-06-04 10:58:32.785768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8edb46cc0a94'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cliente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('telefone', sa.String(length=20), nullable=True),
    sa.Column('endereco', sa.Text(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('produto',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('preco_compra', sa.Float(), nullable=False),
    sa.Column('preco_venda', sa.Float(), nullable=False),
    sa.Column('estoque_atual', sa.Float(), nullable=False),
    sa.Column('estoque_minimo', sa.Float(), nullable=True),
    sa.Column('unidade_medida', sa.String(length=10), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(), nullable=True),
    sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('codigo')
    )
    op.create_table('usuario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('telefone', sa.String(length=20), nullable=True),
    sa.Column('senha', sa.String(length=200), nullable=False),
    sa.Column('funcao', sa.String(length=20), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('estoque_diario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data', sa.Date(), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Float(), nullable=False),
    sa.Column('valor_estoque', sa.Float(), nullable=False),
    sa.Column('entrada', sa.Float(), nullable=False),
    sa.Column('saida', sa.Float(), nullable=False),
    sa.Column('estoque_inicial', sa.Float(), nullable=False),
    sa.Column('estoque_final', sa.Float(), nullable=False),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['produto_id'], ['produto.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('estoque_diario', schema=None) as batch_op:
        batch_op.create_index('idx_estoque_diario_data_produto', ['data', 'produto_id'], unique=True)

    op.create_table('venda',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data_venda', sa.DateTime(), nullable=False),
    sa.Column('valor_total', sa.Float(), nullable=False),
    sa.Column('desconto', sa.Float(), nullable=True),
    sa.Column('forma_pagamento', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('data_pagamento', sa.DateTime(), nullable=True),
    sa.Column('data_cancelamento', sa.DateTime(), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('numero_cupom', sa.String(length=50), nullable=True),
    sa.Column('cliente_id', sa.Integer(), nullable=True),
    sa.Column('nome_cliente', sa.String(length=100), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('data_criacao', sa.DateTime(), nullable=True),
    sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('historico_venda',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=False),
    sa.Column('data_alteracao', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('item_venda',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Float(), nullable=False),
    sa.Column('preco_unitario', sa.Float(), nullable=False),
    sa.Column('desconto', sa.Float(), nullable=True),
    sa.Column('total', sa.Float(), nullable=False),
    sa.Column('data_criacao', sa.DateTime(), nullable=True),
    sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['produto_id'], ['produto.id'], ),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('venda_id', 'produto_id', name='uix_venda_produto')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('item_venda')
    op.drop_table('historico_venda')
    op.drop_table('venda')
    with op.batch_alter_table('estoque_diario', schema=None) as batch_op:
        batch_op.drop_index('idx_estoque_diario_data_produto')

    op.drop_table('estoque_diario')
    op.drop_table('usuario')
    op.drop_table('produto')
    op.drop_table('cliente')
    # ### end Alembic commands ###
