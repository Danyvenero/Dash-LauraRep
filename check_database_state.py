#!/usr/bin/env python3
"""
Verifica estado atual do banco de dados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection

def check_database_state():
    """Verifica estado atual do banco"""
    conn = get_connection()
    cursor = conn.cursor()

    print('📊 Datasets existentes:')
    cursor.execute('SELECT id, name, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint FROM datasets')
    datasets = cursor.fetchall()
    
    for row in datasets:
        print(f'  ID: {row[0]} | Nome: {row[1]}')
        print(f'    Vendas: {"✅" if row[2] else "❌"}')
        print(f'    Cotações: {"✅" if row[3] else "❌"}') 
        print(f'    Materiais: {"✅" if row[4] else "❌"}')
        print()

    # Verifica dados nas tabelas
    cursor.execute('SELECT COUNT(*) FROM vendas')
    vendas_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM cotacoes') 
    cotacoes_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM produtos_cotados')
    materiais_count = cursor.fetchone()[0]

    print(f'📈 Dados nas tabelas:')
    print(f'  Vendas: {vendas_count}')
    print(f'  Cotações: {cotacoes_count}')  
    print(f'  Materiais: {materiais_count}')

    conn.close()

if __name__ == "__main__":
    check_database_state()
