#!/usr/bin/env python3
"""
Verificação simples do mapeamento
"""

# Verificar se o mapeamento foi adicionado corretamente
import re

# Ler o arquivo data_loader_fixed.py
with open('utils/data_loader_fixed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Procurar pela função normalize_produtos_cotados_data
func_match = re.search(r'def normalize_produtos_cotados_data.*?(?=def|\Z)', content, re.DOTALL)

if func_match:
    func_content = func_match.group()
    
    print("🔍 VERIFICANDO MAPEAMENTOS EM normalize_produtos_cotados_data:")
    print("=" * 60)
    
    # Verificar se os mapeamentos estão presentes
    cod_cliente_mappings = [
        "'cod. cliente': 'cod_cliente'",
        "'Cod. Cliente': 'cod_cliente'"
    ]
    
    all_found = True
    for mapping in cod_cliente_mappings:
        if mapping in func_content:
            print(f"✅ Encontrado: {mapping}")
        else:
            print(f"❌ FALTANDO: {mapping}")
            all_found = False
    
    print("\n" + "=" * 60)
    if all_found:
        print("✅ SUCESSO: Todos os mapeamentos estão presentes!")
        print("🎯 A coluna 'Cod. Cliente' agora deve ser mapeada corretamente")
    else:
        print("❌ ERRO: Alguns mapeamentos estão faltando!")
else:
    print("❌ ERRO: Função normalize_produtos_cotados_data não encontrada!")

print("\n🔄 Reinicie a aplicação para aplicar as correções.")
