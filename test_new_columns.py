#!/usr/bin/env python3
"""
Teste das novas colunas nas sugestões
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import load_all_data
from utils.ml_recommendations import SmartPurchaseRecommendations

def test_new_columns():
    """Testa se as novas colunas estão sendo geradas"""
    print("🧪 Testando novas colunas nas sugestões...")
    
    # Carrega dados
    vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
    
    # Gera sugestões
    purchase_recommender = SmartPurchaseRecommendations()
    df_sugestoes = purchase_recommender.generate_purchase_suggestions(
        vendas_df=vendas_df,
        cotacoes_df=cotacoes_df,
        produtos_cotados_df=produtos_cotados_df,
        cliente_filter=None,
        top_n=5
    )
    
    print(f"\n📊 Colunas geradas: {df_sugestoes.columns.tolist()}")
    
    # Verifica colunas específicas
    required_columns = ['material', 'produto', 'cliente', 'cod_cliente']
    for col in required_columns:
        if col in df_sugestoes.columns:
            print(f"✅ {col}: OK")
            print(f"   Amostra: {df_sugestoes[col].head(3).tolist()}")
        else:
            print(f"❌ {col}: FALTANDO")
    
    print(f"\n📋 Primeiras 3 sugestões completas:")
    print(df_sugestoes[['material', 'produto', 'cliente', 'quantidade_sugerida']].head(3).to_string())

if __name__ == "__main__":
    test_new_columns()