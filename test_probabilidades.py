#!/usr/bin/env python3
"""
Teste direto das probabilidades de recompra após correções
"""

import os
import pandas as pd
import numpy as np
import sqlite3
from utils.ml_recommendations import SmartPurchaseRecommendations
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_from_db():
    """Carrega dados do database"""
    try:
        db_path = os.path.join('instance', 'database.sqlite')
        if not os.path.exists(db_path):
            print(f"❌ Database não encontrado: {db_path}")
            return None, None, None
        
        conn = sqlite3.connect(db_path)
        
        # Carregar vendas
        vendas_df = pd.read_sql_query("SELECT * FROM vendas", conn)
        if 'data' in vendas_df.columns:
            vendas_df['data'] = pd.to_datetime(vendas_df['data'])
        
        # Carregar cotações se existir
        try:
            cotacoes_df = pd.read_sql_query("SELECT * FROM cotacoes", conn)
            if 'data' in cotacoes_df.columns:
                cotacoes_df['data'] = pd.to_datetime(cotacoes_df['data'])
        except:
            cotacoes_df = None
        
        # Carregar produtos_cotados se existir
        try:
            produtos_cotados_df = pd.read_sql_query("SELECT * FROM produtos_cotados", conn)
            if 'data' in produtos_cotados_df.columns:
                produtos_cotados_df['data'] = pd.to_datetime(produtos_cotados_df['data'])
        except:
            produtos_cotados_df = None
        
        conn.close()
        return vendas_df, cotacoes_df, produtos_cotados_df
        
    except Exception as e:
        print(f"❌ Erro carregando dados: {e}")
        return None, None, None

def test_probabilidades():
    """Testa as probabilidades após as correções"""
    
    print("🔍 TESTE DAS PROBABILIDADES DE RECOMPRA")
    print("="*50)
    
    try:
        # Carregar dados
        vendas_df, cotacoes_df, produtos_cotados_df = get_data_from_db()
        
        if vendas_df is None:
            print("❌ Erro ao carregar dados")
            return
        
        print(f"✅ Vendas: {len(vendas_df)} registros")
        print(f"✅ Cotações: {len(cotacoes_df) if cotacoes_df is not None else 0} registros")
        print(f"✅ Produtos Cotados: {len(produtos_cotados_df) if produtos_cotados_df is not None else 0} registros")
        
        # Filtrar dados recentes (últimos 2 anos)
        data_limite = pd.Timestamp.now() - pd.DateOffset(years=2)
        vendas_recentes = vendas_df[vendas_df['data'] >= data_limite].copy()
        
        print(f"✅ Vendas recentes (últimos 2 anos): {len(vendas_recentes)} registros")
        
        if len(vendas_recentes) < 100:
            print("⚠️ Usando todos os dados disponíveis")
            vendas_recentes = vendas_df.copy()
        
        # Inicializar ML
        ml_rec = SmartPurchaseRecommendations()
        
        # Extrair features
        print("\n🔬 Extraindo features...")
        features_df = ml_rec.extract_ml_features(vendas_recentes, cotacoes_df, produtos_cotados_df)
        
        if features_df is None or features_df.empty:
            print("❌ Erro: Features vazias")
            return
        
        print(f"✅ Features extraídas: {len(features_df)} registros")
        
        # Analisar coluna probabilidade_recorrencia
        if 'probabilidade_recorrencia' in features_df.columns:
            prob_col = features_df['probabilidade_recorrencia']
            
            print(f"\n📊 ANÁLISE DA PROBABILIDADE_RECORRENCIA:")
            print(f"   Count: {prob_col.count()}")
            print(f"   Min: {prob_col.min():.4f}")
            print(f"   Max: {prob_col.max():.4f}")
            print(f"   Mean: {prob_col.mean():.4f}")
            print(f"   Median: {prob_col.median():.4f}")
            print(f"   Std: {prob_col.std():.4f}")
            
            # Distribuição por faixas
            print(f"\n📈 DISTRIBUIÇÃO POR FAIXAS:")
            bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
            prob_ranges = pd.cut(prob_col, bins=bins, labels=labels, include_lowest=True)
            range_counts = prob_ranges.value_counts()
            
            for range_name, count in range_counts.items():
                pct = (count / len(prob_col)) * 100
                print(f"   {range_name}: {count} ({pct:.1f}%)")
            
            # Verificar valores exatos problemáticos
            exact_85 = (prob_col == 0.85).sum()
            exact_95 = (prob_col == 0.95).sum()
            exact_100 = (prob_col == 1.0).sum()
            exact_values = prob_col.round(3).value_counts().head(10)
            
            print(f"\n🚨 VALORES EXATOS PROBLEMÁTICOS:")
            print(f"   Exatamente 0.85: {exact_85}")
            print(f"   Exatamente 0.95: {exact_95}")
            print(f"   Exatamente 1.00: {exact_100}")
            print(f"\n📊 TOP 10 VALORES MAIS FREQUENTES:")
            for val, count in exact_values.items():
                pct = (count / len(prob_col)) * 100
                display_val = val * 100  # Converter para porcentagem
                print(f"   {display_val:.1f}%: {count} ocorrências ({pct:.1f}%)")
        
        # Testar a função heurística também
        print(f"\n🧮 TESTANDO FUNÇÃO HEURÍSTICA...")
        prob_heuristic = ml_rec._calculate_heuristic_probability(features_df)
        
        if not prob_heuristic.empty:
            print(f"   Count: {prob_heuristic.count()}")
            print(f"   Min: {prob_heuristic.min():.4f}")
            print(f"   Max: {prob_heuristic.max():.4f}")
            print(f"   Mean: {prob_heuristic.mean():.4f}")
            print(f"   Median: {prob_heuristic.median():.4f}")
            
            # Distribuição da heurística
            bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
            heur_ranges = pd.cut(prob_heuristic, bins=bins, labels=labels, include_lowest=True)
            heur_counts = heur_ranges.value_counts()
            
            print(f"\n📈 DISTRIBUIÇÃO HEURÍSTICA:")
            for range_name, count in heur_counts.items():
                pct = (count / len(prob_heuristic)) * 100
                print(f"   {range_name}: {count} ({pct:.1f}%)")
        
        print(f"\n✅ TESTE CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_probabilidades()