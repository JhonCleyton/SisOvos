"""
Script para listar todas as tabelas no banco de dados.
"""
import sys
import os
from sqlalchemy import create_engine, inspect

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def listar_tabelas():
    """Lista todas as tabelas no banco de dados."""
    # Cria uma conexão com o banco de dados
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Cria um inspetor para examinar o banco de dados
    inspector = inspect(engine)
    
    # Obtém a lista de tabelas
    tabelas = inspector.get_table_names()
    
    print("Tabelas no banco de dados:")
    for tabela in tabelas:
        print(f"- {tabela}")
    
    # Verifica se a tabela historico_estoque existe
    if 'historico_estoque' in tabelas:
        print("\nA tabela 'historico_estoque' foi encontrada no banco de dados!")
    else:
        print("\nA tabela 'historico_estoque' NÃO foi encontrada no banco de dados.")

if __name__ == '__main__':
    listar_tabelas()
