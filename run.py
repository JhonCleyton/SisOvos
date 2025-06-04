from __init__ import create_app, db
from models import Usuario
from utils.auth_utils import get_password_hash
import os

def criar_usuario_admin():
    """Cria um usuário admin se não existir"""
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(
            nome='Administrador',
            username='admin',
            email='admin@sisovos.com',
            telefone='(00) 0000-0000',
            senha=get_password_hash('admin123'),
            funcao='ADMIN',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Usuário admin criado com sucesso!')
    return admin

def criar_estrutura_inicial():
    """Cria a estrutura inicial do banco de dados"""
    # Cria as tabelas
    db.create_all()
    
    # Cria o usuário admin
    criar_usuario_admin()
    
    # Adicione aqui outras inicializações necessárias
    print('✅ Estrutura do banco de dados criada com sucesso!')

if __name__ == '__main__':
    # Cria a aplicação
    app = create_app()
    
    with app.app_context():
        # Cria a estrutura inicial do banco de dados
        criar_estrutura_inicial()
    
    # Inicia o servidor
    print('🚀 Servidor rodando em http://0.0.0.0:7000')
    app.run(host='0.0.0.0', port=7000, debug=app.config['DEBUG'])
