#!/usr/bin/env python3
"""Script para debugar o problema de upload de produtos cotados"""

import pandas as pd
import sys
import os

# Adiciona o caminho do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataLoaderFixed

def debug_produtos_cotados():
    """Debug do problema de produtos cotados com valores NULL"""
    
    # Dados de teste que simulam o arquivo real
    test_data = {
        'Cotação': ['COT001', 'COT001', 'COT002'],
        'Código Cliente': ['CLI001', 'CLI001', 'CLI002'],
        'Cliente': ['WEG S.A.', 'WEG S.A.', 'Petrobras'],
        'Centro Fornecedor': ['CF001', 'CF002', 'CF003'],
        'Material': ['MAT001', 'MAT002', 'MAT003'],
        'Descrição': ['Motor Elétrico 5HP', 'Bomba Centrífuga', 'Transformador 500KVA'],
        'Quantidade': [10, 5, 2],
        'Preço Líquido Unitário': [1500.00, 2500.00, 15000.00],
        'Preço Líquido Total': [15000.00, 12500.00, 30000.00]
    }
    
    df_test = pd.DataFrame(test_data)
    
    print("=== DADOS DE TESTE ORIGINAIS ===")
    print(f"Colunas: {list(df_test.columns)}")
    print(df_test)
    print()
    
    # Testa o DataLoaderFixed
    loader = DataLoaderFixed()
    
    print("=== TESTANDO NORMALIZAÇÃO DE PRODUTOS COTADOS ===")
    df_normalized = loader.normalize_produtos_cotados_data(df_test)
    
    print(f"Colunas após normalização: {list(df_normalized.columns)}")
    print(df_normalized)
    print()
    
    # Verifica cada campo problemático
    problematic_fields = ['cotacao', 'cod_cliente', 'centro_fornecedor', 
                         'descricao', 'preco_liquido_unitario', 'preco_liquido_total']
    
    print("=== VERIFICAÇÃO DE CAMPOS PROBLEMÁTICOS ===")
    for field in problematic_fields:
        if field in df_normalized.columns:
            values = df_normalized[field].tolist()
            null_count = df_normalized[field].isna().sum()
            print(f"✅ {field}: {values} (NULL count: {null_count})")
        else:
            print(f"❌ {field}: CAMPO AUSENTE!")
    
    # Verificar se o schema está alinhado
    expected_schema_fields = [
        'dataset_id', 'cotacao', 'cod_cliente', 'cliente', 
        'centro_fornecedor', 'material', 'descricao', 'quantidade',
        'preco_liquido_unitario', 'preco_liquido_total'
    ]
    
    print("\n=== VERIFICAÇÃO DE SCHEMA ===")
    for field in expected_schema_fields:
        if field in df_normalized.columns:
            print(f"✅ {field}: presente")
        elif field == 'dataset_id':
            print(f"ℹ️  {field}: será adicionado pelo sistema")
        else:
            print(f"❌ {field}: AUSENTE!")

if __name__ == "__main__":
    debug_produtos_cotados()
