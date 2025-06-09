"""
Script para verificar a estrutura da tabela historico_estoque.
"""
import sys
import os
from sqlalchemy import create_engine, inspect

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_estrutura_historico():
    """Verifica a estrutura da tabela historico_estoque."""
    try:
        # Usa o caminho correto para o banco de dados
        db_path = os.path.join('instance', 'sisovos.db')
        db_uri = f'sqlite:///{os.path.abspath(db_path)}'
        print(f"Conectando ao banco de dados em: {db_uri}")
        
        # Cria uma conexão com o banco de dados
        engine = create_engine(db_uri)
        
        # Cria um inspetor para examinar o banco de dados
        inspector = inspect(engine)
        
        # Verifica se a tabela existe
        if 'historico_estoque' not in inspector.get_table_names():
            print("❌ A tabela 'historico_estoque' não foi encontrada no banco de dados.")
            return False
        
        print("✅ Tabela 'historico_estoque' encontrada no banco de dados.")
        
        # Obtém as colunas da tabela
        colunas = inspector.get_columns('historico_estoque')
        
        print("\nEstrutura da tabela 'historico_estoque':")
        for coluna in colunas:
            print(f"- {coluna['name']}: {coluna['type']} {'(PK)' if coluna.get('primary_key') else ''} {'(Nullable)' if coluna.get('nullable') else '(Not Null)'}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar a estrutura da tabela: {str(e)}")
        return False

if __name__ == '__main__':
    verificar_estrutura_historico()
