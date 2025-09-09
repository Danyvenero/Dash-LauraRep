import pandas as pd
import os
import sys

# Simular dados de teste
test_data = {
    'Código do Cliente': ['CLI001', 'CLI002'],  
    'Referência do Cliente': ['REF001', 'REF002'], 
    'Material': ['MAT001', 'MAT002']
}

df = pd.DataFrame(test_data)
print("DataFrame original:")
print(df)
print("\nColunas originais:", df.columns.tolist())

# Mapeamento de colunas (versão corrigida)
column_mapping = {
    'código do cliente': 'cod_cliente',
    'codigo do cliente': 'cod_cliente', 
    'código cliente': 'cod_cliente',
    'codigo_cliente': 'cod_cliente',
    'cod cliente': 'cod_cliente',
    'id_cli': 'cod_cliente',
    # REMOVIDO: 'referência do cliente': 'cod_cliente', (INCORRETO)
    # REMOVIDO: 'referencia do cliente': 'cod_cliente', (INCORRETO)
    'material': 'material'
}

# Normalizar nomes das colunas
df_normalized = df.copy()
df_normalized.columns = [col.strip().lower() for col in df_normalized.columns]

print("\nColunas após normalização:", df_normalized.columns.tolist())

# Renomear colunas baseado no mapeamento
df_normalized = df_normalized.rename(columns=column_mapping)

print("\nDataFrame final:")
print(df_normalized)
print("\nColunas finais:", df_normalized.columns.tolist())

if 'cod_cliente' in df_normalized.columns:
    print(f"\nValores em cod_cliente: {df_normalized['cod_cliente'].tolist()}")
    print("✅ SUCESSO: cod_cliente mapeado corretamente!")
else:
    print("\n❌ ERRO: cod_cliente não foi mapeado!")
