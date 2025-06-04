import sqlite3
from datetime import datetime

def update_estoque_diario_schema():
    try:
        # Conecta ao banco de dados
        db_path = "instance/sisovos.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Verificando colunas da tabela 'estoque_diario'...")
        
        # Obtém as colunas atuais da tabela
        cursor.execute("PRAGMA table_info(estoque_diario);")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Colunas atuais: {', '.join(columns)}")
        
        # Colunas que precisam ser adicionadas
        columns_to_add = [
            'entrada FLOAT DEFAULT 0',
            'saida FLOAT DEFAULT 0',
            'estoque_inicial FLOAT DEFAULT 0',
            'estoque_final FLOAT DEFAULT 0',
            'observacoes TEXT',
            'usuario_id INTEGER',
            'FOREIGN KEY (usuario_id) REFERENCES usuario (id)'
        ]
        
        # Adiciona cada coluna que não existe
        for column_def in columns_to_add:
            # Extrai o nome da coluna da definição
            column_name = column_def.split(' ')[0]
            
            if column_name not in columns and not column_name.startswith('FOREIGN'):
                print(f"Adicionando coluna '{column_name}'...")
                try:
                    cursor.execute(f"ALTER TABLE estoque_diario ADD COLUMN {column_def};")
                    print(f"Coluna '{column_name}' adicionada com sucesso!")
                except sqlite3.Error as e:
                    print(f"Erro ao adicionar coluna '{column_name}': {e}")
        
        # Verifica e adiciona a chave estrangeira se não existir
        cursor.execute("PRAGMA foreign_key_list(estoque_diario);")
        fk_exists = any(fk[3] == 'usuario_id' for fk in cursor.fetchall())
        
        if not fk_exists:
            print("Adicionando chave estrangeira para usuario_id...")
            try:
                # SQLite não suporta adicionar FOREIGN KEY com ALTER TABLE diretamente
                # Então precisamos criar uma nova tabela, copiar os dados e renomear
                cursor.execute("PRAGMA foreign_keys=off;")
                
                # Cria uma tabela temporária com a nova estrutura
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS estoque_diario_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data DATE NOT NULL,
                        produto_id INTEGER NOT NULL,
                        quantidade FLOAT NOT NULL,
                        valor_estoque FLOAT NOT NULL,
                        entrada FLOAT DEFAULT 0,
                        saida FLOAT DEFAULT 0,
                        estoque_inicial FLOAT DEFAULT 0,
                        estoque_final FLOAT DEFAULT 0,
                        observacoes TEXT,
                        usuario_id INTEGER,
                        FOREIGN KEY (produto_id) REFERENCES produto (id),
                        FOREIGN KEY (usuario_id) REFERENCES usuario (id)
                    )
                """)
                
                # Copia os dados da tabela antiga para a nova
                cursor.execute("""
                    INSERT INTO estoque_diario_new (
                        id, data, produto_id, quantidade, valor_estoque,
                        entrada, saida, estoque_inicial, estoque_final, observacoes, usuario_id
                    )
                    SELECT 
                        id, data, produto_id, quantidade, valor_estoque,
                        0, 0, 0, 0, NULL, NULL
                    FROM estoque_diario
                """)
                
                # Remove a tabela antiga e renomeia a nova
                cursor.execute("DROP TABLE estoque_diario;")
                cursor.execute("ALTER TABLE estoque_diario_new RENAME TO estoque_diario;")
                cursor.execute("PRAGMA foreign_keys=on;")
                
                print("Chave estrangeira adicionada com sucesso!")
            except sqlite3.Error as e:
                print(f"Erro ao adicionar chave estrangeira: {e}")
        else:
            print("Chave estrangeira já existe.")
        
        # Confirma as alterações
        conn.commit()
        conn.close()
        
        print("\nAtualização do esquema concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro ao atualizar o esquema do banco de dados: {e}")

if __name__ == "__main__":
    print("=== Atualização do Esquema da Tabela Estoque Diário ===")
    update_estoque_diario_schema()
    input("\nPressione Enter para sair...")
