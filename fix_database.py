import os
import sys
import sqlite3
from datetime import datetime

# Adiciona o diretório atual ao path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Importa os modelos após configurar o path
from app import app, db
from models import Usuario, Produto, Cliente, Venda, ItemVenda, EstoqueDiario

def backup_database():
    """Faz backup do banco de dados atual"""
    db_file = 'sistema_ovos.db'
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'{db_file}.backup_{timestamp}'
        with open(db_file, 'rb') as src, open(backup_name, 'wb') as dst:
            dst.write(src.read())
        print(f'Backup criado: {backup_name}')
        return True
    return False

def migrate_data(old_conn, new_conn):
    """Migra os dados do banco antigo para o novo"""
    try:
        cursor = new_conn.cursor()
        
        # Tabela de usuários
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO usuario (id, nome, username, email, senha, admin, ativo)
                SELECT id, nome, email, email, senha, admin, 1 as ativo 
                FROM usuario
            """)
        
        # Tabela de clientes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cliente'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO cliente (id, nome, telefone, email, endereco, data_cadastro, ativo)
                SELECT id, nome, telefone, email, endereco, data_cadastro, ativo 
                FROM cliente
            """)
        
        # Tabela de produtos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produto'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO produto (
                    id, nome, preco_venda, estoque_atual, ativo, 
                    data_atualizacao, estoque_minimo, unidade_medida
                )
                SELECT 
                    id, nome, preco_venda, estoque_atual, ativo, 
                    data_atualizacao, 
                    COALESCE(estoque_minimo, 10) as estoque_minimo,
                    COALESCE(unidade_medida, 'un') as unidade_medida
                FROM produto
            """)
        
        # Tabela de vendas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='venda'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO venda (
                    id, data_venda, cliente_id, valor_total, status, 
                    forma_pagamento, observacoes
                )
                SELECT 
                    id, data_venda, cliente_id, valor_total, status, 
                    forma_pagamento, observacoes
                FROM venda
            """)
        
        # Tabela de itens de venda
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item_venda'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO item_venda (
                    id, venda_id, produto_id, quantidade, preco_unitario, subtotal
                )
                SELECT 
                    id, venda_id, produto_id, quantidade, preco_unitario, subtotal
                FROM item_venda
            """)
        
        # Tabela de estoque diário
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estoque_diario'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO estoque_diario (
                    id, data, estoque_inicial, entrada, saida, 
                    estoque_final, observacoes
                )
                SELECT 
                    id, data, estoque_inicial, entrada, saida, 
                    estoque_final, observacoes
                FROM estoque_diario
            """)
        
        new_conn.commit()
        print("Dados migrados com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao migrar dados: {e}")
        new_conn.rollback()
        import traceback
        traceback.print_exc()
        return False

def recreate_database():
    """Recria o banco de dados com a estrutura correta"""
    print("Criando backup do banco de dados atual...")
    backup_created = backup_database()
    
    if not backup_created:
        print("Nenhum banco de dados encontrado para backup. Continuando...")
    
    # Cria o diretório instance se não existir
    os.makedirs('instance', exist_ok=True)
    
    # Remove o banco de dados existente
    db_file = 'instance/sisovos.db'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f'Arquivo {db_file} removido com sucesso.')
        except PermissionError as e:
            print(f'Erro ao remover o arquivo {db_file}: {e}')
            print('Certifique-se de que nenhum outro processo está usando o banco de dados.')
            return
    
    # Cria as tabelas
    with app.app_context():
        db.create_all()
        print('Banco de dados recriado com sucesso.')
        
        # Adiciona um usuário admin padrão se não existir
        if not Usuario.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = Usuario(
                nome='Administrador',
                username='admin',
                email='admin@example.com',
                senha=generate_password_hash('admin123'),
                admin=True,
                ativo=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Usuário admin criado com sucesso.')
    
    print('Banco de dados configurado com sucesso!')

if __name__ == '__main__':
    recreate_database()