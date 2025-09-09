#!/usr/bin/env python3
"""Teste com diferentes variações de nomes de colunas para produtos cotados"""

import pandas as pd
import sys
import os

# Adiciona o caminho do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataLoaderFixed

def test_column_variations():
    """Testa diferentes variações de nomes de colunas"""
    
    # Teste 1: Nomes padrão
    test1_data = {
        'Cotação': ['COT001'],
        'Código Cliente': ['CLI001'],
        'Cliente': ['WEG S.A.'],
        'Centro Fornecedor': ['CF001'],
        'Material': ['MAT001'],
        'Descrição': ['Motor Elétrico'],
        'Quantidade': [10],
        'Preço Líquido Unitário': [1500.00],
        'Preço Líquido Total': [15000.00]
    }
    
    # Teste 2: Variações alternativas
    test2_data = {
        'Número da Cotação': ['COT002'],
        'Referência do Cliente': ['CLI002'],
        'Cliente': ['Petrobras'],
        'Centro de Fornecedor': ['CF002'],
        'Código Material': ['MAT002'],
        'Descrição do Material': ['Bomba'],
        'Qtd': [5],
        'Valor Unitário': [2500.00],
        'Valor Total': [12500.00]
    }
    
    # Teste 3: Nomes abreviados
    test3_data = {
        'Cotacao': ['COT003'],
        'Ref Cliente': ['CLI003'],
        'Cliente': ['Vale'],
        'Centro_Fornecedor': ['CF003'],
        'Cod_Material': ['MAT003'],
        'Desc_Material': ['Transformador'],
        'Qty': [2],
        'Preco_Unit': [15000.00],
        'Total': [30000.00]
    }
    
    loader = DataLoaderFixed()
    
    tests = [
        ("Nomes Padrão", test1_data),
        ("Variações Alternativas", test2_data),
        ("Nomes Abreviados", test3_data)
    ]
    
    for test_name, test_data in tests:
        print(f"\n=== {test_name.upper()} ===")
        df_test = pd.DataFrame(test_data)
        
        print(f"Colunas originais: {list(df_test.columns)}")
        
        df_normalized = loader.normalize_produtos_cotados_data(df_test)
        
        print(f"Colunas após normalização: {list(df_normalized.columns)}")
        
        # Verifica se todas as colunas esperadas estão presentes
        expected_columns = ['cotacao', 'cod_cliente', 'cliente', 'centro_fornecedor', 
                          'material', 'descricao', 'quantidade', 'preco_liquido_unitario', 
                          'preco_liquido_total']
        
        missing_columns = [col for col in expected_columns if col not in df_normalized.columns]
        
        if missing_columns:
            print(f"❌ Colunas ausentes: {missing_columns}")
        else:
            print(f"✅ Todas as colunas esperadas estão presentes")
            
        # Mostra os valores
        for col in expected_columns:
            if col in df_normalized.columns:
                value = df_normalized[col].iloc[0] if len(df_normalized) > 0 else 'N/A'
                print(f"  {col}: {value}")

if __name__ == "__main__":
    test_column_variations()
