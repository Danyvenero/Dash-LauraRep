"""
Teste simplificado para identificar onde está o travamento
"""

import pandas as pd
import sqlite3
import time

def test_simplified():
    """Teste com timeouts em cada etapa"""
    try:
        print("🔍 Teste simplificado com timeouts...")
        
        from utils.ml_recommendations import SmartPurchaseRecommendations
        
        start_time = time.time()
        print(f"⏰ Iniciando: {time.strftime('%H:%M:%S')}")
        
        recommender = SmartPurchaseRecommendations()
        print(f"✅ Instância criada em {time.time() - start_time:.1f}s")
        
        # Dados mínimos para teste
        conn = sqlite3.connect("instance/database.sqlite")
        
        # Query menor para evitar timeout
        start_query = time.time()
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE data >= date('now', '-6 months')
        AND cod_cliente IN ('782080', '240613', '1024529')
        LIMIT 500
        """
        vendas_df = pd.read_sql_query(vendas_query, conn)
        print(f"✅ Query vendas em {time.time() - start_query:.1f}s - {len(vendas_df)} registros")
        
        start_query = time.time()
        cotacoes_query = """
        SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
        FROM produtos_cotados p
        LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
        WHERE c.data >= date('now', '-6 months')
        AND p.cod_cliente IN ('782080', '240613', '1024529')
        LIMIT 200
        """
        cotacoes_df = pd.read_sql_query(cotacoes_query, conn)
        print(f"✅ Query cotações em {time.time() - start_query:.1f}s - {len(cotacoes_df)} registros")
        
        conn.close()
        
        # Teste cada função com timeout
        cod_cliente = '782080'
        
        # 1. Gaps
        start_test = time.time()
        try:
            gaps = recommender.analyze_market_gaps(vendas_df, cotacoes_df, cod_cliente)
            print(f"✅ Gaps em {time.time() - start_test:.1f}s - {len(gaps)} encontrados")
        except Exception as e:
            print(f"❌ Erro em gaps após {time.time() - start_test:.1f}s: {e}")
        
        # 2. Sazonalidade
        start_test = time.time()
        try:
            seasonality = recommender.detect_seasonality(vendas_df, cod_cliente)
            print(f"✅ Sazonalidade em {time.time() - start_test:.1f}s")
        except Exception as e:
            print(f"❌ Erro em sazonalidade após {time.time() - start_test:.1f}s: {e}")
        
        # 3. KPIs
        start_test = time.time()
        try:
            kpis = recommender.calculate_commercial_kpis(vendas_df, cotacoes_df, cod_cliente)
            print(f"✅ KPIs em {time.time() - start_test:.1f}s")
        except Exception as e:
            print(f"❌ Erro em KPIs após {time.time() - start_test:.1f}s: {e}")
        
        # 4. Benchmark  
        start_test = time.time()
        try:
            benchmark = recommender.analyze_client_benchmark(vendas_df, cod_cliente)
            print(f"✅ Benchmark em {time.time() - start_test:.1f}s")
        except Exception as e:
            print(f"❌ Erro em benchmark após {time.time() - start_test:.1f}s: {e}")
        
        # 5. Alertas (pode ser problemática)
        start_test = time.time()
        try:
            alertas = recommender.generate_intelligent_alerts(vendas_df, cotacoes_df)
            print(f"✅ Alertas em {time.time() - start_test:.1f}s")
        except Exception as e:
            print(f"❌ Erro em alertas após {time.time() - start_test:.1f}s: {e}")
        
        # 6. Insights (mais problemática)
        start_test = time.time()
        try:
            insights = recommender.generate_actionable_insights(vendas_df, cotacoes_df, cod_cliente)
            print(f"✅ Insights em {time.time() - start_test:.1f}s")
        except Exception as e:
            print(f"❌ Erro em insights após {time.time() - start_test:.1f}s: {e}")
        
        print(f"\n⏰ Tempo total: {time.time() - start_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified()