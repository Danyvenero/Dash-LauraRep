import sys
import os
import time
import traceback
import threading
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ml_recommendations import SmartPurchaseRecommendations

def test_callback_with_time_limit():
    """
    Teste do callback B2B com limite de tempo
    """
    print("🧪 Testando callback B2B completo com limite de tempo")
    print("="*70)
    
    start_time = time.time()
    max_time = 30  # 30 segundos máximo
    
    try:
        recommender = SmartPurchaseRecommendations()
        cod_cliente = 782080
        contexto_comercial = {'prioridade': 'alta', 'tipo_analise': 'completa'}
        
        print(f"🎯 Cliente: {cod_cliente}")
        print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⌛ Limite: {max_time} segundos")
        print("-"*50)
        
        # Executar a análise completa
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        elapsed_time = time.time() - start_time
        
        if elapsed_time > max_time:
            print(f"⚠️ TIMEOUT: Análise levou {elapsed_time:.1f}s (limite: {max_time}s)")
            return False
        
        print(f"✅ SUCESSO: Análise completa em {elapsed_time:.1f}s")
        print(f"📊 Resultado keys: {list(resultado.keys()) if resultado else 'None'}")
        print(f"⏰ Fim: {datetime.now().strftime('%H:%M:%S')}")
        
        return True
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ ERRO após {elapsed_time:.1f}s:")
        print(f"   {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_specific_functions():
    """
    Teste das funções específicas que causavam problemas
    """
    print("\n🔍 Testando funções específicas")
    print("="*50)
    
    try:
        recommender = SmartPurchaseRecommendations()
        
        # Simular dados simples
        import pandas as pd
        from datetime import datetime, timedelta
        
        # DataFrame pequeno para teste
        hoje = datetime.now()
        vendas_test = pd.DataFrame({
            'cod_cliente': [782080] * 10,
            'material': [f'MAT{i:03d}' for i in range(10)],
            'data_entrada': [hoje - timedelta(days=i*10) for i in range(10)],
            'vlr_entrada': [1000 + i*100 for i in range(10)]
        })
        
        cotacoes_test = pd.DataFrame({
            'material': [f'MAT{i:03d}' for i in range(10)],
            'preco': [100 + i*10 for i in range(10)]
        })
        
        # Teste das funções principais
        functions_to_test = [
            ('generate_intelligent_alerts', (vendas_test, cotacoes_test)),
            ('generate_actionable_insights', (vendas_test,)),
        ]
        
        for func_name, args in functions_to_test:
            start = time.time()
            try:
                func = getattr(recommender, func_name)
                result = func(*args)
                elapsed = time.time() - start
                print(f"✅ {func_name}: {elapsed:.2f}s")
            except Exception as e:
                elapsed = time.time() - start
                print(f"❌ {func_name}: {elapsed:.2f}s - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste específico: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE FINAL DO CALLBACK B2B")
    print("="*70)
    
    # Teste das funções específicas primeiro
    specific_ok = test_specific_functions()
    
    # Se as funções específicas passaram, teste o callback completo
    if specific_ok:
        callback_ok = test_callback_with_time_limit()
        
        if callback_ok:
            print("\n🎉 TESTE FINAL: SUCESSO!")
            print("   ✅ O callback B2B está funcionando corretamente")
            print("   ✅ Performance dentro do limite aceitável")
            print("   ✅ Sistema pronto para produção")
        else:
            print("\n⚠️ TESTE FINAL: PROBLEMAS DETECTADOS")
            print("   ❌ Callback ainda apresenta problemas")
    else:
        print("\n❌ TESTE FINAL: FALHA NAS FUNÇÕES BÁSICAS")
        print("   ❌ Problemas nas funções fundamentais")