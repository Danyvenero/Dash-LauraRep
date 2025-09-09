#!/usr/bin/env python3
"""Script para verificar o estado atual da tabela produtos_cotados"""

import sqlite3
import pandas as pd

def check_produtos_cotados_table():
    """Verifica o estado atual da tabela produtos_cotados"""
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        # Verifica a estrutura da tabela
        print("=== ESTRUTURA DA TABELA PRODUTOS_COTADOS ===")
        cursor.execute('PRAGMA table_info(produtos_cotados)')
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print(f"\nTotal de colunas: {len(columns)}")
        
        # Verifica os dados
        print("\n=== DADOS NA TABELA ===")
        cursor.execute('SELECT COUNT(*) FROM produtos_cotados')
        total_records = cursor.fetchone()[0]
        print(f"Total de registros: {total_records}")
        
        if total_records > 0:
            # Mostra últimos registros
            cursor.execute("""
                SELECT id, dataset_id, cotacao, cod_cliente, centro_fornecedor, 
                       descricao, preco_liquido_unitario, preco_liquido_total
                FROM produtos_cotados 
                ORDER BY id DESC 
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            print(f"\nÚltimos {len(records)} registros:")
            for record in records:
                id_val, dataset_id, cotacao, cod_cliente, centro_fornecedor, descricao, preco_unit, preco_total = record
                print(f"  ID {id_val}:")
                print(f"    Dataset ID: {dataset_id}")
                print(f"    Cotação: {cotacao}")
                print(f"    Código Cliente: {cod_cliente}")
                print(f"    Centro Fornecedor: {centro_fornecedor}")
                print(f"    Descrição: {descricao}")
                print(f"    Preço Líquido Unitário: {preco_unit}")
                print(f"    Preço Líquido Total: {preco_total}")
                print()
            
            # Estatísticas de valores NULL
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN cotacao IS NULL THEN 1 ELSE 0 END) as cotacao_null,
                    SUM(CASE WHEN cod_cliente IS NULL THEN 1 ELSE 0 END) as cod_cliente_null,
                    SUM(CASE WHEN centro_fornecedor IS NULL THEN 1 ELSE 0 END) as centro_fornecedor_null,
                    SUM(CASE WHEN descricao IS NULL THEN 1 ELSE 0 END) as descricao_null,
                    SUM(CASE WHEN preco_liquido_unitario IS NULL THEN 1 ELSE 0 END) as preco_unit_null,
                    SUM(CASE WHEN preco_liquido_total IS NULL THEN 1 ELSE 0 END) as preco_total_null
                FROM produtos_cotados
            """)
            
            null_stats = cursor.fetchone()
            cotacao_null, cod_cliente_null, centro_fornecedor_null, descricao_null, preco_unit_null, preco_total_null = null_stats
            
            print("=== ESTATÍSTICAS DE VALORES NULL ===")
            print(f"Cotação NULL: {cotacao_null}/{total_records}")
            print(f"Código Cliente NULL: {cod_cliente_null}/{total_records}")
            print(f"Centro Fornecedor NULL: {centro_fornecedor_null}/{total_records}")
            print(f"Descrição NULL: {descricao_null}/{total_records}")
            print(f"Preço Líquido Unitário NULL: {preco_unit_null}/{total_records}")
            print(f"Preço Líquido Total NULL: {preco_total_null}/{total_records}")
            
        else:
            print("Nenhum registro encontrado na tabela.")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro ao verificar tabela: {e}")

if __name__ == "__main__":
    check_produtos_cotados_table()
