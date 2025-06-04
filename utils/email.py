from flask import render_template, current_app
from flask_mail import Message
from extensions import mail
from threading import Thread
from datetime import datetime

def send_async_email(app, msg):
    """Função para enviar e-mail em uma thread separada"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar e-mail: {str(e)}")

def send_email(to, subject, template, **kwargs):
    """
    Envia um e-mail usando um template
    
    Args:
        to: Destinatário ou lista de destinatários
        subject: Assunto do e-mail
        template: Nome do template (sem a extensão .html)
        **kwargs: Variáveis para o template
    """
    app = current_app._get_current_object()
    
    # Adiciona a data atual aos kwargs
    kwargs['now'] = datetime.utcnow()
    
    # Renderiza o template do e-mail
    html = render_template(f'emails/{template}.html', **kwargs)
    
    # Cria a mensagem
    msg = Message(
        subject=subject,
        recipients=[to] if isinstance(to, str) else to,
        html=html,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    
    # Envia o e-mail em uma thread separada
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(usuario, token):
    """Envia um e-mail para redefinição de senha"""
    reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password/{token}"
    expira_em = current_app.config['RESET_TOKEN_EXPIRE_HOURS']
    
    send_email(
        to=usuario.email,
        subject="Redefinição de Senha - SisOvos",
        template="reset_password",
        usuario=usuario,
        reset_url=reset_url,
        expira_em=expira_em
    )
