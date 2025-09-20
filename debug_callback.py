#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils import load_vendas_data

print("=== SIMULAÇÃO DO CALLBACK DE FILTROS ===")

# Simula exatamente o que o callback faz
try:
    print("🔍 Buscando dados para filtros iniciais...")
    
    # Carrega dados padronizados (mesmo que o callback)
    vendas_df = load_vendas_data(limit=1000)
    
    if vendas_df.empty:
        print("❌ Nenhum dado de vendas encontrado")
    else:
        print(f"📊 Dados carregados: {len(vendas_df)} registros")
        
        # Buscar hierarquias de produto nível 1 (já padronizadas)
        if 'hier_produto_1' in vendas_df.columns:
            hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
            hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique)]
            print(f"✅ Hierarquia 1: {len(hier1_options)} opções")
            print("   Primeiras 5 opções:")
            for i, opt in enumerate(hier1_options[:5]):
                print(f"   {i+1}. {opt['label']}")
        else:
            print("❌ Coluna hier_produto_1 não encontrada")
        
        # Buscar unidades de negócio (já padronizadas)
        if 'unidade_negocio' in vendas_df.columns:
            unidade_unique = vendas_df['unidade_negocio'].dropna().unique()
            unidade_options = [{"label": unidade, "value": unidade} for unidade in sorted(unidade_unique)]
            print(f"✅ Unidade de negócio: {len(unidade_options)} opções")
            print("   Opções encontradas:")
            for i, opt in enumerate(unidade_options):
                print(f"   {i+1}. {opt['label']}")
        else:
            print("❌ Coluna unidade_negocio não encontrada")
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   return [{len(hier1_options)} hier1_options], [{len(unidade_options)} unidade_options]")

except Exception as e:
    print(f"❌ Erro na simulação: {e}")
    import traceback
    traceback.print_exc()