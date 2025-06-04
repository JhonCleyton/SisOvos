from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from models import db, Usuario, Venda, Cliente, Produto, EstoqueDiario
from decorators import admin_required
from permissions import has_permission

bp = Blueprint('admin', __name__)

@bp.route('/painel-controle')
@login_required
@admin_required
def painel_controle():
    """Painel de controle administrativo"""
    if not has_permission(current_user, 'admin.painel_controle'):
        abort(403)
    # Estatísticas básicas
    total_usuarios = Usuario.query.count()
    total_clientes = Cliente.query.count()
    total_produtos = Produto.query.filter_by(ativo=True).count()
    
    # Vendas do mês atual
    hoje = datetime.utcnow().date()
    primeiro_dia_mes = hoje.replace(day=1)
    
    if primeiro_dia_mes.month == 12:
        primeiro_dia_prox_mes = primeiro_dia_mes.replace(year=primeiro_dia_mes.year + 1, month=1, day=1)
    else:
        primeiro_dia_prox_mes = primeiro_dia_mes.replace(month=primeiro_dia_mes.month + 1, day=1)
    
    # Total de vendas do mês
    total_vendas_mes = Venda.query.filter(
        Venda.data_venda >= primeiro_dia_mes,
        Venda.data_venda < primeiro_dia_prox_mes
    ).count()
    
    # Valor total de vendas do mês
    valor_total_mes = db.session.query(
        func.sum(Venda.valor_total)
    ).filter(
        Venda.data_venda >= primeiro_dia_mes,
        Venda.data_venda < primeiro_dia_prox_mes,
        Venda.status == 'pago'
    ).scalar() or 0
    
    # Vendas dos últimos 7 dias para o gráfico
    data_7_dias_atras = hoje - timedelta(days=6)
    
    vendas_por_dia = db.session.query(
        func.date(Venda.data_venda).label('data'),
        func.count(Venda.id).label('total'),
        func.sum(Venda.valor_total).label('valor_total')
    ).filter(
        Venda.data_venda >= data_7_dias_atras,
        Venda.status == 'pago'
    ).group_by(
        func.date(Venda.data_venda)
    ).order_by('data').all()
    
    # Prepara dados para o gráfico
    datas = []
    totais = []
    valores = []
    
    for i in range(7):
        data = data_7_dias_atras + timedelta(days=i)
        data_str = data.strftime('%d/%m')
        
        # Encontra os dados para esta data
        dados_dia = next((v for v in vendas_por_dia if v.data == data), None)
        
        datas.append(data_str)
        totais.append(dados_dia.total if dados_dia else 0)
        valores.append(float(dados_dia.valor_total) if dados_dia and dados_dia.valor_total else 0)
    
    # Produtos com estoque baixo
    produtos_estoque_baixo = Produto.query.filter(
        Produto.estoque_atual < Produto.estoque_minimo,
        Produto.ativo == True
    ).order_by(Produto.estoque_atual.asc()).limit(5).all()
    
    # Últimas vendas
    ultimas_vendas = Venda.query.order_by(Venda.data_venda.desc()).limit(5).all()
    
    # Últimos clientes cadastrados
    ultimos_clientes = Cliente.query.order_by(Cliente.data_cadastro.desc()).limit(5).all()
    
    return render_template('admin/painel_controle.html',
                         total_usuarios=total_usuarios,
                         total_clientes=total_clientes,
                         total_produtos=total_produtos,
                         total_vendas_mes=total_vendas_mes,
                         valor_total_mes=valor_total_mes,
                         datas=datas,
                         totais=totais,
                         valores=valores,
                         produtos_estoque_baixo=produtos_estoque_baixo,
                         ultimas_vendas=ultimas_vendas,
                         ultimos_clientes=ultimos_clientes,
                         hoje=hoje)
