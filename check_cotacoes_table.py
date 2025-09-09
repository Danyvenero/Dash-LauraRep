import sqlite3
import os

# Verifica a estrutura atual da tabela cotacoes
db_path = os.path.join('instance', 'database.sqlite')

if os.path.exists(db_path):
    print(f"✅ Verificando estrutura do banco: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica a estrutura da tabela cotacoes
    try:
        cursor.execute("PRAGMA table_info(cotacoes);")
        columns = cursor.fetchall()
        print(f"📊 Estrutura atual da tabela cotacoes:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verifica se numero_revisao existe
        col_names = [col[1] for col in columns]
        if 'numero_revisao' in col_names:
            print(f"✅ Coluna numero_revisao EXISTE")
        else:
            print(f"❌ Coluna numero_revisao NÃO EXISTE")
            print(f"💡 Será necessário fazer ALTER TABLE")
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabela cotacoes: {str(e)}")
    
    conn.close()
else:
    print(f"❌ Banco de dados não encontrado: {db_path}")
