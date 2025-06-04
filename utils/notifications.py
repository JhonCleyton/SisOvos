from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from datetime import datetime, timedelta
from .email import send_email

class Notification:
    """Classe base para notificações"""
    
    def __init__(self, recipient, subject, template, **kwargs):
        self.recipient = recipient
        self.subject = subject
        self.template = template
        self.context = kwargs
    
    def send(self):
        """Envia a notificação"""
        raise NotImplementedError("Método send() deve ser implementado pelas subclasses")


class EmailNotification(Notification):
    """Notificação por e-mail"""
    
    def send(self):
        """Envia o e-mail de notificação"""
        try:
            send_email(
                to=self.recipient.email,
                subject=self.subject,
                template=f'emails/notifications/{self.template}',
                **self.context
            )
            return True
        except Exception as e:
            current_app.logger.error(f'Erro ao enviar notificação por e-mail: {str(e)}')
            return False


class PushNotification(Notification):
    """Notificação push (para implementação futura)"""
    
    def send(self):
        # Implementação futura para notificações push
        pass


def send_welcome_notification(user):
    """Envia uma notificação de boas-vindas para um novo usuário"""
    notification = EmailNotification(
        recipient=user,
        subject='Bem-vindo ao SisOvos!',
        template='welcome.html',
        user=user,
        login_url=current_app.config.get('FRONTEND_URL', '') + '/login'
    )
    return notification.send()

def send_password_reset_notification(user, token):
    """Envia uma notificação de redefinição de senha"""
    reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password/{token}"
    
    notification = EmailNotification(
        recipient=user,
        subject='Redefinição de Senha - SisOvos',
        template='password_reset.html',
        user=user,
        reset_url=reset_url,
        expires_in_hours=current_app.config.get('RESET_TOKEN_EXPIRE_HOURS', 24)
    )
    return notification.send()

def send_new_user_notification(admin_user, new_user):
    """Notifica um administrador sobre um novo usuário"""
    notification = EmailNotification(
        recipient=admin_user,
        subject='Novo Usuário Cadastrado',
        template='new_user.html',
        admin=admin_user,
        new_user=new_user,
        admin_panel_url=current_app.config.get('FRONTEND_URL', '') + '/admin/usuarios'
    )
    return notification.send()

def send_low_stock_alert(product, current_quantity, threshold=10):
    """Envia um alerta de estoque baixo"""
    from models import Usuario
    
    # Encontra todos os administradores
    admins = Usuario.query.filter_by(funcao='ADMIN', ativo=True).all()
    
    if not admins:
        return False
    
    success = True
    
    for admin in admins:
        notification = EmailNotification(
            recipient=admin,
            subject=f'[Alerta] Estoque Baixo - {product.nome}',
            template='low_stock_alert.html',
            product=product,
            current_quantity=current_quantity,
            threshold=threshold,
            inventory_url=current_app.config.get('FRONTEND_URL', '') + '/estoque'
        )
        
        if not notification.send():
            success = False
    
    return success

def send_daily_sales_report(recipients, sales_data, date=None):
    """Envia um relatório diário de vendas"""
    if date is None:
        date = datetime.utcnow().date() - timedelta(days=1)  # Ontem
    
    # Formata a data
    date_str = date.strftime('%d/%m/%Y')
    
    success = True
    
    for recipient in recipients:
        notification = EmailNotification(
            recipient=recipient,
            subject=f'Relatório Diário de Vendas - {date_str}',
            template='daily_sales_report.html',
            sales_data=sales_data,
            date=date_str,
            total_sales=sum(sale['total'] for sale in sales_data),
            dashboard_url=current_app.config.get('FRONTEND_URL', '') + '/dashboard'
        )
        
        if not notification.send():
            success = False
    
    return success
