#!/usr/bin/env python3
"""
Teste direto das sugestões de compra para verificar probabilidades na interface
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

def test_interface_sugestoes():
    """Testa as sugestões como elas aparecem na interface"""
    
    print("🔍 TESTE DAS SUGESTÕES DE COMPRA (INTERFACE)")
    print("="*60)
    
    try:
        # Carregar dados
        vendas_df, cotacoes_df, produtos_cotados_df = get_data_from_db()
        
        if vendas_df is None:
            print("❌ Erro ao carregar dados")
            return
        
        print(f"✅ Vendas: {len(vendas_df)} registros")
        
        # Inicializar recomendações
        smart_rec = SmartPurchaseRecommendations()
        
        # Gerar sugestões como na interface
        print("\n🔮 Gerando sugestões de compra...")
        resultado = smart_rec.generate_purchase_suggestions(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            cliente_filter=None,  # Sem filtro de cliente
            top_n=100
        )
        
        if resultado is None or 'sugestoes' not in resultado:
            print("❌ Erro: Nenhuma sugestão gerada")
            return
        
        if not resultado['sugestoes']:  # Lista vazia
            print("❌ Erro: Lista de sugestões vazia")
            return
        
        sugestoes_df = pd.DataFrame(resultado['sugestoes'])
        
        if sugestoes_df.empty:
            print("❌ Erro: DataFrame de sugestões vazio")
            return
        
        print(f"✅ Sugestões geradas: {len(sugestoes_df)} registros")
        print(f"✅ Colunas disponíveis: {list(sugestoes_df.columns)}")
        
        # Analisar probabilidades
        if 'prob_recompra' in sugestoes_df.columns:
            prob_col = sugestoes_df['prob_recompra']
            
            print(f"\n📊 ANÁLISE DA PROB_RECOMPRA (INTERFACE):")
            print(f"   Count: {prob_col.count()}")
            print(f"   Min: {prob_col.min():.4f}")
            print(f"   Max: {prob_col.max():.4f}")
            print(f"   Mean: {prob_col.mean():.4f}")
            print(f"   Median: {prob_col.median():.4f}")
            print(f"   Std: {prob_col.std():.4f}")
            
            # Verificar valores problemáticos
            exact_100 = (prob_col == 1.0).sum()
            exact_95 = (prob_col >= 0.95).sum()
            exact_values = prob_col.round(3).value_counts().head(10)
            
            print(f"\n🚨 VALORES PROBLEMÁTICOS:")
            print(f"   Exatamente 1.00: {exact_100}")
            print(f"   >= 0.95: {exact_95}")
            
            print(f"\n📊 TOP 10 VALORES MAIS FREQUENTES:")
            for val, count in exact_values.items():
                pct = (count / len(prob_col)) * 100
                display_val = val * 100  # Converter para porcentagem para visualização
                print(f"   {display_val:.1f}%: {count} ocorrências ({pct:.1f}%)")
            
            # Mostrar exemplos
            print(f"\n📋 EXEMPLOS DE SUGESTÕES:")
            for idx, row in sugestoes_df.head(10).iterrows():
                material = row.get('material', 'N/A')
                produto = row.get('produto', 'N/A')[:30] + '...' if len(str(row.get('produto', 'N/A'))) > 30 else row.get('produto', 'N/A')
                prob = row.get('prob_recompra', 0)
                print(f"   {material}: {produto} -> {prob:.3f} ({prob*100:.1f}%)")
        
        print(f"\n✅ TESTE CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_interface_sugestoes()