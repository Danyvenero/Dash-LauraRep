#!/usr/bin/env python3
"""
Teste simples do ETL
"""

import sqlite3
import pandas as pd
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append('.')

try:
    print("🔍 Testando conexão com banco...")
    from utils.db import get_db_connection
    
    conn = get_db_connection()
    print("✅ Conexão estabelecida")
    
    # Testar consulta simples
    df = pd.read_sql_query("SELECT COUNT(*) as total FROM vendas", conn)
    print(f"📊 Total de registros em vendas: {df.iloc[0]['total']}")
    
    df_cotacoes = pd.read_sql_query("SELECT COUNT(*) as total FROM cotacoes", conn)
    print(f"📊 Total de registros em cotações: {df_cotacoes.iloc[0]['total']}")
    
    # Verificar colunas da tabela vendas
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(vendas)")
    colunas_vendas = [row[1] for row in cursor.fetchall()]
    print(f"📋 Colunas vendas: {colunas_vendas}")
    
    conn.close()
    print("✅ Teste concluído com sucesso")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
