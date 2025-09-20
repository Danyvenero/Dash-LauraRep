import sqlite3

# Verifica o banco correto
try:
    conn = sqlite3.connect('instance/database.sqlite')
    tables = [x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"🗃️ instance/database.sqlite:")
    if tables:
        print(f"  Tabelas: {', '.join(tables)}")
        
        # Verifica registros em cada tabela
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  📊 {table}: {count:,} registros")
            except Exception as e:
                print(f"  ❌ {table}: erro - {e}")
                
        # Se tem as tabelas necessárias, mostra estrutura
        if 'vendas' in tables:
            print("\n📋 Estrutura da tabela vendas:")
            columns = conn.execute("PRAGMA table_info(vendas)").fetchall()
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
                
        if 'produtos_cotados' in tables:
            print("\n📋 Estrutura da tabela produtos_cotados:")
            columns = conn.execute("PRAGMA table_info(produtos_cotados)").fetchall()
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
    else:
        print("  (vazio)")
    conn.close()
    
except Exception as e:
    print(f"❌ instance/database.sqlite: {e}")