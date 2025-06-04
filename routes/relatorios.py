from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usar backend que não requer interface gráfica
import matplotlib.pyplot as plt
from sqlalchemy import func, extract, and_
from models import db, Venda, Cliente, Produto, ItemVenda
from decorators import admin_required, financeiro_required, producao_required
from permissions import has_permission

bp = Blueprint('relatorios', __name__)

@bp.route('/financeiro')
@login_required
@financeiro_required
def relatorio_financeiro():
    """Gera relatório financeiro com filtros por período"""
    if not has_permission(current_user, 'relatorios.relatorio_financeiro'):
        abort(403)
    # Valores padrão: último mês
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)
    
    # Aplicar filtros se fornecidos
    if 'data_inicio' in request.args and request.args['data_inicio']:
        try:
            data_inicio = datetime.strptime(request.args['data_inicio'], '%Y-%m-%d')
        except ValueError:
            flash('Data de início inválida. Usando valor padrão (últimos 30 dias).', 'warning')
    
    if 'data_fim' in request.args and request.args['data_fim']:
        try:
            data_fim = datetime.strptime(request.args['data_fim'], '%Y-%m-%d') + timedelta(days=1)  # Inclui o dia final
        except ValueError:
            flash('Data de fim inválida. Usando data atual.', 'warning')
    
    # Ajusta as datas para garantir que estejam no mesmo fuso horário
    data_inicio = data_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    data_fim = data_fim.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Consulta de vendas no período
    vendas = Venda.query.filter(
        Venda.data_venda >= data_inicio,
        Venda.data_venda <= data_fim
    ).order_by(Venda.data_venda).all()
    
    # Cálculo de totais
    total_vendas = len(vendas)
    total_recebido = sum(v.valor_total for v in vendas if v.status == 'finalizada' and v.data_pagamento is not None)
    total_pendente = sum(v.valor_total for v in vendas if v.status == 'finalizada' and v.data_pagamento is None)
    total_cancelado = sum(v.valor_total for v in vendas if v.status == 'cancelada')
    
    # Formata as datas para exibição
    data_inicio_str = data_inicio.strftime('%d/%m/%Y')
    data_fim_str = (data_fim - timedelta(days=1)).strftime('%d/%m/%Y')
    
    # Dados para o gráfico de vendas por dia
    vendas_por_dia = db.session.query(
        func.date(Venda.data_venda).label('data'),
        func.sum(Venda.valor_total).label('total'),
        func.count(Venda.id).label('quantidade')
    ).filter(
        Venda.data_venda.between(data_inicio, data_fim)
    ).group_by(
        func.date(Venda.data_venda)
    ).order_by('data').all()
    
    # Prepara os dados para o gráfico
    datas = [datetime.strptime(str(v.data), '%Y-%m-%d').strftime('%d/%m') for v in vendas_por_dia if v.data is not None]
    valores = [float(v.total) if v.total is not None else 0.0 for v in vendas_por_dia]
    
    # Cria o gráfico
    plt.figure(figsize=(12, 6))
    plt.bar(datas, valores, color='#4e73df')
    plt.title(f'Vendas por Dia - {data_inicio_str} a {data_fim_str}')
    plt.xlabel('Data')
    plt.ylabel('Valor Total (R$)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Salva o gráfico em memória
    img = BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    plt.close()
    
    # Converte a imagem para base64 para exibição no template
    import base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    return render_template('relatorios/financeiro.html',
                         data_inicio=data_inicio.strftime('%Y-%m-%d'),
                         data_fim=(data_fim - timedelta(days=1)).strftime('%Y-%m-%d'),
                         total_vendas=total_vendas,
                         total_recebido=total_recebido,
                         total_pendente=total_pendente,
                         total_cancelado=total_cancelado,
                         vendas_por_dia=vendas_por_dia,
                         grafico_vendas=img_base64,
                         vendas=vendas)

@bp.route('/exportar/financeiro')
@login_required
@financeiro_required
def exportar_relatorio_financeiro():
    """Exporta o relatório financeiro para Excel"""
    if not has_permission(current_user, 'relatorios.exportar_relatorio_financeiro'):
        abort(403)
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Consulta de vendas
    query = Venda.query
    
    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        query = query.filter(Venda.data_venda >= data_inicio)
    
    if data_fim:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Venda.data_venda <= data_fim)
    
    vendas = query.order_by(Venda.data_venda).all()
    
    # Prepara os dados para o Excel
    data = []
    for venda in vendas:
        data.append({
            'ID': venda.id,
            'Data': venda.data_venda.strftime('%d/%m/%Y %H:%M'),
            'Cliente': venda.cliente.nome if venda.cliente else 'Não informado',
            'Valor Total': venda.valor_total,
            'Status': venda.status.capitalize(),
            'Forma de Pagamento': venda.forma_pagamento.replace('_', ' ').title(),
            'Data Pagamento': venda.data_pagamento.strftime('%d/%m/%Y %H:%M') if venda.data_pagamento else 'N/A',
            'Data Cancelamento': venda.data_cancelamento.strftime('%d/%m/%Y %H:%M') if venda.data_cancelamento else 'N/A'
        })
    
    # Cria o DataFrame
    df = pd.DataFrame(data)
    
    # Cria o arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório Financeiro')
        
        # Formatação da planilha
        workbook = writer.book
        worksheet = writer.sheets['Relatório Financeiro']
        
        # Ajusta a largura das colunas
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = column_length
    
    output.seek(0)
    
    # Gera o nome do arquivo com a data
    data_geracao = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f'relatorio_financeiro_{data_geracao}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/estoque')
