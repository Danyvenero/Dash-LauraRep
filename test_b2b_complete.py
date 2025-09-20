"""
Teste completo da análise B2B
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
import sqlite3

def test_b2b_real():
    """Teste da análise B2B real usando módulos corrigidos"""
    try:
        print("🔍 Testando análise B2B completa...")
        
        # Importar o módulo corrigido
        from utils.ml_recommendations import SmartPurchaseRecommendations
        
        # Criar instância
        recommender = SmartPurchaseRecommendations()
        print("✅ Instância do recomendador criada")
        
        # Testar uma das funções específicas
        db_path = "instance/database.sqlite"
        conn = sqlite3.connect(db_path)
        
        # Caregar dados de teste
        vendas_query = """
        SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
        FROM vendas 
        WHERE data >= date('now', '-24 months')
        LIMIT 100
        """
        vendas_df = pd.read_sql_query(vendas_query, conn)
        
        cotacoes_query = """
        SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
        FROM produtos_cotados p
        LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
        WHERE c.data >= date('now', '-24 months')
        LIMIT 100
        """
        cotacoes_df = pd.read_sql_query(cotacoes_query, conn)
        conn.close()
        
        # Pegar cliente de teste
        cod_cliente = vendas_df.iloc[0]['cod_cliente']
        print(f"🎯 Testando cliente: {cod_cliente}")
        
        # Testar função de gaps
        gaps_result = recommender.analyze_market_gaps(vendas_df, cotacoes_df, cod_cliente)
        print(f"✅ Análise de gaps OK: {len(gaps_result)} gaps encontrados")
        
        # Testar função de sazonalidade
        seasonality_result = recommender.detect_seasonality(vendas_df, cod_cliente)
        print(f"✅ Análise de sazonalidade OK: {type(seasonality_result)}")
        
        # Testar análise completa
        contexto_comercial = {
            'vendedor': 'Teste',
            'regiao': 'Nacional',
            'segmento': 'Industrial'
        }
        
        resultado_completo = recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        if resultado_completo.get('status') == 'ERRO':
            print(f"❌ Erro na análise completa: {resultado_completo.get('erro')}")
        else:
            print("✅ Análise B2B completa executada com sucesso!")
            print(f"📊 Status: {resultado_completo.get('status')}")
            print(f"🏆 Cliente: {resultado_completo.get('cliente')}")
            
            resumo = resultado_completo.get('resumo_executivo', {})
            print(f"📈 Oportunidades: {resumo.get('total_oportunidades', 0)}")
            print(f"💰 Valor potencial: R$ {resumo.get('valor_potencial', 0):,.2f}")
        
    except Exception as e:
        print(f"❌ Erro durante teste completo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_b2b_real()