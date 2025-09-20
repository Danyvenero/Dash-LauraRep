#!/usr/bin/env python3
"""
Verificar estrutura do banco de dados
"""

import sqlite3
import os

def check_database(db_name):
    try:
        print(f"🔍 Verificando banco: {db_name}")
        
        if not os.path.exists(db_name):
            print(f"❌ Banco {db_name} não existe")
            return
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print(f"⚠️ Banco {db_name} não tem tabelas")
            conn.close()
            return
        
        print(f"📋 Tabelas encontradas em {db_name}:")
        for table in tables:
            print(f"  - {table[0]}")
            
            # Mostra estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"    Colunas: {[col[1] for col in columns]}")
            
            # Conta registros
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"    Registros: {count}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar {db_name}: {e}")

if __name__ == "__main__":
    # Testa os bancos que encontrei
    databases = ['laura_rep.db', 'laura_dados.db', 'database.db', 'dash_data.db']
    
    for db in databases:
        check_database(db)
        print("-" * 50)