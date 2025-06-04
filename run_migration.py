from __init__ import create_app, db, migrate
from flask_migrate import upgrade, MigrateCommand, Manager
import os

# Cria a aplicação
app = create_app()

# Configura o gerenciador de comandos
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    with app.app_context():
        # Cria o diretório de migrações se não existir
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            os.makedirs(migrations_dir)
            print("✅ Diretório de migrações criado.")
        
        # Tenta aplicar as migrações
        try:
            upgrade()
            print("✅ Migrações aplicadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao aplicar migrações: {e}")
            print("Tentando inicializar o sistema de migração...")
            try:
                os.system("flask db init")
                os.system("flask db migrate -m 'Initial migration'")
                os.system("flask db upgrade")
                print("✅ Migrações aplicadas com sucesso após inicialização!")
            except Exception as e2:
                print(f"❌ Erro ao inicializar migrações: {e2}")
