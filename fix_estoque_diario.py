"""
Script para adicionar manualmente os campos necessários à tabela EstoqueDiario.
Execute este script diretamente com o Python.
"""
import sqlite3
import os
import sys

def main():
    # Caminho para o banco de dados SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'sistema_ovos.db')
    
    # Se o banco de dados não existir, não há nada para fazer
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        print("Verifique se o caminho está correto e tente novamente.")
        sys.exit(1)
    
    print(f"Conectando ao banco de dados em {db_path}...")
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista de colunas para adicionar
        colunas = [
            ('entrada', 'FLOAT DEFAULT 0.0 NOT NULL'),
            ('saida', 'FLOAT DEFAULT 0.0 NOT NULL'),
            ('estoque_inicial', 'FLOAT NOT NULL DEFAULT 0.0'),
            ('estoque_final', 'FLOAT NOT NULL DEFAULT 0.0'),
            ('observacoes', 'TEXT'),
            ('usuario_id', 'INTEGER')
        ]
        
        # Verifica cada coluna e adiciona se não existir
        for coluna, tipo in colunas:
            try:
                # Verifica se a coluna já existe
                cursor.execute(f"ALTER TABLE estoque_diario ADD COLUMN {coluna} {tipo}")
                print(f"✅ Coluna '{coluna}' adicionada com sucesso.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"ℹ️  Coluna '{coluna}' já existe.")
                else:
                    print(f"❌ Erro ao adicionar coluna '{coluna}': {e}")
        
        # Tenta adicionar a chave estrangeira para usuario_id
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estoque_diario_new (
                    id INTEGER PRIMARY KEY,
                    data DATE NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade FLOAT NOT NULL,
                    valor_estoque FLOAT NOT NULL,
                    entrada FLOAT DEFAULT 0.0 NOT NULL,
                    saida FLOAT DEFAULT 0.0 NOT NULL,
                    estoque_inicial FLOAT NOT NULL DEFAULT 0.0,
                    estoque_final FLOAT NOT NULL DEFAULT 0.0,
                    observacoes TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY(produto_id) REFERENCES produto(id),
                    FOREIGN KEY(usuario_id) REFERENCES usuario(id)
                )
            """)
            
            # Copia os dados da tabela antiga para a nova
            cursor.execute("""
                INSERT INTO estoque_diario_new 
                SELECT id, data, produto_id, quantidade, valor_estoque, 
                       0.0, 0.0, 0.0, 0.0, NULL, NULL 
                FROM estoque_diario
            """)
            
            # Remove a tabela antiga e renomeia a nova
            cursor.execute("DROP TABLE estoque_diario")
            cursor.execute("ALTER TABLE estoque_diario_new RENAME TO estoque_diario")
            
            # Recria os índices
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_estoque_diario_data_produto 
                ON estoque_diario (data, produto_id)
            """)
            
            print("✅ Tabela estoque_diario recriada com a estrutura correta.")
            
        except sqlite3.Error as e:
            print(f"⚠️  Aviso: Não foi possível recriar a tabela com as chaves estrangeiras: {e}")
            print("A estrutura básica foi atualizada, mas você pode precisar configurar as chaves estrangeiras manualmente.")
        
        # Confirma as alterações
        conn.commit()
        print("\n✅ Atualização do banco de dados concluída com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao acessar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados encerrada.")

if __name__ == "__main__":
    print("=== Atualização da Tabela EstoqueDiario ===")
    print("Este script irá adicionar os campos necessários à tabela EstoqueDiario.")
    print("Iniciando processo...\n")
    
    try:
        main()
        print("\n✅ Processo concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante a execução: {e}")
        print("Por favor, verifique as mensagens de erro acima e tente novamente.")
        sys.exit(1)
