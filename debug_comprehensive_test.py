#!/usr/bin/env python3
"""
Script para testar callbacks e carregamento de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
from utils.kpis import KPICalculator
from utils.visualizations import VisualizationGenerator
import pandas as pd

def test_comprehensive_data_flow():
    """Testa todo o fluxo de dados da aplicação"""
    print("🔍 ANÁLISE COMPLETA DO FLUXO DE DADOS")
    print("="*60)
    
    # 1. Verifica carregamento básico
    print("📊 1. TESTE DE CARREGAMENTO BÁSICO:")
    vendas_df = load_vendas_data()
    cotacoes_df = load_cotacoes_data()
    produtos_df = load_produtos_cotados_data()
    
    print(f"   ✅ Vendas: {len(vendas_df)} registros")
    print(f"   ✅ Cotações: {len(cotacoes_df)} registros")
    print(f"   ✅ Produtos: {len(produtos_df)} registros")
    print()
    
    # 2. Verifica estrutura dos dados de vendas
    print("📋 2. ESTRUTURA DOS DADOS DE VENDAS:")
    if not vendas_df.empty:
        print(f"   Colunas: {list(vendas_df.columns)}")
        print(f"   Tipos de dados:")
        for col in vendas_df.columns:
            print(f"     {col}: {vendas_df[col].dtype}")
        
        # Verifica se há dados nas colunas críticas
        print(f"   Dados críticos:")
        print(f"     cod_cliente únicos: {vendas_df['cod_cliente'].nunique() if 'cod_cliente' in vendas_df.columns else 'N/A'}")
        print(f"     clientes únicos: {vendas_df['cliente'].nunique() if 'cliente' in vendas_df.columns else 'N/A'}")
        
        # Verifica dados de hierarquia
        for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
            if col in vendas_df.columns:
                print(f"     {col} únicos: {vendas_df[col].nunique()}")
        
        # Verifica canal
        if 'canal_distribuicao' in vendas_df.columns:
            print(f"     canais únicos: {vendas_df['canal_distribuicao'].nunique()}")
            print(f"     canais: {list(vendas_df['canal_distribuicao'].unique()[:5])}")
            
    print()
    
    # 3. Testa KPI Calculator
    print("🧮 3. TESTE DO KPI CALCULATOR:")
    try:
        kpi_calc = KPICalculator()
        
        # Teste com filtros vazios
        filters = {
            'ano': None,
            'mes': None,
            'cliente': None,
            'hierarquia_produto': None,
            'canal': None
        }
        
        print("   Testando cálculo de KPIs gerais...")
        kpis_gerais = kpi_calc.calculate_general_kpis(vendas_df, cotacoes_df, produtos_df, filters)
        print(f"   ✅ KPIs calculados: {list(kpis_gerais.keys())}")
        
        for kpi_name, kpi_data in kpis_gerais.items():
            print(f"     {kpi_name}: {kpi_data}")
        
        print("   Testando KPIs por unidade de negócio...")
        kpis_un = kpi_calc.calculate_business_unit_kpis(vendas_df, filters)
        print(f"   ✅ Unidades de negócio: {list(kpis_un.keys())}")
        
    except Exception as e:
        print(f"   ❌ Erro no KPI Calculator: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 4. Testa Visualization Generator
    print("📈 4. TESTE DO VISUALIZATION GENERATOR:")
    try:
        viz_gen = VisualizationGenerator()
        
        print("   Testando geração de opções de filtro...")
        
        # Testa opções de clientes
        if not vendas_df.empty:
            cliente_options = []
            if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
                clientes_unique = vendas_df[['cod_cliente', 'cliente']].drop_duplicates()
                cliente_options = [
                    {'label': f"{row['cod_cliente']} -- {row['cliente']}", 'value': row['cod_cliente']}
                    for _, row in clientes_unique.head(5).iterrows()  # Apenas 5 primeiros para teste
                    if not pd.isna(row['cod_cliente']) and not pd.isna(row['cliente'])
                ]
            print(f"   ✅ Clientes (amostra): {len(cliente_options)} opções")
            for opt in cliente_options[:3]:
                print(f"     {opt}")
        
        # Testa hierarquia
        hierarquia_options = []
        for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
            if col in vendas_df.columns:
                unique_vals = vendas_df[col].dropna().unique()[:5]  # Apenas 5 primeiros
                for val in unique_vals:
                    if val not in [opt['value'] for opt in hierarquia_options]:
                        hierarquia_options.append({'label': str(val), 'value': str(val)})
        print(f"   ✅ Hierarquia (amostra): {len(hierarquia_options)} opções")
        
        # Testa canais
        canal_options = []
        if 'canal_distribuicao' in vendas_df.columns:
            unique_canais = vendas_df['canal_distribuicao'].dropna().unique()
            canal_options = [{'label': str(canal), 'value': str(canal)} for canal in unique_canais]
        print(f"   ✅ Canais: {len(canal_options)} opções")
        for opt in canal_options:
            print(f"     {opt}")
            
    except Exception as e:
        print(f"   ❌ Erro no Visualization Generator: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 5. Verifica dados por ano/mês
    print("📅 5. ANÁLISE TEMPORAL DOS DADOS:")
    if not vendas_df.empty and 'data' in vendas_df.columns:
        vendas_df['ano'] = pd.to_datetime(vendas_df['data']).dt.year
        vendas_df['mes'] = pd.to_datetime(vendas_df['data']).dt.month
        
        print(f"   Anos disponíveis: {sorted(vendas_df['ano'].unique())}")
        print(f"   Meses disponíveis: {sorted(vendas_df['mes'].unique())}")
        
        # Verifica distribuição por ano
        ano_dist = vendas_df['ano'].value_counts().sort_index()
        print(f"   Distribuição por ano:")
        for ano, count in ano_dist.items():
            print(f"     {ano}: {count:,} registros")
    
    print("\n" + "="*60)
    print("🎯 CONCLUSÃO DA ANÁLISE:")
    print("   - Dados carregados com sucesso")
    print("   - Estrutura verificada")
    print("   - KPIs testados")
    print("   - Filtros analisados")

if __name__ == "__main__":
    test_comprehensive_data_flow()
