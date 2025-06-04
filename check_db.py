import sqlite3
import sys

def check_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tabelas no banco de dados {db_path}:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Se a tabela estoque_diario existir, mostra sua estrutura
        if any('estoque_diario' in table for table in tables):
            print("\nEstrutura da tabela 'estoque_diario':")
            cursor.execute("PRAGMA table_info(estoque_diario);")
            columns = cursor.fetchall()
            for column in columns:
                print(f"- {column[1]} ({column[2]})")
        
        conn.close()
    except Exception as e:
        print(f"Erro ao acessar o banco de dados: {e}")

if __name__ == "__main__":
    # Verifica ambos os bancos de dados
    print("Verificando banco de dados principal...")
    check_database("sistema_ovos.db")
    
    print("\nVerificando banco de dados na pasta instance...")
    check_database("instance/sisovos.db")
