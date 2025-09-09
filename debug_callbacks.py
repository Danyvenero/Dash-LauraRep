"""
Script para debug dos callbacks - Checklist completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from webapp import app
import json

print("🔍 CHECKLIST DE DEPURAÇÃO DE CALLBACKS")
print("=" * 50)

print("\n1️⃣ VERIFICANDO SE CALLBACKS FORAM REGISTRADOS")
print("-" * 40)

# Importa callbacks
try:
    import webapp.callbacks
    print("✅ Módulo webapp.callbacks importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar callbacks: {e}")
    exit(1)

# Verifica callback_map
print(f"\n📋 Total de callbacks registrados: {len(app.callback_map)}")

for callback_id, callback_info in app.callback_map.items():
    print(f"\n🔗 Callback: {callback_id}")
    
    # Outputs
    outputs = callback_info.get('output', [])
    if not isinstance(outputs, list):
        outputs = [outputs]
    print(f"   📤 Outputs: {len(outputs)}")
    for out in outputs:
        print(f"      • {out['id']}.{out['property']}")
    
    # Inputs
    inputs = callback_info.get('inputs', [])
    print(f"   📥 Inputs: {len(inputs)}")
    for inp in inputs:
        print(f"      • {inp['id']}.{inp['property']}")
    
    # States
    states = callback_info.get('state', [])
    if states:
        print(f"   📊 States: {len(states)}")
        for state in states:
            print(f"      • {state['id']}.{state['property']}")

print("\n2️⃣ VERIFICANDO CALLBACKS ESPECÍFICOS")
print("-" * 40)

# Procura por callbacks específicos
target_callbacks = [
    "kpi-entrada-pedidos.children",
    "global-filtro-cliente.options", 
    "evolution-chart.figure"
]

for target in target_callbacks:
    found = False
    for callback_id, callback_info in app.callback_map.items():
        outputs = callback_info.get('output', [])
        if not isinstance(outputs, list):
            outputs = [outputs]
        
        for out in outputs:
            if f"{out['id']}.{out['property']}" == target:
                print(f"✅ {target} - ENCONTRADO")
                found = True
                break
        if found:
            break
    
    if not found:
        print(f"❌ {target} - NÃO ENCONTRADO")

print("\n3️⃣ TESTANDO CARREGAMENTO DE DADOS")
print("-" * 40)

try:
    from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
    
    vendas_df = load_vendas_data()
    cotacoes_df = load_cotacoes_data()
    produtos_df = load_produtos_cotados_data()
    
    print(f"✅ Vendas: {len(vendas_df)} registros")
    print(f"✅ Cotações: {len(cotacoes_df)} registros")
    print(f"✅ Produtos: {len(produtos_df)} registros")
    
    if len(vendas_df) > 0:
        print(f"📊 Colunas vendas: {list(vendas_df.columns)[:5]}...")
        
except Exception as e:
    print(f"❌ Erro ao carregar dados: {e}")

print("\n4️⃣ VERIFICANDO CONFIGURAÇÕES DO APP")
print("-" * 40)

print(f"suppress_callback_exceptions: {getattr(app.config, 'suppress_callback_exceptions', 'Não definido')}")
print(f"Debug mode: {getattr(app.server, 'debug', 'Não definido')}")

print("\n" + "=" * 50)
print("🏁 CHECKLIST CONCLUÍDO")
