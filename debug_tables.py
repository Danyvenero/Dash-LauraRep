#!/usr/bin/env python3
"""
Debug - Lista tabelas do banco
"""
import sqlite3

def list_tables():
    conn = sqlite3.connect('instance/laurarep.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tabelas disponíveis:")
    for table in tables:
        print(f"  - {table}")
        
        # Lista colunas de cada tabela
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"    Colunas: {[col[1] for col in columns]}")
        
        # Conta registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"    Registros: {count}")
        print()
    
    conn.close()

if __name__ == "__main__":
    list_tables()