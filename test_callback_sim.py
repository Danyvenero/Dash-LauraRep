#!/usr/bin/env python3
"""
Teste específico para verificar callback dos filtros iniciais
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import load_vendas_data

def test_callback_data():
    """Simula exatamente o que o callback faz"""
    print("🧪 TESTE: Simulação do Callback de Filtros")
    print("=" * 50)
    
    try:
        print("🔍 Buscando dados para filtros iniciais...")
        
        # Carrega dados padronizados (mesmo que o callback)
        vendas_df = load_vendas_data(limit=1000)  # Amostra para filtros
        
        if vendas_df.empty:
            print("❌ Nenhum dado de vendas encontrado")
            return [], []
        
        print(f"📊 Dados carregados: {len(vendas_df)} registros")
        print(f"🏗️ Colunas disponíveis: {list(vendas_df.columns)}")
        
        # Buscar hierarquias de produto nível 1 (já padronizadas)
        if 'hier_produto_1' in vendas_df.columns:
            hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
            hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique)]
            print(f"✅ Hierarquia 1: {len(hier1_options)} opções")
            print("   Primeiras 5 opções:")
            for i, opt in enumerate(hier1_options[:5]):
                print(f"   {i+1}. {opt['label']}")
        else:
            hier1_options = []
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
            unidade_options = []
            print("❌ Coluna unidade_negocio não encontrada")
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   Hierarquia 1: {len(hier1_options)} opções")
        print(f"   Unidade de Negócio: {len(unidade_options)} opções")
        
        return hier1_options, unidade_options
        
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        import traceback
        traceback.print_exc()
        return [], []

if __name__ == "__main__":
    test_callback_data()