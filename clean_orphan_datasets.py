#!/usr/bin/env python3
"""
Limpa datasets órfãos do banco
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection

def clean_orphan_datasets():
    """Remove datasets que não têm nenhum fingerprint"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🧹 Limpando datasets órfãos...")
    
    # Remove datasets órfãos (sem nenhum fingerprint)
    cursor.execute("""
        DELETE FROM datasets 
        WHERE vendas_fingerprint IS NULL 
        AND cotacoes_fingerprint IS NULL 
        AND produtos_cotados_fingerprint IS NULL
    """)
    
    orphans_removed = cursor.rowcount
    conn.commit()
    
    print(f"✅ {orphans_removed} datasets órfãos removidos")
    
    # Mostra estado final
    print("\n📊 Datasets restantes:")
    cursor.execute('SELECT id, name, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint FROM datasets')
    for row in cursor.fetchall():
        print(f'  ID: {row[0]} | Nome: {row[1]}')
        print(f'    Vendas: {"✅" if row[2] else "❌"}')
        print(f'    Cotações: {"✅" if row[3] else "❌"}') 
        print(f'    Materiais: {"✅" if row[4] else "❌"}')
        print()
    
    conn.close()

if __name__ == "__main__":
    clean_orphan_datasets()
