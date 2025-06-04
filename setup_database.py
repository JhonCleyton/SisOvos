import os
import sys
import sqlite3
import time
from datetime import datetime, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from utils.auth_utils import get_password_hash

# Configuração básica do Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_ovos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Definição dos modelos
class Usuario(db.Model):
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
        if self.funcao == 'ADMIN':
            return True
        return self.funcao == funcao_requerida
    
    def get_funcao_display(self):
        """Retorna o nome amigável da função"""
        return dict(self.FUNCOES).get(self.funcao, self.funcao)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.String(200))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), default='Ovos', nullable=False)
    preco_venda = db.Column(db.Float, nullable=False, default=15.0)
    estoque_atual = db.Column(db.Float, default=0)
    estoque_minimo = db.Column(db.Float, default=10)
    unidade_medida = db.Column(db.String(10), default='un')
    ativo = db.Column(db.Boolean, default=True)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EstoqueDiario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow().date, unique=True)
    estoque_inicial = db.Column(db.Float, default=0)
    entrada = db.Column(db.Float, default=0)
    saida = db.Column(db.Float, default=0)
    estoque_final = db.Column(db.Float, default=0)
    observacoes = db.Column(db.Text)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    valor_total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='pendente')
    forma_pagamento = db.Column(db.String(50))
    observacoes = db.Column(db.Text)

class ItemVenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

def wait_for_database_lock(db_path, timeout=30):
    """Aguarda até que o banco de dados esteja desbloqueado ou o tempo limite seja atingido."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            # Tenta conectar ao banco de dados em modo exclusivo
            conn = sqlite3.connect(f'file:{db_path}?mode=rw', uri=True)
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                print("Banco de dados está bloqueado, aguardando...")
                time.sleep(1)
            else:
                print(f"Erro ao acessar o banco de dados: {e}")
                return False
    return False

def create_database():
    print("=== Configuração do Banco de Dados do SisOvos ===\n")
    
    # Definir caminhos
    db_dir = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'sistema_ovos.db')
    
    print(f"Local do banco de dados: {os.path.abspath(db_path)}")
    
    # Verificar se o banco de dados existe e fazer backup
    if os.path.exists(db_path):
        if not wait_for_database_lock(db_path):
            print("\nERRO: Não foi possível acessar o banco de dados. Verifique se o servidor está rodando.")
            return
            
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'sistema_ovos_backup_{timestamp}.db')
        
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"\nBackup do banco de dados criado em: {os.path.abspath(backup_path)}")
        except Exception as e:
            print(f"\nAVISO: Não foi possível criar backup do banco de dados: {e}")
    
    # Criar todas as tabelas
    print("\nCriando estrutura do banco de dados...")
    with app.app_context():
        try:
            # Remover todas as tabelas existentes
            db.drop_all()
            # Criar todas as tabelas
            db.create_all()
            
            print("Estrutura do banco de dados criada com sucesso!")
            
            # Criar usuários iniciais
            admin = Usuario(
                nome='Administrador',
                username='admin',
                email='admin@sisovos.com',
                telefone='(00) 0000-0000',
                senha=get_password_hash('admin123'),
                funcao='ADMIN',
                ativo=True
            )
            
            pardaro = Usuario(
                nome='Pardaro',
                username='pardaro',
                email='pardaro@example.com',
                telefone='(00) 0000-0001',
                senha=get_password_hash('pardaro123'),
                funcao='PRODUCAO',
                ativo=True
            )
            
            # Adicionar usuários ao banco de dados
            db.session.add(admin)
            db.session.add(pardaro)
            
            # Criar um produto de exemplo
            produto = Produto(
                nome='Ovos de Galinha',
                preco_venda=15.0,
                estoque_atual=1000,  # 1000 ovos
                estoque_minimo=100,   # Mínimo de 100 ovos
                unidade_medida='un',
                ativo=True
            )
            db.session.add(produto)
            
            # Criar um cliente de exemplo
            cliente = Cliente(
                nome='Cliente Padrão',
                telefone='(00) 0000-0000',
                email='cliente@exemplo.com',
                endereco='Endereço do cliente',
                ativo=True
            )
            db.session.add(cliente)
            
            # Criar um registro de estoque diário
            hoje = datetime.now(timezone.utc).date()
            estoque = EstoqueDiario(
                data=hoje,
                produto_id=produto.id,
                quantidade=1000,  # Estoque final
                valor_estoque=1000 * produto.preco_compra,
                estoque_inicial=0,
                entrada=1000,
                saida=0,
                estoque_final=1000,
                observacoes='Estoque inicial',
                usuario_id=admin.id
            )
            db.session.add(estoque)
            
            # Salvar todas as alterações
            db.session.commit()
            
            print("\n=== DADOS INICIAIS CRIADOS COM SUCESSO ===")
            print("\nUSUÁRIOS:")
            print(f"- admin (senha: admin123) - Administrador do sistema")
            print(f"- pardaro (senha: pardaro123) - Usuário padrão")
            
            print("\nPRODUTO PADRÃO:")
            print(f"- Nome: Ovos de Galinha")
            print(f"- Preço: R$ 15,00 (dúzia)")
            print(f"- Estoque: 1000 unidades")
            print(f"- Estoque mínimo: 100 unidades")
            
            print("\nCLIENTE PADRÃO:")
            print("- Nome: Cliente Padrão")
            print("- E-mail: cliente@exemplo.com")
            
            print("\nAgora você pode iniciar o servidor com: flask run")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nERRO ao criar o banco de dados: {e}")
            import traceback
            traceback.print_exc()
            return

if __name__ == '__main__':
    create_database()
