"""
Teste específico da função que está causando erro
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3

def test_specific_error():
    """Testa especificamente onde pode estar o erro"""
    try:
        print("🔍 Testando função específica que pode estar causando erro...")
        
        from utils.ml_recommendations import SmartPurchaseRecommendations
        recommender = SmartPurchaseRecommendations()
        
        # Dados de teste simples
        conn = sqlite3.connect("instance/database.sqlite")
        
        # Query simples para teste
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE cod_cliente = '782080'
        """
        vendas_cliente = pd.read_sql_query(vendas_query, conn)
        
        vendas_base_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        LIMIT 100
        """
        vendas_base = pd.read_sql_query(vendas_base_query, conn)
        
        print(f"📊 Dados carregados: {len(vendas_cliente)} vendas do cliente, {len(vendas_base)} vendas da base")
        
        # Testa cada função individualmente
        print("\n🔍 Testando analyze_market_gaps...")
        try:
            gaps_result = recommender.analyze_market_gaps(vendas_base, pd.DataFrame(), '782080')
            print(f"✅ Gaps: {len(gaps_result)} encontrados")
            print(f"📋 Tipo: {type(gaps_result)}")
            print(f"📋 Colunas: {list(gaps_result.columns) if hasattr(gaps_result, 'columns') else 'N/A'}")
        except Exception as e:
            print(f"❌ Erro em gaps: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🔍 Testando detect_seasonality...")
        try:
            season_result = recommender.detect_seasonality(vendas_base, '782080')
            print(f"✅ Sazonalidade: {type(season_result)}")
        except Exception as e:
            print(f"❌ Erro em sazonalidade: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🔍 Testando calculate_commercial_kpis...")
        try:
            kpis_result = recommender.calculate_commercial_kpis(vendas_base, pd.DataFrame(), '782080')
            print(f"✅ KPIs: {type(kpis_result)}")
        except Exception as e:
            print(f"❌ Erro em KPIs: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🔍 Testando analyze_client_benchmark...")
        try:
            benchmark_result = recommender.analyze_client_benchmark(vendas_base, '782080')
            print(f"✅ Benchmark: {type(benchmark_result)}")
        except Exception as e:
            print(f"❌ Erro em benchmark: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🔍 Testando generate_actionable_insights...")
        try:
            insights_result = recommender.generate_actionable_insights(
                vendas_base, pd.DataFrame(), '782080'
            )
            print(f"✅ Insights: {type(insights_result)}")
        except Exception as e:
            print(f"❌ Erro em insights: {e}")
            import traceback
            traceback.print_exc()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_error()