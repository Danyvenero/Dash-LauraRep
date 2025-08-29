#!/usr/bin/env python3
"""
Script simples para investigar diferenças nos valores
"""

import sqlite3
import pandas as pd

def main():
    print("=== INVESTIGAÇÃO CLIENTE 782080 ===")
    
    # Conectar ao banco
    conn = sqlite3.connect('instance/database.sqlite')
    
    # 1. Verificar se existe tabela raw_vendas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = cursor.fetchall()
    print(f"Tabelas disponíveis: {[t[0] for t in tabelas]}")
    
    # 2. Verificar dados da tabela vendas para cliente 782080
    print("\n=== DADOS DA TABELA VENDAS ===")
    query = "SELECT * FROM vendas WHERE cod_cliente = 782080 LIMIT 5"
    df = pd.read_sql_query(query, conn)
    print(f"Registros encontrados: {len(df)}")
    if not df.empty:
        print("Colunas:", df.columns.tolist())
        print("\nPrimeiros registros:")
        print(df)
    
    # 3. Verificar total por ano para cliente 782080
    print("\n=== TOTAIS POR ANO ===")
    query_total = """
    SELECT 
        strftime('%Y', data_faturamento) as ano,
        COUNT(*) as registros,
        SUM(valor_faturado) as total_valor_faturado
    FROM vendas 
    WHERE cod_cliente = 782080 
    GROUP BY strftime('%Y', data_faturamento)
    ORDER BY ano
    """
    df_total = pd.read_sql_query(query_total, conn)
    print(df_total)
    
    # 4. Verificar se há registros duplicados
    print("\n=== VERIFICAÇÃO DE DUPLICATAS ===")
    query_dup = """
    SELECT 
        cod_cliente,
        data_faturamento,
        material,
        COUNT(*) as contagem
    FROM vendas 
    WHERE cod_cliente = 782080 
    GROUP BY cod_cliente, data_faturamento, material
    HAVING COUNT(*) > 1
    LIMIT 10
    """
    df_dup = pd.read_sql_query(query_dup, conn)
    print(f"Registros duplicados: {len(df_dup)}")
    if not df_dup.empty:
        print(df_dup)
    
    # 5. Verificar outras colunas de valor
    print("\n=== VERIFICAÇÃO DE COLUNAS DE VALOR ===")
    query_colunas = "PRAGMA table_info(vendas)"
    df_colunas = pd.read_sql_query(query_colunas, conn)
    colunas_valor = df_colunas[df_colunas['name'].str.contains('valor|rol|preco', case=False, na=False)]
    print("Colunas relacionadas a valor:")
    print(colunas_valor[['name', 'type']])
    
    conn.close()

if __name__ == "__main__":
    main()
