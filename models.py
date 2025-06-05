from datetime import datetime
from flask_login import UserMixin
from extensions import db

class Usuario(UserMixin, db.Model):
    # Funções disponíveis
    FUNCOES = [
        ('ADMIN', 'Administrador'),
        ('PRODUCAO', 'Produção'),
        ('FATURAMENTO', 'Faturamento'),
        ('FINANCEIRO', 'Financeiro'),
        ('LOGISTICA', 'Logística')
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    senha = db.Column(db.String(200), nullable=False)
    funcao = db.Column(db.String(20), nullable=False, default='PRODUCAO')
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Propriedade de compatibilidade para verificar se é admin
    @property
    def admin(self):
        return self.funcao == 'ADMIN'
    
    @admin.setter
    def admin(self, value):
        if value:
            self.funcao = 'ADMIN'
    
    def tem_permissao(self, funcao_requerida):
        """Verifica se o usuário tem a permissão necessária"""
        if not isinstance(funcao_requerida, str):
            return False
            
        if self.funcao.upper() == 'ADMIN':
            return True
            
        return self.funcao.upper() == funcao_requerida.upper()
    
    def get_funcao_display(self):
        """Retorna o nome amigável da função"""
        return dict(self.FUNCOES).get(self.funcao, self.funcao)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    # Relacionamentos
    vendas = db.relationship('Venda', backref='cliente', lazy=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco_compra = db.Column(db.Float, nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)
    estoque_atual = db.Column(db.Float, nullable=False, default=0)
    estoque_minimo = db.Column(db.Float, default=0)
    unidade_medida = db.Column(db.String(10), default='un')
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relacionamentos
    itens_venda = db.relationship('ItemVenda', backref='produto', lazy=True)

class Venda(db.Model):
    # Status possíveis para uma venda
    STATUS_VENDA = [
        ('rascunho', 'Rascunho'),
        ('pendente', 'Pendente'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada')
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valor_total = db.Column(db.Float, nullable=False, default=0)
    desconto = db.Column(db.Float, default=0)
    forma_pagamento = db.Column(db.String(50), nullable=False, default='dinheiro')
    status = db.Column(db.String(20), default='rascunho')  # rascunho, pendente, finalizada, cancelada
    data_pagamento = db.Column(db.DateTime, nullable=True)  # Data em que o pagamento foi confirmado
    data_cancelamento = db.Column(db.DateTime, nullable=True)  # Data em que a venda foi cancelada
    observacoes = db.Column(db.Text, nullable=True)  # Observações sobre a venda
    numero_cupom = db.Column(db.String(50), nullable=True)  # Número do cupom fiscal
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # Tornado opcional
    nome_cliente = db.Column(db.String(100), nullable=True)  # Nome do cliente para vendas sem cadastro
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    codigo_autenticacao = db.Column(db.String(20), unique=True, nullable=True)  # Código para validação do cupom
    
    # Relacionamentos
    itens = db.relationship('ItemVenda', backref='venda', lazy=True, cascade='all, delete-orphan')
    historico = db.relationship('HistoricoVenda', backref='venda', lazy=True, order_by='desc(HistoricoVenda.data_alteracao)')
    usuario = db.relationship('Usuario', backref='vendas')
    
    def calcular_total(self):
        """Calcula o valor total da venda com base nos itens"""
        total = sum(item.quantidade * item.preco_unitario for item in self.itens)
        self.valor_total = total - (total * (self.desconto / 100) if self.desconto else 0)
        return self.valor_total

    @property
    def nome_do_cliente(self):
        """Retorna o nome do cliente cadastrado ou o nome informado na venda"""
        if self.cliente_id:
            return self.cliente.nome
        return self.nome_cliente or 'Cliente não identificado'



class ItemVenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id', ondelete='CASCADE'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)  # Desconto percentual no item
    total = db.Column(db.Float, nullable=False)  # Valor total do item (quantidade * preco_unitario)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('venda_id', 'produto_id', name='uix_venda_produto'),
    )
    
    def __init__(self, **kwargs):
        super(ItemVenda, self).__init__(**kwargs)
        self.calcular_total()
    
    def calcular_total(self):
        """Calcula o valor total do item"""
        if self.quantidade is not None and self.preco_unitario is not None:
            subtotal = self.quantidade * self.preco_unitario
            if self.desconto:
                subtotal -= subtotal * (self.desconto / 100)
            self.total = subtotal
            return self.total
        return 0.0
    
    def atualizar_estoque(self, acao='adicionar'):
        """Atualiza o estoque do produto"""
        if not self.produto:
            return False
            
        try:
            if acao == 'adicionar':
                # Verifica se há estoque suficiente
                if self.produto.estoque_atual < self.quantidade:
                    return False
                self.produto.estoque_atual -= self.quantidade
            elif acao == 'remover':
                self.produto.estoque_atual += self.quantidade
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f'Erro ao atualizar estoque: {str(e)}')
            return False


class EstoqueDiario(db.Model):
    """
    Modelo para registrar o estoque diário de produtos
    Útil para gerar relatórios históricos de estoque
    """
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    valor_estoque = db.Column(db.Float, nullable=False)  # valor total em estoque (quantidade * preco_compra)
    
    # Campos adicionais para controle de movimentação
    entrada = db.Column(db.Float, default=0.0, nullable=False)  # Quantidade que entrou no estoque
    saida = db.Column(db.Float, default=0.0, nullable=False)    # Quantidade que saiu do estoque
    estoque_inicial = db.Column(db.Float, nullable=False)       # Estoque no início do dia
    estoque_final = db.Column(db.Float, nullable=False)         # Estoque no final do dia
    observacoes = db.Column(db.Text, nullable=True)             # Observações sobre o dia
    
    # Relacionamentos
    produto = db.relationship('Produto', backref='estoque_diario', lazy=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # Usuário que fechou o dia
    usuario = db.relationship('Usuario', backref='estoques_diarios')
    
    # Índice composto para melhorar consultas
    __table_args__ = (
        db.Index('idx_estoque_diario_data_produto', 'data', 'produto_id', unique=True),
    )
    
    def __repr__(self):
        return f"<EstoqueDiario {self.produto.nome} - {self.data} - {self.quantidade}>"


class HistoricoVenda(db.Model):
    """
    Modelo para registrar o histórico de alterações em vendas
    """
    __tablename__ = 'historico_venda'
    
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    data_alteracao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # Ex: 'criada', 'atualizada', 'finalizada', 'cancelada'
    observacao = db.Column(db.Text, nullable=True)  # Descrição da alteração
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='historicos_venda')
    
    def __repr__(self):
        return f"<HistoricoVenda {self.venda_id} - {self.status} - {self.data_alteracao}>"
