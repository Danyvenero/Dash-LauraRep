import sqlite3
import pandas as pd

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')

# Estatísticas básicas de vlr_entrada
print('=== ESTATÍSTICAS VLR_ENTRADA ===')
query = '''
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN vlr_entrada > 0 THEN 1 END) as positivos,
    COUNT(CASE WHEN vlr_entrada = 0 THEN 1 END) as zeros,
    COUNT(CASE WHEN vlr_entrada IS NULL THEN 1 END) as nulls,
    SUM(vlr_entrada) as soma,
    AVG(vlr_entrada) as media
FROM vendas
'''
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

# Verifica dados por ano usando a coluna 'data'
print('\n=== VLR_ENTRADA POR ANO (coluna data) ===')
query2 = '''
SELECT 
    substr(data, 1, 4) as ano,
    COUNT(*) as registros,
    SUM(vlr_entrada) as total_entrada,
    AVG(vlr_entrada) as media_entrada
FROM vendas 
WHERE vlr_entrada > 0 AND data IS NOT NULL
GROUP BY substr(data, 1, 4)
ORDER BY ano
'''
result2 = pd.read_sql_query(query2, conn)
print(result2.to_string(index=False))

# Verifica alguns registros exemplo
print('\n=== EXEMPLOS DE REGISTROS COM VLR_ENTRADA ===')
query3 = '''
SELECT data, vlr_entrada, vlr_rol, data_faturamento
FROM vendas 
WHERE vlr_entrada > 0 
ORDER BY data DESC
LIMIT 10
'''
result3 = pd.read_sql_query(query3, conn)
print(result3.to_string(index=False))

conn.close()
