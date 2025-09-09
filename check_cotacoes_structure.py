#!/usr/bin/env python3
"""Script para verificar a estrutura da tabela cotacoes"""

import sqlite3

def check_cotacoes_structure():
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        print("=== ESTRUTURA DA TABELA COTACOES ===")
        cursor.execute('PRAGMA table_info(cotacoes)')
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print(f"\nTotal de colunas: {len(columns)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro ao verificar estrutura: {e}")

if __name__ == "__main__":
    check_cotacoes_structure()
