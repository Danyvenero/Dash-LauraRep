"""
Teste específico para diagnóstico da página de produtos
"""
import sys
sys.path.append('.')
import pandas as pd
from utils.db import load_vendas_data
from webapp.callbacks import update_products_table

def test_products_callback():
    """Testa o callback de produtos isoladamente"""
    print("🔍 Testando callback de produtos...")
    
    try:
        # Simular chamada do callback
        result = update_products_table(
            filtro_ano=None,
            filtro_mes=None, 
            filtro_cliente=None,
            filtro_hierarquia=None,
            filtro_canal=None,
            material_filter=None,
            pathname='/app/products'
        )
        
        print(f"✅ Callback executado. Tipo do resultado: {type(result)}")
        print(f"✅ Tamanho do resultado: {len(result) if result else 0}")
        
        if result:
            print(f"✅ Primeiro item: {type(result[0])}")
            if isinstance(result[0], dict):
                print(f"✅ Chaves do primeiro item: {list(result[0].keys())}")
            else:
                print(f"❌ Primeiro item não é dict: {result[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_products_callback()