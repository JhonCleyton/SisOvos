import os
import json
from flask import request, session, current_app
from flask_babel import Babel, gettext as _, lazy_gettext

def configure_babel(app):
    """Configura a extensão Flask-Babel"""
    # Diretório de traduções
    translations_dir = os.path.join(app.root_path, 'translations')
    
    # Cria o diretório de traduções se não existir
    os.makedirs(translations_dir, exist_ok=True)
    
    # Inicializa a extensão Babel
    babel = Babel(app)
    
    # Configurações
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = translations_dir
    app.config['BABEL_DEFAULT_LOCALE'] = 'pt_BR'
    app.config['LANGUAGES'] = {
        'pt_BR': 'Português (Brasil)',
        'es': 'Español',
        'en': 'English'
    }
    
    # Callback para obter o idioma atual
    @babel.localeselector
    def get_locale():
        # Verifica se o idioma está na sessão
        if 'language' in session:
            return session['language']
        
        # Tenta detectar o idioma do navegador
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    
    # Adiciona o idioma atual ao contexto do template
    @app.context_processor
    def inject_language():
        return {
            'current_language': get_locale(),
            'languages': app.config['LANGUAGES']
        }
    
    return babel

def set_language(language_code):
    """Define o idioma da sessão atual"""
    if language_code in current_app.config['LANGUAGES']:
        session['language'] = language_code
        return True
    return False

def load_translations(locale='pt_BR'):
    """Carrega as traduções para um idioma específico"""
    translations_dir = os.path.join(current_app.root_path, 'translations')
    translation_file = os.path.join(translations_dir, locale, 'LC_MESSAGES', 'messages.json')
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_translation(key, locale='pt_BR', **kwargs):
    """Obtém uma tradução para uma chave específica"""
    translations = load_translations(locale)
    return translations.get(key, key).format(**kwargs) if key in translations else key

