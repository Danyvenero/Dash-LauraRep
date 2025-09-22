#!/usr/bin/env python3
"""
Teste Isolado da Função de Recomendações
Testa apenas a lógica sem inicializar o app completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from utils.db import load_vendas_data
from utils import load_all_data

def simulate_recommendations_function():
    """Simula exatamente a lógica da função generate_smart_recommendations"""
    print("🔍 Simulando generate_smart_recommendations()...")
    
    try:
        # Carrega dados do sistema (mesma lógica da função real)
        print("   📊 Carregando vendas...")
        vendas_df = load_vendas_data()
        
        # Carrega dados adicionais
        try:
            print("   📊 Carregando dados adicionais...")
            vendas_data, cotacoes_df, produtos_cotados_df = load_all_data()
            # Se vendas_df está vazio, usa o vendas_data da função load_all_data
            if vendas_df.empty and not vendas_data.empty:
                vendas_df = vendas_data
                print("   🔄 Usando vendas_data do load_all_data")
        except Exception as e:
            print(f"   ⚠️ Erro ao carregar dados adicionais: {e}")
            # Cria DataFrames vazios como fallback
            cotacoes_df = pd.DataFrame()
            produtos_cotados_df = pd.DataFrame()
        
        # Verifica se há dados suficientes (lógica exata da função)
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
        print(f"   📋 Datasets: {', '.join(datasets_info)}")
        
        # Condição de dados insuficientes (lógica exata da função)
        if not dados_disponiveis or total_registros < 10:
            print(f"   ❌ DADOS INSUFICIENTES: {total_registros} < 10 mínimo")
            print(f"   🔍 Motivos:")
            print(f"      - dados_disponiveis = {dados_disponiveis}")
            print(f"      - total_registros = {total_registros}")
            print(f"      - vendas_df.empty = {vendas_df.empty}")
            print(f"      - produtos_cotados_df.empty = {produtos_cotados_df.empty}")
            print(f"      - cotacoes_df.empty = {cotacoes_df.empty}")
            return "DADOS_INSUFICIENTES"
        
        # Se chegou aqui, dados são suficientes
        print("   ✅ DADOS SUFICIENTES! Prosseguindo com análise...")
        
        # Análise básica dos dados para gerar recomendações inteligentes
        total_clientes = 0
        total_produtos = 0
        total_cotacoes = 0
        
        # Conta clientes únicos de vendas
        if not vendas_df.empty and 'cod_cliente' in vendas_df.columns:
            total_clientes += len(vendas_df['cod_cliente'].unique())
        
        # Conta produtos únicos de vendas    
        if not vendas_df.empty and 'material' in vendas_df.columns:
            total_produtos = len(vendas_df['material'].unique())
            
        # Conta cotações
        if not produtos_cotados_df.empty:
            total_cotacoes = len(produtos_cotados_df)
        
        # Adiciona clientes de cotações se houver
        if not produtos_cotados_df.empty and 'cod_cliente' in produtos_cotados_df.columns:
            clientes_cotacoes = set(produtos_cotados_df['cod_cliente'].unique())
            if not vendas_df.empty and 'cod_cliente' in vendas_df.columns:
                clientes_vendas = set(vendas_df['cod_cliente'].unique())
                total_clientes = len(clientes_vendas.union(clientes_cotacoes))
            else:
                total_clientes = len(clientes_cotacoes)
        
        print(f"   👥 Total de clientes: {total_clientes}")
        print(f"   📦 Total de produtos: {total_produtos}")
        print(f"   📋 Total de cotações: {total_cotacoes}")
        
        # Se chegou aqui, a função deve retornar recomendações válidas
        return "RECOMENDACOES_GERADAS"
        
    except Exception as e:
        print(f"   ❌ Erro na simulação: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return "ERRO"

if __name__ == "__main__":
    print("🧪 TESTE ISOLADO DAS RECOMENDAÇÕES")
    print("=" * 50)
    
    result = simulate_recommendations_function()
    
    print("\n" + "=" * 50)
    print(f"🔍 RESULTADO: {result}")
    
    if result == "RECOMENDACOES_GERADAS":
        print("🎉 SUCESSO! O botão deve funcionar no dashboard")
        print("\n✅ A função generate_smart_recommendations() deve retornar:")
        print("   - Alert de sucesso com dados analisados")
        print("   - Cards com recomendações inteligentes")
        print("   - Insights baseados nos dados reais")
    elif result == "DADOS_INSUFICIENTES":
        print("❌ PROBLEMA: A função ainda retorna 'dados insuficientes'")
        print("   Verifique os logs acima para entender o motivo")
    else:
        print("❌ ERRO: Houve problemas na execução da função")
    
    print(f"\n📊 Para testar no dashboard:")
    print(f"1. O app está rodando em: http://127.0.0.1:8050")
    print(f"2. Vá para 'Sistema B2B Avançado'")
    print(f"3. Clique em 'Atualizar' nas Recomendações")