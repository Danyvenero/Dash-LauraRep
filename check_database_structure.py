"""
Verificação da estrutura do banco database.sqlite
"""

import sqlite3
import pandas as pd

def check_database_structure():
    """Verifica a estrutura do banco database.sqlite"""
    try:
        db_path = "instance/database.sqlite"
        conn = sqlite3.connect(db_path)
        
        print(f"🔍 Verificando estrutura do banco: {db_path}")
        print(f"📊 Tamanho do arquivo: {33890304 / (1024*1024):.1f} MB")
        
        # Lista todas as tabelas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        
        print(f"\n📋 Tabelas encontradas: {len(tabelas)}")
        for tabela in tabelas:
            print(f"  - {tabela[0]}")
        
        # Verifica estrutura da tabela vendas
        if ('vendas',) in tabelas:
            print(f"\n🔍 Estrutura da tabela VENDAS:")
            cursor.execute("PRAGMA table_info(vendas)")
            colunas_vendas = cursor.fetchall()
            for col in colunas_vendas:
                print(f"  - {col[1]} ({col[2]})")
            
            # Conta registros
            cursor.execute("SELECT COUNT(*) FROM vendas")
            count_vendas = cursor.fetchone()[0]
            print(f"📊 Total de registros em vendas: {count_vendas:,}")
            
            # Verifica algumas colunas específicas
            cursor.execute("SELECT * FROM vendas LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"\n🔍 Exemplo de registro (primeiras 10 colunas):")
                colunas = [desc[0] for desc in cursor.description][:10]
                for i, col in enumerate(colunas):
                    if i < len(sample):
                        print(f"  - {col}: {sample[i]}")
        
        # Verifica tabela cotacoes
        if ('cotacoes',) in tabelas:
            print(f"\n🔍 Estrutura da tabela COTACOES:")
            cursor.execute("PRAGMA table_info(cotacoes)")
            colunas_cotacoes = cursor.fetchall()
            for col in colunas_cotacoes:
                print(f"  - {col[1]} ({col[2]})")
                
            cursor.execute("SELECT COUNT(*) FROM cotacoes")
            count_cotacoes = cursor.fetchone()[0]
            print(f"📊 Total de registros em cotacoes: {count_cotacoes:,}")
        
        # Verifica tabela produtos_cotados
        if ('produtos_cotados',) in tabelas:
            print(f"\n🔍 Estrutura da tabela PRODUTOS_COTADOS:")
            cursor.execute("PRAGMA table_info(produtos_cotados)")
            colunas_produtos = cursor.fetchall()
            for col in colunas_produtos:
                print(f"  - {col[1]} ({col[2]})")
                
            cursor.execute("SELECT COUNT(*) FROM produtos_cotados")
            count_produtos = cursor.fetchone()[0]
            print(f"📊 Total de registros em produtos_cotados: {count_produtos:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_structure()