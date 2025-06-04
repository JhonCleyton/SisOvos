from app import app, db
from flask_migrate import Migrate

# Inicializa o Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        print("Inicializando o diretório de migrações...")
        import os
        if not os.path.exists('migrations'):
            os.system('flask db init')
    elif len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        print("Criando migração...")
        os.system('flask db migrate -m "Atualização do banco de dados"')
    elif len(sys.argv) > 1 and sys.argv[1] == 'upgrade':
        print("Aplicando migração...")
        os.system('flask db upgrade')
    else:
        print("Uso: python run_migrate.py [init|migrate|upgrade]")
