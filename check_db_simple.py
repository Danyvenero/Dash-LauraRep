import sqlite3
import os

# Conecta ao banco
db_path = r"c:\Users\danyv\OneDrive - LAURA REPRESENTACOES LTDA\WORKSPACE\dash_laurarep\instance\database.sqlite"

if os.path.exists(db_path):
    print(f"✅ Banco encontrado: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lista tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📋 Tabelas: {[t[0] for t in tables]}")
    
    # Estrutura da tabela vendas
    if ('vendas',) in tables:
        cursor.execute("PRAGMA table_info(vendas)")
        columns = cursor.fetchall()
        print(f"\n📊 Colunas da tabela vendas:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Conta registros
        cursor.execute("SELECT COUNT(*) FROM vendas")
        count = cursor.fetchone()[0]
        print(f"\n📈 Total de registros: {count}")
        
        # Verifica vlr_entrada
        try:
            cursor.execute("SELECT COUNT(vlr_entrada), SUM(vlr_entrada) FROM vendas WHERE vlr_entrada IS NOT NULL")
            entrada_stats = cursor.fetchone()
            print(f"📊 vlr_entrada - Registros não nulos: {entrada_stats[0]}, Soma: {entrada_stats[1]}")
        except Exception as e:
            print(f"❌ Erro ao consultar vlr_entrada: {e}")
    
    conn.close()
else:
    print(f"❌ Banco não encontrado: {db_path}")
