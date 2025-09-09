#!/usr/bin/env python3
"""Teste das correções para o problema de None sendo convertido para string"""

import pandas as pd
import numpy as np
import sys
import os

# Adiciona o caminho do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataLoaderFixed

def test_none_handling():
    """Testa o tratamento de valores None/NaN"""
    
    # Simula dados problemáticos como vieram do arquivo real
    problematic_data = {
        'Cotação': ['225671850', '225671850', '230469286'],
        'Código Cliente': [None, '', 'CLI003'],  # None real, string vazia, valor válido
        'Cliente': ['WEG S.A.', None, 'Cliente Teste'],  # None no meio
        'Centro Fornecedor': ['1305', '', '1100'],  # String vazia
        'Material': ['MAT001', None, 'MAT003'],  # None
        'Descrição': ['SOFT-STARTER SSW070171T5SZ', '', 'MOTOR ELETRICO TRIFASICO'],  # String vazia
        'Quantidade': [2, 4, 1],
        'Preço Líquido Unitário': [2836.68, 1743.52, 187770.91],
        'Preço Líquido Total': [5673.36, 6974.08, 187770.91]
    }
    
    df_problematic = pd.DataFrame(problematic_data)
    
    print("=== DADOS PROBLEMÁTICOS (ANTES) ===")
    print(f"Colunas: {list(df_problematic.columns)}")
    print(df_problematic)
    print(f"Tipos de dados:")
    for col in df_problematic.columns:
        print(f"  {col}: {df_problematic[col].dtype}")
        null_count = df_problematic[col].isna().sum()
        none_count = (df_problematic[col] == 'None').sum() if df_problematic[col].dtype == 'object' else 0
        empty_count = (df_problematic[col] == '').sum() if df_problematic[col].dtype == 'object' else 0
        print(f"    NULL: {null_count}, 'None': {none_count}, Empty: {empty_count}")
    print()
    
    # Testa com o DataLoaderFixed corrigido
    loader = DataLoaderFixed()
    
    print("=== PROCESSANDO COM CORREÇÕES ===")
    df_processed = loader.normalize_produtos_cotados_data(df_problematic)
    
    print(f"Resultado - Colunas: {list(df_processed.columns)}")
    print(f"Resultado - Shape: {df_processed.shape}")
    print(df_processed)
    print()
    
    print("=== VERIFICAÇÃO FINAL DE TIPOS E VALORES ===")
    for col in df_processed.columns:
        values = df_processed[col].tolist()
        null_count = df_processed[col].isna().sum()
        none_count = (df_processed[col] == 'None').sum() if df_processed[col].dtype == 'object' else 0
        empty_count = (df_processed[col] == '').sum() if df_processed[col].dtype == 'object' else 0
        
        print(f"{col}: {df_processed[col].dtype}")
        print(f"  Valores: {values}")
        print(f"  NULL: {null_count}, 'None': {none_count}, Empty: {empty_count}")
        
        if none_count > 0:
            print(f"  ❌ PROBLEMA: Ainda há strings 'None' em {col}!")
        elif null_count == 0 and col in ['cod_cliente', 'centro_fornecedor', 'descricao']:
            print(f"  ✅ OK: {col} não tem valores None (pode ser normal se dados são válidos)")
        else:
            print(f"  ✅ OK: {col} tratado corretamente")
    
    print()
    
    # Simula o que aconteceria no banco
    print("=== SIMULAÇÃO DO SALVAMENTO NO BANCO ===")
    df_copy = df_processed.copy()
    df_copy['dataset_id'] = 999
    
    valid_produtos_columns = [
        'dataset_id', 'cotacao', 'cod_cliente', 'cliente', 
        'centro_fornecedor', 'material', 'descricao', 'quantidade',
        'preco_liquido_unitario', 'preco_liquido_total'
    ]
    columns_to_keep = [col for col in valid_produtos_columns if col in df_copy.columns]
    df_final = df_copy[columns_to_keep]
    
    print("Dados finais para salvamento:")
    print(df_final)
    
    # Verifica se ainda há problemas
    problema_encontrado = False
    for col in ['cotacao', 'cod_cliente', 'centro_fornecedor', 'descricao']:
        if col in df_final.columns:
            none_strings = (df_final[col] == 'None').sum()
            if none_strings > 0:
                print(f"❌ PROBLEMA: {col} ainda tem {none_strings} valores 'None'!")
                problema_encontrado = True
    
    if not problema_encontrado:
        print("✅ SUCESSO: Nenhuma string 'None' encontrada nos dados finais!")

if __name__ == "__main__":
    test_none_handling()
