from functools import wraps
from flask import flash, redirect, url_for, request, abort
from flask_login import current_user

def permissao_necessaria(*funcoes_permitidas):
    """
    Decorator para verificar se o usuário tem permissão para acessar uma rota
    baseado em suas funções.
    
    Args:
        *funcoes_permitidas: Lista de funções que têm permissão para acessar a rota.
                          Se vazio, apenas o admin tem acesso.
    """
    def decorator(f):
        @wraps(f)
        def funcao_decorada(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
                
            # Admin tem acesso total
            if current_user.funcao == 'ADMIN':
                return f(*args, **kwargs)
                
            # Se não há funções específicas definidas, apenas admin tem acesso
            if not funcoes_permitidas:
                flash('Acesso restrito ao administrador.', 'danger')
                return redirect(url_for('main.dashboard'))
                
            # Verifica se o usuário tem alguma das funções permitidas
            if current_user.funcao not in funcoes_permitidas:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('main.dashboard'))
                
            return f(*args, **kwargs)
        return funcao_decorada
    return decorator

def admin_required(f):
    """Decorator que requer privilégios de administrador"""
    return permissao_necessaria('ADMIN')(f)

def producao_required(f):
    """Decorator que requer privilégios de produção"""
    return permissao_necessaria('PRODUCAO')(f)

def faturamento_required(f):
    """Decorator que requer privilégios de faturamento"""
    return permissao_necessaria('FATURAMENTO')(f)

def financeiro_required(f):
    """Decorator que requer privilégios financeiros"""
    return permissao_necessaria('FINANCEIRO')(f)

def logistica_required(f):
    """Decorator que requer privilégios de logística"""
    return permissao_necessaria('LOGISTICA')(f)
