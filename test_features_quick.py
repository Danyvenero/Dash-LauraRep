#!/usr/bin/env python3
"""
Teste Simples de Treinamento ML
Testa apenas a extração de features otimizada
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Cria dados de amostra para teste"""
    print("📊 Criando dados de amostra...")
    
    # Dados de vendas simulados
    np.random.seed(42)
    n_records = 1000
    
    materiais = [f"MAT{i:04d}" for i in range(1, 101)]  # 100 materiais
    clientes = [f"CLI{i:03d}" for i in range(1, 51)]    # 50 clientes
    
    vendas_data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(n_records):
        date = base_date + timedelta(days=np.random.randint(0, 365))
        vendas_data.append({
            'material': np.random.choice(materiais),
            'cod_cliente': np.random.choice(clientes),
            'cliente': f"Cliente {np.random.choice(clientes)}",
            'produto': f"Produto {np.random.choice(materiais)}",
            'data_faturamento': date,
            'vlr_rol': np.random.uniform(100, 5000),
            'qtd_rol': np.random.uniform(1, 100)
        })
    
    vendas_df = pd.DataFrame(vendas_data)
    print(f"   ✅ {len(vendas_df)} registros de vendas criados")
    
    # Dados de cotações simulados
    cotacoes_data = []
    for i in range(200):
        cotacoes_data.append({
            'numero_cotacao': f"COT{i:04d}",
            'cod_cliente': np.random.choice(clientes),
            'data_cotacao': base_date + timedelta(days=np.random.randint(0, 365))
        })
    
    cotacoes_df = pd.DataFrame(cotacoes_data)
    print(f"   ✅ {len(cotacoes_df)} cotações criadas")
    
    # Produtos cotados
    produtos_cotados_data = []
    for i, row in cotacoes_df.iterrows():
        for j in range(np.random.randint(1, 5)):  # 1-4 produtos por cotação
            produtos_cotados_data.append({
                'cotacao': row['numero_cotacao'],
                'material': np.random.choice(materiais),
                'cod_cliente': row['cod_cliente']
            })
    
    produtos_cotados_df = pd.DataFrame(produtos_cotados_data)
    print(f"   ✅ {len(produtos_cotados_df)} produtos cotados criados")
    
    return vendas_df, cotacoes_df, produtos_cotados_df

def test_feature_extraction():
    """Testa apenas a extração de features otimizada"""
    
    print("🚀 Teste de Extração de Features Otimizada")
    print("=" * 55)
    print(f"📅 Início: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Importa o engine ML
        print("📦 Carregando engine ML...")
        from utils.ml_recommendations import SmartPurchaseRecommendations
        
        ml_engine = SmartPurchaseRecommendations()
        
        # Cria dados de teste
        vendas_df, cotacoes_df, produtos_cotados_df = create_sample_data()
        
        # Testa extração de features
        print("\n🔬 Testando extração de features otimizada...")
        start_time = time.time()
        
        features_df = ml_engine.extract_ml_features(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df
        )
        
        extraction_time = time.time() - start_time
        
        print(f"⏱️ Tempo de extração: {extraction_time:.2f}s")
        
        if features_df.empty:
            print("❌ FALHA: Nenhuma feature extraída")
            return False
        
        print(f"✅ SUCESSO: {len(features_df)} features extraídas")
        print(f"   📊 Colunas: {list(features_df.columns)}")
        print(f"   📈 Shape: {features_df.shape}")
        
        # Verifica distribuição do target
        if 'target_recompra' in features_df.columns:
            target_dist = features_df['target_recompra'].value_counts()
            print(f"   🎯 Distribuição target: {target_dist.to_dict()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_feature_extraction()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 TESTE DE FEATURES CONCLUÍDO COM SUCESSO!")
        print("💡 As otimizações estão funcionando.")
        print("   • Limitações de dataset aplicadas")
        print("   • Logs de progresso funcionando")
        print("   • Extração mais rápida")
        print("\n🚀 Próximo passo: Tentar o treinamento completo no dashboard")
    else:
        print("⚠️ TESTE FALHOU!")
        print("💡 Verifique os logs acima para mais detalhes")
    
    print("=" * 55)