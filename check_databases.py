import sqlite3

# Testa diferentes bancos de dados
databases = ['laura_dados.db', 'vendas_data.db', 'database.db', 'dash_data.db', 'laura_rep.db']

for db_name in databases:
    try:
        conn = sqlite3.connect(db_name)
        tables = [x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"\n🗃️ {db_name}:")
        if tables:
            print(f"  Tabelas: {', '.join(tables)}")
            
            # Verifica se tem vendas e produtos_cotados
            if 'vendas' in tables and 'produtos_cotados' in tables:
                vendas_count = conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
                cotacoes_count = conn.execute("SELECT COUNT(*) FROM produtos_cotados").fetchone()[0]
                print(f"  ✅ Vendas: {vendas_count:,} registros")
                print(f"  ✅ Produtos Cotados: {cotacoes_count:,} registros")
                print(f"  >>> BANCO CORRETO PARA USAR: {db_name}")
        else:
            print("  (vazio)")
        conn.close()
    except Exception as e:
        print(f"❌ {db_name}: {e}")

print("\nUse o banco que contém as tabelas 'vendas' e 'produtos_cotados' com dados.")