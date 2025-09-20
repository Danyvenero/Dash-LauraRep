#!/usr/bin/env python3
"""
Debug específico para extração de features ML
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils import load_all_data

def debug_features():
    """Debug da extração de features"""
    print("🔍 DEBUG: Extração de Features ML")
    print("="*50)
    
    # Carrega dados
    vendas_df, cotacoes_df, produtos_df = load_all_data()
    
    print(f"📊 Dados carregados: {len(vendas_df)} vendas")
    print(f"📋 Colunas vendas: {list(vendas_df.columns)}")
    
    # Verifica datas
    vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'], errors='coerce')
    vendas_df = vendas_df.dropna(subset=['data_faturamento'])
    
    print(f"📅 Após filtro de datas: {len(vendas_df)} registros")
    print(f"📅 Período de dados: {vendas_df['data_faturamento'].min()} a {vendas_df['data_faturamento'].max()}")
    
    # Verifica agrupamento
    print("\n🔍 Testando agrupamento...")
    try:
        grouped = vendas_df.groupby(['material', 'cod_cliente'])
        print(f"✅ Agrupamento funcionou: {len(grouped)} grupos")
        
        # Testa primeiro grupo
        first_group = next(iter(grouped))
        (material, cod_cliente), grupo = first_group
        
        print(f"📦 Primeiro grupo: Material={material}, Cliente={cod_cliente}")
        print(f"📊 Registros no grupo: {len(grupo)}")
        print(f"🗓️ Datas no grupo: {grupo['data_faturamento'].min()} a {grupo['data_faturamento'].max()}")
        
        # Testa cálculos básicos
        valor_medio = grupo['vlr_rol'].mean()
        print(f"💰 Valor médio: {valor_medio}")
        
        # Testa trimestre
        grupo_copia = grupo.copy()
        grupo_copia['trimestre'] = grupo_copia['data_faturamento'].dt.quarter
        print(f"📊 Trimestres: {grupo_copia['trimestre'].value_counts().to_dict()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no agrupamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_features()