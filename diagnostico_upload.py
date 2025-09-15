"""
Script de diagnóstico para verificar problemas no upload de dados
"""
import os
import sys
import sqlite3
import pandas as pd

# Adicionar o caminho do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader_fixed import DataLoaderFixed

def diagnosticar_banco():
    """Verifica estado atual do banco de dados"""
    print("🔍 DIAGNÓSTICO DO BANCO DE DADOS")
    print("="*50)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.sqlite')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não existe!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar tabelas existentes
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = pd.read_sql_query(tables_query, conn)
        print(f"📋 Tabelas existentes: {list(tables['name'])}")
        
        # Verificar contagem de registros
        for table in ['vendas', 'cotacoes', 'materiais_cotados', 'produtos_cotados']:
            try:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = pd.read_sql_query(count_query, conn)
                count = result.iloc[0]['count']
                print(f"📊 {table:<20}: {count:>8} registros")
                
                if count > 0:
                    # Mostrar estrutura da tabela
                    sample_query = f"SELECT * FROM {table} LIMIT 3"
                    sample = pd.read_sql_query(sample_query, conn)
                    print(f"   Colunas: {list(sample.columns)}")
                    
            except Exception as e:
                print(f"❌ {table:<20}: ERRO - {e}")
        
        # Verificar datasets
        try:
            datasets_query = "SELECT * FROM datasets ORDER BY uploaded_at DESC LIMIT 5"
            datasets = pd.read_sql_query(datasets_query, conn)
            print(f"\n📋 Últimos datasets:")
            print(datasets.to_string(index=False))
        except Exception as e:
            print(f"❌ Erro ao consultar datasets: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")

def testar_normalizadores():
    """Testa os normalizadores de dados com dados de exemplo"""
    print("\n🔍 TESTE DOS NORMALIZADORES")
    print("="*50)
    
    loader = DataLoaderFixed()
    
    # Teste 1: Dados de vendas
    print("\n📊 Teste 1: Normalizador de Vendas")
    vendas_sample = pd.DataFrame({
        'Cod. Cliente': ['123', '456'],
        'Cliente': ['Empresa A', 'Empresa B'],
        'Material': ['MAT001', 'MAT002'],
        'Produto': ['Motor 1CV', 'Motor 2CV'],
        'Data': ['2023-01-01', '2023-01-02'],
        'Vlr. Rol': [1000.50, 2000.75]
    })
    
    try:
        vendas_norm = loader.normalize_vendas_data(vendas_sample)
        print(f"✅ Vendas normalizado: {vendas_norm.shape}")
        print(f"   Colunas: {list(vendas_norm.columns)}")
    except Exception as e:
        print(f"❌ Erro vendas: {e}")
    
    # Teste 2: Dados de cotações
    print("\n📊 Teste 2: Normalizador de Cotações")
    cotacoes_sample = pd.DataFrame({
        'Número da Cotação': ['COT001', 'COT002'],
        'Número da Revisão': ['1', '2'],
        'Cod. Cliente': ['123', '456'],
        'Cliente': ['Empresa A', 'Empresa B'],
        'Status': ['Aberta', 'Fechada'],
        'Data': ['2023-01-01', '2023-01-02']
    })
    
    try:
        cotacoes_norm = loader.normalize_cotacoes_data(cotacoes_sample)
        print(f"✅ Cotações normalizado: {cotacoes_norm.shape}")
        print(f"   Colunas: {list(cotacoes_norm.columns)}")
    except Exception as e:
        print(f"❌ Erro cotações: {e}")
    
    # Teste 3: Dados de produtos cotados
    print("\n📊 Teste 3: Normalizador de Produtos Cotados")
    produtos_sample = pd.DataFrame({
        'Cotação': ['COT001', 'COT002'],
        'Cod. Cliente': ['123', '456'],
        'Cliente': ['Empresa A', 'Empresa B'],
        'Material': ['MAT001', 'MAT002'],
        'Descrição': ['Motor 1CV', 'Motor 2CV'],
        'Quantidade': [10, 20],
        'Preço Líquido Unitário': [100.50, 200.75]
    })
    
    try:
        produtos_norm = loader.normalize_produtos_cotados_data(produtos_sample)
        print(f"✅ Produtos normalizado: {produtos_norm.shape}")
        print(f"   Colunas: {list(produtos_norm.columns)}")
    except Exception as e:
        print(f"❌ Erro produtos: {e}")

if __name__ == "__main__":
    diagnosticar_banco()
    testar_normalizadores()
