#!/usr/bin/env python3
"""
Teste específico para verificar o callback generate_suggestions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_specific_callback():
    """Testa especificamente o callback generate_suggestions"""
    
    print("🔍 Testando callback generate_suggestions específico...")
    
    try:
        # Importa o app
        from app import app
        
        print(f"✅ App importado com {len(app.callback_map)} callbacks")
        
        # Procura pelo callback específico que queremos
        target_found = False
        
        print("\n🎯 Procurando por callbacks que contenham 'store-suggestions-data':")
        for callback_id, callback_func in app.callback_map.items():
            callback_str = str(callback_id)
            if 'store-suggestions-data' in callback_str:
                print(f"✅ ENCONTRADO: {callback_id}")
                target_found = True
                
                # Tenta extrair informações sobre o callback
                print(f"   Função: {callback_func}")
                print(f"   Inputs: {getattr(callback_func, 'inputs', 'N/A')}")
                print(f"   Outputs: {getattr(callback_func, 'outputs', 'N/A')}")
                
        if not target_found:
            print("❌ Callback 'store-suggestions-data' NÃO encontrado")
            
            # Lista todos os callbacks para debug
            print("\n📋 Todos os callbacks disponíveis:")
            for i, callback_id in enumerate(app.callback_map.keys(), 1):
                print(f"  {i}. {callback_id}")
                
        print(f"\n📊 Status: {'✅ Callback encontrado' if target_found else '❌ Callback NÃO encontrado'}")
        
        # Teste adicional: verificar se btn-apply-filters-suggestions existe em algum lugar
        print("\n🔍 Procurando por 'btn-apply-filters-suggestions' em qualquer callback:")
        btn_found = False
        for callback_id, callback_func in app.callback_map.items():
            if 'btn-apply-filters-suggestions' in str(callback_id):
                print(f"✅ Botão encontrado em: {callback_id}")
                btn_found = True
                
        if not btn_found:
            print("❌ Botão 'btn-apply-filters-suggestions' NÃO encontrado em nenhum callback")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_callback()