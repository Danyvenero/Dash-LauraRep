#!/usr/bin/env python3
"""
Teste das consultas SQL corrigidas
"""

import sqlite3
import pandas as pd

def test_sql_queries():
    try:
        print("🔍 Testando consultas SQL corrigidas...")
        
        conn = sqlite3.connect('instance/database.sqlite')
        
        # Teste consulta vendas
        print("\n1. Testando consulta vendas:")
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE data >= date('now', '-24 months')
        ORDER BY data DESC
        LIMIT 5
        """
        vendas_df = pd.read_sql_query(vendas_query, conn)
        print(f"✅ Vendas: {len(vendas_df)} registros encontrados")
        if not vendas_df.empty:
            print("   Primeiros 3 registros:")
            print(vendas_df.head(3))
        
        # Teste consulta cotações
        print("\n2. Testando consulta cotações:")
        cotacoes_query = """
        SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
        FROM produtos_cotados p
        LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
        WHERE c.data >= date('now', '-24 months')
        ORDER BY c.data DESC
        LIMIT 5
        """
        cotacoes_df = pd.read_sql_query(cotacoes_query, conn)
        print(f"✅ Cotações: {len(cotacoes_df)} registros encontrados")
        if not cotacoes_df.empty:
            print("   Primeiros 3 registros:")
            print(cotacoes_df.head(3))
        
        conn.close()
        print("\n✅ Todas as consultas SQL funcionaram corretamente!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_queries()