"""
Ferramenta de debug e correção para uploads
"""
import os
import sys
import sqlite3
import pandas as pd

# Adicionar o caminho do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verificar_estrutura_banco():
    """Verifica e corrige a estrutura do banco"""
    print("🔧 VERIFICANDO ESTRUTURA DO BANCO")
    print("="*50)
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.sqlite')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se tabela materiais_cotados existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='materiais_cotados'
        """)
        materiais_exists = cursor.fetchone()
        
        # Verificar se tabela produtos_cotados existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='produtos_cotados'
        """)
        produtos_exists = cursor.fetchone()
        
        print(f"📋 Tabela 'materiais_cotados' existe: {bool(materiais_exists)}")
        print(f"📋 Tabela 'produtos_cotados' existe: {bool(produtos_exists)}")
        
        # Se materiais_cotados não existe, criar como alias para produtos_cotados
        if not materiais_exists and produtos_exists:
            print("🔧 Criando view materiais_cotados -> produtos_cotados")
            cursor.execute("""
                CREATE VIEW materiais_cotados AS 
                SELECT * FROM produtos_cotados
            """)
            conn.commit()
            print("✅ View criada com sucesso")
        
        # Contar registros em cada tabela
        for table in ['vendas', 'cotacoes', 'produtos_cotados']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📊 {table:<20}: {count:>8} registros")
            except Exception as e:
                print(f"❌ {table:<20}: ERRO - {e}")
        
        # Verificar se existe alias materiais_cotados
        try:
            cursor.execute("SELECT COUNT(*) FROM materiais_cotados")
            count = cursor.fetchone()[0]
            print(f"📊 {'materiais_cotados':<20}: {count:>8} registros (view)")
        except Exception as e:
            print(f"❌ {'materiais_cotados':<20}: ERRO - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def mostrar_dados_exemplo():
    """Mostra exemplos dos dados existentes"""
    print("\n📋 EXEMPLOS DE DADOS EXISTENTES")
    print("="*50)
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.sqlite')
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Mostrar exemplo de vendas
        try:
            vendas = pd.read_sql_query("SELECT * FROM vendas LIMIT 3", conn)
            print(f"\n📊 VENDAS ({len(vendas)} primeiros registros):")
            print(f"Colunas: {list(vendas.columns)}")
            if not vendas.empty:
                print(vendas.to_string(index=False, max_cols=8))
        except Exception as e:
            print(f"❌ Erro vendas: {e}")
        
        # Mostrar exemplo de cotacoes
        try:
            cotacoes = pd.read_sql_query("SELECT * FROM cotacoes LIMIT 3", conn)
            print(f"\n📊 COTAÇÕES ({len(cotacoes)} primeiros registros):")
            print(f"Colunas: {list(cotacoes.columns)}")
            if not cotacoes.empty:
                print(cotacoes.to_string(index=False, max_cols=8))
        except Exception as e:
            print(f"❌ Erro cotacoes: {e}")
        
        # Mostrar exemplo de produtos_cotados
        try:
            produtos = pd.read_sql_query("SELECT * FROM produtos_cotados LIMIT 3", conn)
            print(f"\n📊 PRODUTOS COTADOS ({len(produtos)} primeiros registros):")
            print(f"Colunas: {list(produtos.columns)}")
            if not produtos.empty:
                print(produtos.to_string(index=False, max_cols=8))
        except Exception as e:
            print(f"❌ Erro produtos_cotados: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def verificar_datasets():
    """Verifica os datasets carregados"""
    print("\n📋 DATASETS CARREGADOS")
    print("="*50)
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.sqlite')
    
    try:
        conn = sqlite3.connect(db_path)
        
        datasets = pd.read_sql_query("""
            SELECT id, name, uploaded_at, uploaded_by,
                   CASE WHEN vendas_fingerprint IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_vendas,
                   CASE WHEN cotacoes_fingerprint IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_cotacoes,
                   CASE WHEN produtos_cotados_fingerprint IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_produtos
            FROM datasets 
            ORDER BY uploaded_at DESC 
            LIMIT 10
        """, conn)
        
        if not datasets.empty:
            print(datasets.to_string(index=False))
        else:
            print("❌ Nenhum dataset encontrado")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_estrutura_banco()
    mostrar_dados_exemplo()
    verificar_datasets()
