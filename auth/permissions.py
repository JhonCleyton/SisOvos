from functools import wraps
from flask import abort, current_app
from flask_login import current_user

# Definição das permissões
class Permission:
    # Permissões de usuário
    VER_DASHBOARD = 0x01
    GERENCIAR_USUARIOS = 0x02
    
    # Permissões de clientes
    VER_CLIENTES = 0x10
    CRIAR_CLIENTE = 0x20
    EDITAR_CLIENTE = 0x40
    EXCLUIR_CLIENTE = 0x80
    
    # Permissões de produtos
    VER_PRODUTOS = 0x100
    CRIAR_PRODUTO = 0x200
    EDITAR_PRODUTO = 0x400
    EXCLUIR_PRODUTO = 0x800
    
    # Permissões de vendas
    VER_VENDAS = 0x1000
    CRIAR_VENDA = 0x2000
    CANCELAR_VENDA = 0x4000
    
    # Permissões de relatórios
    VER_RELATORIOS = 0x10000
    GERAR_RELATORIOS = 0x20000
    
    # Permissões de configuração
    CONFIGURACOES_GERAIS = 0x100000
    BACKUP_RESTORE = 0x200000

# Funções de usuário e suas permissões
ROLES = {
    'ADMIN': 0xFFFFFFFF,  # Tem todas as permissões
    'GERENTE': (
        Permission.VER_DASHBOARD |
        Permission.VER_CLIENTES |
        Permission.CRIAR_CLIENTE |
        Permission.EDITAR_CLIENTE |
        Permission.VER_PRODUTOS |
        Permission.CRIAR_PRODUTO |
        Permission.EDITAR_PRODUTO |
        Permission.VER_VENDAS |
        Permission.CRIAR_VENDA |
        Permission.VER_RELATORIOS |
        Permission.GERAR_RELATORIOS
    ),
    'VENDEDOR': (
        Permission.VER_DASHBOARD |
        Permission.VER_CLIENTES |
        Permission.CRIAR_CLIENTE |
        Permission.EDITAR_CLIENTE |
        Permission.VER_PRODUTOS |
        Permission.VER_VENDAS |
        Permission.CRIAR_VENDA
    ),
    'ESTOQUISTA': (
        Permission.VER_PRODUTOS |
        Permission.EDITAR_PRODUTO
    ),
    'VISITANTE': (
        Permission.VER_DASHBOARD
    )
}

def obter_permissoes(funcao):
    """Retorna as permissões para uma função de usuário"""
    return ROLES.get(funcao, 0)

def tem_permissao(usuario, permissao):
    """Verifica se um usuário tem uma determinada permissão"""
    if not usuario or not usuario.ativo:
        return False
    
    # Administradores têm todas as permissões
    if usuario.funcao == 'ADMIN':
        return True
    
    # Verifica se a função do usuário tem a permissão necessária
    permissoes = obter_permissoes(usuario.funcao)
    return (permissoes & permissao) == permissao

def permissao_requerida(permissao):
    """Decorador para verificar se o usuário tem uma permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            if not tem_permissao(current_user, permissao):
                abort(403)  # Forbidden
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorador para verificar se o usuário é administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.funcao != 'ADMIN':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def verificar_permissoes(usuario, permissoes_necessarias):
    """Verifica se o usuário tem todas as permissões necessárias"""
    if not usuario or not usuario.ativo:
        return False
    
    # Administradores têm todas as permissões
    if usuario.funcao == 'ADMIN':
        return True
    
    # Verifica se todas as permissões necessárias estão presentes
    permissoes_usuario = obter_permissoes(usuario.funcao)
    return all(permissoes_usuario & permissao == permissao 
              for permissao in permissoes_necessarias)

def obter_permissoes_por_modulo():
    """Retorna as permissões agrupadas por módulo"""
    return {
        'Usuários': {
            'VER_DASHBOARD': 'Acessar o painel',
            'GERENCIAR_USUARIOS': 'Gerenciar usuários',
        },
        'Clientes': {
            'VER_CLIENTES': 'Visualizar clientes',
            'CRIAR_CLIENTE': 'Criar cliente',
            'EDITAR_CLIENTE': 'Editar cliente',
            'EXCLUIR_CLIENTE': 'Excluir cliente',
        },
        'Produtos': {
            'VER_PRODUTOS': 'Visualizar produtos',
            'CRIAR_PRODUTO': 'Criar produto',
            'EDITAR_PRODUTO': 'Editar produto',
            'EXCLUIR_PRODUTO': 'Excluir produto',
        },
        'Vendas': {
            'VER_VENDAS': 'Visualizar vendas',
            'CRIAR_VENDA': 'Realizar venda',
            'CANCELAR_VENDA': 'Cancelar venda',
        },
        'Relatórios': {
            'VER_RELATORIOS': 'Visualizar relatórios',
            'GERAR_RELATORIOS': 'Gerar relatórios',
        },
        'Configurações': {
            'CONFIGURACOES_GERAIS': 'Configurações gerais',
            'BACKUP_RESTORE': 'Backup e restauração',
        }
    }

def obter_permissoes_para_formulario():
    """Retorna as permissões formatadas para uso em formulários"""
    permissoes = {}
    for modulo, mod_perms in obter_permissoes_por_modulo().items():
        permissoes[modulo] = [(f"Permission.{k}", v) for k, v in mod_perms.items()]
    return permissoes
