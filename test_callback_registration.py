#!/usr/bin/env python3
"""
Teste para verificar se o callback está sendo registrado corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_callback_registration():
    """Testa se os callbacks estão sendo registrados"""
    
    print("🔍 Testando registro de callbacks...")
    
    try:
        # Importa o app principal
        from app import app
        
        print(f"✅ App importado com sucesso")
        print(f"📊 Total de callbacks registrados: {len(app.callback_map)}")
        
        # Lista todos os callbacks
        print("\n📋 Callbacks registrados:")
        for i, (callback_id, callback_func) in enumerate(app.callback_map.items(), 1):
            print(f"  {i}. {callback_id}")
            
            # Verifica se é o callback que procuramos
            if 'generate_suggestions' in str(callback_func):
                print(f"    🎯 ENCONTRADO: Este é o callback generate_suggestions!")
                
        # Procura especificamente pelo callback de suggestions
        suggestions_callback = None
        for callback_id, callback_func in app.callback_map.items():
            if 'store-suggestions-data' in str(callback_id):
                suggestions_callback = callback_func
                print(f"\n🎯 Callback de sugestões encontrado!")
                print(f"   ID: {callback_id}")
                print(f"   Função: {callback_func}")
                break
                
        if not suggestions_callback:
            print("\n❌ PROBLEMA: Callback de sugestões NÃO encontrado!")
            print("   Isso explica por que o botão não funciona!")
            
        # Verifica inputs específicos
        print("\n🔍 Procurando por inputs específicos...")
        found_suggestions = False
        for callback_id, callback_func in app.callback_map.items():
            callback_str = str(callback_id)
            if 'btn-apply-filters-suggestions' in callback_str:
                print(f"✅ Encontrado callback com btn-apply-filters-suggestions")
                print(f"   ID: {callback_id}")
                found_suggestions = True
            elif 'store-suggestions-data' in callback_str:
                print(f"✅ Encontrado callback com store-suggestions-data")
                print(f"   ID: {callback_id}")
                found_suggestions = True
                
        if not found_suggestions:
            print("\n🔍 Tentando importar explicitamente purchase_suggestions_callbacks...")
            try:
                import webapp.purchase_suggestions_callbacks
                print("✅ Import manual funcionou")
                print(f"📊 Total de callbacks APÓS import manual: {len(app.callback_map)}")
                
                # Verifica novamente
                for callback_id, callback_func in app.callback_map.items():
                    callback_str = str(callback_id)
                    if 'suggestions' in callback_str.lower():
                        print(f"✅ AGORA encontrado callback com sugestões!")
                        print(f"   ID: {callback_id}")
                        found_suggestions = True
                        
            except Exception as e:
                print(f"❌ Erro no import manual: {e}")
                
        print(f"\n📊 Status final: {'✅ Callbacks de sugestões encontrados' if found_suggestions else '❌ Callbacks de sugestões NÃO encontrados'}")
                
    except Exception as e:
        print(f"❌ Erro ao testar callbacks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_callback_registration()