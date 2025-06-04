from __init__ import create_app, db
from flask_migrate import Migrate, current

# Cria a aplicação
app = create_app()

# Configura o Flask-Migrate
migrate = Migrate(app, db)

with app.app_context():
    # Obtém o diretório de migrações
    directory = migrate.directory
    
    # Verifica o status das migrações
    config = migrate.get_config(directory)
    script = migrate.migration_lister(directory)()
    
    # Obtém a versão atual do banco de dados
    current_rev = current(config, directory)
    
    print(f"Versão atual do banco de dados: {current_rev or 'Nenhuma'}")
    
    # Lista todas as migrações disponíveis
    print("\nMigrações disponíveis:")
    for script in script.walk_revisions():
        print(f"- {script.revision}: {script.doc}")
    
    # Verifica se há migrações pendentes
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    
    context = MigrationContext.configure(db.engine.connect())
    script_dir = ScriptDirectory.from_config(config)
    
    # Verifica se há migrações pendentes
    current_rev = context.get_current_revision()
    head_rev = script_dir.get_heads()[0]
    
    if current_rev != head_rev:
        print(f"\n⚠️  Há migrações pendentes!")
        print(f"Versão atual: {current_rev}")
        print(f"Versão mais recente: {head_rev}")
    else:
        print("\n✅ O banco de dados está atualizado!")
