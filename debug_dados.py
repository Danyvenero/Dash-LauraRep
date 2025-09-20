#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from utils.db import get_connection
from utils.data_standardization import apply_vendas_standardization
import pandas as pd

print("=== TESTE: Verificação de Dados e Padronização ===")

# 1. Dados brutos do banco
print("\n1. DADOS BRUTOS DO BANCO:")
conn = get_connection()
df_raw = pd.read_sql_query("SELECT * FROM vendas LIMIT 50", conn)
conn.close()

print(f"Shape: {df_raw.shape}")
if 'unidade_negocio' in df_raw.columns:
    unidades_raw = df_raw['unidade_negocio'].dropna().unique()
    print(f"Unidades brutas: {list(unidades_raw)}")

if 'hier_produto_1' in df_raw.columns:
    hier1_raw = df_raw['hier_produto_1'].dropna().unique()
    print(f"Hier1 brutas: {list(hier1_raw)[:3]}")

# 2. Dados após padronização manual
print("\n2. DADOS APÓS PADRONIZAÇÃO MANUAL:")
df_padronizado = apply_vendas_standardization(df_raw.copy())
print(f"Shape: {df_padronizado.shape}")

if 'unidade_negocio' in df_padronizado.columns:
    unidades_pad = df_padronizado['unidade_negocio'].dropna().unique()
    print(f"Unidades padronizadas: {list(unidades_pad)}")

if 'hier_produto_1' in df_padronizado.columns:
    hier1_pad = df_padronizado['hier_produto_1'].dropna().unique()
    print(f"Hier1 padronizadas: {list(hier1_pad)[:3]}")

# 3. Dados via load_vendas_data
print("\n3. DADOS VIA LOAD_VENDAS_DATA:")
from utils import load_vendas_data
df_loaded = load_vendas_data(limit=50)
print(f"Shape: {df_loaded.shape}")

if 'unidade_negocio' in df_loaded.columns:
    unidades_loaded = df_loaded['unidade_negocio'].dropna().unique()
    print(f"Unidades via load: {list(unidades_loaded)}")

if 'hier_produto_1' in df_loaded.columns:
    hier1_loaded = df_loaded['hier_produto_1'].dropna().unique()
    print(f"Hier1 via load: {list(hier1_loaded)[:3]}")

print("\n=== CONCLUSÃO ===")
print("Se 'Unidades via load' ainda mostra nomes longos, a padronização não está sendo aplicada no load_vendas_data")