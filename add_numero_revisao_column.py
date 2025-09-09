import sqlite3
import os

# Adiciona a coluna numero_revisao na tabela cotacoes
db_path = os.path.join('instance', 'database.sqlite')

if os.path.exists(db_path):
    print(f"🔧 Adicionando coluna numero_revisao na tabela cotacoes...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Adiciona a coluna numero_revisao
        cursor.execute("ALTER TABLE cotacoes ADD COLUMN numero_revisao TEXT;")
        conn.commit()
        print(f"✅ Coluna numero_revisao adicionada com sucesso!")
        
        # Verifica novamente a estrutura
        cursor.execute("PRAGMA table_info(cotacoes);")
        columns = cursor.fetchall()
        print(f"📊 Nova estrutura da tabela cotacoes:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {str(e)}")
        if "duplicate column name" in str(e).lower():
            print(f"✅ Coluna numero_revisao já existe!")
    
    conn.close()
else:
    print(f"❌ Banco de dados não encontrado: {db_path}")
