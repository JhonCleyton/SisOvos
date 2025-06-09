"""
Configuração de permissões do sistema.
Define quais funções têm acesso a quais rotas.
"""

# Permissões para cada rota
# Cada chave é o nome da função da rota e o valor é uma lista de funções permitidas
PERMISSIONS = {
    # Rotas de Dashboard
    'main.dashboard': ['ADMIN', 'PRODUCAO', 'FATURAMENTO', 'FINANCEIRO', 'LOGISTICA'],
    
    # Rotas de Usuários (apenas admin)
    'main.listar_usuarios': ['ADMIN'],
    'main.novo_usuario': ['ADMIN'],
    'main.editar_usuario': ['ADMIN'],
    'main.alterar_status_usuario': ['ADMIN'],
    'main.excluir_usuario': ['ADMIN'],
    
    # Rotas de Produtos (admin e produção)
    'main.listar_produtos': ['ADMIN', 'PRODUCAO'],
    'main.novo_produto': ['ADMIN', 'PRODUCAO'],
    'main.editar_produto': ['ADMIN', 'PRODUCAO'],
    'main.excluir_produto': ['ADMIN', 'PRODUCAO'],
    'main.alterar_status_produto': ['ADMIN', 'PRODUCAO'],
    'main.visualizar_produto': ['ADMIN', 'PRODUCAO'],
    'main.estoque_diario': ['ADMIN', 'PRODUCAO'],
    
    # Rotas de Vendas (admin, faturamento e financeiro)
    'main.listar_vendas': ['ADMIN', 'FATURAMENTO', 'FINANCEIRO', 'LOGISTICA'],
    'main.nova_venda': ['ADMIN', 'FATURAMENTO'],
    'main.visualizar_venda': ['ADMIN', 'FATURAMENTO', 'FINANCEIRO', 'LOGISTICA'],
    'main.cancelar_venda': ['ADMIN', 'FATURAMENTO'],
    'main.finalizar_venda': ['ADMIN', 'FATURAMENTO'],
    'main.editar_venda': ['ADMIN', 'FATURAMENTO', 'FINANCEIRO'],
    
    # Rotas Financeiras (admin e financeiro)
    'main.aprovar_pagamento': ['ADMIN', 'FINANCEIRO'],
    
    # Rotas de Clientes (admin, faturamento e logística)
    'main.listar_clientes': ['ADMIN', 'FATURAMENTO', 'LOGISTICA'],
    'main.novo_cliente': ['ADMIN', 'FATURAMENTO'],
    'main.editar_cliente': ['ADMIN', 'FATURAMENTO'],
    'main.excluir_cliente': ['ADMIN', 'FATURAMENTO'],
    'main.visualizar_cliente': ['ADMIN', 'FATURAMENTO', 'LOGISTICA'],
    
    # Rotas do Painel de Controle Administrativo
    'admin.painel_controle': ['ADMIN'],
    
    # Rotas de Relatórios
    'relatorios.relatorio_financeiro': ['ADMIN', 'FINANCEIRO'],
    'relatorios.exportar_relatorio_financeiro': ['ADMIN', 'FINANCEIRO'],
    'relatorios.relatorio_estoque': ['ADMIN', 'PRODUCAO'],
    'relatorios.exportar_relatorio_estoque': ['ADMIN', 'PRODUCAO'],
    
    # Rotas de Ajuda (todos os usuários autenticados)
    'main.ajuda': ['ADMIN', 'PRODUCAO', 'FATURAMENTO', 'FINANCEIRO', 'LOGISTICA'],
    'main.contato': ['ADMIN', 'PRODUCAO', 'FATURAMENTO', 'FINANCEIRO', 'LOGISTICA'],
    
    # Rotas de Configurações (apenas admin)
    'configuracoes.sistema': ['ADMIN'],
    'configuracoes.seguranca': ['ADMIN'],
    'configuracoes.backup': ['ADMIN'],
    'configuracoes.gerar_backup': ['ADMIN'],
    'configuracoes.baixar_backup': ['ADMIN'],
    'configuracoes.excluir_backup': ['ADMIN'],
    'configuracoes.salvar_configuracoes_backup': ['ADMIN'],
    'configuracoes.restaurar_backup': ['ADMIN'],
    'configuracoes.limpar_sessoes': ['ADMIN'],
    'configuracoes.forcar_redefinicao_senha': ['ADMIN'],
}

def get_required_roles(endpoint):
    """
    Retorna as funções necessárias para acessar uma rota específica.
    Se a rota não estiver na lista de permissões, apenas o admin tem acesso.
    """
    return PERMISSIONS.get(endpoint, ['ADMIN'])

def has_permission(user, endpoint):
    """
    Verifica se um usuário tem permissão para acessar uma rota específica.
    """
    if not user.is_authenticated:
        return False
        
    # Admin tem acesso a tudo
    if user.funcao == 'ADMIN':
        return True
        
    # Verifica se o usuário tem alguma das funções necessárias
    required_roles = get_required_roles(endpoint)
    return user.funcao in required_roles
