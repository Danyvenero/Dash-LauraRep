import sqlite3
import pandas as pd

# Conectar ao banco
conn = sqlite3.connect('instance/database.sqlite')

print("=== INVESTIGAÇÃO DE DIFERENÇAS ===")

# Cliente 782080
print("\n--- CLIENTE 782080 ---")
query = """
SELECT 
    COUNT(*) as registros,
    SUM(valor_faturado) as total_valor,
    SUM(CASE WHEN valor_faturado IS NULL THEN 1 ELSE 0 END) as valores_nulos
FROM vendas 
WHERE cod_cliente = '782080'
AND strftime('%Y', data_faturamento) = '2024'
"""

result = pd.read_sql_query(query, conn)
print("Dados processados 2024:")
print(result)

# Verificar dados raw se existir
try:
    query_raw = """
    SELECT 
        COUNT(*) as registros_raw,
        SUM(CAST("Vlr. ROL" AS REAL)) as total_raw
    FROM raw_vendas 
    WHERE "Cód. Cliente" = 782080
    AND strftime('%Y', "Data Fat.") = '2024'
    """
    
    result_raw = pd.read_sql_query(query_raw, conn)
    print("Dados RAW 2024:")
    print(result_raw)
except Exception as e:
    print(f"Erro ao consultar raw_vendas: {e}")

# Cliente 926929
print("\n--- CLIENTE 926929 ---")
query = """
SELECT 
    COUNT(*) as registros,
    SUM(valor_faturado) as total_valor,
    SUM(CASE WHEN valor_faturado IS NULL THEN 1 ELSE 0 END) as valores_nulos
FROM vendas 
WHERE cod_cliente = '926929'
AND strftime('%Y', data_faturamento) = '2024'
"""

result = pd.read_sql_query(query, conn)
print("Dados processados 2024:")
print(result)

# Verificar alguns registros para entender o problema
print("\n--- AMOSTRA DE REGISTROS 782080 ---")
query_sample = """
SELECT 
    data_faturamento,
    valor_faturado,
    material
FROM vendas 
WHERE cod_cliente = '782080'
AND strftime('%Y', data_faturamento) = '2024'
ORDER BY valor_faturado DESC
LIMIT 5
"""

sample = pd.read_sql_query(query_sample, conn)
print(sample)

conn.close()
