#!/usr/bin/env python3
"""
Script para testar o mapeamento correto de colunas para cod_cliente
"""

import pandas as pd
import sys
import os

# Adiciona o diretório pai ao path para importar utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader_fixed import normalize_column_names

def test_column_mapping():
    """Testa o mapeamento de colunas para cod_cliente"""
    
    print("🧪 TESTE DE MAPEAMENTO DE COLUNAS - cod_cliente")
    print("=" * 60)
    
    # Teste 1: Colunas que DEVEM ser mapeadas para cod_cliente
    correct_columns = [
        'Código do Cliente',
        'codigo do cliente', 
        'ID_Cli',
        'id_cli',
        'Código Cliente',
        'codigo_cliente',
        'Cod Cliente',
        'cod cliente'
    ]
    
    print("✅ COLUNAS CORRETAS (devem mapear para cod_cliente):")
    for col in correct_columns:
        df_test = pd.DataFrame({col: ['TEST001']})
        df_normalized = normalize_column_names(df_test)
        if 'cod_cliente' in df_normalized.columns:
            print(f"   ✅ '{col}' → 'cod_cliente' ✓")
        else:
            print(f"   ❌ '{col}' → NÃO MAPEADA!")
    
    print("\n" + "=" * 60)
    
    # Teste 2: Colunas que NÃO DEVEM ser mapeadas para cod_cliente  
    incorrect_columns = [
        'Referência do Cliente',
        'referencia do cliente',
        'Ref Cliente',
        'ref cliente'
    ]
    
    print("❌ COLUNAS INCORRETAS (NÃO devem mapear para cod_cliente):")
    for col in incorrect_columns:
        df_test = pd.DataFrame({col: ['REF001']})
        df_normalized = normalize_column_names(df_test)
        if 'cod_cliente' in df_normalized.columns:
            print(f"   ❌ '{col}' → 'cod_cliente' (ERRO - deve ser corrigido!)")
        else:
            print(f"   ✅ '{col}' → NÃO MAPEADA ✓")
    
    print("\n" + "=" * 60)
    
    # Teste 3: Simulação de planilha real
    print("📊 TESTE COM DADOS SIMULADOS:")
    
    test_data = {
        'Código do Cliente': ['CLI001', 'CLI002', 'CLI003'],
        'Referência do Cliente': ['REF001', 'REF002', 'REF003'],
        'Cliente': ['Cliente A', 'Cliente B', 'Cliente C'],
        'Material': ['MAT001', 'MAT002', 'MAT003']
    }
    
    df_test = pd.DataFrame(test_data)
    print(f"\n🔍 DataFrame original:")
    print(df_test.head())
    
    df_normalized = normalize_column_names(df_test)
    print(f"\n🔄 DataFrame após normalização:")
    print(df_normalized.head())
    
    if 'cod_cliente' in df_normalized.columns:
        print(f"\n✅ Valores em cod_cliente: {df_normalized['cod_cliente'].tolist()}")
        if df_normalized['cod_cliente'].tolist() == ['CLI001', 'CLI002', 'CLI003']:
            print("✅ SUCESSO: cod_cliente contém valores corretos do 'Código do Cliente'")
        else:
            print("❌ ERRO: cod_cliente contém valores incorretos!")
    else:
        print("\n❌ ERRO: Coluna cod_cliente não foi criada!")

if __name__ == "__main__":
    test_column_mapping()
