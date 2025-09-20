"""
Teste rápido da funcionalidade de análise de conversão
Verifica se a importação get_db_connection está funcionando
"""

def test_conversion_analysis():
    """Testa a análise de conversão isoladamente"""
    print("🧪 Testando Análise de Conversão...")
    
    try:
        # Testa importações
        from utils.db import get_connection as get_db_connection
        from utils.ml_recommendations import get_conversion_analyzer
        import pandas as pd
        
        print("✅ Importações OK")
        
        # Testa conexão DB
        conn = get_db_connection()
        print("✅ Conexão com banco OK")
        
        # Testa carregamento de dados
        vendas_df = pd.read_sql_query("SELECT * FROM vendas LIMIT 100", conn)
        produtos_cotados_df = pd.read_sql_query("SELECT * FROM produtos_cotados LIMIT 100", conn)
        conn.close()
        
        print(f"✅ Dados carregados: {len(vendas_df)} vendas, {len(produtos_cotados_df)} cotações")
        
        # Testa analisador de conversão
        analyzer = get_conversion_analyzer()
        print("✅ Analisador de conversão inicializado")
        
        # Testa análise (pequena amostra)
        conversion_results = analyzer.analyze_conversion_rates(vendas_df, produtos_cotados_df)
        print(f"✅ Análise concluída: {len(conversion_results)} produtos analisados")
        
        if not conversion_results.empty:
            print("📊 Amostra dos resultados:")
            print(conversion_results[['material', 'total_cotacoes', 'total_vendas', 'taxa_conversao_cotacao']].head())
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ O erro de importação foi corrigido")
        print("✅ A funcionalidade de análise de conversão está funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_conversion_analysis()