from app import create_app, db
from models import Venda

app = create_app()

with app.app_context():
    # Verifica se a coluna já existe
    inspector = db.inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('venda')]
    
    if 'codigo_autenticacao' not in columns:
        print("Aplicando migração: Adicionando coluna codigo_autenticacao à tabela venda")
        # Adiciona a coluna
        db.engine.execute('ALTER TABLE venda ADD COLUMN codigo_autenticacao VARCHAR(20) UNIQUE')
        print("Migração aplicada com sucesso!")
    else:
        print("A coluna codigo_autenticacao já existe na tabela venda")
