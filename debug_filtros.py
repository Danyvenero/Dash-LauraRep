#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection
from utils.data_standardization import apply_vendas_standardization
import pandas as pd

# Teste simples e direto
conn = get_connection()
df_raw = pd.read_sql_query("SELECT * FROM vendas LIMIT 100", conn)
conn.close()

print(f"Dados brutos: {len(df_raw)} registros")
print(f"Colunas: {list(df_raw.columns)}")

# Aplica padronização
df_std = apply_vendas_standardization(df_raw.copy())
print(f"Dados padronizados: {len(df_std)} registros")

# Verifica hierarquia 1
if 'hier_produto_1' in df_std.columns:
    hier1 = df_std['hier_produto_1'].dropna().unique()
    print(f"Hierarquia 1: {len(hier1)} valores -> {list(hier1)[:5]}")

# Verifica unidade
if 'unidade_negocio' in df_std.columns:
    unidades = df_std['unidade_negocio'].dropna().unique()
    print(f"Unidades: {len(unidades)} valores -> {list(unidades)}")