#!/usr/bin/env python3
"""
Implementação corrigida do callback B2B baseada na lógica dos filtros globais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import load_vendas_data

def test_global_filter_logic():
    """Testa a lógica dos filtros globais"""
    print("🔍 Testando lógica dos filtros globais...")
    
    # Carrega dados SEM LIMIT (como nos filtros globais)
    vendas_df = load_vendas_data()
    print(f"📊 Dados carregados: {len(vendas_df)} registros")
    
    if vendas_df.empty:
        print("❌ Nenhum dado encontrado")
        return
    
    # LÓGICA DOS FILTROS GLOBAIS - HIERARQUIA
    print("\n🏷️ HIERARQUIAS (lógica dos filtros globais):")
    hierarquia_options = []
    for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
        if col in vendas_df.columns:
            unique_vals = vendas_df[col].dropna().unique()
            print(f"   {col}: {len(unique_vals)} valores únicos")
            for val in unique_vals:
                if val not in [opt['value'] for opt in hierarquia_options]:
                    hierarquia_options.append({'label': str(val), 'value': str(val)})
    
    print(f"✅ Total hierarquias combinadas: {len(hierarquia_options)}")
    print("   Primeiras 10:", [opt['value'] for opt in hierarquia_options[:10]])
    
    # HIERARQUIA NÍVEL 1 ESPECÍFICO (para B2B)
    print("\n🎯 HIERARQUIA NÍVEL 1 ESPECÍFICO:")
    if 'hier_produto_1' in vendas_df.columns:
        hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
        hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique)]
        print(f"   Hierarquia 1: {len(hier1_options)} opções")
        print(f"   Valores: {[opt['value'] for opt in hier1_options]}")
    
    # UNIDADES DE NEGÓCIO
    print("\n🏢 UNIDADES DE NEGÓCIO:")
    if 'unidade_negocio' in vendas_df.columns:
        unidade_unique = vendas_df['unidade_negocio'].dropna().unique()
        unidade_options = [{"label": unidade, "value": unidade} for unidade in sorted(unidade_unique)]
        print(f"   Unidades: {len(unidade_options)} opções")
        print(f"   Valores: {[opt['value'] for opt in unidade_options]}")
    
    return hier1_options, unidade_options, hierarquia_options

def test_current_b2b_logic():
    """Testa a lógica atual do B2B (com limit=1000)"""
    print("\n" + "="*60)
    print("🔍 Testando lógica atual do B2B (limit=1000)...")
    
    # Carrega dados COM LIMIT (como no callback B2B atual)
    vendas_df = load_vendas_data(limit=1000)
    print(f"📊 Dados carregados: {len(vendas_df)} registros")
    
    # Hierarquia 1
    hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
    hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique)]
    print(f"🏷️ Hierarquia 1: {len(hier1_options)} opções")
    print(f"   Valores: {[opt['value'] for opt in hier1_options]}")
    
    # Unidades
    unidade_unique = vendas_df['unidade_negocio'].dropna().unique()
    unidade_options = [{"label": unidade, "value": unidade} for unidade in sorted(unidade_unique)]
    print(f"🏢 Unidades: {len(unidade_options)} opções")
    print(f"   Valores: {[opt['value'] for opt in unidade_options]}")
    
    return hier1_options, unidade_options

if __name__ == "__main__":
    print("🧪 COMPARAÇÃO: Filtros Globais vs B2B Atual")
    
    # Teste 1: Lógica dos filtros globais
    try:
        global_hier1, global_unidades, global_hierarquia_combinada = test_global_filter_logic()
    except Exception as e:
        print(f"❌ Erro nos filtros globais: {e}")
        global_hier1, global_unidades, global_hierarquia_combinada = [], [], []
    
    # Teste 2: Lógica atual do B2B
    try:
        b2b_hier1, b2b_unidades = test_current_b2b_logic()
    except Exception as e:
        print(f"❌ Erro no B2B atual: {e}")
        b2b_hier1, b2b_unidades = [], []
    
    # Comparação
    print(f"\n📋 RESUMO COMPARATIVO:")
    print(f"   Hierarquia 1 - Global: {len(global_hier1)} vs B2B: {len(b2b_hier1)}")
    print(f"   Unidades - Global: {len(global_unidades)} vs B2B: {len(b2b_unidades)}")
    print(f"   Hierarquia combinada (Global): {len(global_hierarquia_combinada)}")
    
    if len(global_unidades) > len(b2b_unidades):
        print(f"⚠️ PROBLEMA: B2B perdendo unidades por causa do LIMIT!")
        missing = set([opt['value'] for opt in global_unidades]) - set([opt['value'] for opt in b2b_unidades])
        print(f"   Unidades perdidas: {missing}")
    
    if len(global_hier1) > len(b2b_hier1):
        print(f"⚠️ PROBLEMA: B2B perdendo hierarquias por causa do LIMIT!")
        missing = set([opt['value'] for opt in global_hier1]) - set([opt['value'] for opt in b2b_hier1])
        print(f"   Hierarquias perdidas: {missing}")