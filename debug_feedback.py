#!/usr/bin/env python3
"""
Script para debugar problema da taxa de aprovação 100%
"""
import sqlite3
import sys
import os

# Adiciona o path atual para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ml_recommendations import SmartPurchaseRecommendations

def debug_feedback():
    print("=== DEBUG TAXA DE APROVAÇÃO ===")
    
    # 1. Verifica tabelas no banco
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tabelas no banco: {[t[0] for t in tables]}")
        
        # 2. Verifica se existe feedback_recomendacoes
        if 'feedback_recomendacoes' in [t[0] for t in tables]:
            cursor.execute("SELECT * FROM feedback_recomendacoes")
            feedbacks = cursor.fetchall()
            print(f"📊 Feedbacks na tabela: {feedbacks}")
        else:
            print("❌ Tabela feedback_recomendacoes NÃO existe")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro acessando banco: {e}")
    
    # 3. Testa método get_feedback_stats diretamente
    try:
        recommender = SmartPurchaseRecommendations()
        stats = recommender.get_feedback_stats()
        print(f"📈 Stats retornadas pelo método: {stats}")
        
    except Exception as e:
        print(f"❌ Erro no método get_feedback_stats: {e}")

def debug_probabilidade():
    print("\n=== DEBUG PROBABILIDADE DE RECOMPRA ===")
    
    try:
        from utils.data_loader import load_vendas_data, load_cotacoes_data
        
        # Carrega dados
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        
        print(f"📊 Dados carregados - Vendas: {len(vendas_df)}, Cotações: {len(cotacoes_df)}")
        
        # Filtra uma amostra pequena
        vendas_sample = vendas_df.head(100)
        
        # Testa extração de features
        recommender = SmartPurchaseRecommendations()
        features_df = recommender.extract_ml_features(vendas_sample, cotacoes_df)
        
        print(f"📋 Features extraídas: {len(features_df)} registros")
        if not features_df.empty:
            print(f"📊 Colunas: {list(features_df.columns)}")
            
            # Verifica se probabilidade_recorrencia existe
            if 'probabilidade_recorrencia' in features_df.columns:
                prob_stats = features_df['probabilidade_recorrencia'].describe()
                print(f"📈 Stats probabilidade_recorrencia: {prob_stats}")
            else:
                print("❌ Coluna probabilidade_recorrencia NÃO existe")
                
            # Testa heurística
            prob_heuristica = recommender._calculate_heuristic_probability(features_df)
            print(f"📊 Heurística - min: {prob_heuristica.min():.3f}, max: {prob_heuristica.max():.3f}, mean: {prob_heuristica.mean():.3f}")
        
    except Exception as e:
        print(f"❌ Erro no debug de probabilidade: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_feedback()
    debug_probabilidade()