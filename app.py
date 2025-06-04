from flask import Flask, render_template, redirect, url_for, flash, request, session, abort, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_sqlalchemy.pagination import Pagination
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import generate_csrf

from datetime import datetime, timedelta
from functools import wraps
import os

# Importa a aplicação criada no __init__.py
from __init__ import create_app

# Cria a aplicação
app = create_app()

# Importa as extensões
from extensions import db

# Importa os modelos depois de criar o app para evitar importação circular
with app.app_context():
    from models import Usuario, Cliente, Produto, Venda, ItemVenda
    from forms import ProdutoForm, VendaForm, UsuarioForm, BuscarUsuarioForm

# Decorator para verificar permissões
def permissao_necessaria(funcao_requerida):
    def decorator(f):
        @wraps(f)
        def funcao_decorada(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
            if not current_user.tem_permissao(funcao_requerida):
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return funcao_decorada
    return decorator

# As rotas são registradas através do __init__.py

# Inicialização das extensões
from extensions import login_manager, csrf

# Configura o login_manager
login_manager.init_app(app)
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# Inicializa o CSRF
csrf.init_app(app)

# Adiciona CSRF token a todas as respostas
@app.after_request
def set_csrf_cookie(response):
    if 'csrf_token' not in session:
        session['csrf_token'] = generate_csrf()
    response.set_cookie('csrf_token', session['csrf_token'])
    return response

# Filtro para formatar datas no Jinja2
def format_datetime_filter(value, format='%d/%m/%Y %H:%M'):
    if value is None:
        return ''
    if isinstance(value, str):
        # Tenta converter a string para datetime se necessário
        try:
            value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except (ValueError, TypeError):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                return value  # Retorna o valor original se não for possível converter
    
    # Formata a data de acordo com o formato especificado
    try:
        return value.strftime(format)
    except (AttributeError, ValueError):
        return value  # Retorna o valor original se não for possível formatar

# Adiciona o filtro ao ambiente Jinja2
app.jinja_env.filters['datetimeformat'] = format_datetime_filter

# Carregador de usuário para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import Usuario
    return Usuario.query.get(int(user_id))

# ... (restante do código)
    # e procure por 'IPv4 Address' na sua conexão de rede
