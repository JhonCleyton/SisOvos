from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import logging

def init_scheduler(app):
    """Inicializa o agendador de tarefas"""
    # Configura o logger do APScheduler
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    
    # Cria o agendador
    scheduler = BackgroundScheduler()
    
    # Configura o timezone
    scheduler.timezone = 'America/Sao_Paulo'  # Ajuste para o fuso horário correto
    
    # Adiciona as tarefas agendadas
    with app.app_context():
        # Tarefa diária de backup do banco de dados (meia-noite)
        scheduler.add_job(
            id='backup_database',
            func=backup_database_task,
            trigger=CronTrigger(hour=0, minute=0),  # Meia-noite
            replace_existing=True
        )
        
        # Tarefa diária de limpeza de arquivos temporários (1h da manhã)
        scheduler.add_job(
            id='cleanup_temp_files',
            func=cleanup_temp_files_task,
            trigger=CronTrigger(hour=1, minute=0),
            replace_existing=True
        )
        
        # Tarefa diária de envio de relatórios (8h da manhã)
        scheduler.add_job(
            id='send_daily_reports',
            func=send_daily_reports_task,
            trigger=CronTrigger(hour=8, minute=0),
            replace_existing=True
        )
        
        # Tarefa mensal de backup completo (primeiro dia do mês, 2h da manhã)
        scheduler.add_job(
            id='monthly_full_backup',
            func=monthly_full_backup_task,
            trigger=CronTrigger(day=1, hour=2, minute=0),
            replace_existing=True
        )
    
    # Inicia o agendador
    scheduler.start()
    
    return scheduler

def backup_database_task():
    """Tarefa de backup do banco de dados"""
    try:
        from utils.backup import create_database_backup
        backup_file = create_database_backup()
        current_app.logger.info(f'Backup do banco de dados criado com sucesso: {backup_file}')
        return True
    except Exception as e:
        current_app.logger.error(f'Erro ao criar backup do banco de dados: {str(e)}')
        return False

def cleanup_temp_files_task():
    """Tarefa de limpeza de arquivos temporários"""
    try:
        import os
        import glob
        from datetime import datetime, timedelta
        
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
        if not os.path.exists(temp_dir):
            return True
        
        # Remove arquivos com mais de 7 dias
        cutoff_time = datetime.now() - timedelta(days=7)
        deleted_files = 0
        
        for file_path in glob.glob(os.path.join(temp_dir, '*')):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff_time:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_files += 1
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                        deleted_files += 1
                except Exception as e:
                    current_app.logger.error(f'Erro ao remover arquivo temporário {file_path}: {str(e)}')
        
        current_app.logger.info(f'Limpeza de arquivos temporários concluída. {deleted_files} arquivos removidos.')
        return True
    except Exception as e:
        current_app.logger.error(f'Erro na limpeza de arquivos temporários: {str(e)}')
        return False

def send_daily_reports_task():
    """Tarefa de envio de relatórios diários"""
    try:
        from models import Usuario, Venda, db
        from datetime import date, timedelta
        from utils.notifications import send_daily_sales_report
        
        # Obtém a data de ontem
        yesterday = date.today() - timedelta(days=1)
        
        # Busca as vendas de ontem
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday, datetime.max.time())
        
        vendas = Venda.query.filter(
            Venda.data_venda.between(start_date, end_date)
        ).all()
        
        # Prepara os dados para o relatório
        sales_data = []
        for venda in vendas:
            sales_data.append({
                'id': venda.id,
                'cliente': venda.cliente.nome if venda.cliente else 'Consumidor',
                'data': venda.data_venda.strftime('%d/%m/%Y %H:%M'),
                'total': venda.valor_total,
                'itens': len(venda.itens)
            })
        
        # Encontra os destinatários (administradores)
        admins = Usuario.query.filter_by(funcao='ADMIN', ativo=True).all()
        
        if admins:
            send_daily_sales_report(admins, sales_data, yesterday)
        
        return True
    except Exception as e:
        current_app.logger.error(f'Erro ao enviar relatório diário: {str(e)}')
        return False

def monthly_full_backup_task():
    """Tarefa de backup mensal completo"""
    try:
        from utils.backup import create_full_backup
        backup_file = create_full_backup()
        current_app.logger.info(f'Backup mensal completo criado com sucesso: {backup_file}')
        return True
    except Exception as e:
        current_app.logger.error(f'Erro ao criar backup mensal completo: {str(e)}')
        return False

def check_scheduled_tasks():
    """Verifica e executa tarefas agendadas pendentes"""
    # Esta função pode ser chamada periodicamente para garantir que as tarefas sejam executadas
    # mesmo que o servidor tenha sido reiniciado
    pass
