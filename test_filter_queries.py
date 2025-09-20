#!/usr/bin/env python3
"""
Teste rápido para verificar filtros de hierarquia e unidade de negócio
"""

import pandas as pd
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection

def test_filter_queries():
    """Testa as queries que populam os filtros"""
    print("🧪 TESTE: Queries dos Filtros")
    print("=" * 50)
    
    try:
        conn = get_connection()
        
        # Testa query de hierarquia 1
        print("🏗️ Testando hierarquia 1...")
        query_hier1 = """
            SELECT DISTINCT hier_produto_1 
            FROM vendas 
            WHERE hier_produto_1 IS NOT NULL
            ORDER BY hier_produto_1
            LIMIT 10
        """
        df_hier1 = pd.read_sql_query(query_hier1, conn)
        print(f"   Encontrados: {len(df_hier1)} valores")
        if not df_hier1.empty:
            print("   Primeiros 5 valores:")
            for i, val in enumerate(df_hier1['hier_produto_1'].head(5)):
                print(f"   {i+1}. {val}")
        else:
            print("   ❌ Nenhum valor encontrado!")
        
        # Testa query de unidade de negócio
        print("\n🏢 Testando unidade de negócio...")
        query_unidade = """
            SELECT DISTINCT unidade_negocio 
            FROM vendas 
            WHERE unidade_negocio IS NOT NULL
            ORDER BY unidade_negocio
        """
        df_unidade = pd.read_sql_query(query_unidade, conn)
        print(f"   Encontrados: {len(df_unidade)} valores")
        if not df_unidade.empty:
            print("   Valores encontrados:")
            for i, val in enumerate(df_unidade['unidade_negocio']):
                print(f"   {i+1}. {val}")
        else:
            print("   ❌ Nenhum valor encontrado!")
        
        # Verifica total de registros na tabela vendas
        print(f"\n📊 Verificando total de registros...")
        total_query = "SELECT COUNT(*) as total FROM vendas"
        total_df = pd.read_sql_query(total_query, conn)
        print(f"   Total de registros na tabela vendas: {total_df['total'].iloc[0]}")
        
        # Verifica se há dados com colunas não nulas
        stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(hier_produto_1) as hier1_count,
                COUNT(unidade_negocio) as unidade_count
            FROM vendas
        """
        stats_df = pd.read_sql_query(stats_query, conn)
        print(f"   Registros com hier_produto_1: {stats_df['hier1_count'].iloc[0]}")
        print(f"   Registros com unidade_negocio: {stats_df['unidade_count'].iloc[0]}")
        
        conn.close()
        
        return len(df_hier1) > 0 and len(df_unidade) > 0
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    test_filter_queries()