from functools import wraps
from flask import flash, redirect, url_for, request, current_app
from flask_login import current_user

def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.funcao != 'ADMIN':
            flash('Acesso restrito a administradores.', 'warning')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def permissao_requerida(*funcoes):
    """Decorator para verificar se o usuário tem alguma das funções especificadas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
                
            if current_user.funcao not in funcoes and current_user.funcao != 'ADMIN':
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('main.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def carregar_usuario(user_id):
    """Função para carregar um usuário a partir do ID"""
    from models import Usuario
    return Usuario.query.get(int(user_id))

def verificar_senha(senha_digitada, senha_hash):
    """Verifica se a senha digitada corresponde ao hash armazenado"""
    from werkzeug.security import check_password_hash
    return check_password_hash(senha_hash, senha_digitada)

def gerar_token_redefinicao(usuario):
    """Gera um token para redefinição de senha"""
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(usuario.email, salt='redefinir-senha')

def verificar_token_redefinicao(token, max_age=3600):
    """Verifica se o token de redefinição é válido"""
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = serializer.loads(
            token,
            salt='redefinir-senha',
            max_age=max_age
        )
    except (SignatureExpired, BadSignature):
        return None
        
    from models import Usuario
    return Usuario.query.filter_by(email=email).first()
