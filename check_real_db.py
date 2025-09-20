#!/usr/bin/env python3
"""
Verificar estrutura do banco SQLite real
"""

import sqlite3
import os

def check_sqlite_database():
    try:
        db_path = 'instance/database.sqlite'
        print(f"🔍 Verificando banco: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ Banco {db_path} não existe")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print(f"⚠️ Banco {db_path} não tem tabelas")
            conn.close()
            return
        
        print(f"📋 Tabelas encontradas em {db_path}:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # Mostra estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"    Colunas: {[col[1] for col in columns]}")
            
            # Conta registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    Registros: {count}")
            
            # Se for tabela vendas, mostra alguns exemplos de clientes
            if table_name == 'vendas' and count > 0:
                cursor.execute("SELECT DISTINCT cod_cliente, cliente FROM vendas WHERE cod_cliente IS NOT NULL LIMIT 5")
                examples = cursor.fetchall()
                print(f"    Exemplos de clientes: {examples}")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

if __name__ == "__main__":
    check_sqlite_database()