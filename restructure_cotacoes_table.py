import sqlite3
import os

# Recria a tabela cotacoes com a nova estrutura otimizada
db_path = os.path.join('instance', 'database.sqlite')

if os.path.exists(db_path):
    print(f"🔧 Reestruturando tabela cotacoes...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Backup dos dados existentes (se houver)
        cursor.execute("SELECT COUNT(*) FROM cotacoes;")
        existing_records = cursor.fetchone()[0]
        print(f"📊 Registros existentes em cotacoes: {existing_records}")
        
        if existing_records > 0:
            print(f"💾 Fazendo backup dos dados existentes...")
            cursor.execute("""
                CREATE TABLE cotacoes_backup AS 
                SELECT * FROM cotacoes;
            """)
        
        # Remove a tabela antiga
        cursor.execute("DROP TABLE IF EXISTS cotacoes;")
        print(f"🗑️ Tabela antiga removida")
        
        # Cria a nova tabela com estrutura otimizada
        cursor.execute("""
            CREATE TABLE cotacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                numero_cotacao TEXT,
                numero_revisao TEXT,
                linhas_cotacao TEXT,
                status_cotacao TEXT,
                cod_cliente TEXT,
                cliente TEXT,
                data DATE,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            );
        """)
        print(f"✅ Nova tabela cotacoes criada com estrutura otimizada!")
        
        # Verifica a nova estrutura
        cursor.execute("PRAGMA table_info(cotacoes);")
        columns = cursor.fetchall()
        print(f"📊 Nova estrutura da tabela cotacoes:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.commit()
        print(f"✅ Estrutura atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao reestruturar tabela: {str(e)}")
        conn.rollback()
    
    conn.close()
else:
    print(f"❌ Banco de dados não encontrado: {db_path}")
