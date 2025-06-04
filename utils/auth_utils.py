from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

def get_password_hash(password):
    """Gera um hash seguro para a senha"""
    return generate_password_hash(
        password,
        method=current_app.config.get('PASSWORD_HASH_METHOD', 'sha256'),
        salt_length=8
    )

def check_password(hashed_password, password):
    """Verifica se a senha corresponde ao hash armazenado"""
    try:
        if not hashed_password or not password:
            return False
            
        from werkzeug.security import check_password_hash
        
        # Se o hash já começa com 'sha256$', verifica normalmente
        if hashed_password.startswith('sha256$'):
            return check_password_hash(hashed_password, password)
        # Se for um hash do tipo pbkdf2, verifica normalmente
        elif hashed_password.startswith('pbkdf2:'):
            return check_password_hash(hashed_password, password)
        else:
            # Se não tiver prefixo, tenta adicionar o prefixo sha256$
            return check_password_hash(f'sha256${hashed_password}', password) or \
                   check_password_hash(hashed_password, password)
            
    except Exception as e:
        import traceback
        current_app.logger.error(f"Erro ao verificar senha: {str(e)}")
        current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return False
