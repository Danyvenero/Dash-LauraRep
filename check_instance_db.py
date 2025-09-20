import sqlite3

# Verifica o banco na pasta instance
try:
    conn = sqlite3.connect('instance/laurarep.db')
    tables = [x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"🗃️ instance/laurarep.db:")
    if tables:
        print(f"  Tabelas: {', '.join(tables)}")
        
        # Verifica registros em cada tabela
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  📊 {table}: {count:,} registros")
            except Exception as e:
                print(f"  ❌ {table}: erro - {e}")
                
        # Se tem as tabelas necessárias, testa uma consulta
        if 'vendas' in tables and 'produtos_cotados' in tables:
            print("\n✅ Banco correto encontrado!")
            
            # Amostra de dados
            print("\n📋 Amostra de vendas:")
            vendas_sample = conn.execute("SELECT material, descricao, cliente LIMIT 3").fetchall()
            for row in vendas_sample:
                print(f"  • {row[0]}: {row[1]} ({row[2]})")
                
            print("\n📋 Amostra de produtos_cotados:")
            cotados_sample = conn.execute("SELECT material, descricao, cliente LIMIT 3").fetchall()
            for row in cotados_sample:
                print(f"  • {row[0]}: {row[1]} ({row[2]})")
    else:
        print("  (vazio)")
    conn.close()
    
except Exception as e:
    print(f"❌ instance/laurarep.db: {e}")