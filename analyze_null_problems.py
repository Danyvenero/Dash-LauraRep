#!/usr/bin/env python3
"""Script para analisar os problemas nas tabelas cotacoes e produtos_cotados"""

import sqlite3

def analyze_tables():
    """Analisa os problemas nas tabelas"""
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        print("=== ANÁLISE DA TABELA COTACOES ===")
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(*) FROM cotacoes")
        total_cotacoes = cursor.fetchone()[0]
        print(f"Total de registros: {total_cotacoes}")
        
        # Estatísticas de NULL
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN cod_cliente IS NULL THEN 1 ELSE 0 END) as cod_cliente_null,
                SUM(CASE WHEN cliente IS NULL THEN 1 ELSE 0 END) as cliente_null,
                SUM(CASE WHEN data IS NULL THEN 1 ELSE 0 END) as data_null,
                SUM(CASE WHEN numero_cotacao IS NULL THEN 1 ELSE 0 END) as numero_cotacao_null
            FROM cotacoes
        """)
        
        stats = cursor.fetchone()
        cod_cliente_null, cliente_null, data_null, numero_cotacao_null = stats
        
        print(f"Valores NULL em cotacoes:")
        print(f"  cod_cliente: {cod_cliente_null}/{total_cotacoes}")
        print(f"  cliente: {cliente_null}/{total_cotacoes}")
        print(f"  data: {data_null}/{total_cotacoes}")
        print(f"  numero_cotacao: {numero_cotacao_null}/{total_cotacoes}")
        
        # Mostra alguns exemplos
        print(f"\nExemplos de registros:")
        cursor.execute("""
            SELECT numero_cotacao, cod_cliente, cliente, data
            FROM cotacoes 
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        for i, (num_cot, cod_cli, cliente, data) in enumerate(examples, 1):
            print(f"  {i}: cotacao='{num_cot}', cod_cliente='{cod_cli}', cliente='{cliente}', data='{data}'")
        
        print("\n=== ANÁLISE DA TABELA PRODUTOS_COTADOS ===")
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(*) FROM produtos_cotados")
        total_produtos = cursor.fetchone()[0]
        print(f"Total de registros: {total_produtos}")
        
        # Estatísticas de NULL
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN cod_cliente IS NULL THEN 1 ELSE 0 END) as cod_cliente_null,
                SUM(CASE WHEN cliente IS NULL THEN 1 ELSE 0 END) as cliente_null,
                SUM(CASE WHEN cotacao IS NULL THEN 1 ELSE 0 END) as cotacao_null
            FROM produtos_cotados
        """)
        
        stats = cursor.fetchone()
        cod_cliente_null, cliente_null, cotacao_null = stats
        
        print(f"Valores NULL em produtos_cotados:")
        print(f"  cod_cliente: {cod_cliente_null}/{total_produtos}")
        print(f"  cliente: {cliente_null}/{total_produtos}")
        print(f"  cotacao: {cotacao_null}/{total_produtos}")
        
        # Mostra alguns exemplos
        print(f"\nExemplos de registros:")
        cursor.execute("""
            SELECT cotacao, cod_cliente, cliente, centro_fornecedor
            FROM produtos_cotados 
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        for i, (cotacao, cod_cli, cliente, centro_forn) in enumerate(examples, 1):
            print(f"  {i}: cotacao='{cotacao}', cod_cliente='{cod_cli}', cliente='{cliente}', centro_fornecedor='{centro_forn}'")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro na análise: {e}")

if __name__ == "__main__":
    analyze_tables()
