#!/usr/bin/env python3
"""
Script para investigar diferenças específicas nos clientes 782080 e 926929
"""

import sqlite3
import pandas as pd
from datetime import datetime

def investigar_clientes_especificos():
    print("=== INVESTIGAÇÃO DETALHADA DOS CLIENTES ===")
    
    # Conectar ao banco
    conn = sqlite3.connect('instance/database.sqlite')
    
    clientes = [619167, 782080, 926929]
    
    for cliente in clientes:
        print(f"\n{'='*50}")
        print(f"CLIENTE {cliente}")
        print(f"{'='*50}")
        
        # 1. Verificar dados na tabela vendas
        query = """
        SELECT 
            cod_cliente,
            strftime('%Y', data_faturamento) as ano,
            COUNT(*) as registros,
            SUM(valor_faturado) as total_valor,
            SUM(CASE WHEN valor_faturado IS NULL THEN 1 ELSE 0 END) as valores_nulos,
            SUM(CASE WHEN data_faturamento IS NULL THEN 1 ELSE 0 END) as datas_nulas
        FROM vendas 
        WHERE cod_cliente = ?
        GROUP BY cod_cliente, strftime('%Y', data_faturamento)
        ORDER BY ano
        """
        
        df_vendas = pd.read_sql_query(query, conn, params=(str(cliente),))
        print("DADOS POR ANO:")
        print(df_vendas)
        
        # 2. Verificar especificamente 2024
        query_2024 = """
        SELECT 
            COUNT(*) as total_registros,
            SUM(valor_faturado) as soma_valor_faturado,
            AVG(valor_faturado) as media_valor,
            MIN(valor_faturado) as min_valor,
            MAX(valor_faturado) as max_valor,
            SUM(CASE WHEN valor_faturado IS NULL THEN 1 ELSE 0 END) as valores_nulos
        FROM vendas 
        WHERE cod_cliente = ? 
        AND strftime('%Y', data_faturamento) = '2024'
        """
        
        df_2024 = pd.read_sql_query(query_2024, conn, params=(str(cliente),))
        print("\nDETALHES 2024:")
        print(df_2024)
        
        # 3. Verificar alguns registros específicos de 2024
        query_sample = """
        SELECT 
            data_faturamento,
            valor_faturado,
            material,
            quantidade_faturada
        FROM vendas 
        WHERE cod_cliente = ? 
        AND strftime('%Y', data_faturamento) = '2024'
        ORDER BY data_faturamento
        LIMIT 10
        """
        
        df_sample = pd.read_sql_query(query_sample, conn, params=(str(cliente),))
        print("\nAMOSTRA DE REGISTROS 2024:")
        print(df_sample)
        
        # 4. Verificar se há registros com datas problemáticas
        query_datas = """
        SELECT 
            data_faturamento,
            COUNT(*) as registros,
            SUM(valor_faturado) as valor_total
        FROM vendas 
        WHERE cod_cliente = ?
        AND (data_faturamento IS NULL 
             OR data_faturamento = '' 
             OR strftime('%Y', data_faturamento) NOT BETWEEN '2020' AND '2025')
        GROUP BY data_faturamento
        """
        
        df_datas_prob = pd.read_sql_query(query_datas, conn, params=(str(cliente),))
        if not df_datas_prob.empty:
            print("\nREGISTROS COM DATAS PROBLEMÁTICAS:")
            print(df_datas_prob)
    
    # 5. Verificar dados raw vs processados
    print(f"\n{'='*50}")
    print("COMPARAÇÃO RAW VS PROCESSADOS")
    print(f"{'='*50}")
    
    # Verificar se tabela raw_vendas existe
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_vendas'")
    if cursor.fetchone():
        for cliente in clientes:
            print(f"\nCLIENTE {cliente} - RAW vs PROCESSADO:")
            
            # RAW
            query_raw = """
            SELECT 
                COUNT(*) as registros_raw,
                SUM(CAST("Vlr. ROL" AS REAL)) as total_vlr_rol_raw
            FROM raw_vendas 
            WHERE "Cód. Cliente" = ?
            AND strftime('%Y', "Data Fat.") = '2024'
            """
            
            try:
                df_raw = pd.read_sql_query(query_raw, conn, params=(cliente,))
                print(f"RAW: {df_raw['registros_raw'].iloc[0]} registros, Total: {df_raw['total_vlr_rol_raw'].iloc[0]:,.2f}")
            except Exception as e:
                print(f"Erro ao consultar RAW: {e}")
            
            # PROCESSADO
            query_proc = """
            SELECT 
                COUNT(*) as registros_proc,
                SUM(valor_faturado) as total_valor_proc
            FROM vendas 
            WHERE cod_cliente = ?
            AND strftime('%Y', data_faturamento) = '2024'
            """
            
            df_proc = pd.read_sql_query(query_proc, conn, params=(str(cliente),))
            print(f"PROCESSADO: {df_proc['registros_proc'].iloc[0]} registros, Total: {df_proc['total_valor_proc'].iloc[0]:,.2f}")
    
    conn.close()

if __name__ == "__main__":
    investigar_clientes_especificos()