def init_translations():
    """Inicializa as traduções padrão se não existirem"""
    translations_dir = os.path.join(current_app.root_path, 'translations')
    
    # Traduções padrão em português do Brasil
    default_translations = {
        'pt_BR': {
            'Welcome': 'Bem-vindo',
            'Login': 'Entrar',
            'Logout': 'Sair',
            'Username': 'Usuário',
            'Password': 'Senha',
            'Email': 'E-mail',
            'Save': 'Salvar',
            'Cancel': 'Cancelar',
            'Delete': 'Excluir',
            'Edit': 'Editar',
            'Add': 'Adicionar',
            'Search': 'Pesquisar',
            'Actions': 'Ações',
            'Dashboard': 'Painel',
            'Users': 'Usuários',
            'Products': 'Produtos',
            'Customers': 'Clientes',
            'Sales': 'Vendas',
            'Reports': 'Relatórios',
            'Settings': 'Configurações',
            'Profile': 'Perfil',
            'Logout': 'Sair',
            'Language': 'Idioma',
            'Theme': 'Tema',
            'Dark': 'Escuro',
            'Light': 'Claro',
            'System': 'Sistema',
            'Save changes': 'Salvar alterações',
            'Changes saved successfully': 'Alterações salvas com sucesso',
            'Error saving changes': 'Erro ao salvar alterações',
            'Are you sure?': 'Tem certeza?',
            'This action cannot be undone': 'Esta ação não pode ser desfeita',
            'Yes, delete it!': 'Sim, excluir!',
            'No': 'Não',
            'Yes': 'Sim',
            'Close': 'Fechar',
            'Loading...': 'Carregando...',
            'No data available': 'Nenhum dado disponível',
            'Showing %(start)s to %(end)s of %(total)s entries': 
                'Mostrando %(start)s a %(end)s de %(total)s registros',
            'First': 'Primeiro',
            'Previous': 'Anterior',
            'Next': 'Próximo',
            'Last': 'Último',
            'No matching records found': 'Nenhum registro encontrado',
            'Filter': 'Filtrar',
            'Clear': 'Limpar',
            'Apply': 'Aplicar',
            'From': 'De',
            'To': 'Até',
            'Date': 'Data',
            'Status': 'Status',
            'Type': 'Tipo',
            'Description': 'Descrição',
            'Value': 'Valor',
            'Quantity': 'Quantidade',
            'Unit': 'Unidade',
            'Total': 'Total',
            'Price': 'Preço',
            'Subtotal': 'Subtotal',
            'Discount': 'Desconto',
            'Tax': 'Imposto',
            'Shipping': 'Frete',
            'Grand Total': 'Total Geral',
            'Print': 'Imprimir',
            'Export': 'Exportar',
            'Export to Excel': 'Exportar para Excel',
            'Export to PDF': 'Exportar para PDF',
            'Export to CSV': 'Exportar para CSV',
            'Export to JSON': 'Exportar para JSON',
            'Import': 'Importar',
            'Import from Excel': 'Importar do Excel',
            'Import from CSV': 'Importar do CSV',
            'Download template': 'Baixar modelo',
            'Upload file': 'Enviar arquivo',
            'File': 'Arquivo',
            'Size': 'Tamanho',
            'Uploaded at': 'Enviado em',
            'Download': 'Baixar',
            'Remove': 'Remover',
            'Upload': 'Enviar',
            'Drag and drop a file here or click to select': 
                'Arraste e solte um arquivo aqui ou clique para selecionar',
            'or': 'ou',
            'File is too large': 'Arquivo muito grande',
            'File type not allowed': 'Tipo de arquivo não permitido',
            'Maximum file size: %(size)s': 'Tamanho máximo do arquivo: %(size)s',
            'Allowed file types: %(types)s': 'Tipos de arquivo permitidos: %(types)s',
            'Uploading...': 'Enviando...',
            'Upload complete': 'Upload concluído',
            'Upload failed': 'Falha no upload',
            'Server error': 'Erro no servidor',
            'Connection error': 'Erro de conexão',
            'Abort': 'Cancelar',
            'Retry': 'Tentar novamente',
            'Done': 'Concluído',
            'Error': 'Erro',
            'Warning': 'Aviso',
            'Info': 'Informação',
            'Success': 'Sucesso',
            'Please wait...': 'Por favor, aguarde...',
            'Processing...': 'Processando...',
            'No results found': 'Nenhum resultado encontrado',
            'All': 'Todos',
            'Active': 'Ativo',
            'Inactive': 'Inativo',
            'Pending': 'Pendente',
            'Completed': 'Concluído',
            'Cancelled': 'Cancelado',
            'Refunded': 'Reembolsado',
            'Shipped': 'Enviado',
            'Delivered': 'Entregue',
            'Returned': 'Devolvido',
            'Paid': 'Pago',
            'Unpaid': 'Não pago',
            'Overdue': 'Atrasado',
            'Draft': 'Rascunho',
            'Sent': 'Enviado',
            'Received': 'Recebido',
            'Read': 'Lido',
            'Unread': 'Não lido',
            'Archived': 'Arquivado',
            'Trash': 'Lixeira',
            'Spam': 'Spam',
            'Starred': 'Com estrela',
            'Important': 'Importante',
            'Scheduled': 'Agendado',
            'Today': 'Hoje',
            'Yesterday': 'Ontem',
            'This week': 'Esta semana',
            'Last week': 'Semana passada',
            'This month': 'Este mês',
            'Last month': 'Mês passado',
            'This year': 'Este ano',
            'Last year': 'Ano passado',
            'Custom range': 'Período personalizado',
            'Apply': 'Aplicar',
            'Cancel': 'Cancelar',
            'Custom Range': 'Período personalizado',
            'Start Date': 'Data inicial',
            'End Date': 'Data final',
            'to': 'até',
            'January': 'Janeiro',
            'February': 'Fevereiro',
            'March': 'Março',
            'April': 'Abril',
            'May': 'Maio',
            'June': 'Junho',
            'July': 'Julho',
            'August': 'Agosto',
            'September': 'Setembro',
            'October': 'Outubro',
            'November': 'Novembro',
            'December': 'Dezembro',
            'Jan': 'Jan',
            'Feb': 'Fev',
            'Mar': 'Mar',
            'Apr': 'Abr',
            'May': 'Mai',
            'Jun': 'Jun',
            'Jul': 'Jul',
            'Aug': 'Ago',
            'Sep': 'Set',
            'Oct': 'Out',
            'Nov': 'Nov',
            'Dec': 'Dez',
            'Sunday': 'Domingo',
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sun': 'Dom',
            'Mon': 'Seg',
            'Tue': 'Ter',
            'Wed': 'Qua',
            'Thu': 'Qui',
            'Fri': 'Sex',
            'Sat': 'Sáb',
            'Su': 'D',
            'Mo': 'S',
            'Tu': 'T',
            'We': 'Q',
            'Th': 'Q',
            'Fr': 'S',
            'Sa': 'S',
            'January 2023': 'Janeiro de 2023',
            'February 2023': 'Fevereiro de 2023',
            'March 2023': 'Março de 2023',
            'April 2023': 'Abril de 2023',
            'May 2023': 'Maio de 2023',
            'June 2023': 'Junho de 2023',
            'July 2023': 'Julho de 2023',
            'August 2023': 'Agosto de 2023',
            'September 2023': 'Setembro de 2023',
            'October 2023': 'Outubro de 2023',
            'November 2023': 'Novembro de 2023',
            'December 2023': 'Dezembro de 2023'
        },
        # Adicione mais idiomas conforme necessário
    }
    
    # Cria os diretórios de tradução para cada idioma
    for lang, translations in default_translations.items():
        lang_dir = os.path.join(translations_dir, lang, 'LC_MESSAGES')
        os.makedirs(lang_dir, exist_ok=True)
        
        translation_file = os.path.join(lang_dir, 'messages.json')
        
        # Se o arquivo de tradução não existir, cria com as traduções padrão
        if not os.path.exists(translation_file):
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)

# Atalhos para funções de tradução comuns
_ = gettext
_lazy = lazy_gettext
_n = lambda s, *args, **kwargs: s.format(*args, **kwargs) if (args or kwargs) else s
