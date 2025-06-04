from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, jsonify
from flask_login import login_required, current_user, logout_user
from functools import wraps
from models import db, Usuario
from forms import ConfiguracaoSistemaForm, ConfiguracaoSegurancaForm, ConfiguracaoBackupForm
import os
import json
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

configuracoes_bp = Blueprint('configuracoes', __name__)

# Configurações
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
ALLOWED_EXTENSIONS = {'sqlite', 'db', 'sqlite3'}

# Garante que a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def permissao_necessaria(funcao_requerida):
    """Decorator para verificar permissões"""
    @wraps(funcao_requerida)
    def decorador(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.tem_permissao('ADMIN'):
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return funcao_requerida(*args, **kwargs)
    return decorador

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_backup_list():
    """Retorna a lista de arquivos de backup"""
    if not os.path.exists(UPLOAD_FOLDER):
        return []
    
    backups = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(('.sqlite', '.db', '.sqlite3')):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            backups.append({
                'nome': filename,
                'tamanho': f"{os.path.getsize(filepath) / 1024:.1f} KB",
                'data_criacao': datetime.fromtimestamp(os.path.getmtime(filepath))
            })
    
    # Ordena por data de criação (mais recente primeiro)
    backups.sort(key=lambda x: x['data_criacao'], reverse=True)
    return backups

@configuracoes_bp.route('/sistema', methods=['GET', 'POST'])
@login_required
@permissao_necessaria
def sistema():
    """Página de configurações do sistema"""
    form = ConfiguracaoSistemaForm()
    
    # Caminho para o arquivo de configurações
    config_path = os.path.join(current_app.instance_path, 'config_sistema.json')
    
    # Carrega as configurações existentes
    configuracoes = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                configuracoes = json.load(f)
        except json.JSONDecodeError:
            flash('Erro ao carregar as configurações. O arquivo de configuração está corrompido.', 'danger')
            configuracoes = {}
    
    if form.validate_on_submit():
        try:
            # Atualiza as configurações
            configuracoes.update({
                'nome_empresa': form.nome_empresa.data,
                'email_contato': form.email_contato.data,
                'itens_por_pagina': form.itens_por_pagina.data,
                'horario_abertura': form.horario_abertura.data,
                'horario_fechamento': form.horario_fechamento.data,
                'notificacoes_por_email': form.notificacoes_por_email.data,
                'modo_manutencao': form.modo_manutencao.data,
                'mensagem_manutencao': form.mensagem_manutencao.data,
                'ultima_atualizacao': datetime.now().isoformat()
            })
            
            # Salva as configurações no arquivo
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(configuracoes, f, indent=4, ensure_ascii=False)
            
            flash('Configurações salvas com sucesso!', 'success')
            return redirect(url_for('configuracoes.sistema'))
            
        except Exception as e:
            current_app.logger.error(f'Erro ao salvar configurações: {str(e)}')
            flash('Ocorreu um erro ao salvar as configurações. Por favor, tente novamente.', 'danger')
    
    # Preenche o formulário com os valores atuais
    elif request.method == 'GET':
        form.nome_empresa.data = configuracoes.get('nome_empresa', '')
        form.email_contato.data = configuracoes.get('email_contato', '')
        form.itens_por_pagina.data = configuracoes.get('itens_por_pagina', 10)
        form.horario_abertura.data = configuracoes.get('horario_abertura', '08:00')
        form.horario_fechamento.data = configuracoes.get('horario_fechamento', '18:00')
        form.notificacoes_por_email.data = configuracoes.get('notificacoes_por_email', True)
        form.modo_manutencao.data = configuracoes.get('modo_manutencao', False)
        form.mensagem_manutencao.data = configuracoes.get('mensagem_manutencao', '')
    
    return render_template('configuracoes/sistema.html', form=form, title='Configurações do Sistema')

@configuracoes_bp.route('/seguranca', methods=['GET', 'POST'])
@login_required
@permissao_necessaria
def seguranca():
    """Página de configurações de segurança"""
    form = ConfiguracaoSegurancaForm()
    config_path = os.path.join(current_app.instance_path, 'config_seguranca.json')
    
    # Configurações padrão
    config = {
        'forca_senha': 'media',
        'autenticacao_dois_fatores': False,
        'bloqueio_tentativas': True,
        'tempo_sessao': 30
    }
    
    # Carrega configurações salvas
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except json.JSONDecodeError:
            flash('Erro ao carregar as configurações de segurança. O arquivo de configuração está corrompido.', 'danger')
    
    if form.validate_on_submit():
        try:
            # Atualiza as configurações
            config.update({
                'forca_senha': form.forca_senha.data,
                'autenticacao_dois_fatores': form.autenticacao_dois_fatores.data,
                'bloqueio_tentativas': form.bloqueio_tentativas.data,
                'tempo_sessao': form.tempo_sessao.data,
                'ultima_atualizacao': datetime.now().isoformat()
            })
            
            # Salva as configurações
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            flash('Configurações de segurança salvas com sucesso!', 'success')
            return redirect(url_for('configuracoes.seguranca'))
            
        except Exception as e:
            current_app.logger.error(f'Erro ao salvar configurações de segurança: {str(e)}')
            flash('Ocorreu um erro ao salvar as configurações de segurança. Por favor, tente novamente.', 'danger')
    
    # Preenche o formulário com os valores atuais
    elif request.method == 'GET':
        form.forca_senha.data = config.get('forca_senha', 'media')
        form.autenticacao_dois_fatores.data = config.get('autenticacao_dois_fatores', False)
        form.bloqueio_tentativas.data = config.get('bloqueio_tentativas', True)
        form.tempo_sessao.data = config.get('tempo_sessao', 30)
    
    return render_template('configuracoes/seguranca.html', 
                         title='Configurações de Segurança',
                         form=form,
                         active_page='seguranca')

@configuracoes_bp.route('/seguranca/limpar-sessoes', methods=['POST'])
@login_required
@permissao_necessaria
def limpar_sessoes():
    """Limpa todas as sessões dos usuários"""
    try:
        # Limpa a tabela de sessões (ajuste conforme seu backend de sessão)
        db.session.execute('DELETE FROM sessions')
        db.session.commit()
        
        # Desloga o usuário atual
        logout_user()
        
        flash('Todas as sessões foram encerradas. Por favor, faça login novamente.', 'success')
        return redirect(url_for('main.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar as sessões: {str(e)}', 'danger')
        return redirect(url_for('configuracoes.seguranca'))

@configuracoes_bp.route('/seguranca/forcar-redefinicao-senha', methods=['POST'])
@login_required
@permissao_necessaria
def forcar_redefinicao_senha():
    """Força todos os usuários a redefinirem suas senhas no próximo login"""
    try:
        # Atualiza todos os usuários para forçar redefinição de senha
        usuarios = Usuario.query.all()
        for usuario in usuarios:
            usuario.alterar_senha_proximo_login = True
        
        db.session.commit()
        flash('Todos os usuários serão solicitados a redefinir suas senhas no próximo login.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar as configurações de senha: {str(e)}', 'danger')
    
    return redirect(url_for('configuracoes.seguranca'))

@configuracoes_bp.route('/backup', methods=['GET', 'POST'])
@login_required
@permissao_necessaria
def backup():
    """Página de backup e restauração"""
    form = ConfiguracaoBackupForm()
    backups = get_backup_list()
    
    # Carrega configurações de backup
    config_path = os.path.join(current_app.instance_path, 'config_backup.json')
    config = {
        'backup_automatico': True,
        'frequencia_backup': 'diario',
        'hora_backup': '02:00',
        'manter_backups': 30
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config.update(json.load(f))
    
    # Se for POST, processa o formulário
    if form.validate_on_submit():
        try:
            # Atualiza as configurações com os dados do formulário
            config.update({
                'backup_automatico': form.backup_automatico.data,
                'frequencia_backup': form.frequencia_backup.data,
                'hora_backup': form.hora_backup.data,
                'manter_backups': form.manter_backups.data,
                'ultima_atualizacao': datetime.now().isoformat()
            })
            
            # Salva as configurações no arquivo
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            flash('Configurações de backup salvas com sucesso!', 'success')
            return redirect(url_for('configuracoes.backup'))
            
        except Exception as e:
            flash(f'Erro ao salvar as configurações: {str(e)}', 'danger')
    elif request.method == 'GET':
        # Preenche o formulário com as configurações atuais
        form.backup_automatico.data = config.get('backup_automatico', True)
        form.frequencia_backup.data = config.get('frequencia_backup', 'diario')
        form.hora_backup.data = config.get('hora_backup', '02:00')
        form.manter_backups.data = config.get('manter_backups', 30)
    
    return render_template('configuracoes/backup.html', 
                         title='Backup e Restauração',
                         form=form,
                         backups=backups,
                         total_backups=len(backups),
                         config=config,
                         active_page='backup')

@configuracoes_bp.route('/backup/gerar', methods=['POST'])
@login_required
@permissao_necessaria
def gerar_backup():
    """Gera um novo backup do banco de dados"""
    try:
        # Nome do arquivo de backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_{timestamp}.db'
        backup_path = os.path.join(UPLOAD_FOLDER, backup_file)
        
        # Copia o banco de dados atual para o arquivo de backup
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        shutil.copy2(db_path, backup_path)
        
        flash(f'Backup criado com sucesso: {backup_file}', 'success')
    except Exception as e:
        flash(f'Erro ao criar o backup: {str(e)}', 'danger')
    
    return redirect(url_for('configuracoes.backup'))

@configuracoes_bp.route('/backup/<nome_arquivo>/baixar')
@login_required
@permissao_necessaria
def baixar_backup(nome_arquivo):
    """Faz o download de um arquivo de backup"""
    try:
        # Previne path traversal
        nome_arquivo = secure_filename(nome_arquivo)
        
        if not os.path.exists(os.path.join(UPLOAD_FOLDER, nome_arquivo)):
            flash('Arquivo de backup não encontrado.', 'danger')
            return redirect(url_for('configuracoes.backup'))
        
        return send_from_directory(
            UPLOAD_FOLDER,
            nome_arquivo,
            as_attachment=True,
            download_name=f'backup_{datetime.now().strftime("%Y%m%d")}.db',
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        flash(f'Erro ao baixar o backup: {str(e)}', 'danger')
        return redirect(url_for('configuracoes.backup'))

@configuracoes_bp.route('/backup/<nome_arquivo>/excluir', methods=['POST'])
@login_required
@permissao_necessaria
def excluir_backup(nome_arquivo):
    """Exclui um arquivo de backup"""
    try:
        # Previne path traversal
        nome_arquivo = secure_filename(nome_arquivo)
        backup_path = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            flash('Backup excluído com sucesso.', 'success')
        else:
            flash('Arquivo de backup não encontrado.', 'warning')
    except Exception as e:
        flash(f'Erro ao excluir o backup: {str(e)}', 'danger')
    
    return redirect(url_for('configuracoes.backup'))

@configuracoes_bp.route('/backup/salvar-configuracoes', methods=['POST'])
@login_required
@permissao_necessaria
def salvar_configuracoes_backup():
    """Salva as configurações de backup automático"""
    try:
        config_path = os.path.join(current_app.instance_path, 'config_backup.json')
        config = {
            'backup_automatico': 'backup_automatico' in request.form,
            'frequencia_backup': request.form.get('frequencia_backup', 'diario'),
            'hora_backup': request.form.get('hora_backup', '02:00'),
            'manter_backups': int(request.form.get('manter_backups', 30))
        }
        
        # Salva as configurações
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        flash('Configurações de backup salvas com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar as configurações: {str(e)}', 'danger')
    
    return redirect(url_for('configuracoes.backup'))

@configuracoes_bp.route('/backup/restaurar', methods=['POST'])
@login_required
@permissao_necessaria
def restaurar_backup():
    """Restaura um backup do banco de dados"""
    if 'arquivo_backup' not in request.files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('configuracoes.backup'))
    
    arquivo = request.files['arquivo_backup']
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('configuracoes.backup'))
    
    if arquivo and allowed_file(arquivo.filename):
        try:
            # Salva o arquivo temporariamente
            temp_path = os.path.join(current_app.instance_path, 'temp_restore.db')
            arquivo.save(temp_path)
            
            # Faz backup do banco atual
            db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            backup_path = os.path.join(UPLOAD_FOLDER, f'pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(db_path, backup_path)
            
            # Substitui o banco de dados
            shutil.copy2(temp_path, db_path)
            
            # Remove o arquivo temporário
            os.remove(temp_path)
            
            flash('Backup restaurado com sucesso! Um backup do banco anterior foi criado.', 'success')
            return redirect(url_for('main.logout'))  # Força logout para recarregar as permissões
            
        except Exception as e:
            flash(f'Erro ao restaurar o backup: {str(e)}', 'danger')
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        flash('Tipo de arquivo não permitido. Use apenas arquivos .db ou .sqlite', 'danger')
    
    return redirect(url_for('configuracoes.backup'))
