"""
Teste específico para generate_actionable_insights
"""

import pandas as pd
import sqlite3

def test_insights_specific():
    """Testa especificamente a função que está dando erro"""
    try:
        print("🔍 Testando generate_actionable_insights especificamente...")
        
        from utils.ml_recommendations import SmartPurchaseRecommendations
        recommender = SmartPurchaseRecommendations()
        
        # Dados mínimos
        conn = sqlite3.connect("instance/database.sqlite")
        
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE cod_cliente = '782080'
        LIMIT 50
        """
        vendas_df = pd.read_sql_query(vendas_query, conn)
        conn.close()
        
        print(f"📊 Dados: {len(vendas_df)} vendas")
        
        # Testa a função problematica linha por linha
        print("🔍 Executando generate_actionable_insights...")
        
        contexto_comercial = {'vendedor': 'Teste', 'regiao': 'Nacional'}
        
        resultado = recommender.generate_actionable_insights(
            vendas_df, pd.DataFrame(), '782080', contexto_comercial
        )
        
        print(f"✅ Insights gerados: {type(resultado)}")
        
        if isinstance(resultado, dict):
            print(f"📋 Chaves: {list(resultado.keys())}")
        
    except Exception as e:
        print(f"❌ Erro específico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_insights_specific()