import sqlite3
import pandas as pd

# Conectar ao banco
conn = sqlite3.connect('instance/database.sqlite')

print("=== VERIFICAÇÃO ESPECÍFICA DO CLIENTE 782080 ===")

# 1. Total sem filtros (exceto ano 2024)
query_base = """
SELECT 
    COUNT(*) as registros,
    SUM(valor_faturado) as total_valor
FROM vendas 
WHERE cod_cliente = '782080'
AND strftime('%Y', data_faturamento) = '2024'
"""

result_base = pd.read_sql_query(query_base, conn)
print("SEM FILTROS DE HIERARQUIA:")
print(f"Registros: {result_base['registros'].iloc[0]}")
print(f"Total: {result_base['total_valor'].iloc[0]:,.2f}")

# 2. Verificar quais materiais existem para esse cliente
query_materiais = """
SELECT DISTINCT material
FROM vendas 
WHERE cod_cliente = '782080'
AND strftime('%Y', data_faturamento) = '2024'
ORDER BY material
"""

materiais = pd.read_sql_query(query_materiais, conn)
print(f"\nMATERIAIS DO CLIENTE 782080 (total: {len(materiais)}):")
print(materiais['material'].tolist()[:10])  # Primeiros 10

# 3. Verificar na tabela raw_vendas quais hierarquias correspondem a esses materiais
try:
    query_hier = """
    SELECT DISTINCT 
        Material,
        "Hier. Produto 1",
        "Hier. Produto 2", 
        "Hier. Produto 3"
    FROM raw_vendas 
    WHERE Material IN (
        SELECT DISTINCT material
        FROM vendas 
        WHERE cod_cliente = '782080'
        AND strftime('%Y', data_faturamento) = '2024'
    )
    AND ("Hier. Produto 1" LIKE '%CONTROLS%' 
         OR "Hier. Produto 2" LIKE '%CONTROLS%' 
         OR "Hier. Produto 3" LIKE '%CONTROLS%')
    """
    
    hier_controls = pd.read_sql_query(query_hier, conn)
    print(f"\nMATERIAIS COM HIERARQUIA CONTROLS (total: {len(hier_controls)}):")
    print(hier_controls.head())
    
    # Verificar o valor para materiais CONTROLS
    materiais_controls = hier_controls['Material'].unique()
    if len(materiais_controls) > 0:
        placeholders = ','.join(['?' for _ in materiais_controls])
        query_valor_controls = f"""
        SELECT 
            COUNT(*) as registros,
            SUM(valor_faturado) as total_valor
        FROM vendas 
        WHERE cod_cliente = '782080'
        AND strftime('%Y', data_faturamento) = '2024'
        AND material IN ({placeholders})
        """
        
        result_controls = pd.read_sql_query(query_valor_controls, conn, params=materiais_controls.tolist())
        print(f"\nCOM FILTRO CONTROLS:")
        print(f"Registros: {result_controls['registros'].iloc[0]}")  
        print(f"Total: {result_controls['total_valor'].iloc[0]:,.2f}")
        
        # Verificar se há diferença
        diferenca = result_base['total_valor'].iloc[0] - result_controls['total_valor'].iloc[0]
        print(f"\nDIFERENÇA: {diferenca:,.2f}")
        
except Exception as e:
    print(f"Erro ao verificar hierarquias: {e}")

# 4. Verificar materiais que NÃO têm hierarquia CONTROLS
try:
    query_sem_controls = """
    SELECT DISTINCT Material
    FROM raw_vendas 
    WHERE Material IN (
        SELECT DISTINCT material
        FROM vendas 
        WHERE cod_cliente = '782080'
        AND strftime('%Y', data_faturamento) = '2024'
    )
    AND NOT ("Hier. Produto 1" LIKE '%CONTROLS%' 
             OR "Hier. Produto 2" LIKE '%CONTROLS%' 
             OR "Hier. Produto 3" LIKE '%CONTROLS%')
    """
    
    materiais_sem_controls = pd.read_sql_query(query_sem_controls, conn)
    print(f"\nMATERIAIS SEM CONTROLS (total: {len(materiais_sem_controls)}):")
    print(materiais_sem_controls['Material'].tolist()[:10])
    
    # Valor dos materiais sem CONTROLS
    if len(materiais_sem_controls) > 0:
        placeholders = ','.join(['?' for _ in materiais_sem_controls['Material']])
        query_valor_sem_controls = f"""
        SELECT 
            COUNT(*) as registros,
            SUM(valor_faturado) as total_valor
        FROM vendas 
        WHERE cod_cliente = '782080'
        AND strftime('%Y', data_faturamento) = '2024'
        AND material IN ({placeholders})
        """
        
        result_sem_controls = pd.read_sql_query(query_valor_sem_controls, conn, params=materiais_sem_controls['Material'].tolist())
        print(f"\nVALOR DOS MATERIAIS SEM CONTROLS:")
        print(f"Registros: {result_sem_controls['registros'].iloc[0]}")
        print(f"Total: {result_sem_controls['total_valor'].iloc[0]:,.2f}")

except Exception as e:
    print(f"Erro ao verificar materiais sem CONTROLS: {e}")

conn.close()
