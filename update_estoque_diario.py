"""
Script para atualizar a tabela EstoqueDiario com os campos necessários.
Execute este script uma única vez para adicionar os campos ausentes.
"""
from app import app, db
from models import EstoqueDiario

def atualizar_estoque_diario():
    """Adiciona os campos ausentes na tabela EstoqueDiario"""
    with app.app_context():
        # Obtém o engine do banco de dados
        engine = db.engine
        
        # Verifica se a tabela existe
        if not engine.dialect.has_table(engine, 'estoque_diario'):
            print("A tabela 'estoque_diario' não existe. Nenhuma alteração necessária.")
            return
        
        # Verifica se as colunas já existem
        inspector = db.inspect(engine)
        columns = [column['name'] for column in inspector.get_columns('estoque_diario')]
        
        # Lista de colunas a serem adicionadas
        colunas_para_adicionar = [
            ('entrada', 'FLOAT DEFAULT 0.0 NOT NULL'),
            ('saida', 'FLOAT DEFAULT 0.0 NOT NULL'),
            ('estoque_inicial', 'FLOAT NOT NULL'),
            ('estoque_final', 'FLOAT NOT NULL'),
            ('observacoes', 'TEXT'),
            ('usuario_id', 'INTEGER NOT NULL')
        ]
        
        # Adiciona as colunas que não existem
        with engine.connect() as conn:
            for coluna, tipo in colunas_para_adicionar:
                if coluna not in columns:
                    try:
                        # Tenta adicionar a coluna
                        alter_sql = f"ALTER TABLE estoque_diario ADD COLUMN {coluna} {tipo}"
                        conn.execute(alter_sql)
                        print(f"Coluna '{coluna}' adicionada com sucesso.")
                        
                        # Se for a coluna usuario_id, adiciona a chave estrangeira
                        if coluna == 'usuario_id':
                            fk_sql = """
                            ALTER TABLE estoque_diario 
                            ADD CONSTRAINT fk_estoque_diario_usuario
                            FOREIGN KEY(usuario_id) REFERENCES usuario(id)
                            """
                            conn.execute(fk_sql)
                            print("Chave estrangeira para usuario_id adicionada com sucesso.")
                            
                    except Exception as e:
                        print(f"Erro ao adicionar a coluna {coluna}: {str(e)}")
                else:
                    print(f"A coluna '{coluna}' já existe. Nenhuma alteração necessária.")
        
        print("Atualização da tabela EstoqueDiario concluída.")

if __name__ == '__main__':
    print("Iniciando atualização da tabela EstoqueDiario...")
    atualizar_estoque_diario()
    print("Processo concluído.")
