"""
Teste final do callback B2B com timeout
"""

import signal
import time
from datetime import datetime

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Timeout!")

def test_with_timeout():
    """Testa com timeout de 30 segundos"""
    try:
        # Define timeout de 30 segundos
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        print("🔍 Teste do callback B2B com timeout de 30s...")
        start_time = time.time()
        
        from utils.ml_recommendations import SmartPurchaseRecommendations
        recommender = SmartPurchaseRecommendations()
        
        contexto_comercial = {
            'vendedor': 'Equipe Comercial',
            'regiao': 'Nacional',
            'segmento': 'Industrial',
            'data_analise': datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"⏰ Iniciando análise às {time.strftime('%H:%M:%S')}")
        
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente='782080',
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        elapsed = time.time() - start_time
        signal.alarm(0)  # Cancela o timeout
        
        print(f"✅ Concluído em {elapsed:.1f} segundos!")
        print(f"📊 Status: {resultado.get('status')}")
        
        if resultado.get('status') == 'SUCESSO':
            resumo = resultado.get('resumo_executivo', {})
            print(f"🏆 Classificação: {resumo.get('classificacao_cliente', 'N/A')}")
            print(f"🎯 Oportunidades: {resumo.get('total_oportunidades', 0)}")
            print(f"💰 Valor potencial: R$ {resumo.get('valor_potencial', 0):,.2f}")
            return True
        else:
            print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
            return False
            
    except TimeoutException:
        print("⏰ TIMEOUT! A análise demorou mais de 30 segundos")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    if test_with_timeout():
        print("\n🎉 CALLBACK B2B FUNCIONANDO PERFEITAMENTE!")
    else:
        print("\n❌ Ainda há problemas no callback B2B")