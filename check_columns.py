import sqlite3
import pandas as pd

conn = sqlite3.connect('instance/database.sqlite')

print("🔍 ESTRUTURA DAS TABELAS")
print("=" * 50)

# Vendas
print("\n📊 TABELA VENDAS:")
vendas_sample = pd.read_sql_query("SELECT * FROM vendas LIMIT 3", conn)
print(f"Colunas: {list(vendas_sample.columns)}")
print(vendas_sample.head(2))

# Cotações
print("\n📋 TABELA COTACOES:")
cotacoes_sample = pd.read_sql_query("SELECT * FROM cotacoes LIMIT 3", conn)
print(f"Colunas: {list(cotacoes_sample.columns)}")
print(cotacoes_sample.head(2))

# Produtos cotados
print("\n🛒 TABELA PRODUTOS_COTADOS:")
produtos_sample = pd.read_sql_query("SELECT * FROM produtos_cotados LIMIT 3", conn)
print(f"Colunas: {list(produtos_sample.columns)}")
print(produtos_sample.head(2))

conn.close()