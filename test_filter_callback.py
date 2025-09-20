#!/usr/bin/env python3
"""
Teste específico para verificar o callback de filtros iniciais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_filter_callback_specifically():
    """Testa especificamente o callback de filtros que criamos"""
    try:
        # Importa o callback diretamente
        from webapp.b2b_advanced_callbacks import update_initial_filter_options
        print("✅ Callback update_initial_filter_options importado com sucesso")
        
        # Testa execução manual
        print("🧪 Executando callback manualmente...")
        result = update_initial_filter_options(pathname="/b2b-advanced", n_intervals=1)
        
        print(f"📊 Resultado: hierarquias={len(result[0])}, unidades={len(result[1])}")
        
        if result[0]:
            print(f"🏷️ Hierarquias: {[opt['value'] for opt in result[0][:3]]}")  # Primeiras 3
        if result[1]:
            print(f"🏢 Unidades: {[opt['value'] for opt in result[1]]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro no callback: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_dash_app_callbacks():
    """Verifica se o callback está registrado na app Dash"""
    try:
        from app import app
        
        # Lista todos os outputs que começam com filter-b2b
        filter_callbacks = []
        if hasattr(app, 'callback_map'):
            for callback_id in app.callback_map.keys():
                if 'filter-b2b' in str(callback_id):
                    filter_callbacks.append(callback_id)
                    print(f"🔍 Encontrado callback de filtro: {callback_id}")
        
        if not filter_callbacks:
            print("❌ Nenhum callback de filtro B2B encontrado!")
            return False
        else:
            print(f"✅ Encontrados {len(filter_callbacks)} callbacks de filtro B2B")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar app: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Teste específico do callback de filtros...")
    
    # Teste 1: Execução do callback
    callback_ok = test_filter_callback_specifically()
    
    # Teste 2: Verificação na app
    app_ok = check_dash_app_callbacks()
    
    print(f"\n📋 Resumo:")
    print(f"   Callback executável: {'✅' if callback_ok else '❌'}")
    print(f"   Registrado na app:   {'✅' if app_ok else '❌'}")