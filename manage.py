import os
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand
from app import create_app, db
from models import Usuario

# Cria a aplicação
app = create_app()
manager = Manager(app)

def make_shell_context():
    return dict(app=app, db=db, Usuario=Usuario)

# Adiciona comandos do shell
manager.add_command("shell", Shell(make_context=make_shell_context))

# Adiciona comandos de migração
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
