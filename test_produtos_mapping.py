#!/usr/bin/env python3
"""
Script para testar o mapeamento de "Cod. Cliente" em produtos cotados
"""

import pandas as pd
import sys
import os

# Adiciona o diretório pai ao path para importar utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import DataProcessor

def test_produtos_cotados_mapping():
    """Testa o mapeamento de Cod. Cliente para produtos cotados"""
    
    print("🧪 TESTE DE MAPEAMENTO - Produtos Cotados")
    print("=" * 55)
    
    # Simula dados de produtos cotados
    test_data = {
        'Cotação': ['COT001', 'COT002', 'COT003'],
        'Cod. Cliente': ['CLI001', 'CLI002', 'CLI003'],  # ✅ Coluna com ponto
        'Cliente': ['Cliente A', 'Cliente B', 'Cliente C'],
        'Material': ['MAT001', 'MAT002', 'MAT003'],
        'Descrição': ['Produto A', 'Produto B', 'Produto C'],
        'Quantidade': [10, 20, 30],
        'Preço Líquido Unitário': [100.0, 200.0, 300.0]
    }
    
    df = pd.DataFrame(test_data)
    print("📊 DataFrame original (Produtos Cotados):")
    print(df)
    print()
    
    # Processa usando DataProcessor
    processor = DataProcessor()
    
    try:
        df_normalized = processor.normalize_produtos_cotados_data(df)
        
        print("📋 DataFrame após processamento:")
        print(df_normalized)
        print()
        print(f"🔍 Colunas finais: {list(df_normalized.columns)}")
        print()
        
        if 'cod_cliente' in df_normalized.columns:
            cod_cliente_values = df_normalized['cod_cliente'].tolist()
            print(f"✅ SUCESSO: cod_cliente mapeado!")
            print(f"   Valores: {cod_cliente_values}")
            
            expected_values = ['CLI001', 'CLI002', 'CLI003']
            if cod_cliente_values == expected_values:
                print(f"✅ PERFEITO: Valores corretos da coluna 'Cod. Cliente'!")
                return True
            else:
                print(f"❌ ERRO: Valores incorretos!")
                print(f"   Esperado: {expected_values}")
                print(f"   Atual: {cod_cliente_values}")
                return False
        else:
            print("❌ ERRO: cod_cliente NÃO foi mapeado!")
            print(f"   Colunas disponíveis: {list(df_normalized.columns)}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO durante processamento: {e}")
        return False

if __name__ == "__main__":
    success = test_produtos_cotados_mapping()
    print("\n" + "=" * 55)
    if success:
        print("🎉 TESTE PASSOU: Mapeamento funcionando corretamente!")
    else:
        print("❌ TESTE FALHOU: Mapeamento precisa ser corrigido!")
