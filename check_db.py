#!/usr/bin/env python3

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path('instance/database.sqlite')
print(f"Database path: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}")

try:
    conn = sqlite3.connect(DB_PATH)
    
    print('\n📊 STATUS ATUAL DAS TABELAS:')
    print('=' * 50)
    
    # Verificar registros em cada tabela
    tables_to_check = ['vendas', 'cotacoes', 'produtos_cotados', 'datasets']
    
    for table in tables_to_check:
        try:
            result = pd.read_sql(f'SELECT COUNT(*) as count FROM {table}', conn)
            count = result.iloc[0]['count']
            print(f'📊 {table.upper()}: {count:,} registros')
        except Exception as e:
            print(f'❌ {table.upper()}: Tabela vazia ou inexistente')
    
    print('\n📚 ÚLTIMOS DATASETS:')
    print('-' * 30)
    
    # Verificar últimos datasets salvos
    try:
        datasets = pd.read_sql('''
            SELECT id, dataset_name, upload_date, 
                   vendas_count, cotacoes_count, produtos_cotados_count 
            FROM datasets 
            ORDER BY upload_date DESC 
            LIMIT 5
        ''', conn)
        
        for _, row in datasets.iterrows():
            print(f'ID {row["id"]}: {row["dataset_name"]} - {row["upload_date"]}')
            print(f'   📈 Vendas: {row["vendas_count"]} | 📋 Cotações: {row["cotacoes_count"]} | 🛍️ Produtos: {row["produtos_cotados_count"]}')
            print()
            
    except Exception as e:
        print(f'Erro ao verificar datasets: {e}')
    
    # Verificar estrutura das tabelas principais
    print('🏗️ ESTRUTURA DAS TABELAS:')
    print('-' * 30)
    
    for table in ['vendas', 'cotacoes', 'produtos_cotados']:
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            if columns:
                print(f"\n✅ {table.upper()}:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print(f"\n❌ {table.upper()}: Não existe")
        except Exception as e:
            print(f"\n❌ {table.upper()}: Erro - {str(e)}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
