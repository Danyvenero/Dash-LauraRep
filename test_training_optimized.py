#!/usr/bin/env python3
"""
Teste Rápido de Treinamento ML Otimizado
Testa o treinamento com as novas otimizações implementadas
"""

import sys
import os
import time
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_optimized_training():
    """Testa o treinamento ML otimizado"""
    
    print("🚀 Teste de Treinamento ML Otimizado")
    print("=" * 50)
    print(f"📅 Início: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Importações
        print("📦 Carregando módulos...")
        from utils.ml_recommendations import SmartPurchaseRecommendations
        from utils.data_loader import DataManager
        
        # Inicializa componentes
        print("🔧 Inicializando componentes...")
        ml_engine = SmartPurchaseRecommendations()
        data_manager = DataManager()
        
        # Carrega dados com limite
        print("📊 Carregando dados (versão limitada)...")
        start_time = time.time()
        
        # Força usar apenas dados recentes para teste rápido
        vendas_df = data_manager.load_vendas_data()
        cotacoes_df = data_manager.load_cotacoes_data()
        produtos_cotados_df = data_manager.load_produtos_cotados_data()
        
        print(f"   ✅ Vendas: {len(vendas_df) if vendas_df is not None else 0} registros")
        print(f"   ✅ Cotações: {len(cotacoes_df) if cotacoes_df is not None else 0} registros")
        print(f"   ✅ Produtos Cotados: {len(produtos_cotados_df) if produtos_cotados_df is not None else 0} registros")
        
        if vendas_df is None or vendas_df.empty:
            print("❌ Erro: Dados de vendas não encontrados")
            return False
        
        # Reduz dataset para teste (últimos 6 meses)
        print("✂️ Aplicando filtro temporal (últimos 6 meses)...")
        if 'data_faturamento' in vendas_df.columns:
            vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'], errors='coerce')
            cutoff_date = datetime.now() - timedelta(days=180)  # 6 meses
            vendas_df = vendas_df[vendas_df['data_faturamento'] >= cutoff_date]
            print(f"   ✅ Dataset reduzido para: {len(vendas_df)} registros")
        
        # Inicia treinamento
        print("\n🤖 Iniciando treinamento otimizado...")
        print("   ⚡ Limitações ativas:")
        print("   • Máximo 15.000 registros de vendas")
        print("   • Máximo 5.000 combinações material-cliente") 
        print("   • Timeout de 5 minutos")
        print("   • Logs de progresso a cada 1.000 iterações")
        
        training_start = time.time()
        
        # Executa treinamento com timeout manual
        resultado = ml_engine.train_repurchase_model(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            retrain=True
        )
        
        training_time = time.time() - training_start
        total_time = time.time() - start_time
        
        print(f"\n⏱️ Tempo de treinamento: {training_time:.1f}s")
        print(f"⏱️ Tempo total: {total_time:.1f}s")
        
        # Verifica resultado
        if 'erro' in resultado:
            if 'timeout' in resultado:
                print("⏰ TIMEOUT: Treinamento interrompido por timeout")
                print("   💡 Recomendação: Reduzir ainda mais o dataset")
            else:
                print(f"❌ ERRO: {resultado['erro']}")
            return False
        else:
            print("✅ SUCESSO: Treinamento concluído!")
            print(f"   📊 Score: {resultado.get('cv_auc_mean', 'N/A')}")
            print(f"   📈 Samples: {resultado.get('num_samples', 'N/A')}")
            print(f"   🔧 Features: {resultado.get('num_features', 'N/A')}")
            return True
            
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        import pandas as pd
        from datetime import timedelta
        success = test_optimized_training()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print("💡 O treinamento otimizado está funcionando.")
            print("   Você pode tentar novamente no dashboard.")
        else:
            print("⚠️ TESTE FALHOU!")
            print("💡 Recomendações:")
            print("   • Verificar conectividade com banco de dados")
            print("   • Reduzir período de dados (3 meses)")
            print("   • Verificar logs detalhados")
        print("=" * 50)
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que todos os módulos estão disponíveis")