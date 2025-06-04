import sqlite3
import os

def check_venda_table():
    # Caminho para o banco de dados SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'sistema_ovos.db')
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtém informações sobre a tabela venda
        cursor.execute("PRAGMA table_info(venda)")
        columns = cursor.fetchall()
        
        if columns:
            print("\nColunas da tabela 'venda':")
            print("-" * 40)
            for column in columns:
                print(f"- {column[1]} ({column[2]})")
        else:
            print("❌ Tabela 'venda' não encontrada ou sem colunas.")
            
        # Verifica se a coluna nome_cliente existe
        column_names = [col[1] for col in columns]
        if 'nome_cliente' in column_names:
            print("\n✅ A coluna 'nome_cliente' já existe na tabela 'venda'.")
        else:
            print("\n❌ A coluna 'nome_cliente' NÃO existe na tabela 'venda'.")
            
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_venda_table()
