"""
Debug do erro no callback B2B
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ml_recommendations import purchase_recommender
from utils.db import get_connection
import pandas as pd
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_b2b_analysis():
    """Testa a análise B2B para identificar o erro"""
    try:
        # Verifica conexão com banco
        conn = get_connection()
        
        # Pega um cliente de exemplo
        clientes_query = "SELECT DISTINCT cod_cliente FROM vendas WHERE cod_cliente IS NOT NULL LIMIT 5"
        clientes_df = pd.read_sql_query(clientes_query, conn)
        
        if clientes_df.empty:
            print("❌ Nenhum cliente encontrado no banco")
            return
            
        cod_cliente = clientes_df.iloc[0]['cod_cliente']
        print(f"🔍 Testando análise B2B para cliente: {cod_cliente}")
        
        # Contexto comercial de teste
        contexto_comercial = {
            'vendedor': 'Equipe Comercial',
            'regiao': 'Nacional', 
            'segmento': 'Industrial',
            'data_analise': '2025-09-16'
        }
        
        # Executa análise
        resultado = purchase_recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        if resultado.get('status') == 'ERRO':
            print(f"❌ Erro na análise: {resultado.get('erro')}")
            return
            
        print("✅ Análise B2B executada com sucesso!")
        print(f"📊 Cliente: {resultado.get('cliente')}")
        print(f"🎯 Oportunidades: {resultado.get('resumo_executivo', {}).get('total_oportunidades', 0)}")
        print(f"💰 Valor potencial: R$ {resultado.get('resumo_executivo', {}).get('valor_potencial', 0):,.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        print("🔍 Traceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    test_b2b_analysis()