#!/usr/bin/env python3
"""Teste completo de upload de produtos cotados"""

import pandas as pd
import sys
import os

# Adiciona o caminho do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataLoaderFixed
from utils.db import save_dataset

def test_produtos_cotados_pipeline():
    """Testa o pipeline completo de produtos cotados"""
    
    # Dados de teste realistas
    produtos_data = {
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
    
    df_produtos = pd.DataFrame(produtos_data)
    
    print("=== DADOS DE TESTE CRIADOS ===")
    print(f"Produtos - Colunas: {list(df_produtos.columns)}")
    print(df_produtos)
    print()
    
    # Testa normalização
    loader = DataLoaderFixed()
    
    print("=== NORMALIZANDO DADOS ===")
    df_produtos_norm = loader.normalize_produtos_cotados_data(df_produtos)
    
    print(f"Produtos normalizados - Colunas: {list(df_produtos_norm.columns)}")
    print(df_produtos_norm)
    print()
    
    # Testa salvamento no banco
    try:
        print("=== TESTANDO SALVAMENTO NO BANCO ===")
        dataset_id = save_dataset(
            name="Teste Pipeline Produtos Cotados",
            uploaded_by=1,
            vendas_df=None,
            cotacoes_df=None,
            produtos_cotados_df=df_produtos_norm
        )
        
        print(f"✅ Salvamento concluído! Dataset ID: {dataset_id}")
        
        # Verifica se os dados foram salvos corretamente
        import sqlite3
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cotacao, cod_cliente, centro_fornecedor, descricao, 
                   preco_liquido_unitario, preco_liquido_total
            FROM produtos_cotados 
            WHERE dataset_id = ?
        """, (dataset_id,))
        
        rows = cursor.fetchall()
        
        print(f"\n=== VERIFICAÇÃO NO BANCO ===")
        print(f"Registros salvos: {len(rows)}")
        for i, row in enumerate(rows):
            cotacao, cod_cliente, centro_fornecedor, descricao, preco_unit, preco_total = row
            print(f"Registro {i+1}:")
            print(f"  Cotação: {cotacao}")
            print(f"  Código Cliente: {cod_cliente}")
            print(f"  Centro Fornecedor: {centro_fornecedor}")
            print(f"  Descrição: {descricao}")
            print(f"  Preço Líquido Unitário: {preco_unit}")
            print(f"  Preço Líquido Total: {preco_total}")
            print()
        
        # Verifica se há valores NULL
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN cotacao IS NULL THEN 1 ELSE 0 END) as cotacao_null,
                   SUM(CASE WHEN cod_cliente IS NULL THEN 1 ELSE 0 END) as cod_cliente_null,
                   SUM(CASE WHEN centro_fornecedor IS NULL THEN 1 ELSE 0 END) as centro_fornecedor_null,
                   SUM(CASE WHEN descricao IS NULL THEN 1 ELSE 0 END) as descricao_null,
                   SUM(CASE WHEN preco_liquido_unitario IS NULL THEN 1 ELSE 0 END) as preco_unit_null,
                   SUM(CASE WHEN preco_liquido_total IS NULL THEN 1 ELSE 0 END) as preco_total_null
            FROM produtos_cotados 
            WHERE dataset_id = ?
        """, (dataset_id,))
        
        null_stats = cursor.fetchone()
        total, cotacao_null, cod_cliente_null, centro_fornecedor_null, descricao_null, preco_unit_null, preco_total_null = null_stats
        
        print(f"=== ESTATÍSTICAS DE VALORES NULL ===")
        print(f"Total de registros: {total}")
        print(f"Cotação NULL: {cotacao_null}")
        print(f"Código Cliente NULL: {cod_cliente_null}")
        print(f"Centro Fornecedor NULL: {centro_fornecedor_null}")
        print(f"Descrição NULL: {descricao_null}")
        print(f"Preço Líquido Unitário NULL: {preco_unit_null}")
        print(f"Preço Líquido Total NULL: {preco_total_null}")
        
        if any([cotacao_null, cod_cliente_null, centro_fornecedor_null, descricao_null, preco_unit_null, preco_total_null]):
            print("❌ ATENÇÃO: Encontrados valores NULL!")
        else:
            print("✅ SUCESSO: Nenhum valor NULL encontrado!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro no salvamento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_produtos_cotados_pipeline()
