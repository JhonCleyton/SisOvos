from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os

def main():
    # Cria o aplicativo Flask
    app = Flask(__name__)
    
    # Configuração do banco de dados
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'sisovos.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializa o SQLAlchemy
    db = SQLAlchemy(app)
    
    # Define o modelo Venda para uso no script
    class Venda(db.Model):
        __tablename__ = 'venda'
        id = db.Column(db.Integer, primary_key=True)
        data_venda = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        valor_total = db.Column(db.Float, nullable=False, default=0)
        desconto = db.Column(db.Float, default=0)
        forma_pagamento = db.Column(db.String(50), nullable=False)
        status = db.Column(db.String(20), default='pendente')
        data_pagamento = db.Column(db.DateTime, nullable=True)
        data_cancelamento = db.Column(db.DateTime, nullable=True)
        observacoes = db.Column(db.Text, nullable=True)
        numero_cupom = db.Column(db.String(50), nullable=True)
        cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
        nome_cliente = db.Column(db.String(100), nullable=True)
        usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Define o modelo Cliente para uso no script
    class Cliente(db.Model):
        __tablename__ = 'cliente'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=True)
        telefone = db.Column(db.String(20), nullable=True)
        endereco = db.Column(db.Text, nullable=True)
        data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
        ativo = db.Column(db.Boolean, default=True)
    
    # Cria um contexto de aplicativo
    with app.app_context():
        # Verifica se a coluna já existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('venda')]
        
        if 'nome_cliente' not in columns:
            print("Adicionando coluna 'nome_cliente' à tabela 'venda'...")
            
            try:
                # Adiciona a coluna usando text() para executar SQL bruto
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE venda ADD COLUMN nome_cliente VARCHAR(100)'))
                    conn.commit()
                print("Coluna 'nome_cliente' adicionada com sucesso.")
                
                # Atualiza os registros existentes com o nome do cliente
                vendas = Venda.query.all()
                print(f"Atualizando {len(vendas)} registros de venda...")
                
                for venda in vendas:
                    if venda.cliente_id:
                        cliente = Cliente.query.get(venda.cliente_id)
                        if cliente:
                            venda.nome_cliente = cliente.nome
                
                # Salva as alterações
                db.session.commit()
                print("Registros atualizados com sucesso.")
                
            except Exception as e:
                print(f"Erro ao adicionar a coluna 'nome_cliente': {e}")
                db.session.rollback()
        else:
            print("A coluna 'nome_cliente' já existe na tabela 'venda'.")

if __name__ == '__main__':
    main()
