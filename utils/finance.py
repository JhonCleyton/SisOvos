from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import calendar
from sqlalchemy import extract, func, and_, or_
from models import db, Venda, Despesa, Cliente, Produto, ItemVenda

def calcular_resumo_financeiro(data_inicio=None, data_fim=None):
    """
    Calcula um resumo financeiro para o período especificado
    
    Args:
        data_inicio: Data de início do período (opcional)
        data_fim: Data de fim do período (opcional)
        
    Returns:
        dict: Dicionário com o resumo financeiro
    """
    # Filtros de data
    filtros = []
    if data_inicio:
        filtros.append(Venda.data_venda >= data_inicio)
    if data_fim:
        # Adiciona 1 dia para incluir o dia final
        filtros.append(Venda.data_venda < data_fim + timedelta(days=1))
    
    # Consulta para vendas
    query_vendas = Venda.query
    if filtros:
        query_vendas = query_vendas.filter(and_(*filtros))
    
    # Total de vendas
    total_vendas = query_vendas.with_entities(
        func.coalesce(func.sum(Venda.valor_total), Decimal('0.00'))
    ).scalar() or Decimal('0.00')
    
    # Total de itens vendidos
    total_itens = db.session.query(
        func.coalesce(func.sum(ItemVenda.quantidade), 0)
    ).join(ItemVenda.venda).filter(and_(*filtros)).scalar() or 0
    
    # Média de valor por venda
    media_por_venda = Decimal('0.00')
    total_vendas_count = query_vendas.count()
    if total_vendas_count > 0:
        media_por_venda = (total_vendas / Decimal(str(total_vendas_count))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    # Consulta para despesas
    query_despesas = Despesa.query
    if data_inicio:
        query_despesas = query_despesas.filter(Despesa.data >= data_inicio)
    if data_fim:
        query_despesas = query_despesas.filter(Despesa.data <= data_fim)
    
    # Total de despesas
    total_despesas = query_despesas.with_entities(
        func.coalesce(func.sum(Despesa.valor), Decimal('0.00'))
    ).scalar() or Decimal('0.00')
    
    # Lucro bruto
    lucro_bruto = total_vendas - total_despesas
    
    # Margem de lucro
    margem_lucro = Decimal('0.00')
    if total_vendas > 0:
        margem_lucro = ((lucro_bruto / total_vendas) * 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    return {
        'total_vendas': total_vendas,
        'total_despesas': total_despesas,
        'lucro_bruto': lucro_bruto,
        'margem_lucro': margem_lucro,
        'total_itens_vendidos': total_itens,
        'media_por_venda': media_por_venda,
        'quantidade_vendas': total_vendas_count,
        'periodo': {
            'inicio': data_inicio,
            'fim': data_fim
        }
    }

def obter_vendas_por_periodo(periodo='dia', data_referencia=None):
    """
    Obtém o total de vendas agrupado por período
    
    Args:
        periodo: 'dia', 'semana', 'mes' ou 'ano'
        data_referencia: Data de referência para o período (padrão: hoje)
        
    Returns:
        list: Lista de dicionários com os totais por período
    """
    if data_referencia is None:
        data_referencia = datetime.now().date()
    
    # Define os filtros de data com base no período
    if periodo == 'dia':
        # Últimos 7 dias
        data_inicio = data_referencia - timedelta(days=6)
        data_fim = data_referencia
        
        # Gera todas as datas do período
        dates = [data_inicio + timedelta(days=x) for x in range((data_fim - data_inicio).days + 1)]
        
        # Formata as datas para agrupamento
        date_format = '%Y-%m-%d'
        group_by = func.date(Venda.data_venda)
        
    elif periodo == 'semana':
        # Últimas 8 semanas
        data_inicio = data_referencia - timedelta(weeks=7)
        data_fim = data_referencia
        
        # Gera todas as semanas do período
        dates = [data_inicio + timedelta(weeks=x) for x in range(8)]
        
        # Formata as datas para agrupamento por semana
        date_format = 'Semana %U/%Y'
        group_by = func.concat(
            'Semana ',
            func.lpad(func.week(Venda.data_venda, 3).cast(db.String), 2, '0'),
            '/',
            func.year(Venda.data_venda)
        )
        
    elif periodo == 'mes':
        # Últimos 12 meses
        data_inicio = (data_referencia.replace(day=1) - timedelta(days=365)).replace(day=1)
        data_fim = data_referencia
        
        # Gera todos os meses do período
        dates = []
        current = data_inicio
        while current <= data_fim:
            dates.append(current)
            # Próximo mês
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
        
        # Formata as datas para agrupamento por mês
        date_format = '%b/%Y'
        group_by = func.date_format(Venda.data_venda, '%Y-%m-01')
        
    elif periodo == 'ano':
        # Últimos 5 anos
        ano_atual = data_referencia.year
        years = range(ano_atual - 4, ano_atual + 1)
        
        # Gera todos os anos do período
        dates = [datetime(year=y, month=1, day=1).date() for y in years]
        
        # Formata as datas para agrupamento por ano
        date_format = '%Y'
        group_by = func.year(Venda.data_venda)
        
    else:
        raise ValueError("Período inválido. Use 'dia', 'semana', 'mes' ou 'ano'.")
    
    # Consulta o banco de dados para obter os totais
    resultados = db.session.query(
        group_by.label('periodo'),
        func.coalesce(func.sum(Venda.valor_total), Decimal('0.00')).label('total')
    ).filter(
        Venda.data_venda.between(data_inicio, data_fim + timedelta(days=1))
    ).group_by(
        group_by
    ).order_by(
        'periodo'
    ).all()
    
    # Converte os resultados para um dicionário
    totais = {str(r.periodo): r.total for r in resultados}
    
    # Preenche os períodos sem vendas com zero
    dados = []
    for data in dates:
        if periodo == 'dia':
            chave = data.strftime('%Y-%m-%d')
            rotulo = data.strftime('%d/%m')
        elif periodo == 'semana':
            chave = f'Semana {data.strftime("%U/%Y")}'
            rotulo = chave
        elif periodo == 'mes':
            chave = data.strftime('%Y-%m-01')
            rotulo = data.strftime('%b/%Y')
        elif periodo == 'ano':
            chave = str(data.year)
            rotulo = chave
        
        dados.append({
            'periodo': rotulo,
            'total': totais.get(chave, Decimal('0.00'))
        })
    
    return dados

def obter_metricas_principais(data_inicio=None, data_fim=None):
    """
    Obtém as métricas principais para o dashboard
    
    Args:
        data_inicio: Data de início do período (opcional)
        data_fim: Data de fim do período (opcional)
        
    Returns:
        dict: Dicionário com as métricas principais
    """
    # Filtros de data
    filtros = []
    if data_inicio:
        filtros.append(Venda.data_venda >= data_inicio)
    if data_fim:
        filtros.append(Venda.data_venda < data_fim + timedelta(days=1))
    
    # Total de vendas no período
    total_vendas = Venda.query.with_entities(
        func.coalesce(func.sum(Venda.valor_total), Decimal('0.00'))
    )
    if filtros:
        total_vendas = total_vendas.filter(and_(*filtros))
    total_vendas = total_vendas.scalar() or Decimal('0.00')
    
    # Total de clientes ativos (que fizeram pelo menos uma compra no período)
    total_clientes = Cliente.query.filter(
        Cliente.id.in_(
            db.session.query(Venda.cliente_id).filter(and_(*filtros)).distinct()
        )
    ).count()
    
    # Ticket médio
    ticket_medio = Decimal('0.00')
    total_vendas_count = Venda.query.filter(and_(*filtros)).count()
    if total_vendas_count > 0:
        ticket_medio = (total_vendas / Decimal(str(total_vendas_count))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    # Produto mais vendido
    produto_mais_vendido = db.session.query(
        Produto.nome,
        func.sum(ItemVenda.quantidade).label('total_vendido')
    ).join(
        ItemVenda.produto
    ).join(
        ItemVenda.venda
    )
    
    if filtros:
        produto_mais_vendido = produto_mais_vendido.filter(and_(*filtros))
    
    produto_mais_vendido = produto_mais_vendido.group_by(
        Produto.id
    ).order_by(
        db.desc('total_vendido')
    ).first()
    
    return {
        'total_vendas': total_vendas,
        'total_clientes': total_clientes,
        'ticket_medio': ticket_medio,
        'produto_mais_vendido': {
            'nome': produto_mais_vendido[0] if produto_mais_vendido else 'Nenhum',
            'quantidade': produto_mais_vendido[1] if produto_mais_vendido else 0
        } if produto_mais_vendido else None
    }

def gerar_relatorio_financeiro(tipo_relatorio, data_inicio=None, data_fim=None):
    """
    Gera um relatório financeiro com base nos parâmetros fornecidos
    
    Args:
        tipo_relatorio: Tipo de relatório ('vendas', 'despesas', 'lucratividade')
        data_inicio: Data de início do período (opcional)
        data_fim: Data de fim do período (opcional)
        
    Returns:
        dict: Dicionário com os dados do relatório
    """
    if tipo_relatorio == 'vendas':
        return gerar_relatorio_vendas(data_inicio, data_fim)
    elif tipo_relatorio == 'despesas':
        return gerar_relatorio_despesas(data_inicio, data_fim)
    elif tipo_relatorio == 'lucratividade':
        return gerar_relatorio_lucratividade(data_inicio, data_fim)
    else:
        raise ValueError("Tipo de relatório inválido")

def gerar_relatorio_vendas(data_inicio, data_fim):
    """Gera um relatório detalhado de vendas"""
    # Implementação do relatório de vendas
    pass

def gerar_relatorio_despesas(data_inicio, data_fim):
    """Gera um relatório detalhado de despesas"""
    # Implementação do relatório de despesas
    pass

def gerar_relatorio_lucratividade(data_inicio, data_fim):
    """Gera um relatório de lucratividade"""
    # Implementação do relatório de lucratividade
    pass