@login_required
@producao_required
def relatorio_estoque():
    """Gera relatório de estoque atual"""
    if not has_permission(current_user, 'relatorios.relatorio_estoque'):
        abort(403)
    # Obtém todos os produtos ativos ordenados por nome
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    
    # Calcula totais
    total_produtos = len(produtos)
    total_estoque = sum(p.estoque_atual for p in produtos)
    total_valor_estoque = sum(p.estoque_atual * p.preco_compra for p in produtos)
    
    # Obtém a data e hora atual
    data_geracao = datetime.now()
    
    # Verifica produtos com estoque abaixo do mínimo
    produtos_baixo_estoque = [p for p in produtos if p.estoque_atual < p.estoque_minimo]
    
    return render_template('relatorios/estoque.html',
                         produtos=produtos,
                         total_produtos=total_produtos,
                         total_estoque=total_estoque,
                         total_valor_estoque=total_valor_estoque,
                         produtos_baixo_estoque=produtos_baixo_estoque,
                         data_geracao=data_geracao)

@bp.route('/exportar/estoque')
@login_required
@producao_required
def exportar_relatorio_estoque():
    """Exporta o relatório de estoque para Excel"""
    if not has_permission(current_user, 'relatorios.exportar_relatorio_estoque'):
        abort(403)
    # Obtém todos os produtos ativos ordenados por nome
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    
    # Prepara os dados para o Excel
    data = []
    for produto in produtos:
        valor_total = produto.estoque_atual * produto.preco_compra
        status_estoque = 'Abaixo do Mínimo' if produto.estoque_atual < produto.estoque_minimo else 'OK'
        
        data.append({
            'Código': produto.codigo,
            'Produto': produto.nome,
            'Estoque Atual': produto.estoque_atual,
            'Estoque Mínimo': produto.estoque_minimo,
            'Unidade de Medida': produto.unidade_medida,
            'Preço de Compra': produto.preco_compra,
            'Preço de Venda': produto.preco_venda,
            'Valor Total em Estoque': valor_total,
            'Status': status_estoque
        })
    
    # Cria o DataFrame
    df = pd.DataFrame(data)
    
    # Cria o arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório de Estoque')
        
        # Formatação da planilha
        workbook = writer.book
        worksheet = writer.sheets['Relatório de Estoque']
        
        # Ajusta a largura das colunas
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = column_length
            
            # Formata colunas numéricas
            if column in ['Preço de Compra', 'Preço de Venda', 'Valor Total em Estoque']:
                for row in range(2, len(df) + 2):
                    cell = worksheet.cell(row=row, column=col_idx + 1)
                    cell.number_format = 'R$ #,##0.00'
    
    output.seek(0)
    
    # Gera o nome do arquivo com a data
    data_geracao = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f'relatorio_estoque_{data_geracao}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
