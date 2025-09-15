#!/usr/bin/env python3
"""
Script para verificar especificamente vlr_entrada
"""

import sqlite3
import pandas as pd

# Conecta ao banco
db_path = r"instance\database.sqlite"

try:
    conn = sqlite3.connect(db_path)
    
    # Verifica dados de vlr_entrada
    query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(vlr_entrada) as entrada_non_null,
        COUNT(CASE WHEN vlr_entrada > 0 THEN 1 END) as entrada_positive,
        SUM(vlr_entrada) as entrada_sum,
        AVG(vlr_entrada) as entrada_avg,
        MIN(vlr_entrada) as entrada_min,
        MAX(vlr_entrada) as entrada_max,
        COUNT(vlr_rol) as rol_non_null,
        SUM(vlr_rol) as rol_sum
    FROM vendas
    """
    
    result = pd.read_sql_query(query, conn)
    print("📊 ESTATÍSTICAS VLR_ENTRADA:")
    print(f"Total de registros: {result['total_records'].iloc[0]}")
    print(f"vlr_entrada não nulos: {result['entrada_non_null'].iloc[0]}")
    print(f"vlr_entrada positivos: {result['entrada_positive'].iloc[0]}")
    print(f"Soma vlr_entrada: R$ {result['entrada_sum'].iloc[0]:,.2f}" if result['entrada_sum'].iloc[0] else "Soma vlr_entrada: 0")
    print(f"Média vlr_entrada: R$ {result['entrada_avg'].iloc[0]:,.2f}" if result['entrada_avg'].iloc[0] else "Média vlr_entrada: 0")
    print(f"Min vlr_entrada: R$ {result['entrada_min'].iloc[0]:,.2f}" if result['entrada_min'].iloc[0] else "Min vlr_entrada: 0")
    print(f"Max vlr_entrada: R$ {result['entrada_max'].iloc[0]:,.2f}" if result['entrada_max'].iloc[0] else "Max vlr_entrada: 0")
    print(f"vlr_rol não nulos: {result['rol_non_null'].iloc[0]}")
    print(f"Soma vlr_rol: R$ {result['rol_sum'].iloc[0]:,.2f}" if result['rol_sum'].iloc[0] else "Soma vlr_rol: 0")
    
    # Verifica alguns registros
    print("\n🔍 AMOSTRA DE DADOS:")
    sample_query = """
    SELECT vlr_entrada, vlr_rol, data_faturamento, produto 
    FROM vendas 
    WHERE vlr_entrada IS NOT NULL OR vlr_rol IS NOT NULL
    LIMIT 10
    """
    sample = pd.read_sql_query(sample_query, conn)
    print(sample)
    
    # Verifica dados por mês
    print("\n📅 DADOS POR MÊS:")
    monthly_query = """
    SELECT 
        strftime('%m', data_faturamento) as mes,
        COUNT(*) as registros,
        SUM(vlr_entrada) as total_entrada,
        SUM(vlr_rol) as total_rol
    FROM vendas 
    WHERE data_faturamento IS NOT NULL
    GROUP BY strftime('%m', data_faturamento)
    ORDER BY mes
    """
    monthly = pd.read_sql_query(monthly_query, conn)
    print(monthly)
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
