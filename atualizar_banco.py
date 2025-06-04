"""
Script para atualizar a tabela EstoqueDiario com os campos necessários.
"""
from app import app, db
from models import EstoqueDiario

def main():
    print("Iniciando atualização da tabela EstoqueDiario...")
    
    with app.app_context():
        # Verifica se a tabela existe
        if not db.engine.dialect.has_table(db.engine, 'estoque_diario'):
            print("A tabela 'estoque_diario' não existe. Criando...")
            db.create_all()
        
        # Executa a migração para adicionar as novas colunas
        try:
            # Adiciona as colunas se não existirem
            with db.engine.connect() as conn:
                # Verifica e adiciona cada coluna individualmente
                
                # Coluna 'entrada'
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN entrada FLOAT DEFAULT 0.0 NOT NULL")
                    print("Coluna 'entrada' adicionada com sucesso.")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'entrada' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'entrada': {e}")
                
                # Coluna 'saida'
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN saida FLOAT DEFAULT 0.0 NOT NULL")
                    print("Coluna 'saida' adicionada com sucesso.")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'saida' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'saida': {e}")
                
                # Coluna 'estoque_inicial'
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN estoque_inicial FLOAT NOT NULL DEFAULT 0.0")
                    print("Coluna 'estoque_inicial' adicionada com sucesso.")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'estoque_inicial' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'estoque_inicial': {e}")
                
                # Coluna 'estoque_final'
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN estoque_final FLOAT NOT NULL DEFAULT 0.0")
                    print("Coluna 'estoque_final' adicionada com sucesso.")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'estoque_final' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'estoque_final': {e}")
                
                # Coluna 'observacoes'
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN observacoes TEXT")
                    print("Coluna 'observacoes' adicionada com sucesso.")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'observacoes' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'observacoes': {e}")
                
                # Coluna 'usuario_id' e chave estrangeira
                try:
                    conn.execute("ALTER TABLE estoque_diario ADD COLUMN usuario_id INTEGER")
                    print("Coluna 'usuario_id' adicionada com sucesso.")
                    
                    # Tenta adicionar a chave estrangeira
                    try:
                        conn.execute("""
                            ALTER TABLE estoque_diario 
                            ADD CONSTRAINT fk_estoque_diario_usuario
                            FOREIGN KEY(usuario_id) REFERENCES usuario(id)
                        """)
                        print("Chave estrangeira para 'usuario_id' adicionada com sucesso.")
                    except Exception as e:
                        print(f"Aviso: Não foi possível adicionar a chave estrangeira: {e}")
                        print("Você pode precisar adicionar manualmente a chave estrangeira.")
                        
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna 'usuario_id' já existe.")
                    else:
                        print(f"Erro ao adicionar coluna 'usuario_id': {e}")
            
            print("\n✅ Atualização da tabela EstoqueDiario concluída com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Ocorreu um erro durante a atualização: {e}")
            print("Verifique se você tem permissões suficientes no banco de dados.")

if __name__ == '__main__':
    main()
