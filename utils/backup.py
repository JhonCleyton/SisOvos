import os
import shutil
import zipfile
from datetime import datetime
import logging
from flask import current_app

def ensure_backup_dir():
    """Garante que o diretório de backups existe"""
    backup_dir = os.path.join(current_app.root_path, '..', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def create_database_backup():
    """Cria um backup do banco de dados SQLite"""
    try:
        from app import db
        import sqlite3
        
        # Configurações
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_dir = ensure_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.db')
        
        # Fecha todas as conexões com o banco de dados
        db.session.close_all()
        
        # Cria uma cópia do arquivo do banco de dados
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as src_conn:
                with sqlite3.connect(backup_file) as dest_conn:
                    src_conn.backup(dest_conn)
            
            current_app.logger.info(f'Backup do banco de dados criado: {backup_file}')
            return backup_file
        else:
            current_app.logger.error('Arquivo do banco de dados não encontrado')
            return None
            
    except Exception as e:
        current_app.logger.error(f'Erro ao criar backup do banco de dados: {str(e)}')
        return None

def create_full_backup():
    """Cria um backup completo da aplicação (banco de dados + uploads)"""
    try:
        import tempfile
        from pathlib import Path
        
        # Configurações
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = ensure_backup_dir()
        backup_filename = f'full_backup_{timestamp}.zip'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Cria um diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Faz backup do banco de dados
            db_backup = create_database_backup()
            if db_backup:
                shutil.copy2(db_backup, os.path.join(temp_dir, os.path.basename(db_backup)))
            
            # 2. Copia a pasta de uploads
            uploads_src = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            uploads_dest = os.path.join(temp_dir, 'uploads')
            
            if os.path.exists(uploads_src):
                shutil.copytree(uploads_src, uploads_dest)
            
            # 3. Copia os logs
            logs_src = os.path.join(current_app.root_path, 'logs')
            logs_dest = os.path.join(temp_dir, 'logs')
            
            if os.path.exists(logs_src):
                shutil.copytree(logs_src, logs_dest)
            
            # 4. Cria um arquivo com informações da aplicação
            with open(os.path.join(temp_dir, 'backup_info.txt'), 'w') as f:
                f.write(f'Aplicação: {current_app.name}\n')
                f.write(f'Data do backup: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'Versão: {current_app.config.get("VERSION", "1.0.0")}\n')
            
            # 5. Cria o arquivo ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            current_app.logger.info(f'Backup completo criado: {backup_path}')
            return backup_path
    
    except Exception as e:
        current_app.logger.error(f'Erro ao criar backup completo: {str(e)}')
        return None

def restore_database(backup_file):
    """Restaura o banco de dados a partir de um backup"""
    try:
        from app import db
        import sqlite3
        
        # Configurações
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Verifica se o arquivo de backup existe
        if not os.path.exists(backup_file):
            current_app.logger.error('Arquivo de backup não encontrado')
            return False
        
        # Cria um backup do banco de dados atual
        current_backup = create_database_backup()
        if not current_backup:
            current_app.logger.error('Falha ao criar backup do banco de dados atual')
            return False
        
        # Fecha todas as conexões com o banco de dados
        db.session.close_all()
        
        # Remove o arquivo do banco de dados atual
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Restaura o banco de dados a partir do backup
        with sqlite3.connect(backup_file) as src_conn:
            with sqlite3.connect(db_path) as dest_conn:
                src_conn.backup(dest_conn)
        
        current_app.logger.info('Banco de dados restaurado com sucesso')
        return True
        
    except Exception as e:
        current_app.logger.error(f'Erro ao restaurar banco de dados: {str(e)}')
        return False

def list_backups():
    """Lista todos os backups disponíveis"""
    backup_dir = ensure_backup_dir()
    backups = []
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            file_stat = os.stat(filepath)
            backups.append({
                'name': filename,
                'path': filepath,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime),
                'modified': datetime.fromtimestamp(file_stat.st_mtime)
            })
    
    # Ordena por data de modificação (mais recente primeiro)
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return backups

def delete_old_backups(days_to_keep=30):
    """Remove backups antigos"""
    try:
        backup_dir = ensure_backup_dir()
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted = 0
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted += 1
                except Exception as e:
                    current_app.logger.error(f'Erro ao remover arquivo {filename}: {str(e)}')
        
        current_app.logger.info(f'Removidos {deleted} backups antigos')
        return deleted
    except Exception as e:
        current_app.logger.error(f'Erro ao remover backups antigos: {str(e)}')
        return 0
