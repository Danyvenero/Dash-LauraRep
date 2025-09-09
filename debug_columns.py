#!/usr/bin/env python3
"""
Debug das colunas dos dados
"""

from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data

def debug_data_columns():
    print("=== DEBUG DAS COLUNAS DOS DADOS ===")
    
    # Carrega dados de vendas
    try:
        vendas_df = load_vendas_data()
        print(f"\n📊 VENDAS - Shape: {vendas_df.shape}")
        print(f"📊 VENDAS - Colunas ({len(vendas_df.columns)}):")
        for i, col in enumerate(vendas_df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        if not vendas_df.empty:
            print(f"\n📊 VENDAS - Primeira linha:")
            for col in vendas_df.columns[:10]:  # Primeiras 10 colunas
                print(f"  {col}: {vendas_df.iloc[0][col]}")
    except Exception as e:
        print(f"❌ Erro ao carregar vendas: {e}")
    
    # Carrega dados de cotações
    try:
        cotacoes_df = load_cotacoes_data()
        print(f"\n📋 COTAÇÕES - Shape: {cotacoes_df.shape}")
        print(f"📋 COTAÇÕES - Colunas ({len(cotacoes_df.columns)}):")
        for i, col in enumerate(cotacoes_df.columns, 1):
            print(f"  {i:2d}. {col}")
    except Exception as e:
        print(f"❌ Erro ao carregar cotações: {e}")
    
    # Carrega dados de produtos
    try:
        produtos_df = load_produtos_cotados_data()
        print(f"\n📦 PRODUTOS - Shape: {produtos_df.shape}")
        print(f"📦 PRODUTOS - Colunas ({len(produtos_df.columns)}):")
        for i, col in enumerate(produtos_df.columns, 1):
            print(f"  {i:2d}. {col}")
    except Exception as e:
        print(f"❌ Erro ao carregar produtos: {e}")

if __name__ == "__main__":
    debug_data_columns()
