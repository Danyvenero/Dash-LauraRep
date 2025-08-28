# setup_database.py
"""
Script para inicialização do banco de dados e configuração inicial
"""

import os
import sys
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import init_database, add_user
from utils.security import hash_password

def setup_initial_database():
    """Configura o banco de dados inicial com usuário admin"""
    
    print("🔧 Configurando banco de dados inicial...")
    
    # Criar diretório instance se não existir
    os.makedirs('instance', exist_ok=True)
    
    # Inicializar banco de dados
    try:
        init_database()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False
    
    # Criar usuário admin padrão
    try:
        admin_created = add_user('admin', 'admin123')
        if admin_created:
            print("✅ Usuário admin criado com sucesso!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        else:
            print("ℹ️  Usuário admin já existe")
    except Exception as e:
        print(f"❌ Erro ao criar usuário admin: {e}")
        return False
    
    # Verificar estrutura do banco
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tabelas criadas: {', '.join(tables)}")
        
        # Verificar usuários
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"👤 Usuários no sistema: {user_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Erro ao verificar banco: {e}")
    
    print("\n🚀 Configuração concluída!")
    print("🌐 Execute o dashboard com: python app.py")
    print("🔗 Acesse: http://localhost:8050")
    
    return True

def reset_database():
    """Remove e recria o banco de dados"""
    
    print("⚠️  ATENÇÃO: Esta operação apagará TODOS os dados!")
    confirm = input("Digite 'CONFIRMO' para continuar: ")
    
    if confirm != 'CONFIRMO':
        print("❌ Operação cancelada.")
        return
    
    # Remover arquivo do banco
    db_path = 'instance/database.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Banco de dados anterior removido.")
    
    # Recriar
    setup_initial_database()

def add_sample_data():
    """Adiciona dados de exemplo para teste"""
    
    print("📊 Adicionando dados de exemplo...")
    
    try:
        import pandas as pd
        import sqlite3
        from datetime import datetime
        
        # Conectar diretamente ao banco
        conn = sqlite3.connect('instance/database.sqlite')
        
        # Dados de exemplo de vendas (sem dataset_id)
        sample_vendas = pd.DataFrame({
            'cod_cliente': [1001, 1002, 1003, 1001, 1002],
            'cliente': ['Cliente A Ltda', 'Cliente B S.A.', 'Cliente C Eireli', 'Cliente A Ltda', 'Cliente B S.A.'],
            'material': [12345, 23456, 34567, 12345, 45678],
            'produto': ['Motor WEG 1CV', 'Motor WEG 2CV', 'Motor WEG 5CV', 'Motor WEG 1CV', 'Motor WEG 10CV'],
            'unidade_negocio': ['Motores', 'Motores', 'Motores', 'Motores', 'Motores'],
            'data_faturamento': ['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12'],
            'quantidade_faturada': [2, 1, 3, 1, 2],
            'valor_faturado': [1500.00, 2800.00, 8500.00, 1500.00, 15000.00],
            'valor_entrada': [1500.00, 2800.00, 8500.00, 1500.00, 15000.00],
            'valor_carteira': [0.00, 0.00, 0.00, 0.00, 0.00]
        })
        
        # Dados de exemplo de cotações (sem dataset_id)
        sample_cotacoes = pd.DataFrame({
            'cod_cliente': [1001, 1002, 1003, 1004, 1001],
            'cliente': ['Cliente A Ltda', 'Cliente B S.A.', 'Cliente C Eireli', 'Cliente D Corp', 'Cliente A Ltda'],
            'material': [12345, 23456, 34567, 45678, 56789],
            'data': ['2024-01-10', '2024-02-15', '2024-03-05', '2024-04-01', '2024-05-08'],
            'quantidade': [5, 2, 4, 3, 2]
        })
        
        # Inserir dados usando pandas
        sample_vendas.to_sql('vendas', conn, if_exists='append', index=False)
        sample_cotacoes.to_sql('cotacoes', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Dados de exemplo inseridos:")
        print(f"   📈 Vendas: {len(sample_vendas)} registros")
        print(f"   📋 Cotações: {len(sample_cotacoes)} registros")
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados de exemplo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuração do Dashboard WEG')
    parser.add_argument('--reset', action='store_true', help='Reset completo do banco de dados')
    parser.add_argument('--sample-data', action='store_true', help='Adicionar dados de exemplo')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    elif args.sample_data:
        add_sample_data()
    else:
        setup_initial_database()
