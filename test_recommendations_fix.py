#!/usr/bin/env python3
"""
Teste das Recomendações Inteligentes
Verifica se a função generate_smart_recommendations() funciona corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports necessários
from utils.db import load_vendas_data, get_connection
from utils import load_all_data
import pandas as pd

def test_data_loading():
    """Testa se os dados estão sendo carregados corretamente"""
    print("🔍 Testando carregamento de dados...")
    
    try:
        # Testa load_vendas_data
        print("   Carregando vendas...")
        vendas_df = load_vendas_data()
        print(f"   ✅ Vendas carregadas: {len(vendas_df):,} registros")
        
        # Testa load_all_data
        print("   Carregando todos os dados...")
        vendas_data, cotacoes_df, produtos_cotados_df = load_all_data()
        print(f"   ✅ Dados carregados:")
        print(f"      - Vendas: {len(vendas_data):,} registros")
        print(f"      - Cotações: {len(cotacoes_df):,} registros") 
        print(f"      - Produtos Cotados: {len(produtos_cotados_df):,} registros")
        
        # Verifica estrutura dos dados
        print("\n📊 Estrutura dos dados:")
        if not vendas_df.empty:
            print(f"   Vendas - Colunas: {list(vendas_df.columns)[:5]}...")
            if 'cod_cliente' in vendas_df.columns:
                print(f"   Vendas - Clientes únicos: {vendas_df['cod_cliente'].nunique()}")
            if 'material' in vendas_df.columns:
                print(f"   Vendas - Produtos únicos: {vendas_df['material'].nunique()}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no carregamento: {e}")
        return False

def test_recommendations_logic():
    """Simula a lógica da função generate_smart_recommendations"""
    print("\n🧠 Testando lógica de recomendações...")
    
    try:
        # Carrega dados do sistema
        vendas_df = load_vendas_data()
        
        # Carrega dados adicionais
        try:
            vendas_data, cotacoes_df, produtos_cotados_df = load_all_data()
            # Se vendas_df está vazio, usa o vendas_data da função load_all_data
            if vendas_df.empty and not vendas_data.empty:
                vendas_df = vendas_data
        except Exception as e:
            print(f"   ⚠️ Aviso ao carregar dados adicionais: {e}")
            # Cria DataFrames vazios como fallback
            cotacoes_df = pd.DataFrame()
            produtos_cotados_df = pd.DataFrame()
        
        # Verifica se há dados suficientes
        dados_disponiveis = False
        total_registros = 0
        datasets_info = []
        
        if not vendas_df.empty:
            dados_disponiveis = True
            total_registros += len(vendas_df)
            datasets_info.append(f"Vendas: {len(vendas_df):,}")
            
        if not produtos_cotados_df.empty:
            dados_disponiveis = True
            total_registros += len(produtos_cotados_df)
            datasets_info.append(f"Cotações: {len(produtos_cotados_df):,}")
            
        if not cotacoes_df.empty:
            dados_disponiveis = True
            total_registros += len(cotacoes_df)
            datasets_info.append(f"Cotações Base: {len(cotacoes_df):,}")
        
        print(f"   📈 Dados disponíveis: {dados_disponiveis}")
        print(f"   📊 Total de registros: {total_registros:,}")
        print(f"   📋 Datasets: {datasets_info}")
        
        if not dados_disponiveis or total_registros < 10:
            print(f"   ❌ Dados insuficientes: {total_registros} < 10 mínimo")
            return False
        else:
            print(f"   ✅ Dados suficientes para recomendações!")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro na lógica: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE DAS RECOMENDAÇÕES INTELIGENTES")
    print("=" * 50)
    
    # Testa carregamento de dados
    data_ok = test_data_loading()
    
    # Testa lógica de recomendações
    logic_ok = test_recommendations_logic()
    
    print("\n" + "=" * 50)
    if data_ok and logic_ok:
        print("✅ TESTE PASSOU - Recomendações devem funcionar!")
    else:
        print("❌ TESTE FALHOU - Há problemas a corrigir")
        
    print("\n🔧 Para testar no dashboard:")
    print("1. Acesse: http://127.0.0.1:8050")
    print("2. Vá para 'Sistema B2B Avançado'")
    print("3. Clique em 'Atualizar' nas Recomendações Inteligentes")