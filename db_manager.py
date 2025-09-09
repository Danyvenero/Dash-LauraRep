#!/usr/bin/env python3
"""
Script CLI para gerenciamento do banco de dados Dashboard WEG
Uso: python db_manager.py [comando]

Comandos disponíveis:
  init       - Inicializa o banco de dados
  stats      - Mostra estatísticas do banco
  reset      - Reseta completamente o banco (CUIDADO!)
  check      - Verifica integridade do banco
  help       - Mostra esta ajuda
"""

import sys
import os
import sqlite3
from utils.db import init_db, get_dataset_statistics

def init_database():
    """Inicializa o banco de dados"""
    try:
        print("🔧 Inicializando banco de dados...")
        init_db()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {str(e)}")
        return False

def show_stats():
    """Mostra estatísticas do banco"""
    try:
        print("📊 ESTATÍSTICAS DO BANCO DE DADOS")
        print("=" * 50)
        
        stats = get_dataset_statistics()
        print(f"📋 Total de datasets: {stats['total_datasets']}")
        print(f"💼 Total de vendas: {stats['total_vendas']}")
        print(f"📄 Total de cotações: {stats['total_cotacoes']}")
        print(f"🛍️  Total de produtos cotados: {stats['total_produtos_cotados']}")
        print()
        
        print(f"🔢 Fingerprints únicos:")
        print(f"  - Vendas: {stats['unique_vendas_fps']}")
        print(f"  - Cotações: {stats['unique_cotacoes_fps']}")
        print(f"  - Produtos: {stats['unique_produtos_fps']}")
        print()
        
        if stats['recent_datasets']:
            print("📋 DATASETS RECENTES:")
            for i, ds in enumerate(stats['recent_datasets'], 1):
                print(f"  {i}. {ds['name']} - {ds['uploaded_at']}")
                print(f"     Vendas: {ds['tem_vendas']} | Cotações: {ds['tem_cotacoes']} | Produtos: {ds['tem_produtos']}")
        else:
            print("📋 Nenhum dataset encontrado.")
            
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {str(e)}")

def reset_database():
    """Reseta completamente o banco"""
    print("⚠️  ATENÇÃO: Esta operação irá APAGAR TODOS OS DADOS!")
    response = input("Digite 'CONFIRMO' para continuar: ").strip()
    
    if response != 'CONFIRMO':
        print("❌ Operação cancelada.")
        return
        
    try:
        # Remove banco existente
        db_path = 'instance/database.sqlite'
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️  Banco de dados anterior removido.")
        
        # Recria banco
        init_db()
        print("✅ Banco de dados recriado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao resetar banco: {str(e)}")

def check_database():
    """Verifica integridade do banco"""
    try:
        print("🔍 VERIFICAÇÃO DO BANCO DE DADOS")
        print("=" * 50)
        
        db_path = 'instance/database.sqlite'
        if not os.path.exists(db_path):
            print("❌ Banco de dados não encontrado!")
            print("💡 Execute: python db_manager.py init")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Tabelas encontradas: {len(tables)}")
        for table in tables:
            table_name = table[0]
            
            # Conta registros em cada tabela
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            # Verifica estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"  • {table_name}: {count:,} registros, {len(columns)} colunas")
        
        # Verifica índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
        print(f"📊 Índices encontrados: {len(indexes)}")
        
        # Verifica integridade
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()
        
        if integrity[0] == 'ok':
            print("✅ Integridade do banco: OK")
        else:
            print(f"❌ Problema de integridade: {integrity[0]}")
        
        conn.close()
        print("✅ Verificação concluída!")
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {str(e)}")

def show_help():
    """Mostra ajuda"""
    print(__doc__)

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("❌ Erro: Comando requerido")
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        'init': init_database,
        'stats': show_stats,
        'reset': reset_database,
        'check': check_database,
        'help': show_help
    }
    
    if command in commands:
        print(f"🚀 Executando comando: {command}")
        print("-" * 30)
        commands[command]()
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("💡 Comandos disponíveis:", ", ".join(commands.keys()))
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
