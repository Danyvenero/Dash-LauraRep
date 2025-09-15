#!/usr/bin/env python3
"""
Script para simular análise de sazonalidade e debug de vlr_entrada
"""

import sqlite3
import pandas as pd
import numpy as np

try:
    # Conecta ao banco
    conn = sqlite3.connect('instance/database.sqlite')
    
    # Carrega dados como na aplicação
    query = "SELECT * FROM vendas"
    vendas_df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"📊 Total de registros carregados: {len(vendas_df)}")
    print(f"📊 Colunas disponíveis: {list(vendas_df.columns)}")
    
    # Verifica vlr_entrada
    entrada_stats = {
        'total': len(vendas_df),
        'non_null': vendas_df['vlr_entrada'].notna().sum(),
        'zeros': (vendas_df['vlr_entrada'] == 0).sum(),
        'positives': (vendas_df['vlr_entrada'] > 0).sum(),
        'sum': vendas_df['vlr_entrada'].sum(),
        'mean': vendas_df['vlr_entrada'].mean()
    }
    
    print(f"\n📈 Estatísticas vlr_entrada:")
    for key, value in entrada_stats.items():
        print(f"  {key}: {value}")
    
    # Simula filtros como na aplicação
    vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'], errors='coerce')
    
    # Filtro por ano (2018-2025)
    vendas_filtrado = vendas_df[
        (vendas_df['data_faturamento'].dt.year >= 2018) & 
        (vendas_df['data_faturamento'].dt.year <= 2025)
    ].copy()
    
    print(f"\n📅 Após filtro de ano (2018-2025): {len(vendas_filtrado)} registros")
    
    # Top 10 clientes por vlr_rol
    top_clientes = vendas_filtrado.groupby('cod_cliente')['vlr_rol'].sum().nlargest(10).index.tolist()
    vendas_top = vendas_filtrado[vendas_filtrado['cod_cliente'].isin(top_clientes)].copy()
    
    print(f"📊 Após filtro top 10 clientes: {len(vendas_top)} registros")
    
    # Agora simula análise de sazonalidade
    vendas_top['month'] = vendas_top['data_faturamento'].dt.month
    vendas_top['month_name'] = vendas_top['data_faturamento'].dt.strftime('%b')
    
    print(f"\n🔍 Debug dados sazonalidade:")
    print(f"   Registros para análise: {len(vendas_top)}")
    print(f"   Range de datas: {vendas_top['data_faturamento'].min()} até {vendas_top['data_faturamento'].max()}")
    
    # Analisa vlr_rol
    rol_monthly = vendas_top.groupby(['month', 'month_name'])['vlr_rol'].agg(['sum', 'count']).reset_index()
    rol_monthly.columns = ['month_num', 'month_name', 'total_rol', 'count_rol']
    
    print(f"\n📊 vlr_rol por mês:")
    for _, row in rol_monthly.iterrows():
        print(f"   {row['month_name']}: R$ {row['total_rol']:,.2f} ({row['count_rol']} transações)")
    
    # Analisa vlr_entrada
    entrada_monthly = vendas_top.groupby(['month', 'month_name'])['vlr_entrada'].agg(['sum', 'count']).reset_index()
    entrada_monthly.columns = ['month_num', 'month_name', 'total_entrada', 'count_entrada']
    
    print(f"\n📊 vlr_entrada por mês:")
    for _, row in entrada_monthly.iterrows():
        print(f"   {row['month_name']}: R$ {row['total_entrada']:,.2f} ({row['count_entrada']} transações)")
    
    # Verifica se há registros com vlr_entrada > 0 nos dados filtrados
    entrada_positivos = vendas_top[vendas_top['vlr_entrada'] > 0]
    print(f"\n🔍 Registros com vlr_entrada > 0 após filtros: {len(entrada_positivos)}")
    
    if len(entrada_positivos) > 0:
        print(f"   Amostra:")
        for i, (_, row) in enumerate(entrada_positivos.head(5).iterrows()):
            print(f"     {i+1}: entrada=R${row['vlr_entrada']:,.2f}, rol=R${row['vlr_rol']:,.2f}, data={row['data_faturamento']}")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
