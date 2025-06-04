import os
import sys
from flask import Flask, request

# Obtém o diretório do projeto
project_dir = os.path.dirname(os.path.abspath(__file__))

# Adiciona o diretório do projeto ao path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Importa as extensões
from extensions import db, login_manager, mail, migrate, csrf

# Importa as configurações
try:
    from config import config
except ImportError as e:
    print(f"Erro ao importar config: {e}")
    # Tenta importar de .config se a importação direta falhar
    try:
        from .config import config
    except ImportError as e:
        print(f"Erro ao importar .config: {e}")
        # Tenta importar diretamente
        import config
        config = config.config

# Exporta as extensões para uso em outros módulos
__all__ = ['db', 'login_manager', 'mail', 'migrate', 'csrf', 'create_app']

def create_app(config_name='development'):
    """Cria e configura a aplicação Flask"""
    app = Flask(__name__)
    
    # Carrega as configurações padrão
    app.config.from_object(config[config_name])
    
    # Carrega as configurações do arquivo .env se existir
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configurações específicas para o ambiente
    if config_name == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['SQLALCHEMY_ECHO'] = False
    elif config_name == 'testing':
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:  # development
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
        app.config['SQLALCHEMY_ECHO'] = True
    
    # Configura as extensões
    configure_extensions(app)
    
    # Configura o Flask-Migrate
    from extensions import migrate
    migrate.init_app(app, db)
    
    # Configura os blueprints
    configure_blueprints(app)
    
    # Adiciona o contexto de permissões aos templates
    from permissions import has_permission
    
    @app.context_processor
    def inject_permissions():
        return dict(has_permission=has_permission)
    
    # Configura os filtros de template
    configure_template_filters(app)
    
    # Configura os manipuladores de erro
    configure_error_handlers(app)
    
    # Configura os comandos do CLI
    configure_cli_commands(app)
    
    return app

def configure_extensions(app):
    """Configura as extensões do Flask"""
    # Inicializa as extensões
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configura o carregador de usuário
    from models import Usuario
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

def configure_blueprints(app):
    """Registra os blueprints da aplicação"""
    from routes import main_bp
    from routes.relatorios import bp as relatorios_bp
    from routes.admin import bp as admin_bp
    from routes.configuracoes import configuracoes_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(configuracoes_bp, url_prefix='/configuracoes')

def configure_template_filters(app):
    """Configura os filtros de template e contextos globais"""
    from datetime import datetime
    
    # Adiciona a data/hora atual a todos os templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None:
            return 'R$ 0,00'
        return f'R$ {value:,.2f}'.replace('.', 'v').replace(',', '.').replace('v', ',')
    
    @app.template_filter('format_date')
    def format_date(value, format='%d/%m/%Y'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        if value is None:
            return ''
        if isinstance(value, str):
            # Tenta converter a string para datetime se necessário
            try:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except (ValueError, TypeError):
                try:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    return value  # Retorna o valor original se não for possível converter
        
        # Formata a data de acordo com o formato especificado
        try:
            return value.strftime(format)
        except (AttributeError, ValueError):
            return value  # Retorna o valor original se não for possível formatar

def configure_error_handlers(app):
    """Configura os manipuladores de erro"""
    from flask import render_template, jsonify
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Acesso proibido'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Página não encontrada'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Erro interno do servidor'}), 500
        return render_template('errors/500.html'), 500

def configure_cli_commands(app):
    """Configura os comandos do CLI"""
    @app.cli.command('create-admin')
    def create_admin():
        """Cria um usuário administrador"""
        from models import Usuario, db
        from utils.auth_utils import get_password_hash
        
        nome = input('Nome: ')
        email = input('E-mail: ')
        senha = input('Senha: ')
        
        admin = Usuario(
            nome=nome,
            username=email.split('@')[0],
            email=email,
            senha=get_password_hash(senha),
            funcao='ADMIN',
            ativo=True
        )
        
        db.session.add(admin)
        db.session.commit()
        print('✅ Usuário administrador criado com sucesso!')
