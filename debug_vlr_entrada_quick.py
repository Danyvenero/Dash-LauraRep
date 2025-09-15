#!/usr/bin/env python3
"""
Debug rápido para verificar vlr_entrada
"""

import sqlite3
import pandas as pd

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')

# Verifica vlr_entrada com dados reais
query = '''
SELECT 
    COUNT(*) as total_registros,
    COUNT(vlr_entrada) as vlr_entrada_nao_nulos,
    COUNT(CASE WHEN vlr_entrada > 0 THEN 1 END) as vlr_entrada_positivos,
    MIN(vlr_entrada) as vlr_entrada_min,
    MAX(vlr_entrada) as vlr_entrada_max,
    AVG(vlr_entrada) as vlr_entrada_media,
    SUM(vlr_entrada) as vlr_entrada_soma
FROM vendas
'''

resultado = pd.read_sql_query(query, conn)
print('📊 ESTATÍSTICAS VLR_ENTRADA NO BANCO:')
for col in resultado.columns:
    print(f'  {col}: {resultado[col].iloc[0]}')

# Verifica alguns registros com vlr_entrada > 0
query2 = '''
SELECT vlr_entrada, vlr_rol, data, data_faturamento, produto, cliente
FROM vendas 
WHERE vlr_entrada > 0 
LIMIT 10
'''

amostra = pd.read_sql_query(query2, conn)
print(f'\n🔍 AMOSTRA DE REGISTROS COM VLR_ENTRADA > 0:')
print(f'Encontrados: {len(amostra)} registros')
if len(amostra) > 0:
    for i, row in amostra.iterrows():
        print(f'  vlr_entrada: {row["vlr_entrada"]}, data: {row["data"]}, data_faturamento: {row["data_faturamento"]}')

# Verifica qual coluna tem dados válidos
print(f'\n📅 VERIFICAÇÃO DE COLUNAS DE DATA:')
query3 = '''
SELECT 
    COUNT(CASE WHEN data IS NOT NULL AND data != '' THEN 1 END) as data_validas,
    COUNT(CASE WHEN data_faturamento IS NOT NULL AND data_faturamento != '' THEN 1 END) as data_faturamento_validas,
    COUNT(CASE WHEN vlr_entrada > 0 AND data IS NOT NULL AND data != '' THEN 1 END) as vlr_entrada_com_data,
    COUNT(CASE WHEN vlr_entrada > 0 AND data_faturamento IS NOT NULL AND data_faturamento != '' THEN 1 END) as vlr_entrada_com_data_faturamento
FROM vendas
WHERE vlr_entrada > 0
'''

resultado3 = pd.read_sql_query(query3, conn)
for col in resultado3.columns:
    print(f'  {col}: {resultado3[col].iloc[0]}')

conn.close()
