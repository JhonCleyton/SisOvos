from __init__ import create_app
from extensions import db
from models import Usuario, Cliente, Produto, Venda, ItemVenda, EstoqueDiario

def atualizar_banco_dados():
    """Atualiza a estrutura do banco de dados"""
    app = create_app()
    
    with app.app_context():
        # Cria todas as tabelas que ainda não existem
        db.create_all()
        
        # Verifica as colunas que precisam ser adicionadas
        from sqlalchemy import inspect, text
        
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('venda')]
        
        # Adiciona a coluna data_pagamento se não existir
        if 'data_pagamento' not in columns:
            print("Adicionando a coluna 'data_pagamento' à tabela 'venda'...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE venda ADD COLUMN data_pagamento DATETIME'))
                    conn.commit()
                print("✅ Coluna 'data_pagamento' adicionada com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao adicionar a coluna 'data_pagamento': {e}")
        else:
            print("ℹ️  A coluna 'data_pagamento' já existe na tabela 'venda'.")
        
        # Adiciona a coluna data_cancelamento se não existir
        if 'data_cancelamento' not in columns:
            print("Adicionando a coluna 'data_cancelamento' à tabela 'venda'...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE venda ADD COLUMN data_cancelamento DATETIME'))
                    conn.commit()
                print("✅ Coluna 'data_cancelamento' adicionada com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao adicionar a coluna 'data_cancelamento': {e}")
        else:
            print("ℹ️  A coluna 'data_cancelamento' já existe na tabela 'venda'.")
        
        print("✅ Estrutura do banco de dados verificada e atualizada com sucesso!")

if __name__ == '__main__':
    atualizar_banco_dados()
