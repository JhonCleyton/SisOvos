from __init__ import create_app, db
from flask_migrate import Migrate, upgrade, migrate as migrate_db
import os

# Cria a aplicação
app = create_app()

# Configura o Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Cria a pasta de migrações se não existir
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            print("Criando pasta de migrações...")
            os.makedirs(migrations_dir, exist_ok=True)
            print("✅ Pasta de migrações criada com sucesso!")
        
        # Cria as migrações
        print("Criando migrações...")
        migrate_db(message='Initial migration')
        
        # Aplica as migrações
        print("Aplicando migrações...")
        upgrade()
        
        print("✅ Migrações aplicadas com sucesso!")
