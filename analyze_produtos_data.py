#!/usr/bin/env python3
"""Análise detalhada dos dados na tabela produtos_cotados"""

import sqlite3
import pandas as pd

def analyze_produtos_cotados():
    """Analisa os dados na tabela por dataset_id"""
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        
        # Verifica quantos datasets existem
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT dataset_id, COUNT(*) as registros
            FROM produtos_cotados 
            GROUP BY dataset_id 
            ORDER BY dataset_id DESC
        """)
        
        datasets = cursor.fetchall()
        
        print("=== ANÁLISE POR DATASET ===")
        for dataset_id, count in datasets:
            print(f"\nDataset {dataset_id}: {count} registros")
            
            # Verifica estatísticas de NULL para este dataset
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN cotacao IS NULL OR cotacao = '' OR cotacao = 'None' THEN 1 ELSE 0 END) as cotacao_null,
                    SUM(CASE WHEN cod_cliente IS NULL OR cod_cliente = '' OR cod_cliente = 'None' THEN 1 ELSE 0 END) as cod_cliente_null,
                    SUM(CASE WHEN centro_fornecedor IS NULL OR centro_fornecedor = '' OR centro_fornecedor = 'None' THEN 1 ELSE 0 END) as centro_fornecedor_null,
                    SUM(CASE WHEN descricao IS NULL OR descricao = '' OR descricao = 'None' THEN 1 ELSE 0 END) as descricao_null,
                    SUM(CASE WHEN preco_liquido_unitario IS NULL THEN 1 ELSE 0 END) as preco_unit_null,
                    SUM(CASE WHEN preco_liquido_total IS NULL THEN 1 ELSE 0 END) as preco_total_null
                FROM produtos_cotados 
                WHERE dataset_id = ?
            """, (dataset_id,))
            
            stats = cursor.fetchone()
            cotacao_null, cod_cliente_null, centro_fornecedor_null, descricao_null, preco_unit_null, preco_total_null = stats
            
            print(f"  NULLs: cotacao={cotacao_null}, cod_cliente={cod_cliente_null}, centro_fornecedor={centro_fornecedor_null}")
            print(f"         descricao={descricao_null}, preco_unit={preco_unit_null}, preco_total={preco_total_null}")
            
            # Mostra algumas amostras
            cursor.execute("""
                SELECT cotacao, cod_cliente, centro_fornecedor, descricao, preco_liquido_unitario, preco_liquido_total
                FROM produtos_cotados 
                WHERE dataset_id = ?
                LIMIT 3
            """, (dataset_id,))
            
            samples = cursor.fetchall()
            print(f"  Amostras:")
            for i, sample in enumerate(samples):
                cotacao, cod_cliente, centro_fornecedor, descricao, preco_unit, preco_total = sample
                print(f"    {i+1}: cotacao='{cotacao}', cod_cliente='{cod_cliente}', centro_fornecedor='{centro_fornecedor}'")
                print(f"       descricao='{descricao[:50] if descricao else None}...', precos={preco_unit}/{preco_total}")
        
        # Verifica quando foram criados os datasets
        print("\n=== INFORMAÇÕES DOS DATASETS ===")
        cursor.execute("""
            SELECT id, name, uploaded_at, 
                   (SELECT COUNT(*) FROM produtos_cotados WHERE dataset_id = datasets.id) as produtos_count
            FROM datasets 
            ORDER BY id DESC
            LIMIT 10
        """)
        
        dataset_info = cursor.fetchall()
        for dataset_id, name, uploaded_at, produtos_count in dataset_info:
            print(f"Dataset {dataset_id}: '{name}' - {uploaded_at} - {produtos_count} produtos")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro na análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_produtos_cotados()
