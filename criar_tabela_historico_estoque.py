"""
Script para criar a tabela historico_estoque no banco de dados.
"""
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import HistoricoEstoque

def criar_tabela_historico_estoque():
    """Cria a tabela historico_estoque no banco de dados."""
    app = create_app()
    
    with app.app_context():
        # Cria todas as tabelas definidas nos modelos
        db.create_all()
        print("Tabelas criadas com sucesso!")
        
        # Verifica se a tabela foi criada
        inspector = db.inspect(db.engine)
        if 'historico_estoque' in inspector.get_table_names():
            print("A tabela 'historico_estoque' foi criada com sucesso!")
        else:
            print("ERRO: A tabela 'historico_estoque' não foi criada.")

if __name__ == '__main__':
    criar_tabela_historico_estoque()
