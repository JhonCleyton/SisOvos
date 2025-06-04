import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, flash
from PIL import Image
from io import BytesIO
import magic

# Tipos de arquivo permitidos
ALLOWED_EXTENSIONS = {
    'image': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'},
    'archive': {'zip', 'rar', '7z'}
}

def allowed_file(filename, file_type='image'):
    """Verifica se o arquivo tem uma extensão permitida"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, set())

def get_file_type(file_stream):
    """Determina o tipo do arquivo baseado no conteúdo"""
    # Lê os primeiros 2048 bytes para identificar o tipo
    header = file_stream.read(2048)
    file_stream.seek(0)  # Volta para o início do arquivo
    
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(header)
    
    return file_type

def save_uploaded_file(file, folder='uploads', allowed_types=None, max_size_mb=5):
    """
    Salva um arquivo enviado pelo usuário
    
    Args:
        file: Objeto de arquivo do Flask
        folder: Pasta de destino dentro do diretório de uploads
        allowed_types: Lista de tipos MIME permitidos (None para todos)
        max_size_mb: Tamanho máximo do arquivo em MB
        
    Returns:
        str: Caminho relativo do arquivo salvo ou None em caso de erro
    """
    if not file or file.filename == '':
        flash('Nenhum arquivo selecionado.', 'warning')
        return None
    
    # Verifica o tamanho do arquivo
    file_stream = file.stream
    file_size = len(file_stream.read())
    file_stream.seek(0)  # Volta para o início do arquivo
    
    if file_size > max_size_mb * 1024 * 1024:  # Converte MB para bytes
        flash(f'O arquivo é muito grande. O tamanho máximo permitido é {max_size_mb}MB.', 'warning')
        return None
    
    # Verifica o tipo do arquivo
    file_type = get_file_type(file_stream)
    
    if allowed_types and file_type not in allowed_types:
        flash(f'Tipo de arquivo não suportado. Tipos permitidos: {", ".join(allowed_types)}', 'warning')
        return None
    
    # Cria um nome seguro para o arquivo
    original_filename = secure_filename(file.filename)
    ext = os.path.splitext(original_filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    
    # Cria o diretório se não existir
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    # Caminho completo do arquivo
    filepath = os.path.join(upload_folder, filename)
    
    try:
        # Salva o arquivo
        file.save(filepath)
        
        # Se for uma imagem, otimiza
        if file_type.startswith('image/'):
            optimize_image(filepath)
        
        # Retorna o caminho relativo
        return os.path.join(folder, filename)
        
    except Exception as e:
        current_app.logger.error(f'Erro ao salvar arquivo: {str(e)}')
        flash('Erro ao processar o arquivo. Por favor, tente novamente.', 'danger')
        return None

def optimize_image(filepath, max_size=(1200, 1200), quality=85):
    """
    Otimiza uma imagem redimensionando e comprimindo
    
    Args:
        filepath: Caminho completo da imagem
        max_size: Tamanho máximo (largura, altura)
        quality: Qualidade da imagem (0-100)
    """
    try:
        with Image.open(filepath) as img:
            # Converte para RGB se for RGBA (para evitar problemas com JPEG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensiona mantendo a proporção
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Salva a imagem otimizada
            img.save(
                filepath,
                optimize=True,
                quality=quality,
                progressive=True
            )
            
    except Exception as e:
        current_app.logger.error(f'Erro ao otimizar imagem {filepath}: {str(e)}')

def delete_file(filepath):
    """Remove um arquivo do sistema de arquivos"""
    if not filepath:
        return False
    
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
        if os.path.isfile(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f'Erro ao remover arquivo {filepath}: {str(e)}')
    
    return False

def get_file_url(filepath):
    """Retorna a URL para acessar o arquivo"""
    if not filepath:
        return None
    
    return f"/uploads/{filepath}"
