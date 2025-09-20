#!/usr/bin/env python3
"""
Teste Ultra-Rápido do Treinamento
Testa com dataset mínimo para garantir que funciona
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_minimal_training():
    """Testa treinamento com dataset mínimo"""
    
    print("⚡ TESTE ULTRA-RÁPIDO - Dataset Mínimo")
    print("=" * 50)
    
    try:
        # Importa o engine ML
        from utils.ml_recommendations import SmartPurchaseRecommendations
        
        print("📦 Engine ML carregado")
        ml_engine = SmartPurchaseRecommendations()
        
        # Cria dataset mínimo (100 registros apenas)
        print("📊 Criando dataset mínimo (100 registros)...")
        
        np.random.seed(42)
        n_records = 100
        materiais = [f"MAT{i:03d}" for i in range(1, 21)]  # 20 materiais
        clientes = [f"CLI{i:02d}" for i in range(1, 11)]  # 10 clientes
        
        vendas_data = []
        base_date = datetime.now() - timedelta(days=180)  # 6 meses
        
        for i in range(n_records):
            date = base_date + timedelta(days=np.random.randint(0, 180))
            vendas_data.append({
                'material': np.random.choice(materiais),
                'cod_cliente': np.random.choice(clientes),
                'cliente': f"Cliente {np.random.choice(clientes)}",
                'produto': f"Produto {np.random.choice(materiais)}",
                'data_faturamento': date,
                'vlr_rol': np.random.uniform(100, 1000),
                'qtd_rol': np.random.uniform(1, 10)
            })
        
        vendas_df = pd.DataFrame(vendas_data)
        
        # Dados de cotações mínimos
        cotacoes_data = []
        for i in range(20):
            cotacoes_data.append({
                'numero_cotacao': f"COT{i:03d}",
                'cod_cliente': np.random.choice(clientes),
                'data_cotacao': base_date + timedelta(days=np.random.randint(0, 180))
            })
        
        cotacoes_df = pd.DataFrame(cotacoes_data)
        
        # Produtos cotados mínimos
        produtos_cotados_data = []
        for i, row in cotacoes_df.iterrows():
            produtos_cotados_data.append({
                'cotacao': row['numero_cotacao'],
                'material': np.random.choice(materiais),
                'cod_cliente': row['cod_cliente']
            })
        
        produtos_cotados_df = pd.DataFrame(produtos_cotados_data)
        
        print(f"   ✅ {len(vendas_df)} vendas")
        print(f"   ✅ {len(cotacoes_df)} cotações")
        print(f"   ✅ {len(produtos_cotados_df)} produtos cotados")
        
        # Testa treinamento completo
        print("\n🤖 Iniciando treinamento completo...")
        start_time = time.time()
        
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
            print(f"   📊 Score: {resultado.get('cv_auc_mean', 'N/A')}")
            print(f"   📈 Samples: {resultado.get('num_samples', 'N/A')}")
            return True
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_training()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TESTE MÍNIMO FUNCIONOU!")
        print("💡 Dataset pequeno treina normalmente.")
        print("   O problema é o volume de dados do sistema real.")
        print("\n🎯 Estratégia:")
        print("   • Filtrar dados por período (últimos 3 meses)")
        print("   • Ou filtrar por cliente específico")
        print("   • Ou usar apenas top produtos")
    else:
        print("⚠️ FALHA MESMO COM DATASET MÍNIMO!")
        print("   Há um problema mais fundamental no código.")
    print("=" * 50)