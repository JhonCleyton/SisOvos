from app import app, db, Usuario
from utils.auth_utils import get_password_hash

def init_db():
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        # Verificar se já existe um usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        
        if not admin:
            # Criar usuário admin padrão
            admin = Usuario(
                nome='Administrador',
                username='admin',
                email='admin@sisovos.com',
                senha=get_password_hash('admin123'),
                funcao='ADMIN'
            )
            db.session.add(admin)
            print("Usuário admin criado com sucesso!")
        
        # Verificar se já existe o usuário pardaro
        pardaro = Usuario.query.filter_by(username='pardaro').first()
        
        if not pardaro:
            # Criar usuário pardaro
            pardaro = Usuario(
                nome='Pardaro',
                username='pardaro',
                email='pardaro@example.com',
                senha=get_password_hash('pardaro123'),
                funcao='PRODUCAO'
            )
            db.session.add(pardaro)
            print("Usuário pardaro criado com sucesso!")
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
