import sqlite3
import pandas as pd

conn = sqlite3.connect('instance/database.sqlite')

print('STATUS DAS TABELAS:')
print('=' * 40)

# Verificar cada tabela
tables = ['vendas', 'cotacoes', 'produtos_cotados', 'datasets']

for table in tables:
    try:
        result = pd.read_sql(f'SELECT COUNT(*) as count FROM {table}', conn)
        count = result.iloc[0]['count']
        print(f'{table}: {count:,} registros')
    except:
        print(f'{table}: Nao existe')

print('\nDATASETS:')
print('-' * 30)

try:
    datasets = pd.read_sql('SELECT id, dataset_name, upload_date, vendas_count, cotacoes_count, produtos_cotados_count FROM datasets ORDER BY upload_date DESC LIMIT 3', conn)
    for _, row in datasets.iterrows():
        print(f'ID {row["id"]}: {row["dataset_name"]}')
        print(f'  Vendas: {row["vendas_count"]} | Cotacoes: {row["cotacoes_count"]} | Produtos: {row["produtos_cotados_count"]}')
        print()
except Exception as e:
    print(f'Erro: {e}')

conn.close()
