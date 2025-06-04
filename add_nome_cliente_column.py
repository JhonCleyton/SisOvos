import sqlite3
import os

def add_nome_cliente_column():
    # Caminho para o banco de dados SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'sistema_ovos.db')
    backup_path = db_path + '.backup'
    
    # Cria um backup do banco de dados
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"✅ Backup do banco de dados criado em: {backup_path}")
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível criar o backup: {e}")
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(venda)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'nome_cliente' in column_names:
            print("✅ A coluna 'nome_cliente' já existe na tabela 'venda'.")
            return
            
        # Adiciona a coluna nome_cliente
        print("Adicionando a coluna 'nome_cliente' à tabela 'venda'...")
        cursor.execute("ALTER TABLE venda ADD COLUMN nome_cliente VARCHAR(100)")
        
        # Atualiza os registros existentes com o nome do cliente
        print("Atualizando registros existentes...")
        cursor.execute("""
            UPDATE venda 
            SET nome_cliente = (SELECT nome FROM cliente WHERE id = venda.cliente_id)
            WHERE cliente_id IS NOT NULL
        """)
        
        # Confirma as alterações
        conn.commit()
        print("✅ Coluna 'nome_cliente' adicionada e registros atualizados com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao modificar a tabela: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_nome_cliente_column()
