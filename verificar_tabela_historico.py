"""
Script para verificar se a tabela historico_estoque existe no banco de dados.
"""
import sys
import os
from sqlalchemy import create_engine, inspect

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def verificar_tabela_historico():
    """Verifica se a tabela historico_estoque existe no banco de dados."""
    try:
        # Cria uma conexão com o banco de dados
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Cria um inspetor para examinar o banco de dados
        inspector = inspect(engine)
        
        # Obtém a lista de tabelas
        tabelas = inspector.get_table_names()
        
        print("\nTabelas no banco de dados:")
        for tabela in tabelas:
            print(f"- {tabela}")
        
        # Verifica se a tabela historico_estoque existe
        if 'historico_estoque' in tabelas:
            print("\n✅ A tabela 'historico_estoque' foi encontrada no banco de dados!")
            
            # Mostra as colunas da tabela
            colunas = inspector.get_columns('historico_estoque')
            print("\nColunas da tabela 'historico_estoque':")
            for coluna in colunas:
                print(f"- {coluna['name']} ({coluna['type']})")
            
            return True
        else:
            print("\n❌ A tabela 'historico_estoque' NÃO foi encontrada no banco de dados.")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao verificar a tabela: {str(e)}")
        return False

if __name__ == '__main__':
    verificar_tabela_historico()
