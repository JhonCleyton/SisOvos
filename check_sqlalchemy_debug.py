from app import create_app, db
import os

app = create_app()

with app.app_context():
    # Verifica as configurações do SQLAlchemy
    print("SQLALCHEMY_DATABASE_URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))
    print("SQLALCHEMY_TRACK_MODIFICATIONS:", app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS'))
    print("SQLALCHEMY_ECHO:", app.config.get('SQLALCHEMY_ECHO'))
    
    # Verifica se o arquivo do banco de dados existe
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'sistema_ovos.db')
    print("\nCaminho do banco de dados:", db_path)
    print("Banco de dados existe:", os.path.exists(db_path))
