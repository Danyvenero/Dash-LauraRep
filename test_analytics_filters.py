#!/usr/bin/env python3
"""
Teste direto dos filtros nos Analytics Avançados
"""

import sys
import os
sys.path.append(os.getcwd())

from webapp.callbacks import apply_filters, load_vendas_data, load_cotacoes_data
from utils import AdvancedAnalytics

def test_analytics_filters():
    """Testa se os filtros funcionam corretamente no Analytics Avançados"""
    print("🧪 Testando filtros dos Analytics Avançados...")
    
    # Carregar dados
    df_vendas = load_vendas_data()
    df_cotacoes = load_cotacoes_data()
    
    print(f"📊 Dados carregados - Vendas: {len(df_vendas) if df_vendas is not None else 0} registros")
    print(f"📊 Dados carregados - Cotações: {len(df_cotacoes) if df_cotacoes is not None else 0} registros")
    
    if df_vendas is None or df_vendas.empty:
        print("❌ Sem dados de vendas para testar")
        return
    
    # Teste 1: Sem filtros
    print("\n🔍 Teste 1: Sem filtros")
    dados_sem_filtro = apply_filters(df_vendas, None, None, None, None, None, None)
    print(f"Registros sem filtro: {len(dados_sem_filtro)}")
    
    # Teste 2: Filtro por ano
    print("\n🔍 Teste 2: Filtro por ano 2024")
    dados_filtro_ano = apply_filters(df_vendas, 2024, None, None, None, None, None)
    print(f"Registros com filtro ano 2024: {len(dados_filtro_ano)}")
    
    # Verificar quais anos existem nos dados
    if 'data_faturamento' in df_vendas.columns:
        import pandas as pd
        df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
        anos_unicos = df_vendas['data_faturamento'].dt.year.dropna().unique()
        print(f"Anos disponíveis nos dados: {sorted(anos_unicos)}")
    elif 'data' in df_vendas.columns:
        import pandas as pd
        df_vendas['data'] = pd.to_datetime(df_vendas['data'], errors='coerce')
        anos_unicos = df_vendas['data'].dt.year.dropna().unique()
        print(f"Anos disponíveis nos dados: {sorted(anos_unicos)}")
    
    # Teste 3: Analytics com dados filtrados
    print("\n🔍 Teste 3: Analytics com dados filtrados")
    try:
        analytics = AdvancedAnalytics(dados_filtro_ano, df_cotacoes)
        sazonalidade = analytics.analyze_seasonality(vendas_df=dados_filtro_ano)
        print(f"✅ Análise de sazonalidade gerada com {len(sazonalidade) if sazonalidade is not None else 0} pontos")
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 4: Verificar colunas disponíveis
    print("\n🔍 Teste 4: Verificar colunas disponíveis")
    print(f"Colunas em vendas: {list(df_vendas.columns)}")
    
    # Teste 5: Filtro por canal (se existir)
    if 'canal_distribuicao' in df_vendas.columns:
        canais = df_vendas['canal_distribuicao'].dropna().unique()[:3]  # Pegar primeiros 3
        if len(canais) > 0:
            print(f"\n🔍 Teste 5: Filtro por canal '{canais[0]}'")
            dados_filtro_canal = apply_filters(df_vendas, None, None, None, None, canais[0], None)
            print(f"Registros com filtro canal: {len(dados_filtro_canal)}")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    test_analytics_filters()
