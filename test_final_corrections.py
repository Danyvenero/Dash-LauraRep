"""
Teste Final das Correções Implementadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.ml_recommendations import SmartPurchaseRecommendations

def test_final_corrections():
    """Teste abrangente das correções implementadas"""
    
    print("🎯 TESTE FINAL DAS CORREÇÕES")
    print("=" * 60)
    
    # Dados de teste mais realistas
    vendas_test = []
    materiais = ['MAT001', 'MAT002', 'MAT003', 'MAT004', 'MAT005', 'MAT006']
    clientes = ['CLI001', 'CLI002', 'CLI003']
    
    # Gera diferentes padrões de compra
    for material in materiais:
        # MAT001: Produto com apenas 1 compra (deve ser filtrado)
        if material == 'MAT001':
            vendas_test.append({
                'material': material,
                'produto': f'PRODUTO {material} - UMA COMPRA',
                'cod_cliente': 'CLI001',
                'cliente': 'Cliente 001',
                'qtd_rol': 5,
                'vlr_rol': 5000,
                'data_faturamento': datetime.now() - timedelta(days=30)
            })
        
        # MAT002: Produto regular (baixa variabilidade)
        elif material == 'MAT002':
            for i in range(6):
                vendas_test.append({
                    'material': material,
                    'produto': f'PRODUTO {material} - REGULAR',
                    'cod_cliente': np.random.choice(clientes),
                    'cliente': f'Cliente {np.random.choice(["001", "002", "003"])}',
                    'qtd_rol': np.random.randint(4, 6),  # Baixa variabilidade
                    'vlr_rol': np.random.uniform(4800, 5200),
                    'data_faturamento': datetime.now() - timedelta(days=i*30 + np.random.randint(0, 10))
                })
        
        # MAT003: Produto irregular (alta variabilidade)
        elif material == 'MAT003':
            for i in range(5):
                vendas_test.append({
                    'material': material,
                    'produto': f'PRODUTO {material} - IRREGULAR',
                    'cod_cliente': np.random.choice(clientes),
                    'cliente': f'Cliente {np.random.choice(["001", "002", "003"])}',
                    'qtd_rol': np.random.randint(1, 15),  # Alta variabilidade
                    'vlr_rol': np.random.uniform(1000, 10000),
                    'data_faturamento': datetime.now() - timedelta(days=i*45 + np.random.randint(0, 30))
                })
        
        # MAT004-006: Outros produtos com histórico mínimo
        else:
            for i in range(3):
                vendas_test.append({
                    'material': material,
                    'produto': f'PRODUTO {material}',
                    'cod_cliente': np.random.choice(clientes),
                    'cliente': f'Cliente {np.random.choice(["001", "002", "003"])}',
                    'qtd_rol': np.random.randint(2, 8),
                    'vlr_rol': np.random.uniform(2000, 6000),
                    'data_faturamento': datetime.now() - timedelta(days=i*60 + np.random.randint(0, 20))
                })
    
    vendas_df = pd.DataFrame(vendas_test)
    print(f"📊 Dados de teste criados: {len(vendas_df)} registros")
    print(f"📦 Produtos únicos: {vendas_df['material'].nunique()}")
    print(f"🛒 Distribuição por produto:")
    for mat, count in vendas_df['material'].value_counts().items():
        print(f"  • {mat}: {count} transações")
    
    # Instancia o recomendador
    recommender = SmartPurchaseRecommendations()
    
    # TESTE 1: Verificar filtro de histórico insuficiente
    print(f"\n🔍 TESTE 1: Filtro de Histórico Insuficiente")
    classificacao = recommender.classify_abc_xyz(vendas_df)
    
    if not classificacao.empty:
        produtos_filtrados = set(vendas_df['material'].unique()) - set(classificacao['material'].unique())
        print(f"✅ Classificação executada")
        print(f"📊 Produtos antes do filtro: {vendas_df['material'].nunique()}")
        print(f"📊 Produtos após filtro: {len(classificacao)}")
        if produtos_filtrados:
            print(f"🚫 Produtos filtrados (< 2 transações): {produtos_filtrados}")
        else:
            print(f"⚠️ Nenhum produto foi filtrado (todos têm ≥ 2 transações)")
    else:
        print("❌ Erro na classificação")
        return
    
    # TESTE 2: Verificar diversidade de métricas
    print(f"\n📊 TESTE 2: Diversidade de Métricas")
    
    sugestoes = recommender.generate_purchase_suggestions(vendas_df, top_n=10)
    
    if not sugestoes.empty:
        print(f"✅ {len(sugestoes)} sugestões geradas")
        
        # Análise de diversidade
        cobertura_valores = sugestoes['cobertura_dias'].nunique()
        servico_valores = sugestoes['nivel_servico'].nunique()
        cv_maior_zero = (sugestoes['coef_variacao'] > 0).sum()
        
        print(f"\n📈 DIVERSIDADE DAS MÉTRICAS:")
        print(f"  🕒 Valores únicos de cobertura: {cobertura_valores}")
        print(f"  🎯 Valores únicos de nível de serviço: {servico_valores}")
        print(f"  📊 Produtos com CV > 0: {cv_maior_zero}/{len(sugestoes)}")
        
        print(f"\n📋 RESUMO DAS SUGESTÕES:")
        for i, (_, row) in enumerate(sugestoes.head(5).iterrows()):
            print(f"  {i+1}. {row['material']} ({row['classificacao']})")
            print(f"     📦 Qtd: {row['quantidade_sugerida']}")
            print(f"     📅 Cobertura: {row['cobertura_dias']} dias")
            print(f"     🎯 NS: {row['nivel_servico']:.0%}")
            print(f"     📊 CV: {row['coef_variacao']:.3f}")
            print()
        
        # Verifica se MAT001 foi filtrado
        if 'MAT001' not in sugestoes['material'].values:
            print("✅ SUCESSO: MAT001 (1 transação) foi corretamente filtrado!")
        else:
            print("❌ ERRO: MAT001 não deveria aparecer nas sugestões!")
            
    else:
        print("❌ Nenhuma sugestão gerada")
    
    # TESTE 3: Verificar se colinearidade foi reduzida
    print(f"\n🔬 TESTE 3: Verificação de Features ML")
    
    try:
        features_df = recommender.extract_ml_features(vendas_df)
        if not features_df.empty:
            print(f"✅ Features extraídas: {len(features_df)} registros")
            
            # Verifica features removidas
            removed_features = ['regularidade_cv', 'compras_por_ano']
            existing_features = set(features_df.columns)
            
            print(f"\n🔧 FEATURES REMOVIDAS (colinearidade):")
            for feat in removed_features:
                if feat not in existing_features:
                    print(f"  ✅ {feat} - Removida com sucesso")
                else:
                    print(f"  ❌ {feat} - Ainda presente!")
            
            print(f"\n📊 FEATURES ATUAIS: {len(features_df.columns) - 3} features")  # -3 para material, cod_cliente, target
            feature_list = [col for col in features_df.columns if col not in ['material', 'cod_cliente', 'target_recompra']]
            for feat in feature_list:
                print(f"  • {feat}")
                
        else:
            print("❌ Erro na extração de features")
            
    except Exception as e:
        print(f"❌ Erro no teste de features: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎉 TESTE FINAL CONCLUÍDO!")
    
    return sugestoes

if __name__ == "__main__":
    test_final_corrections()