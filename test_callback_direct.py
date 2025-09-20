#!/usr/bin/env python3
"""
Script para testar diretamente o callback de produtos
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from webapp.callbacks import update_products_charts

if __name__ == "__main__":
    print("🚀 Testando callback de produtos diretamente...")
    
    try:
        # Chamar o callback com parâmetros padrão
        fig_bolhas, fig_pareto = update_products_charts(
            filtro_ano=None,
            filtro_mes=None,
            filtro_cliente=None,
            filtro_hierarquia=None,
            filtro_canal=None,
            filtro_top_clientes=None,
            top_produtos=20,
            derived_virtual_data=None,
            pathname='/app/products'
        )
        
        print(f"✅ Callback executado com sucesso!")
        print(f"   - Bolhas: {type(fig_bolhas)}")
        print(f"   - Pareto: {type(fig_pareto)}")
        
    except Exception as e:
        print(f"❌ Erro no callback: {e}")
        import traceback
        traceback.print_exc()