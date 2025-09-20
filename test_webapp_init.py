"""
Teste de inicialização da aplicação
"""

import os
import sys

try:
    print("🔍 Testando inicialização da webapp...")
    
    # Simula apenas a importação que estava causando problema
    from webapp import app as dash_app
    print("✅ Webapp importada com sucesso")
    
    # Testa os callbacks que estavam dando problema
    from webapp.b2b_advanced_callbacks import run_complete_b2b_analysis
    print("✅ Callbacks B2B carregados com sucesso")
    
    print("✅ Todas as importações funcionando!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()