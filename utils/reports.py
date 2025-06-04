from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

def register_fonts():
    """Registra fontes personalizadas"""
    # Caminho para as fontes (ajuste conforme necessário)
    font_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
    
    # Tenta registrar a fonte Arial (ou outra fonte padrão)
    try:
        pdfmetrics.registerFont(TTFont('Arial', os.path.join(font_dir, 'Arial.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(font_dir, 'Arial-Bold.ttf')))
    except:
        # Usa a fonte padrão do ReportLab se não encontrar a fonte personalizada
        pass

def get_report_styles():
    """Retorna os estilos para o relatório"""
    styles = getSampleStyleSheet()
    
    # Estilo para o título
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    
    # Estilo para o subtítulo
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=30
    ))
    
    # Estilo para o cabeçalho da tabela
    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Arial-Bold'
    ))
    
    # Estilo para as células da tabela
    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        fontName='Arial'
    ))
    
    # Estilo para o rodapé
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceBefore=20
    ))
    
    return styles

def create_pdf_report(title, data, columns, filename=None, user=None):
    """
    Cria um relatório em PDF com os dados fornecidos
    
    Args:
        title: Título do relatório
        data: Lista de dicionários com os dados
        columns: Lista de tuplas (chave, título, largura)
        filename: Nome do arquivo para salvar (None para retornar o buffer)
        user: Usuário que gerou o relatório
        
    Returns:
        BytesIO: Buffer com o PDF gerado ou None se foi salvo em arquivo
    """
    # Registra as fontes
    register_fonts()
    
    # Configura o documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        filename or buffer,
        pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=50, bottomMargin=50
    )
    
    # Estilos
    styles = get_report_styles()
    
    # Conteúdo do relatório
    story = []
    
    # Cabeçalho
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=0.8*inch)
        story.append(logo)
        story.append(Spacer(1, 20))
    
    # Título
    story.append(Paragraph(title, styles['Title']))
    
    # Subtítulo
    subtitle = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if user:
        subtitle += f" | Usuário: {user.nome} ({user.email})"
    story.append(Paragraph(subtitle, styles['Subtitle']))
    
    # Tabela de dados
    if data and columns:
        # Cabeçalho da tabela
        table_data = [[col[1] for col in columns]]
        
        # Dados da tabela
        for item in data:
            row = []
            for col in columns:
                value = item.get(col[0], '')
                # Formata valores especiais
                if isinstance(value, datetime):
                    value = value.strftime('%d/%m/%Y %H:%M')
                elif isinstance(value, bool):
                    value = 'Sim' if value else 'Não'
                row.append(Paragraph(str(value), styles['TableCell']))
            table_data.append(row)
        
        # Cria a tabela
        col_widths = [col[2] * cm for col in columns]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Estilo da tabela
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a6fa5')),  # Cabeçalho
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Linhas pares
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Adiciona zebrado
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
        
        table.setStyle(TableStyle(table_style))
        story.append(table)
    else:
        story.append(Paragraph("Nenhum dado disponível para exibição.", styles['Normal']))
    
    # Rodapé
    footer = f"SisOvos - Sistema de Gerenciamento de Vendas de Ovos | Página <page>"
    story.append(Paragraph(footer, styles['Footer']))
    
    # Gera o PDF
    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )
    
    if filename:
        return None
    
    buffer.seek(0)
    return buffer

def add_page_number(canvas, doc):
    """Adiciona número de página ao rodapé"""
    page_num = canvas.getPageNumber()
    text = f"Página {page_num}"
    canvas.saveState()
    canvas.setFont('Arial', 8)
    canvas.drawRightString(200*mm, 10*mm, text)
    canvas.restoreState()

def generate_sales_report(vendas, filename=None, user=None):
    """Gera um relatório de vendas"""
    columns = [
        ('id', 'ID', 2),
        ('data_venda', 'Data', 4),
        ('cliente_nome', 'Cliente', 6),
        ('valor_total', 'Valor Total', 4),
        ('status', 'Status', 3)
    ]
    
    # Prepara os dados
    data = []
    for venda in vendas:
        data.append({
            'id': venda.id,
            'data_venda': venda.data_venda,
            'cliente_nome': venda.cliente.nome if venda.cliente else 'Consumidor',
            'valor_total': f'R$ {venda.valor_total:.2f}',
            'status': venda.status
        })
    
    return create_pdf_report(
        title='Relatório de Vendas',
        data=data,
        columns=columns,
        filename=filename,
        user=user
    )

def generate_inventory_report(estoque, filename=None, user=None):
    """Gera um relatório de estoque"""
    columns = [
        ('produto', 'Produto', 6),
        ('quantidade', 'Quantidade', 3),
        ('valor_unitario', 'Valor Unitário', 3),
        ('valor_total', 'Valor Total', 3)
    ]
    
    # Prepara os dados
    data = []
    for item in estoque:
        data.append({
            'produto': item.produto.nome,
            'quantidade': item.quantidade,
            'valor_unitario': f'R$ {item.valor_unitario:.2f}',
            'valor_total': f'R$ {item.quantidade * item.valor_unitario:.2f}'
        })
    
    return create_pdf_report(
        title='Relatório de Estoque',
        data=data,
        columns=columns,
        filename=filename,
        user=user
    )
