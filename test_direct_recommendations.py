#!/usr/bin/env python3
"""
Teste Direto da Função generate_smart_recommendations
Simula exatamente o que acontece quando o botão é clicado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_generate_smart_recommendations():
    """Testa diretamente a função de recomendações"""
    print("🧪 TESTANDO FUNÇÃO generate_smart_recommendations()")
    print("=" * 60)
    
    try:
        # Importa a função diretamente
        from webapp.b2b_advanced_callbacks import generate_smart_recommendations
        
        print("✅ Função importada com sucesso")
        print("🔄 Executando generate_smart_recommendations()...")
        
        # Executa a função
        result = generate_smart_recommendations()
        
        print("✅ Função executada sem erros!")
        print(f"📊 Tipo do resultado: {type(result)}")
        
        # Verifica se o resultado é válido (não é uma mensagem de erro)
        if hasattr(result, 'children'):
            print("✅ Resultado contém children (recomendações geradas)")
            if isinstance(result.children, list) and len(result.children) > 1:
                print(f"✅ {len(result.children)} elementos nas recomendações")
                
                # Verifica se o primeiro elemento é um Alert de sucesso
                first_element = result.children[0]
                if hasattr(first_element, 'color') and first_element.color == 'success':
                    print("✅ Alert de sucesso encontrado - dados suficientes!")
                    return True
                else:
                    print("⚠️ Primeiro elemento não é alert de sucesso")
            else:
                print("⚠️ Poucas recomendações geradas")
        else:
            # Se não tem children, pode ser um Alert direto
            if hasattr(result, 'color'):
                if result.color == 'warning':
                    print("❌ Retornou alert de warning - dados insuficientes")
                    return False
                elif result.color == 'success':
                    print("✅ Alert de sucesso - funcionou!")
                    return True
            print("⚠️ Resultado em formato inesperado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar função: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_generate_smart_recommendations()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCESSO! As recomendações devem funcionar no dashboard")
        print("\n🚀 Para testar:")
        print("1. Acesse http://127.0.0.1:8050")
        print("2. Faça login (admin/admin123)")
        print("3. Vá para 'Sistema B2B Avançado'")
        print("4. Clique no botão 'Atualizar' em Recomendações Inteligentes")
        print("5. Deve aparecer recomendações baseadas nos dados!")
    else:
        print("❌ FALHOU! Ainda há problemas a corrigir")