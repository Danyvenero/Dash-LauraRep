#!/usr/bin/env python3
"""
Teste para verificar quantos clientes únicos existem
"""

import sqlite3
import pandas as pd

def test_clientes():
    try:
        # Conecta ao banco
        conn = sqlite3.connect('laura_rep.db')
        
        # Query direta
        query = """
        SELECT DISTINCT cod_cliente, cliente 
        FROM entrada 
        WHERE cod_cliente IS NOT NULL 
        AND cod_cliente != ''
        AND cod_cliente != 'nan'
        ORDER BY cod_cliente
        """
        
        df = pd.read_sql(query, conn)
        print(f"✅ Total de clientes únicos: {len(df)}")
        
        if len(df) > 0:
            print("\n📋 Primeiros 10 clientes:")
            print(df.head(10))
            
            print(f"\n📋 Últimos 5 clientes:")
            print(df.tail(5))
        
        conn.close()
        return len(df)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 0

if __name__ == "__main__":
    test_clientes()