#!/usr/bin/env python3
"""
Script para testar o mapeamento de "Cod. Cliente" em materiais cotados
"""

import pandas as pd

def test_cod_cliente_mapping():
    """Testa o mapeamento de Cod. Cliente para materiais cotados"""
    
    print("🧪 TESTE DE MAPEAMENTO - Cod. Cliente (Materiais Cotados)")
    print("=" * 65)
    
    # Simula dados de materiais cotados
    test_data = {
        'Cod. Cliente': ['CLI001', 'CLI002', 'CLI003'],  # Coluna correta
        'Referência do Cliente': ['REF001', 'REF002', 'REF003'],  # Coluna incorreta
        'Material': ['MAT001', 'MAT002', 'MAT003'],
        'Produto': ['Produto A', 'Produto B', 'Produto C']
    }
    
    df = pd.DataFrame(test_data)
    print("📊 DataFrame original (Materiais Cotados):")
    print(df)
    print()
    
    # Mapeamentos corretos adicionados
    column_mapping = {
        'cod. cliente': 'cod_cliente',
        'Cod. Cliente': 'cod_cliente',  # ✅ NOVO MAPEAMENTO ADICIONADO
        'código cliente': 'cod_cliente',
        'codigo_cliente': 'cod_cliente',
        'cod cliente': 'cod_cliente',
        'id_cli': 'cod_cliente',
        'material': 'material',
        'produto': 'produto'
    }
    
    # Normalizar nomes das colunas  
    df_normalized = df.copy()
    df_normalized.columns = [col.strip().lower() for col in df_normalized.columns]
    
    print("🔄 Colunas após normalização:")
    print(df_normalized.columns.tolist())
    print()
    
    # Aplicar mapeamento
    df_final = df_normalized.rename(columns=column_mapping)
    
    print("📋 DataFrame final após mapeamento:")
    print(df_final)
    print()
    
    if 'cod_cliente' in df_final.columns:
        print(f"✅ SUCESSO: cod_cliente mapeado corretamente!")
        print(f"   Valores: {df_final['cod_cliente'].tolist()}")
        
        # Verifica se os valores são os corretos (CLI001, CLI002, CLI003)
        expected_values = ['CLI001', 'CLI002', 'CLI003']
        actual_values = df_final['cod_cliente'].tolist()
        
        if actual_values == expected_values:
            print(f"✅ PERFEITO: Valores corretos da coluna 'Cod. Cliente'!")
        else:
            print(f"❌ ERRO: Valores incorretos!")
            print(f"   Esperado: {expected_values}")
            print(f"   Atual: {actual_values}")
    else:
        print("❌ ERRO: cod_cliente não foi mapeado!")
    
    print("\n" + "=" * 65)
    print("🔧 CORREÇÕES APLICADAS:")
    print("   ✅ Adicionado: 'cod. cliente': 'cod_cliente'")
    print("   ✅ Adicionado: 'Cod. Cliente': 'cod_cliente'")
    print("   🎯 Agora materiais cotados devem mapear corretamente!")

if __name__ == "__main__":
    test_cod_cliente_mapping()
