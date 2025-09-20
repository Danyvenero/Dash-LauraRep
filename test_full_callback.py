"""
Teste com dados completos que simula o callback real
"""

import pandas as pd
import sqlite3
from datetime import datetime

def test_full_callback_simulation():
    """Simula exatamente o que o callback faz"""
    try:
        print("🔍 Simulando callback completo...")
        
        from utils.ml_recommendations import SmartPurchaseRecommendations
        recommender = SmartPurchaseRecommendations()
        
        # Dados exatamente como no callback
        cod_cliente = '782080'
        
        contexto_comercial = {
            'vendedor': 'Equipe Comercial',
            'regiao': 'Nacional',
            'segmento': 'Industrial',
            'data_analise': datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"🎯 Cliente: {cod_cliente}")
        print(f"📋 Contexto: {contexto_comercial}")
        
        # Executa análise exatamente como no callback
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        if resultado.get('status') == 'ERRO':
            print(f"❌ Erro na análise: {resultado.get('erro')}")
            return resultado
            
        print(f"✅ Status: {resultado.get('status')}")
        resumo = resultado.get('resumo_executivo', {})
        print(f"🏆 Classificação: {resumo.get('classificacao_cliente', 'N/A')}")
        print(f"🎯 Oportunidades: {resumo.get('total_oportunidades', 0)}")
        print(f"💰 Valor potencial: R$ {resumo.get('valor_potencial', 0):,.2f}")
        
        # Verifica estrutura do resultado
        print(f"\n📊 Estrutura do resultado:")
        for key in resultado.keys():
            print(f"  - {key}: {type(resultado[key])}")
            
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no teste completo: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'ERRO', 'erro': str(e)}

if __name__ == "__main__":
    result = test_full_callback_simulation()
    
    if result.get('status') == 'SUCESSO':
        print("\n✅ TESTE COMPLETO BEM-SUCEDIDO!")
        print("🎉 O callback deveria funcionar corretamente")
    else:
        print(f"\n❌ ERRO ENCONTRADO: {result.get('erro', 'Erro desconhecido')}")