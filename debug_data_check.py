#!/usr/bin/env python3
"""
Script para verificar se há dados no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import get_connection
import pandas as pd

def check_database_data():
    """Verifica se há dados nas tabelas"""
    try:
        conn = get_connection()
        
        # Verifica tabelas principais
        tables = ['vendas', 'cotacoes', 'produtos_cotados']
        
        print("🔍 VERIFICANDO DADOS NO BANCO...")
        print("="*50)
        
        for table in tables:
            try:
                query = f"SELECT COUNT(*) as total FROM {table}"
                result = pd.read_sql_query(query, conn)
                total = result['total'].iloc[0]
                
                print(f"📊 Tabela {table}: {total:,} registros")
                
                if total > 0:
                    # Mostra algumas colunas
                    sample_query = f"SELECT * FROM {table} LIMIT 3"
                    sample_data = pd.read_sql_query(sample_query, conn)
                    print(f"   Colunas: {list(sample_data.columns)}")
                    print(f"   Exemplo de dados:")
                    for idx, row in sample_data.iterrows():
                        print(f"     Registro {idx+1}: {dict(row)}")
                    print()
                    
            except Exception as e:
                print(f"❌ Erro ao verificar tabela {table}: {e}")
        
        # Verifica se há dados recentes
        print("\n🔍 VERIFICANDO DADOS RECENTES...")
        print("="*50)
        
        for table in tables:
            try:
                recent_query = f"""
                SELECT dataset_id, COUNT(*) as total, MIN(id) as min_id, MAX(id) as max_id
                FROM {table} 
                GROUP BY dataset_id 
                ORDER BY dataset_id DESC
                """
                recent_data = pd.read_sql_query(recent_query, conn)
                
                if not recent_data.empty:
                    print(f"📈 Tabela {table} - Datasets:")
                    for _, row in recent_data.iterrows():
                        print(f"   Dataset {row['dataset_id']}: {row['total']:,} registros (IDs: {row['min_id']}-{row['max_id']})")
                else:
                    print(f"📈 Tabela {table}: Nenhum dataset encontrado")
                print()
                    
            except Exception as e:
                print(f"❌ Erro ao verificar dados recentes da tabela {table}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")

if __name__ == "__main__":
    check_database_data()
