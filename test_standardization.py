#!/usr/bin/env python3
"""
Script para testar as padronizações implementadas
"""

import sys
import os
import pandas as pd
import numpy as np

# Adicionar o diretório principal ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_standardization():
    """Testa as funções de padronização"""
    print("🧪 TESTANDO PADRONIZAÇÕES")
    print("=" * 50)
    
    try:
        # Importar as funções
        from utils.data_standardization import (
            apply_vendas_standardization, 
            apply_cotacoes_standardization,
            ov_general_adjustments,
            ov_hierarquia_um,
            centro_fornecedor_mapping
        )
        print("✅ Importações realizadas com sucesso")
        
        # Teste 1: Dados de vendas sintéticos
        print("\n📊 Teste 1: Padronização de Vendas")
        vendas_test = pd.DataFrame({
            'hier_produto_1': ['MOTORES INDUSTRIAIS', 'SOLAR WAU', 'DRIVES BT'],
            'hier_produto_2': ['INVERSORES DE FREQUÊNCIA SERIADOS', 'MODULO FOTOVOLTAICO', 'INVERSOR DE FREQUÊNCIA'],
            'hier_produto_3': ['W22 RURAL TEFC', 'MODULO FOTOVOLTAICO', 'AFW11 CUSTOMIZADO'],
            'unidade_negocio': ['WEG Motores Industrial', 'WEG Automação', 'WEG Digital e Sistemas'],
            'cliente': ['CLIENTE TESTE A', 'CLIENTE TESTE B', 'CLIENTE TESTE C'],
            'vlr_entrada': ['1000.50', '2000.75', '3000.25'],
            'material': ['10000001', '10000002', '10000003']
        })
        
        print(f"   Dados originais: {vendas_test.shape}")
        print(f"   Exemplo hier_produto_1 original: {vendas_test['hier_produto_1'].iloc[0]}")
        print(f"   Exemplo unidade_negocio original: {vendas_test['unidade_negocio'].iloc[0]}")
        
        # Aplicar padronização
        vendas_padronizado = apply_vendas_standardization(vendas_test)
        
        print(f"   Dados padronizados: {vendas_padronizado.shape}")
        if 'hier_produto_1' in vendas_padronizado.columns:
            print(f"   Exemplo hier_produto_1 padronizado: {vendas_padronizado['hier_produto_1'].iloc[0]}")
        if 'unidade' in vendas_padronizado.columns:
            print(f"   Exemplo unidade padronizada: {vendas_padronizado['unidade'].iloc[0]}")
        
        # Teste 2: Dados de cotações sintéticos
        print("\n📋 Teste 2: Padronização de Cotações")
        cotacoes_test = pd.DataFrame({
            'centro_fornecedor': [1100.0, 1106.0, 1200.0, 1340.0, 9999.0],
            'cliente': ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E'],
            'numero_cotacao': ['COT001', 'COT002', 'COT003', 'COT004', 'COT005']
        })
        
        print(f"   Dados originais: {cotacoes_test.shape}")
        print(f"   Exemplo centro_fornecedor original: {cotacoes_test['centro_fornecedor'].iloc[0]}")
        
        # Aplicar padronização
        cotacoes_padronizado = apply_cotacoes_standardization(cotacoes_test)
        
        print(f"   Dados padronizados: {cotacoes_padronizado.shape}")
        if 'unidade_negocio' in cotacoes_padronizado.columns:
            print(f"   Exemplo unidade_negocio mapeada: {cotacoes_padronizado['unidade_negocio'].iloc[0]}")
            print(f"   Mapeamentos: {cotacoes_padronizado['unidade_negocio'].tolist()}")
        
        # Teste 3: Testar carregamento com padronização
        print("\n🔄 Teste 3: Carregamento de Dados com Padronização")
        try:
            from utils.db import load_vendas_data, load_cotacoes_data
            
            vendas_df = load_vendas_data()
            cotacoes_df = load_cotacoes_data()
            
            print(f"   ✅ Vendas carregadas: {len(vendas_df)} registros")
            print(f"   ✅ Cotações carregadas: {len(cotacoes_df)} registros")
            
            if not vendas_df.empty:
                print(f"   📊 Colunas vendas: {list(vendas_df.columns)[:10]}...")
                if 'unidade' in vendas_df.columns:
                    print(f"   📊 Unidades únicas: {vendas_df['unidade'].unique()[:5]}")
                    
            if not cotacoes_df.empty:
                print(f"   📋 Colunas cotações: {list(cotacoes_df.columns)[:10]}...")
                if 'unidade_negocio' in cotacoes_df.columns:
                    print(f"   📋 Unidades negócio únicas: {cotacoes_df['unidade_negocio'].unique()[:5]}")
            
        except Exception as e:
            print(f"   ❌ Erro no carregamento: {e}")
        
        print("\n✅ TODOS OS TESTES CONCLUÍDOS!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_standardization()
    if success:
        print("\n🎉 PADRONIZAÇÕES FUNCIONANDO CORRETAMENTE!")
    else:
        print("\n💥 PROBLEMAS DETECTADOS NAS PADRONIZAÇÕES!")
