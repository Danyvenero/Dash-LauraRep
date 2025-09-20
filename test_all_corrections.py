"""
Teste das correções implementadas para o sistema de recomendações ML
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.ml_recommendations import SmartPurchaseRecommendations

def test_corrections():
    """Testa todas as correções implementadas"""
    
    print("🧪 TESTANDO CORREÇÕES IMPLEMENTADAS")
    print("=" * 50)
    
    # Dados de teste simulando vendas
    vendas_test = []
    materiais = ['7505591', '8602115', '18531309', '8745241', '18531310']
    clientes = ['929433', '767194', '920113', '1075583']
    
    # Gera dados de vendas com variabilidade
    for i in range(100):
        material = np.random.choice(materiais)
        cliente = np.random.choice(clientes)
        
        # Simula diferentes padrões de demanda
        if material == '7505591':  # Produto de alta variabilidade
            qtd = np.random.randint(1, 15)
            vlr = qtd * np.random.uniform(8000, 12000)
        elif material == '8602115':  # Produto de baixa variabilidade
            qtd = np.random.randint(3, 7)
            vlr = qtd * np.random.uniform(4500, 5500)
        else:  # Outros produtos
            qtd = np.random.randint(1, 10)
            vlr = qtd * np.random.uniform(2000, 8000)
        
        vendas_test.append({
            'material': material,
            'produto': f'PRODUTO TESTE {material}',
            'cod_cliente': cliente,
            'cliente': f'Cliente {cliente}',
            'qtd_rol': qtd,
            'vlr_rol': vlr,
            'data_faturamento': datetime.now() - timedelta(days=np.random.randint(1, 180))
        })
    
    vendas_df = pd.DataFrame(vendas_test)
    print(f"📊 Dados de teste criados: {len(vendas_df)} registros")
    
    # Instancia o recomendador
    recommender = SmartPurchaseRecommendations()
    
    # TESTE 1: Classificação ABC-XYZ com coeficiente de variação corrigido
    print("\n🔍 TESTE 1: Classificação ABC-XYZ")
    classificacao = recommender.classify_abc_xyz(vendas_df)
    
    if not classificacao.empty:
        print("✅ Classificação ABC-XYZ executada com sucesso")
        print(f"📈 CV médio: {classificacao['cv_valor'].mean():.3f}")
        print(f"📊 Produtos com CV > 0: {(classificacao['cv_valor'] > 0).sum()}")
        print(f"📋 Distribuição XYZ: {classificacao['classe_xyz'].value_counts().to_dict()}")
    else:
        print("❌ Erro na classificação ABC-XYZ")
    
    # TESTE 2: Cálculo de safety stock com níveis de serviço dinâmicos
    print("\n🛡️ TESTE 2: Safety Stock com Níveis de Serviço Dinâmicos")
    
    test_demand = [5, 8, 3, 12, 6, 9, 4, 7, 11, 5]
    
    # Testa diferentes classificações
    classificacoes_test = [('A', 'X'), ('B', 'Y'), ('C', 'Z')]
    
    for abc, xyz in classificacoes_test:
        safety_result = recommender.calculate_safety_stock(
            test_demand, 
            classificacao_abc=abc,
            classificacao_xyz=xyz
        )
        
        nivel_servico = safety_result['nivel_servico']
        safety_stock = safety_result['safety_stock']
        
        print(f"  📊 {abc}{xyz}: Nível {nivel_servico:.0%} → Safety Stock: {safety_stock:.1f}")
    
    # TESTE 3: Cobertura dinâmica baseada na variabilidade
    print("\n📅 TESTE 3: Cobertura Dinâmica")
    
    for material in materiais[:3]:
        material_data = vendas_df[vendas_df['material'] == material]
        if not material_data.empty:
            produto_info = classificacao[classificacao['material'] == material]
            if not produto_info.empty:
                abc_class = produto_info.iloc[0]['classe_abc']
                xyz_class = produto_info.iloc[0]['classe_xyz']
                
                demanda_info = recommender.calculate_demand_forecast(
                    vendas_df, 
                    material, 
                    None,
                    classificacao_abc=abc_class,
                    classificacao_xyz=xyz_class
                )
                
                if 'erro' not in demanda_info:
                    cobertura = demanda_info['cobertura_dias']
                    nivel_servico = demanda_info['nivel_servico']
                    cv = demanda_info['coef_variacao']
                    
                    print(f"  📦 {material} ({abc_class}{xyz_class}): {cobertura} dias, NS: {nivel_servico:.0%}, CV: {cv:.3f}")
    
    # TESTE 4: Geração de sugestões completas
    print("\n🎯 TESTE 4: Geração de Sugestões Completas")
    
    sugestoes = recommender.generate_purchase_suggestions(
        vendas_df, 
        top_n=5
    )
    
    if not sugestoes.empty:
        print("✅ Sugestões geradas com sucesso")
        print(f"📊 Total de sugestões: {len(sugestoes)}")
        
        # Verifica diversidade nos valores
        print("\n📈 ANÁLISE DE DIVERSIDADE:")
        print(f"  🔹 Cobertura única: {sugestoes['cobertura_dias'].nunique()} valores diferentes")
        print(f"  🔹 Nível de serviço único: {sugestoes['nivel_servico'].nunique()} valores diferentes")
        print(f"  🔹 CV > 0: {(sugestoes['coef_variacao'] > 0).sum()} produtos")
        
        print("\n📋 RESUMO DAS PRIMEIRAS 3 SUGESTÕES:")
        for i, (_, row) in enumerate(sugestoes.head(3).iterrows()):
            print(f"  {i+1}. {row['material']} ({row['classificacao']})")
            print(f"     Qtd: {row['quantidade_sugerida']}, Cobertura: {row['cobertura_dias']} dias")
            print(f"     NS: {row['nivel_servico']:.0%}, CV: {row['coef_variacao']:.3f}")
            print()
    else:
        print("❌ Erro na geração de sugestões")
    
    print("\n" + "=" * 50)
    print("✅ TESTE CONCLUÍDO!")
    
    return sugestoes

if __name__ == "__main__":
    test_corrections()