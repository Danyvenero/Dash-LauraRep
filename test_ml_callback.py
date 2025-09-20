#!/usr/bin/env python3
"""
Teste direto do callback generate_suggestions com ML real
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ml_callback():
    """Testa o callback diretamente"""
    
    print("🔍 Testando callback ML real...")
    
    try:
        # Importa diretamente a função
        from webapp.purchase_suggestions_callbacks_simple import generate_suggestions
        
        print("✅ Função importada com sucesso")
        
        # Simula clique do botão
        result = generate_suggestions(
            btn_apply=1,  # Simula clique
            btn_refresh=None,
            cliente_filter=None,  # Todos os clientes
            periodo_meses=12,     # Último ano
            abc_filter="ALL",
            xyz_filter="ALL", 
            top_n=10,
            selected_hierarchy_tab="tab-hier1",
            hierarchy_filter=None
        )
        
        sugestoes_data, message = result
        
        print(f"📊 Resultado do callback:")
        print(f"   - Sugestões: {len(sugestoes_data) if sugestoes_data else 0}")
        print(f"   - Mensagem: {message}")
        
        if sugestoes_data and len(sugestoes_data) > 0:
            print(f"   - Primeira sugestão: {sugestoes_data[0]}")
            print("✅ CALLBACK FUNCIONANDO COM ML REAL!")
        else:
            print("⚠️  Callback retornou dados vazios")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ml_callback()