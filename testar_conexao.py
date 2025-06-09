"""
Script para testar a conexão com o banco de dados e listar as tabelas existentes.
"""
import sys
import os
from sqlalchemy import create_engine, inspect

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def testar_conexao():
    """Testa a conexão com o banco de dados e lista as tabelas."""
    try:
        # Usa o caminho correto para o banco de dados
        db_path = os.path.join('instance', 'sisovos.db')
        db_uri = f'sqlite:///{os.path.abspath(db_path)}'
        print(f"Conectando ao banco de dados em: {db_uri}")
        
        # Cria uma conexão com o banco de dados
        engine = create_engine(db_uri)
        
        # Testa a conexão
        with engine.connect() as conn:
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
            
            # Lista as tabelas existentes
            inspector = inspect(engine)
            tabelas = inspector.get_table_names()
            
            print("\nTabelas no banco de dados:")
            if tabelas:
                for tabela in tabelas:
                    print(f"- {tabela}")
            else:
                print("Nenhuma tabela encontrada no banco de dados.")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao banco de dados: {str(e)}")
        return False

if __name__ == '__main__':
    testar_conexao()
