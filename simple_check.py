import sys
import os
sys.path.append(os.getcwd())

from utils import db
import pandas as pd

print("=== VERIFICAÇÃO SIMPLES ===")

# 1. Carregar dados limpos
try:
    df_vendas = db.get_clean_vendas_as_df()
    print(f"Total de registros: {len(df_vendas)}")
    print(f"Colunas: {df_vendas.columns.tolist()}")
    
    # 2. Filtrar por 2024  
    df_2024 = df_vendas[df_vendas['data_faturamento'].dt.year == 2024]
    print(f"Registros 2024: {len(df_2024)}")
    
    # 3. Cliente 782080
    cliente_782080 = df_2024[df_2024['cod_cliente'] == '782080']
    print(f"Cliente 782080 registros: {len(cliente_782080)}")
    
    if len(cliente_782080) > 0:
        valor_total = cliente_782080['valor_faturado'].sum()
        print(f"Valor total 782080: {valor_total:,.2f}")
        
        # Verificar se há valores nulos
        nulos = cliente_782080['valor_faturado'].isnull().sum()
        print(f"Valores nulos: {nulos}")
        
        # Verificar valores negativos
        negativos = (cliente_782080['valor_faturado'] < 0).sum()
        print(f"Valores negativos: {negativos}")
        
    else:
        print("ERRO: Cliente 782080 não encontrado")
        
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
