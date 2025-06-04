from __init__ import create_app, db
from models import HistoricoVenda

# Cria a aplicação
app = create_app()

with app.app_context():
    try:
        # Cria todas as tabelas que ainda não existem
        print("Criando tabelas...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verifica se a tabela historico_venda foi criada
        inspector = db.inspect(db.engine)
        if 'historico_venda' in inspector.get_table_names():
            print("\n✅ Tabela 'historico_venda' criada com sucesso!")
            
            # Mostra as colunas da tabela
            columns = inspector.get_columns('historico_venda')
            print("\nColunas da tabela 'historico_venda':")
            print("-" * 40)
            for column in columns:
                print(f"- {column['name']} ({column['type']}" + 
                      (f"({column['type'].length})" if hasattr(column['type'], 'length') else "") + 
                      ")")
        else:
            print("\n❌ Erro ao criar a tabela 'historico_venda'")
            
    except Exception as e:
        print(f"\n❌ Erro ao criar as tabelas: {str(e)}")
