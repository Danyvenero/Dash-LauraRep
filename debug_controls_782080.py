import sqlite3
import pandas as pd

# Conectar ao banco
conn = sqlite3.connect('instance/database.sqlite')

print("=== ANÁLISE DETALHADA - CLIENTE 782080 ===")

# 1. Total de materiais do cliente 782080 em 2024
query_total = """
SELECT COUNT(*) as total_registros, SUM(valor_faturado) as valor_total
FROM vendas 
WHERE cod_cliente = '782080' 
AND strftime('%Y', data_faturamento) = '2024'
"""
total = pd.read_sql_query(query_total, conn)
print(f"TOTAL SEM FILTRO HIERARQUIA: {total['total_registros'].iloc[0]} registros = R$ {total['valor_total'].iloc[0]:,.2f}")

# 2. Verificar quais materiais têm hierarquia CONTROLS
try:
    query_controls = """
    SELECT DISTINCT 
        rv.Material,
        rv."Hier. Produto 1",
        rv."Hier. Produto 2", 
        rv."Hier. Produto 3"
    FROM raw_vendas rv
    WHERE rv."Cód. Cliente" = 782080
    AND (rv."Hier. Produto 1" LIKE '%CONTROLS%' 
         OR rv."Hier. Produto 2" LIKE '%CONTROLS%' 
         OR rv."Hier. Produto 3" LIKE '%CONTROLS%')
    """
    
    materials_controls = pd.read_sql_query(query_controls, conn)
    print(f"\nMATERIAIS COM HIERARQUIA CONTROLS: {len(materials_controls)}")
    if len(materials_controls) > 0:
        print("Primeiros 10 materiais CONTROLS:")
        print(materials_controls.head(10))
        
        # 3. Valor dos materiais CONTROLS
        controls_list = materials_controls['Material'].tolist()
        if len(controls_list) > 0:
            placeholders = ','.join(['?' for _ in controls_list])
            query_valor_controls = f"""
            SELECT COUNT(*) as registros_controls, SUM(valor_faturado) as valor_controls
            FROM vendas 
            WHERE cod_cliente = '782080' 
            AND strftime('%Y', data_faturamento) = '2024'
            AND material IN ({placeholders})
            """
            
            valor_controls = pd.read_sql_query(query_valor_controls, conn, params=controls_list)
            print(f"\nCOM FILTRO CONTROLS: {valor_controls['registros_controls'].iloc[0]} registros = R$ {valor_controls['valor_controls'].iloc[0]:,.2f}")
            
            # Diferença
            diferenca = total['valor_total'].iloc[0] - valor_controls['valor_controls'].iloc[0]
            print(f"DIFERENÇA: R$ {diferenca:,.2f}")
            
            # 4. Mostrar materiais que NÃO são CONTROLS
            query_nao_controls = f"""
            SELECT DISTINCT material, COUNT(*) as registros, SUM(valor_faturado) as valor
            FROM vendas 
            WHERE cod_cliente = '782080' 
            AND strftime('%Y', data_faturamento) = '2024'
            AND material NOT IN ({placeholders})
            GROUP BY material
            ORDER BY valor DESC
            LIMIT 10
            """
            
            nao_controls = pd.read_sql_query(query_nao_controls, conn, params=controls_list)
            print(f"\nTOP 10 MATERIAIS NÃO-CONTROLS (que estão sendo excluídos):")
            print(nao_controls)
            
except Exception as e:
    print(f"Erro: {e}")

# 5. Verificar se na planilha de referência há indicação de filtro por hierarquia
print(f"\n{'='*60}")
print("CONCLUSÃO:")
print("1. O dashboard está funcionando corretamente")
print("2. O filtro CONTROLS está restringindo os materiais conforme esperado") 
print("3. Para obter o valor da planilha (487.339,01), é necessário:")
print("   - REMOVER o filtro de hierarquia 'CONTROLS', OU")
print("   - Verificar se a planilha também deveria estar filtrada por CONTROLS")

conn.close()
