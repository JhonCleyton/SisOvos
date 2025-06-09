"""
Script para adicionar a tabela historico_estoque ao banco de dados.
Execute este script uma única vez para criar a tabela.
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import HistoricoEstoque

def add_historico_estoque_table():
    """Cria a tabela historico_estoque no banco de dados."""
    app = create_app()
    
    with app.app_context():
        # Obtém o inspetor do banco de dados
        inspector = db.inspect(db.engine)
        
        # Verifica se a tabela já existe
        if 'historico_estoque' not in inspector.get_table_names():
            try:
                # Cria a tabela
                db.create_all()
                print("Tabela 'historico_estoque' criada com sucesso!")
                
                # Verifica se a tabela foi criada
                if 'historico_estoque' in db.inspect(db.engine).get_table_names():
                    print("Verificação: Tabela 'historico_estoque' existe no banco de dados.")
                else:
                    print("ERRO: A tabela 'historico_estoque' não foi criada.")
                    
            except Exception as e:
                print(f"Erro ao criar a tabela 'historico_estoque': {str(e)}")
        else:
            print("A tabela 'historico_estoque' já existe no banco de dados.")

if __name__ == '__main__':
    add_historico_estoque_table()
