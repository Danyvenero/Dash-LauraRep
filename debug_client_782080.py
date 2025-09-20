"""
Debug específico para o cliente 782080 que está causando erro
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
import sqlite3
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_client_782080():
    """Debug específico para o cliente 782080"""
    try:
        print("🔍 Debugando cliente 782080 - aildo borges cabral e cia ltda")
        
        # Conecta ao banco
        db_path = "instance/database.sqlite"
        conn = sqlite3.connect(db_path)
        
        # Verifica se o cliente existe
        client_query = "SELECT DISTINCT cod_cliente, cliente FROM vendas WHERE cod_cliente = '782080'"
        client_df = pd.read_sql_query(client_query, conn)
        
        if client_df.empty:
            print("❌ Cliente 782080 não encontrado na base")
            return
            
        print(f"✅ Cliente encontrado: {client_df.iloc[0]['cliente']}")
        
        # Verifica dados do cliente
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE cod_cliente = '782080'
        ORDER BY data DESC
        LIMIT 10
        """
        vendas_df = pd.read_sql_query(vendas_query, conn)
        
        print(f"📊 Vendas do cliente: {len(vendas_df)} registros")
        if not vendas_df.empty:
            print("Últimas vendas:")
            for _, row in vendas_df.head(3).iterrows():
                print(f"  - {row['data']}: {row['material']} - R$ {row['vlr_entrada']}")
        
        # Testa análise B2B específica
        from utils.ml_recommendations import SmartPurchaseRecommendations
        recommender = SmartPurchaseRecommendations()
        
        print("\n🔍 Testando análise de gaps...")
        try:
            # Carrega dados para análise
            vendas_query_full = """
            SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
            FROM vendas 
            WHERE data >= date('now', '-24 months')
            LIMIT 1000
            """
            vendas_full = pd.read_sql_query(vendas_query_full, conn)
            
            cotacoes_query = """
            SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
            FROM produtos_cotados p
            LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
            WHERE c.data >= date('now', '-24 months')
            LIMIT 1000
            """
            cotacoes_full = pd.read_sql_query(cotacoes_query, conn)
            
            gaps_result = recommender.analyze_market_gaps(vendas_full, cotacoes_full, '782080')
            print(f"✅ Análise de gaps OK: {len(gaps_result)} gaps")
            
        except Exception as e:
            print(f"❌ Erro na análise de gaps: {e}")
            traceback.print_exc()
        
        print("\n🔍 Testando análise completa...")
        try:
            contexto_comercial = {
                'vendedor': 'Teste',
                'regiao': 'Nacional',
                'segmento': 'Industrial'
            }
            
            resultado = recommender.run_complete_b2b_analysis(
                cod_cliente='782080',
                contexto_comercial=contexto_comercial,
                export_format='completo'
            )
            
            if resultado.get('status') == 'ERRO':
                print(f"❌ Erro na análise completa: {resultado.get('erro')}")
            else:
                print(f"✅ Análise completa OK - Status: {resultado.get('status')}")
                resumo = resultado.get('resumo_executivo', {})
                print(f"📈 Oportunidades: {resumo.get('total_oportunidades', 0)}")
                
        except Exception as e:
            print(f"❌ Erro na análise completa: {e}")
            traceback.print_exc()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_client_782080()