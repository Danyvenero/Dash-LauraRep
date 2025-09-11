import sqlite3
import os

db_path = "instance/database.sqlite"
print(f"Verificando banco: {db_path}")
print(f"Arquivo existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lista todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    print(f"Tabelas: {[t[0] for t in tabelas]}")
    
    # Verifica vendas
    try:
        cursor.execute('SELECT COUNT(*) FROM vendas')
        vendas_count = cursor.fetchone()[0]
        print(f'Vendas: {vendas_count} registros')
        
        if vendas_count > 0:
            cursor.execute('PRAGMA table_info(vendas)')
            colunas = cursor.fetchall()
            print('Colunas vendas:', [col[1] for col in colunas])
            
            # Verifica se há material
            cursor.execute('SELECT material FROM vendas LIMIT 5')
            materiais = cursor.fetchall()
            print('Primeiros materiais:', materiais)
    except Exception as e:
        print(f'Erro vendas: {e}')
    
    # Verifica cotacoes
    try:
        cursor.execute('SELECT COUNT(*) FROM cotacoes')
        cotacoes_count = cursor.fetchone()[0]
        print(f'Cotacoes: {cotacoes_count} registros')
    except Exception as e:
        print(f'Erro cotacoes: {e}')
    
    conn.close()
