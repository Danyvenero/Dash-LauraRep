#!/usr/bin/env python3
"""Debug específico do processo de upload de produtos cotados"""

import pandas as pd
import sys
import os

# Adiciona o caminho do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataLoaderFixed
from utils.db import save_dataset

def debug_upload_process():
    """Simula exatamente o processo de upload"""
    
    # Simula dados que poderiam vir de um arquivo Excel real
    # com possíveis problemas de formatação
    raw_data = {
        'Cotação': ['225671850', '225671850', '230469286'],
        'Código Cliente': ['CLI001', None, ''],  # Teste com valores vazios
        'Cliente': ['WEG S.A.', 'WEG S.A.', 'Cliente Teste'],
        'Centro Fornecedor': ['1305', '1305', '1100'],
        'Material': ['MAT001', 'MAT002', 'MAT003'],
        'Descrição': ['SOFT-STARTER SSW070171T5SZ', 'SOFT-STARTER SSW070085T5SZ', 'MOTOR ELETRICO TRIFASICO'],
        'Quantidade': [2, 4, 1],
        'Preço Líquido Unitário': [2836.68, 1743.52, 187770.91],
        'Preço Líquido Total': [5673.36, 6974.08, 187770.91]
    }
    
    df_raw = pd.DataFrame(raw_data)
    
    print("=== DADOS RAW (ANTES DO PROCESSAMENTO) ===")
    print(f"Colunas: {list(df_raw.columns)}")
    print(df_raw)
    print()
    
    # Simula o processo exato do callback
    print("=== SIMULANDO PROCESSO DO CALLBACK ===")
    data_loader = DataLoaderFixed()
    
    print("Chamando normalize_produtos_cotados_data...")
    df_processed = data_loader.normalize_produtos_cotados_data(df_raw)
    
    print(f"Resultado - Colunas: {list(df_processed.columns)}")
    print(f"Resultado - Shape: {df_processed.shape}")
    print(df_processed)
    print()
    
    # Verifica se há valores None/NaN
    print("=== VERIFICAÇÃO DE VALORES NULOS ===")
    for col in df_processed.columns:
        null_count = df_processed[col].isna().sum()
        none_count = (df_processed[col] == 'None').sum() if df_processed[col].dtype == 'object' else 0
        empty_count = (df_processed[col] == '').sum() if df_processed[col].dtype == 'object' else 0
        
        print(f"{col}: {null_count} NaN, {none_count} 'None', {empty_count} vazios")
        
        if null_count > 0 or none_count > 0 or empty_count > 0:
            print(f"  Valores problemáticos em {col}: {df_processed[col].tolist()}")
    
    print()
    
    # Simula exatamente o que acontece no save_dataset
    print("=== SIMULANDO SAVE_DATASET ===")
    
    try:
        # Preparação dos dados como no db.py
        produtos_df_copy = df_processed.copy()
        produtos_df_copy['dataset_id'] = 999  # ID fictício
        
        print(f"Dados antes da filtragem de colunas:")
        print(f"Colunas: {list(produtos_df_copy.columns)}")
        
        # Filtragem exata como no db.py
        valid_produtos_columns = [
            'dataset_id', 'cotacao', 'cod_cliente', 'cliente', 
            'centro_fornecedor', 'material', 'descricao', 'quantidade',
            'preco_liquido_unitario', 'preco_liquido_total'
        ]
        columns_to_keep = [col for col in valid_produtos_columns if col in produtos_df_copy.columns]
        produtos_df_copy = produtos_df_copy[columns_to_keep]
        
        print(f"Colunas após filtragem: {list(produtos_df_copy.columns)}")
        print(f"Dados finais que seriam salvos:")
        print(produtos_df_copy)
        print()
        
        # Verifica valores nulos nos dados finais
        print("=== VERIFICAÇÃO FINAL DE NULOS ===")
        for col in produtos_df_copy.columns:
            null_count = produtos_df_copy[col].isna().sum()
            print(f"{col}: {null_count} NaN de {len(produtos_df_copy)} registros")
            
            if null_count > 0:
                print(f"  Índices com NULL em {col}: {produtos_df_copy[produtos_df_copy[col].isna()].index.tolist()}")
        
    except Exception as e:
        print(f"❌ Erro na simulação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_upload_process()
