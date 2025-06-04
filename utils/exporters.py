import csv
import json
import xlsxwriter
from io import StringIO, BytesIO
from datetime import datetime
from flask import Response, send_file

class BaseExporter:
    """Classe base para exportação de dados"""
    
    def __init__(self, data, columns, title=None):
        """
        Inicializa o exportador
        
        Args:
            data: Lista de dicionários com os dados a serem exportados
            columns: Lista de tuplas (chave, título, largura) ou (chave, título)
            title: Título do relatório
        """
        self.data = data or []
        self.columns = columns or []
        self.title = title or 'Relatório'
        self.filename = f"{self.title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def export(self):
        """Método principal para exportar os dados"""
        raise NotImplementedError("Método export() deve ser implementado pelas subclasses")


class CSVExporter(BaseExporter):
    """Exporta dados para CSV"""
    
    def export(self, delimiter=','):
        """
        Exporta os dados para CSV
        
        Args:
            delimiter: Delimitador de campos
            
        Returns:
            Response: Resposta HTTP com o arquivo CSV
        """
        if not self.data or not self.columns:
            return None
        
        # Cria um buffer de string para o CSV
        si = StringIO()
        
        # Extrai os cabeçalhos das colunas
        fieldnames = [col[0] for col in self.columns]
        headers = {col[0]: col[1] for col in self.columns}
        
        # Cria o escritor CSV
        writer = csv.DictWriter(si, fieldnames=fieldnames, delimiter=delimiter)
        
        # Escreve o cabeçalho
        writer.writerow(headers)
        
        # Escreve os dados
        for row in self.data:
            # Filtra apenas as colunas desejadas
            filtered_row = {k: row.get(k, '') for k in fieldnames}
            writer.writerow(filtered_row)
        
        # Prepara a resposta
        output = si.getvalue()
        si.close()
        
        return Response(
            output,
            mimetype=f"text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment;filename={self.filename}.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )


class ExcelExporter(BaseExporter):
    """Exporta dados para Excel (XLSX)"""
    
    def export(self):
        """
        Exporta os dados para Excel (XLSX)
        
        Returns:
            Response: Resposta HTTP com o arquivo XLSX
        """
        if not self.data or not self.columns:
            return None
        
        # Cria um buffer de bytes para o Excel
        output = BytesIO()
        
        # Cria um novo arquivo Excel
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        
        # Formatações
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4a6fa5',
            'border': 1,
            'color': 'white'
        })
        
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        datetime_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
        currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        
        # Larguras das colunas
        for col_num, column in enumerate(self.columns):
            width = column[2] if len(column) > 2 else 15
            worksheet.set_column(col_num, col_num, width)
        
        # Cabeçalhos
        for col_num, column in enumerate(self.columns):
            worksheet.write(0, col_num, column[1], header_format)
        
        # Dados
        for row_num, row_data in enumerate(self.data, 1):
            for col_num, column in enumerate(self.columns):
                col_key = column[0]
                value = row_data.get(col_key, '')
                
                # Aplica formatação com base no tipo de dado
                cell_format = None
                
                if isinstance(value, datetime):
                    if value.hour == 0 and value.minute == 0:
                        cell_format = date_format
                    else:
                        cell_format = datetime_format
                elif col_key.lower().endswith(('valor', 'preco', 'total', 'custo')) and isinstance(value, (int, float)):
                    cell_format = currency_format
                
                # Escreve a célula
                if cell_format:
                    worksheet.write(row_num, col_num, value, cell_format)
                else:
                    worksheet.write(row_num, col_num, value)
        
        # Fecha o workbook
        workbook.close()
        
        # Prepara a resposta
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{self.filename}.xlsx"
        )


class JSONExporter(BaseExporter):
    """Exporta dados para JSON"""
    
    def export(self, indent=2):
        """
        Exporta os dados para JSON
        
        Args:
            indent: Indentação do JSON
            
        Returns:
            Response: Resposta HTTP com o arquivo JSON
        """
        if not self.data:
            return None
        
        # Filtra apenas as colunas desejadas
        fieldnames = [col[0] for col in self.columns] if self.columns else None
        
        if fieldnames:
            filtered_data = []
            for item in self.data:
                filtered_item = {k: v for k, v in item.items() if k in fieldnames}
                filtered_data.append(filtered_item)
        else:
            filtered_data = self.data
        
        # Converte para JSON
        output = json.dumps(
            {
                'title': self.title,
                'generated_at': datetime.now().isoformat(),
                'count': len(filtered_data),
                'data': filtered_data
            },
            indent=indent,
            ensure_ascii=False,
            default=str
        )
        
        return Response(
            output,
            mimetype='application/json; charset=utf-8',
            headers={
                "Content-Disposition": f"attachment;filename={self.filename}.json"
            }
        )


def export_data(data, columns, format_type, title=None):
    """
    Função auxiliar para exportar dados em diferentes formatos
    
    Args:
        data: Lista de dicionários com os dados
        columns: Lista de tuplas (chave, título, largura) ou (chave, título)
        format_type: 'csv', 'excel' ou 'json'
        title: Título do relatório
        
    Returns:
        Response: Resposta HTTP com o arquivo gerado
    """
    format_type = format_type.lower()
    
    if format_type == 'csv':
        exporter = CSVExporter(data, columns, title)
    elif format_type == 'excel':
        exporter = ExcelExporter(data, columns, title)
    elif format_type == 'json':
        exporter = JSONExporter(data, columns, title)
    else:
        raise ValueError(f"Formato não suportado: {format_type}")
    
    return exporter.export()
