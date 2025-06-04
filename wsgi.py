import os
import sys

# Obtém o diretório do projeto
project_dir = os.path.dirname(os.path.abspath(__file__))

# Adiciona o diretório do projeto ao path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Configura o ambiente
os.environ['FLASK_APP'] = 'wsgi.py'
os.environ['FLASK_ENV'] = 'development'

def create_app():
    """Cria e configura a aplicação Flask"""
    from __init__ import create_app
    return create_app()

# Cria a aplicação
app = create_app()

if __name__ == "__main__":
    # Importa o db aqui para evitar importação circular
    from extensions import db
    
    # Cria as tabelas do banco de dados se não existirem
    with app.app_context():
        db.create_all()
    
    # Inicia o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
