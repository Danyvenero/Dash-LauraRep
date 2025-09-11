"""
Script para inserir dados de teste para verificar a funcionalidade da tabela de produtos
"""
import sqlite3
import pandas as pd
from datetime import datetime, date
from pathlib import Path

# Caminho para o banco
db_path = Path("instance/database.sqlite")

def inserir_dados_teste():
    """Insere dados de teste nas tabelas vendas e cotacoes"""
    
    conn = sqlite3.connect(db_path)
    
    # Verifica se já existem dados
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vendas")
    vendas_count = cursor.fetchone()[0]
    
    if vendas_count > 0:
        print(f"✅ Banco já possui {vendas_count} registros de vendas")
        return
    
    print("🔄 Inserindo dados de teste...")
    
    # Dados de teste para vendas
    vendas_teste = [
        {
            'dataset_id': 1,
            'material': 'MAT001',
            'hier_produto_1': 'Motor Elétrico 1CV',
            'vlr_rol': 1500.00,
            'qty_vendida': 2,
            'cod_cliente': 'CLI001',
            'data': '2024-01-15',
            'data_faturamento': '2024-01-15'
        },
        {
            'dataset_id': 1,
            'material': 'MAT002',
            'hier_produto_1': 'Motor Elétrico 2CV',
            'vlr_rol': 2200.00,
            'qty_vendida': 1,
            'cod_cliente': 'CLI002',
            'data': '2024-01-20',
            'data_faturamento': '2024-01-20'
        },
        {
            'dataset_id': 1,
            'material': 'MAT003',
            'hier_produto_1': 'Redutor de Velocidade',
            'vlr_rol': 800.00,
            'qty_vendida': 3,
            'cod_cliente': 'CLI001',
            'data': '2024-02-10',
            'data_faturamento': '2024-02-10'
        },
        {
            'dataset_id': 1,
            'material': 'MAT001',
            'hier_produto_1': 'Motor Elétrico 1CV',
            'vlr_rol': 1600.00,
            'qty_vendida': 1,
            'cod_cliente': 'CLI003',
            'data': '2024-02-15',
            'data_faturamento': '2024-02-15'
        }
    ]
    
    # Dados de teste para cotações
    cotacoes_teste = [
        {
            'dataset_id': 1,
            'material': 'MAT001',
            'numero_cotacao': 'COT001',
            'qtde': 5,
            'cod_cliente': 'CLI001',
            'data': '2024-01-10'
        },
        {
            'dataset_id': 1,
            'material': 'MAT002',
            'numero_cotacao': 'COT002',
            'qtde': 2,
            'cod_cliente': 'CLI002',
            'data': '2024-01-18'
        },
        {
            'dataset_id': 1,
            'material': 'MAT003',
            'numero_cotacao': 'COT003',
            'qtde': 4,
            'cod_cliente': 'CLI001',
            'data': '2024-02-05'
        },
        {
            'dataset_id': 1,
            'material': 'MAT001',
            'numero_cotacao': 'COT004',
            'qtde': 3,
            'cod_cliente': 'CLI003',
            'data': '2024-02-12'
        }
    ]
    
    try:
        # Insere dados de vendas
        vendas_df = pd.DataFrame(vendas_teste)
        vendas_df.to_sql('vendas', conn, if_exists='append', index=False)
        print(f"✅ Inseridos {len(vendas_teste)} registros de vendas")
        
        # Insere dados de cotações
        cotacoes_df = pd.DataFrame(cotacoes_teste)
        cotacoes_df.to_sql('cotacoes', conn, if_exists='append', index=False)
        print(f"✅ Inseridos {len(cotacoes_teste)} registros de cotações")
        
        # Verifica a inserção
        cursor.execute("SELECT COUNT(*) FROM vendas")
        vendas_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cotacoes")
        cotacoes_count = cursor.fetchone()[0]
        
        print(f"📊 Total no banco - Vendas: {vendas_count}, Cotações: {cotacoes_count}")
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inserir_dados_teste()
