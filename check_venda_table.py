import sys
import os
from sqlalchemy import inspect

# Adiciona o diretório pai ao path para permitir importações corretas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    # Obtém o inspetor do banco de dados
    inspector = inspect(db.engine)
    
    # Verifica se a tabela venda existe
    if 'venda' in inspector.get_table_names():
        print("\nTabela 'venda' encontrada!")
        
        # Mostra as colunas da tabela venda
        print("\nColunas da tabela 'venda':")
        print("-" * 40)
        columns = inspector.get_columns('venda')
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
    else:
        print("\n❌ Tabela 'venda' NÃO encontrada!")
