import re
from datetime import datetime
from wtforms.validators import ValidationError

def validar_cpf(cpf):
    """Valida um CPF"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    digito1 = resto if resto < 10 else 0
    
    if digito1 != int(cpf[9]):
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    digito2 = resto if resto < 10 else 0
    
    if digito2 != int(cpf[10]):
        return False
    
    return True

def validar_cnpj(cnpj):
    """Valida um CNPJ"""
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação do primeiro dígito verificador
    multiplicadores = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if digito1 != int(cnpj[12]):
        return False
    
    # Validação do segundo dígito verificador
    multiplicadores = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if digito2 != int(cnpj[13]):
        return False
    
    return True

def validar_telefone(telefone):
    """Valida um número de telefone (formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX)"""
    return bool(re.match(r'^\(\d{2}\) \d{4,5}-\d{4}$', str(telefone)))

def validar_email(email):
    """Valida um endereço de e-mail"""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(email)))

def validar_data(data_str, formato='%d/%m/%Y'):
    """Valida uma data no formato especificado"""
    try:
        datetime.strptime(data_str, formato)
        return True
    except (ValueError, TypeError):
        return False

def validar_hora(hora_str, formato='%H:%M'):
    """Valida um horário no formato especificado"""
    try:
        datetime.strptime(hora_str, formato)
        return True
    except (ValueError, TypeError):
        return False

class CPFValidator:
    """Validador de CPF para WTForms"""
    def __init__(self, message=None):
        self.message = message or 'CPF inválido.'
    
    def __call__(self, form, field):
        if field.data and not validar_cpf(field.data):
            raise ValidationError(self.message)

class CNPJValidator:
    """Validador de CNPJ para WTForms"""
    def __init__(self, message=None):
        self.message = message or 'CNPJ inválido.'
    
    def __call__(self, form, field):
        if field.data and not validar_cnpj(field.data):
            raise ValidationError(self.message)

class TelefoneValidator:
    """Validador de telefone para WTForms"""
    def __init__(self, message=None):
        self.message = message or 'Telefone inválido. Use o formato (XX) XXXXX-XXXX.'
    
    def __call__(self, form, field):
        if field.data and not validar_telefone(field.data):
            raise ValidationError(self.message)

class DataValidator:
    """Validador de data para WTForms"""
    def __init__(self, formato='%d/%m/%Y', message=None):
        self.formato = formato
        self.message = message or f'Data inválida. Use o formato {formato}.'
    
    def __call__(self, form, field):
        if field.data and not validar_data(field.data, self.formato):
            raise ValidationError(self.message)
