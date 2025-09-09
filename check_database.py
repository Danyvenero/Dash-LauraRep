import sqlite3
import os
import pandas as pd

# Verifica o banco de dados
db_path = os.path.join('instance', 'database.sqlite')

if os.path.exists(db_path):
    print(f"✅ Banco de dados encontrado: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lista tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📊 Tabelas disponíveis: {[table[0] for table in tables]}")
    
    # Verifica datasets
    try:
        cursor.execute("SELECT COUNT(*) FROM datasets;")
        dataset_count = cursor.fetchone()[0]
        print(f"📈 Número de datasets: {dataset_count}")
        
        if dataset_count > 0:
            cursor.execute("SELECT id, name, type, upload_date, row_count FROM datasets ORDER BY upload_date DESC LIMIT 5;")
            recent_datasets = cursor.fetchall()
            print(f"🔍 Datasets mais recentes:")
            for dataset in recent_datasets:
                print(f"  - ID: {dataset[0]}, Nome: {dataset[1]}, Tipo: {dataset[2]}, Data: {dataset[3]}, Linhas: {dataset[4]}")
                
    except Exception as e:
        print(f"❌ Erro ao consultar datasets: {str(e)}")
    
    # Verifica usuários
    try:
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"👥 Número de usuários: {user_count}")
    except Exception as e:
        print(f"❌ Erro ao consultar usuários: {str(e)}")
    
    conn.close()
else:
    print(f"❌ Banco de dados não encontrado: {db_path}")

# Verifica se há arquivos de dados temporários
print(f"\n📁 Verificando arquivos na pasta instance:")
instance_path = 'instance'
if os.path.exists(instance_path):
    files = os.listdir(instance_path)
    print(f"Arquivos em instance/: {files}")
else:
    print("Pasta instance/ não encontrada")
