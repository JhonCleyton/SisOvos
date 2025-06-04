from __init__ import create_app, db
from sqlalchemy import inspect

# Cria a aplicação
app = create_app()

with app.app_context():
    # Obtém o inspetor do banco de dados
    inspector = inspect(db.engine)
    
    # Lista todas as tabelas
    tables = inspector.get_table_names()
    
    print("\nTabelas no banco de dados:")
    print("-" * 30)
    for table in sorted(tables):
        print(f"- {table}")
    
    # Verifica se a tabela historico_venda existe
    if 'historico_venda' in tables:
        print("\n✅ Tabela 'historico_venda' encontrada!")
        
        # Mostra as colunas da tabela historico_venda
        print("\nColunas da tabela 'historico_venda':")
        print("-" * 40)
        columns = inspector.get_columns('historico_venda')
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
    else:
        print("\n❌ Tabela 'historico_venda' NÃO encontrada!")
