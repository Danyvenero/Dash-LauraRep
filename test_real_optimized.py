#!/usr/bin/env python3
"""
Teste com dados reais mas limitados
Testa a otimização com dados do sistema mas com filtros agressivos
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_data_optimized():
    """Testa treinamento com dados reais limitados"""
    
    print("🚀 TESTE COM DADOS REAIS OTIMIZADOS")
    print("=" * 50)
    
    try:
        # Importa componentes
        from utils.ml_recommendations import SmartPurchaseRecommendations
        
        print("📦 Carregando dados reais do banco...")
        
        # Conecta ao banco e carrega dados limitados
        import sqlite3
        import pandas as pd
        
        conn = sqlite3.connect('instance/database.sqlite')
        
        # Carrega apenas dados recentes para teste rápido
        vendas_df = pd.read_sql_query("""
            SELECT * FROM vendas 
            WHERE data_faturamento >= date('now', '-6 months')
            LIMIT 5000
        """, conn)
        
        cotacoes_df = pd.read_sql_query("""
            SELECT * FROM cotacoes 
            WHERE data >= date('now', '-6 months')
            LIMIT 2000
        """, conn)
        
        produtos_cotados_df = pd.read_sql_query("""
            SELECT * FROM produtos_cotados 
            LIMIT 3000
        """, conn)
        
        conn.close()
        
        print(f"   📊 {len(vendas_df)} vendas")
        print(f"   📊 {len(cotacoes_df)} cotações")
        print(f"   📊 {len(produtos_cotados_df)} produtos cotados")
        
        # Filtro agressivo: últimos 3 meses apenas
        import pandas as pd
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=90)
        
        if 'data_faturamento' in vendas_df.columns:
            vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'])
            vendas_filtradas = vendas_df[vendas_df['data_faturamento'] >= cutoff_date]
            
            if len(vendas_filtradas) > 500:  # Se há dados suficientes nos últimos 3 meses
                vendas_df = vendas_filtradas
                print(f"   ✂️ Filtro 3 meses: {len(vendas_filtradas)} vendas")
            else:
                # Usa últimos 6 meses se 3 meses for muito pouco
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=180)
                vendas_filtradas = vendas_df[vendas_df['data_faturamento'] >= cutoff_date]
                vendas_df = vendas_filtradas
                print(f"   ✂️ Filtro 6 meses: {len(vendas_filtradas)} vendas")
        
        # Limita também cotações se muito grandes
        if len(cotacoes_df) > 5000:
            cotacoes_df = cotacoes_df.tail(5000)
            print(f"   ✂️ Limitando cotações: 5000 mais recentes")
        
        if len(produtos_cotados_df) > 10000:
            produtos_cotados_df = produtos_cotados_df.tail(10000)
            print(f"   ✂️ Limitando produtos cotados: 10000 mais recentes")
        
        # Teste de treinamento
        print(f"\n🤖 Iniciando treinamento otimizado...")
        start_time = time.time()
        
        ml_engine = SmartPurchaseRecommendations()
        
        resultado = ml_engine.train_repurchase_model(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            retrain=True
        )
        
        training_time = time.time() - start_time
        
        print(f"\n⏱️ Tempo total: {training_time:.2f}s")
        
        if 'erro' in resultado:
            print(f"❌ ERRO: {resultado['erro']}")
            return False
        else:
            print("✅ SUCESSO!")
            print(f"   📊 Score CV: {resultado.get('cv_auc_mean', 'N/A'):.4f}")
            print(f"   📈 Samples: {resultado.get('num_samples', 'N/A')}")
            print(f"   🎯 Features: {resultado.get('num_features', 'N/A')}")
            
            # Se treinou rápido (<30s), é aceitável
            if training_time < 30:
                print(f"   ⚡ TEMPO ACEITÁVEL! ({training_time:.1f}s < 30s)")
                return True
            else:
                print(f"   ⚠️ Ainda lento ({training_time:.1f}s)")
                return False
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_data_optimized()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 OTIMIZAÇÃO FUNCIONOU!")
        print("✅ Treinamento com dados reais é rápido agora.")
        print("\n📋 Otimizações aplicadas:")
        print("   • Filtragem por período (3-6 meses)")
        print("   • Top 20 materiais + top 15 clientes")
        print("   • Máximo 300 combinações")
        print("   • Timeout 2 minutos")
        print("   • Features simplificadas")
        print("\n🚀 Pode usar no dashboard!")
    else:
        print("⚠️ AINDA PRECISA AJUSTES")
        print("   Considere filtros ainda mais agressivos")
        print("   ou implementar cache dos modelos treinados.")
    print("=" * 50)