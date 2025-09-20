#!/usr/bin/env python3
"""
Teste direto da função load_all_data
"""

from utils import load_all_data
import pandas as pd

def test_load_data():
    try:
        print("🔄 Testando load_all_data()...")
        
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        print(f"✅ Vendas DF: {len(vendas_df)} registros")
        if not vendas_df.empty:
            print(f"   Colunas: {list(vendas_df.columns)}")
            if 'cod_cliente' in vendas_df.columns:
                clientes_unicos = vendas_df[['cod_cliente', 'cliente']].drop_duplicates()
                print(f"   Clientes únicos: {len(clientes_unicos)}")
                print("   Primeiros 5 clientes:")
                print(clientes_unicos.head())
            else:
                print("   ❌ Coluna 'cod_cliente' não encontrada")
        
        print(f"✅ Cotações DF: {len(cotacoes_df)} registros")
        print(f"✅ Produtos DF: {len(produtos_df)} registros")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load_data()