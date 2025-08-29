from app import app
from utils import db
import pandas as pd

with app.app_context():
    print("=== DIAGNÓSTICO SIMPLES ===")
    
    # Carregar dados
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    
    print(f"Total de registros vendas: {len(df_vendas)}")
    print(f"Total de registros cotações: {len(df_cotacoes)}")
    
    print(f"\nColunas em vendas: {df_vendas.columns.tolist()}")
    
    # Verificar valores de produto/material
    if 'produto' in df_vendas.columns:
        produtos_controls = df_vendas[df_vendas['produto'].str.contains('CONTROLS', case=False, na=False)]
        print(f"\nRegistros com CONTROLS em produto: {len(produtos_controls)}")
        clientes_controls = produtos_controls['cliente'].unique()
        print(f"Clientes únicos com CONTROLS: {len(clientes_controls)}")
        print(f"Clientes: {clientes_controls[:10]}")
    
    # Verificar valores negativos
    if 'valor_faturado' in df_vendas.columns:
        negativos = df_vendas[df_vendas['valor_faturado'] < 0]
        print(f"\nRegistros com valor_faturado negativo: {len(negativos)}")
        if len(negativos) > 0:
            print(negativos[['cod_cliente', 'cliente', 'valor_faturado']].head())
    
    # Verificar anos disponíveis
    if 'data_faturamento' in df_vendas.columns:
        df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
        anos = df_vendas['data_faturamento'].dt.year.value_counts().sort_index()
        print(f"\nRegistros por ano:")
        print(anos)
    
    # Simular o filtro da imagem
    print(f"\n=== SIMULAÇÃO DOS FILTROS ===")
    df_filtered = df_vendas.copy()
    
    # Filtro anos 2024-2025
    if 'data_faturamento' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['data_faturamento'].dt.year.isin([2024, 2025])]
        print(f"Após filtro anos 2024-2025: {len(df_filtered)} registros")
    
    # Filtro mês 12
    if 'data_faturamento' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['data_faturamento'].dt.month == 12]
        print(f"Após filtro mês 12: {len(df_filtered)} registros")
    
    # Filtro CONTROLS
    if 'produto' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['produto'].str.contains('CONTROLS', case=False, na=False)]
        print(f"Após filtro CONTROLS: {len(df_filtered)} registros")
        
        if len(df_filtered) > 0:
            clientes_finais = df_filtered.groupby('cod_cliente').agg({
                'cliente': 'first',
                'valor_faturado': 'sum',
                'data_faturamento': 'max'
            }).reset_index()
            print(f"\nClientes após todos os filtros:")
            print(clientes_finais)
