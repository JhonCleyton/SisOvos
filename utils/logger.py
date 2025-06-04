import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def configure_logger(app):
    """Configura o sistema de logs da aplicação"""
    # Cria a pasta de logs se não existir
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Formato dos logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Nível de log baseado nas configurações
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    
    # Configura o logger principal
    logger = logging.getLogger('sisovos')
    logger.setLevel(log_level)
    
    # Remove handlers existentes
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Handler para arquivo de log
    log_file = os.path.join(log_dir, f'sisovos_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10240, backupCount=10, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Handler para console (apenas em desenvolvimento)
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    
    logger.addHandler(file_handler)
    logger.propagate = False
    
    # Configura o logger do SQLAlchemy
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.WARNING)
    
    # Configura o logger do Werkzeug
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    
    return logger

def log_activity(action, user_id=None, details=None, ip_address=None):
    """Registra uma atividade do usuário"""
    from flask import request, current_app
    import json
    
    logger = logging.getLogger('sisovos.activity')
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
        'ip_address': ip_address or request.remote_addr,
        'user_agent': request.user_agent.string if request else None,
        'details': details
    }
    
    logger.info(json.dumps(log_data, ensure_ascii=False))

def log_error(error, extra=None):
    """Registra um erro no log"""
    from flask import request
    import traceback
    import sys
    
    logger = logging.getLogger('sisovos.error')
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    error_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'error': str(error),
        'type': error.__class__.__name__,
        'stack_trace': stack_trace,
        'request_url': request.url if request else None,
        'request_method': request.method if request else None,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request and hasattr(request, 'user_agent') else None,
        'extra': extra
    }
    
    logger.error(error_data)
