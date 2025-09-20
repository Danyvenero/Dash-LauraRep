#!/usr/bin/env python3
"""
Teste para verificar todos os callbacks registrados na aplicação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def list_all_callbacks():
    """Lista todos os callbacks registrados na app"""
    try:
        from app import app
        
        print(f"🔍 Verificando callbacks da aplicação...")
        
        if hasattr(app, 'callback_map'):
            print(f"📊 Total de callbacks registrados: {len(app.callback_map)}")
            
            # Procura por callbacks relacionados aos filtros
            filter_callbacks = []
            for i, (callback_id, callback_info) in enumerate(app.callback_map.items(), 1):
                callback_str = str(callback_id)
                
                # Verifica se é relacionado aos filtros B2B
                if any(filter_id in callback_str for filter_id in ['filter-b2b-hier-produto-1', 'filter-b2b-unidade-negocio']):
                    filter_callbacks.append((callback_id, callback_info))
                    print(f"✅ Callback de filtro encontrado: {callback_id}")
                
                # Lista alguns callbacks para debug
                if i <= 10:
                    print(f"   {i}. {callback_str[:100]}...")
            
            if not filter_callbacks:
                print("❌ Nenhum callback dos filtros B2B encontrado!")
                
                # Procura por qualquer callback que contenha 'filter-b2b'
                print("\n🔍 Procurando por qualquer callback com 'filter-b2b'...")
                for callback_id in app.callback_map.keys():
                    if 'filter-b2b' in str(callback_id):
                        print(f"   🎯 Encontrado: {callback_id}")
                        
                # Procura por qualquer callback que contenha 'update_initial'
                print("\n🔍 Procurando por qualquer callback com 'update_initial'...")
                for callback_id in app.callback_map.keys():
                    if 'update_initial' in str(callback_id):
                        print(f"   🎯 Encontrado: {callback_id}")
                        
            else:
                print(f"✅ Encontrados {len(filter_callbacks)} callbacks dos filtros B2B")
                return True
                
        return False
        
    except Exception as e:
        print(f"❌ Erro ao verificar callbacks: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_callback_function_directly():
    """Verifica se a função do callback existe e é chamável"""
    try:
        from webapp.b2b_advanced_callbacks import update_initial_filter_options
        print(f"✅ Função update_initial_filter_options encontrada")
        print(f"📍 Localizada em: {update_initial_filter_options.__module__}")
        print(f"🔧 É chamável: {callable(update_initial_filter_options)}")
        
        # Verifica se tem decorador @callback
        if hasattr(update_initial_filter_options, '__name__'):
            print(f"📝 Nome da função: {update_initial_filter_options.__name__}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar função: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Verificação completa de callbacks...")
    
    # Teste 1: Verifica se a função existe
    func_ok = check_callback_function_directly()
    
    # Teste 2: Lista todos os callbacks da app
    app_ok = list_all_callbacks()
    
    print(f"\n📋 Resumo:")
    print(f"   Função existe:       {'✅' if func_ok else '❌'}")
    print(f"   Registrado na app:   {'✅' if app_ok else '❌'}")
    
    if func_ok and not app_ok:
        print(f"\n⚠️ A função existe mas não está registrada na app!")
        print(f"   Isso indica um problema no decorador @callback")
    elif func_ok and app_ok:
        print(f"\n✅ Tudo parece estar funcionando corretamente!")
        print(f"   O callback deveria estar executando automaticamente.")