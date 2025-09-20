#!/usr/bin/env python3
"""
Debug Script - Análise de geração de sugestões limitadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import load_all_data
from utils.ml_recommendations import SmartPurchaseRecommendations

def debug_suggestions_generation():
    """Debug para entender por que só 2 sugestões estão sendo geradas"""
    print("🔍 DEBUG: Iniciando análise de geração de sugestões...")
    
    try:
        # Carrega dados
        print("📊 Carregando dados...")
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        print(f"   - Vendas: {len(vendas_df)} registros")
        print(f"   - Cotações: {len(cotacoes_df)} registros")
        print(f"   - Produtos Cotados: {len(produtos_cotados_df)} registros")
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas!")
            return
        
        # Inicializa recomendador
        purchase_recommender = SmartPurchaseRecommendations()
        
        # Testa geração de sugestões
        print("\n🤖 Gerando sugestões sem filtro de cliente...")
        df_sugestoes = purchase_recommender.generate_purchase_suggestions(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            cliente_filter=None,  # Sem filtro
            top_n=20
        )
        
        print(f"\n📊 RESULTADO: {len(df_sugestoes)} sugestões geradas")
        
        if not df_sugestoes.empty:
            print("\n🎯 Primeiras sugestões:")
            print(df_sugestoes[['material', 'quantidade_sugerida', 'classificacao', 'priority_score']].head(10))
        
        # Testa classificação ABC-XYZ diretamente
        print("\n🔬 Testando classificação ABC-XYZ diretamente...")
        classificacao = purchase_recommender.classify_abc_xyz(vendas_df, None)
        print(f"   - Produtos classificados: {len(classificacao)}")
        
        if not classificacao.empty:
            print("   - Distribuição por classe ABC:")
            print(classificacao['classe_abc'].value_counts())
            
            print("   - Produtos A/B:")
            produtos_ab = classificacao[classificacao['classe_abc'].isin(['A', 'B'])]
            print(f"     Total: {len(produtos_ab)}")
            print(produtos_ab[['material', 'classe_abc', 'classe_xyz', 'valor_total']].head(10))
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_suggestions_generation()