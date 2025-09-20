"""
Teste para verificar se o erro de features foi corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.ml_recommendations import SmartPurchaseRecommendations

def test_model_training_fix():
    """Testa se o erro de treinamento foi corrigido"""
    
    print("🔧 TESTE: Correção do Erro de Treinamento ML")
    print("=" * 50)
    
    # Cria dados de teste simples
    vendas_test = []
    for i in range(20):
        vendas_test.append({
            'material': f'MAT{i%3:03d}',
            'produto': f'PRODUTO {i%3:03d}',
            'cod_cliente': f'CLI{i%2:03d}',
            'cliente': f'Cliente {i%2:03d}',
            'qtd_rol': np.random.randint(1, 10),
            'vlr_rol': np.random.uniform(1000, 5000),
            'data_faturamento': datetime.now() - timedelta(days=np.random.randint(1, 365))
        })
    
    vendas_df = pd.DataFrame(vendas_test)
    print(f"📊 Dados de teste: {len(vendas_df)} registros")
    
    # Instancia o recomendador
    recommender = SmartPurchaseRecommendations()
    
    # Força limpeza de modelos antigos
    print("🧹 Limpando modelos antigos...")
    recommender._clear_incompatible_model()
    
    try:
        # Tenta treinar o modelo
        print("🤖 Testando treinamento do modelo...")
        result = recommender.train_repurchase_model(vendas_df, retrain=True)
        
        if 'erro' not in result:
            print("✅ Treinamento executado com sucesso!")
            print(f"📊 Resultado: {result}")
            
            # Testa predição
            print("🔮 Testando predições...")
            probs = recommender.predict_repurchase_probability(vendas_df)
            
            if not probs.empty:
                print("✅ Predições funcionando!")
                print(f"📊 {len(probs)} predições geradas")
                print(f"📈 Probabilidades: min={probs['prob_recompra_ml'].min():.3f}, max={probs['prob_recompra_ml'].max():.3f}")
            else:
                print("❌ Erro nas predições")
                
        else:
            print(f"❌ Erro no treinamento: {result}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 TESTE CONCLUÍDO!")

if __name__ == "__main__":
    test_model_training_fix()