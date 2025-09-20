"""
Script de teste para validar o sistema de Sugestões Inteligentes de Compra
Dashboard Laura Representações - WEG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dos módulos
from utils.ml_recommendations import purchase_recommender
from utils import load_all_data

def test_abc_xyz_classification():
    """Testa classificação ABC-XYZ"""
    print("\n" + "="*50)
    print("🔍 TESTE: Classificação ABC-XYZ")
    print("="*50)
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas para teste")
            return False
        
        print(f"📊 Dados carregados: {len(vendas_df)} registros de vendas")
        
        # Executa classificação
        resultado = purchase_recommender.classify_abc_xyz(vendas_df)
        
        if resultado.empty:
            print("❌ Classificação ABC-XYZ retornou vazio")
            return False
        
        print(f"✅ Classificação concluída: {len(resultado)} produtos classificados")
        
        # Mostra distribuição
        distribuicao = resultado['classificacao'].value_counts()
        print("\n📈 Distribuição ABC-XYZ:")
        for classe, count in distribuicao.items():
            print(f"   {classe}: {count} produtos ({count/len(resultado)*100:.1f}%)")
        
        # Mostra top 5 produtos
        print("\n🏆 Top 5 produtos (valor):")
        top_5 = resultado.head()
        for _, row in top_5.iterrows():
            print(f"   {row['material']}: {row['classificacao']} - R$ {row['valor_total']:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na classificação ABC-XYZ: {e}")
        return False

def test_safety_stock_calculation():
    """Testa cálculo de safety stock"""
    print("\n" + "="*50)
    print("🔍 TESTE: Cálculo Safety Stock")
    print("="*50)
    
    try:
        # Dados de teste
        demanda_teste = [100, 120, 90, 110, 105, 95, 115, 125, 85, 100]
        
        print(f"📊 Demanda histórica teste: {demanda_teste}")
        
        # Calcula safety stock
        resultado = purchase_recommender.calculate_safety_stock(
            demanda_historica=demanda_teste,
            nivel_servico=0.95,
            leadtime_dias=30
        )
        
        if 'erro' in resultado:
            print(f"❌ Erro no cálculo: {resultado['erro']}")
            return False
        
        print("✅ Safety stock calculado com sucesso:")
        print(f"   Demanda média: {resultado['demanda_media']:.1f}")
        print(f"   Desvio padrão: {resultado['desvio_padrao']:.1f}")
        print(f"   Safety stock: {resultado['safety_stock']:.1f}")
        print(f"   Coef. variação: {resultado['coef_variacao']:.3f}")
        print(f"   Nível serviço: {resultado['nivel_servico']*100:.0f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no cálculo safety stock: {e}")
        return False

def test_demand_forecast():
    """Testa previsão de demanda"""
    print("\n" + "="*50)
    print("🔍 TESTE: Previsão de Demanda")
    print("="*50)
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas para teste")
            return False
        
        # Pega primeiro material com dados
        materiais_com_dados = vendas_df['material'].value_counts()
        if materiais_com_dados.empty:
            print("❌ Sem materiais com dados suficientes")
            return False
        
        material_teste = materiais_com_dados.index[0]
        print(f"📦 Testando material: {material_teste}")
        print(f"📊 Vendas históricas: {materiais_com_dados.iloc[0]} registros")
        
        # Calcula previsão
        resultado = purchase_recommender.calculate_demand_forecast(
            vendas_df, material_teste
        )
        
        if 'erro' in resultado:
            print(f"❌ Erro na previsão: {resultado['erro']}")
            return False
        
        print("✅ Previsão de demanda calculada:")
        print(f"   Demanda média mensal: {resultado['demanda_media_mensal']:.1f}")
        print(f"   Demanda média diária: {resultado['demanda_media_diaria']:.1f}")
        print(f"   Quantidade sugerida: {resultado['quantidade_sugerida']}")
        print(f"   Safety stock: {resultado['safety_stock']}")
        print(f"   Cobertura (dias): {resultado['cobertura_dias']}")
        print(f"   Confiança: {resultado['confianca']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na previsão de demanda: {e}")
        return False

def test_ml_features():
    """Testa extração de features ML"""
    print("\n" + "="*50)
    print("🔍 TESTE: Extração Features ML")
    print("="*50)
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas para teste")
            return False
        
        # Extrai features
        features_df = purchase_recommender.extract_ml_features(
            vendas_df, cotacoes_df
        )
        
        if features_df.empty:
            print("❌ Extração de features retornou vazio")
            return False
        
        print(f"✅ Features extraídas: {len(features_df)} registros")
        print(f"📊 Colunas: {list(features_df.columns)}")
        
        # Mostra estatísticas
        print("\n📈 Estatísticas das features:")
        stats_cols = ['recencia_dias', 'frequencia_12m', 'target_recompra']
        for col in stats_cols:
            if col in features_df.columns:
                print(f"   {col}: média={features_df[col].mean():.2f}, "
                     f"std={features_df[col].std():.2f}")
        
        # Mostra distribuição de target
        target_dist = features_df['target_recompra'].value_counts()
        print(f"\n🎯 Distribuição target:")
        for valor, count in target_dist.items():
            print(f"   {valor}: {count} casos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na extração de features: {e}")
        return False

def test_ml_model():
    """Testa modelo ML (se bibliotecas disponíveis)"""
    print("\n" + "="*50)
    print("🔍 TESTE: Modelo ML")
    print("="*50)
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas para teste")
            return False
        
        # Treina modelo
        resultado_treino = purchase_recommender.train_repurchase_model(
            vendas_df, cotacoes_df
        )
        
        if 'erro' in resultado_treino:
            print(f"⚠️ Modelo ML não disponível: {resultado_treino['erro']}")
            print("📊 Sistema usará heurísticas")
            return True
        
        print("✅ Modelo ML treinado com sucesso:")
        print(f"   Status: {resultado_treino['status']}")
        print(f"   Amostras: {resultado_treino['num_samples']}")
        print(f"   Features: {resultado_treino['num_features']}")
        if 'cv_auc_mean' in resultado_treino:
            print(f"   AUC CV: {resultado_treino['cv_auc_mean']:.3f} ± {resultado_treino['cv_auc_std']:.3f}")
        
        # Testa predições
        predicoes_df = purchase_recommender.predict_repurchase_probability(
            vendas_df, cotacoes_df
        )
        
        if not predicoes_df.empty:
            print(f"✅ Predições geradas: {len(predicoes_df)} registros")
            prob_stats = predicoes_df['prob_recompra_ml'].describe()
            print(f"   Probabilidades: min={prob_stats['min']:.3f}, "
                 f"max={prob_stats['max']:.3f}, média={prob_stats['mean']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no modelo ML: {e}")
        return False

def test_full_suggestions():
    """Testa geração completa de sugestões"""
    print("\n" + "="*50)
    print("🔍 TESTE: Sugestões Completas")
    print("="*50)
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_df = load_all_data()
        
        if vendas_df.empty:
            print("❌ Sem dados de vendas para teste")
            return False
        
        # Gera sugestões
        sugestoes_df = purchase_recommender.generate_purchase_suggestions(
            vendas_df, cotacoes_df, top_n=10
        )
        
        if sugestoes_df.empty:
            print("❌ Nenhuma sugestão gerada")
            return False
        
        print(f"✅ Sugestões geradas: {len(sugestoes_df)} produtos")
        
        # Mostra top 5
        print("\n🏆 Top 5 sugestões:")
        top_5 = sugestoes_df.head()
        for _, row in top_5.iterrows():
            print(f"   {row['material']}: {row['classificacao']} - "
                 f"Qtd: {row['quantidade_sugerida']} - "
                 f"Score: {row['priority_score']:.1f}")
        
        # Estatísticas
        print(f"\n📊 Estatísticas:")
        print(f"   Quantidade total sugerida: {sugestoes_df['quantidade_sugerida'].sum():,.0f}")
        print(f"   Safety stock médio: {sugestoes_df['safety_stock'].mean():.1f}")
        print(f"   Confiança média: {sugestoes_df['confianca'].mean():.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na geração de sugestões: {e}")
        return False

def test_feedback_system():
    """Testa sistema de feedback"""
    print("\n" + "="*50)
    print("🔍 TESTE: Sistema de Feedback")
    print("="*50)
    
    try:
        # Testa salvar feedback
        sucesso = purchase_recommender.save_feedback(
            material="TESTE_001",
            cod_cliente="CLI_TESTE",
            feedback_type="positivo",
            motivo="Teste automatizado",
            quantidade_sugerida=100,
            usuario="teste"
        )
        
        if sucesso:
            print("✅ Feedback salvo com sucesso")
        else:
            print("❌ Erro ao salvar feedback")
            return False
        
        # Testa obter estatísticas
        stats = purchase_recommender.get_feedback_stats()
        
        if 'erro' not in stats:
            print("✅ Estatísticas de feedback obtidas:")
            print(f"   Total feedbacks: {stats['total_feedbacks']}")
            print(f"   Taxa aceitação: {stats['taxa_aceitacao']*100:.1f}%")
        else:
            print(f"⚠️ Erro nas estatísticas: {stats['erro']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de feedback: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO SISTEMA ML")
    print("Dashboard Laura Representações - WEG")
    print("Data:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    # Lista de testes
    testes = [
        ("ABC-XYZ Classification", test_abc_xyz_classification),
        ("Safety Stock Calculation", test_safety_stock_calculation),
        ("Demand Forecast", test_demand_forecast),
        ("ML Features", test_ml_features),
        ("ML Model", test_ml_model),
        ("Full Suggestions", test_full_suggestions),
        ("Feedback System", test_feedback_system)
    ]
    
    # Executa testes
    resultados = []
    for nome, teste_func in testes:
        try:
            resultado = teste_func()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ ERRO CRÍTICO em {nome}: {e}")
            resultados.append((nome, False))
    
    # Relatório final
    print("\n" + "="*50)
    print("📋 RELATÓRIO FINAL DOS TESTES")
    print("="*50)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status}: {nome}")
        if resultado:
            sucessos += 1
    
    print(f"\n🎯 RESULTADO: {sucessos}/{len(testes)} testes passaram")
    
    if sucessos == len(testes):
        print("🎉 TODOS OS TESTES PASSARAM! Sistema ML funcionando corretamente.")
    elif sucessos >= len(testes) * 0.7:
        print("⚠️ MAIORIA DOS TESTES PASSOU. Sistema funcional com algumas limitações.")
    else:
        print("❌ MUITOS TESTES FALHARAM. Sistema precisa de correções.")
    
    return sucessos == len(testes)

if __name__ == "__main__":
    main()