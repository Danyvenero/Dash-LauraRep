#!/usr/bin/env python3
"""
Debug para verificar os dados de unidades de negócio e hierarquias
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import load_vendas_data

print("🔍 Verificando dados completos...")

# Carrega dados completos (sem limit)
vendas_df = load_vendas_data()
print(f"📊 Total de registros: {len(vendas_df)}")
print(f"📊 Colunas: {list(vendas_df.columns)}")

# Verifica unidades de negócio
if 'unidade_negocio' in vendas_df.columns:
    unidades = vendas_df['unidade_negocio'].dropna().unique()
    print(f"\n🏢 UNIDADES DE NEGÓCIO ({len(unidades)}):")
    for i, unidade in enumerate(sorted(unidades), 1):
        count = len(vendas_df[vendas_df['unidade_negocio'] == unidade])
        print(f"   {i}. {unidade} ({count} registros)")
else:
    print("❌ Coluna 'unidade_negocio' não encontrada")

# Verifica hierarquias
for nivel in [1, 2, 3]:
    col = f'hier_produto_{nivel}'
    if col in vendas_df.columns:
        values = vendas_df[col].dropna().unique()
        print(f"\n🏷️ HIERARQUIA NÍVEL {nivel} ({len(values)}):")
        for i, val in enumerate(sorted(values), 1):
            count = len(vendas_df[vendas_df[col] == val])
            print(f"   {i}. {val} ({count} registros)")
    else:
        print(f"❌ Coluna '{col}' não encontrada")

# Testa com limit=1000 (como usado no callback B2B)
print(f"\n" + "="*60)
print("🔍 Verificando dados com LIMIT=1000 (como no callback B2B)...")

vendas_limited = load_vendas_data(limit=1000)
print(f"📊 Total de registros limitados: {len(vendas_limited)}")

# Verifica unidades limitadas
unidades_limited = vendas_limited['unidade_negocio'].dropna().unique()
print(f"\n🏢 UNIDADES COM LIMIT=1000 ({len(unidades_limited)}):")
for unidade in sorted(unidades_limited):
    count = len(vendas_limited[vendas_limited['unidade_negocio'] == unidade])
    print(f"   - {unidade} ({count} registros)")

# Verifica se a limitação está afetando a diversidade
print(f"\n🔍 ANÁLISE DO PROBLEMA:")
print(f"   - Unidades totais: {len(unidades)} vs limitadas: {len(unidades_limited)}")
print(f"   - Diferença: {set(unidades) - set(unidades_limited)}")