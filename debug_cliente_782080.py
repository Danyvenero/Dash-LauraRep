#!/usr/bin/env python3
"""
Script para investigar diferenças nos valores do cliente 782080
"""

import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

# Adicionar o diretório utils ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils import db, kpis

def investigar_cliente_782080():
    print("=== INVESTIGAÇÃO CLIENTE 782080 ===")
    
    # 1. Verificar dados brutos (raw_vendas)
    print("\n1. DADOS RAW_VENDAS:")
    try:
        df_raw = db.get_raw_data_as_df('raw_vendas')
        if not df_raw.empty:
            # Filtrar para cliente 782080
            cliente_raw = df_raw[df_raw['Cód. Cliente'] == 782080]
            print(f"Registros no raw_vendas para cliente 782080: {len(cliente_raw)}")
            
            # Verificar ano 2024
            if 'Data Fat.' in cliente_raw.columns:
                cliente_raw['Data Fat.'] = pd.to_datetime(cliente_raw['Data Fat.'], errors='coerce')
                cliente_2024 = cliente_raw[cliente_raw['Data Fat.'].dt.year == 2024]
                print(f"Registros de 2024: {len(cliente_2024)}")
                
                # Somar valores usando Vlr. ROL
                if 'Vlr. ROL' in cliente_2024.columns:
                    total_vlr_rol = cliente_2024['Vlr. ROL'].sum()
                    print(f"Total Vlr. ROL em 2024: {total_vlr_rol:,.2f}")
                
                # Mostrar alguns registros
                print("\nPrimeiros 5 registros de 2024:")
                colunas_exibir = ['Data Fat.', 'Vlr. ROL', 'Material', 'Hier. Produto 1']
                colunas_disponiveis = [col for col in colunas_exibir if col in cliente_2024.columns]
                if colunas_disponiveis:
                    print(cliente_2024[colunas_disponiveis].head())
    except Exception as e:
        print(f"Erro ao verificar raw_vendas: {e}")
    
    # 2. Verificar dados limpos (vendas)
    print("\n2. DADOS TABELA VENDAS:")
    try:
        df_vendas = db.get_clean_vendas_as_df()
        if not df_vendas.empty:
            print(f"Colunas disponíveis: {df_vendas.columns.tolist()}")
            
            # Filtrar para cliente 782080
            cliente_vendas = df_vendas[df_vendas['cod_cliente'] == 782080]
            print(f"Registros na tabela vendas para cliente 782080: {len(cliente_vendas)}")
            
            # Verificar ano 2024
            if 'data_faturamento' in cliente_vendas.columns:
                cliente_vendas['data_faturamento'] = pd.to_datetime(cliente_vendas['data_faturamento'], errors='coerce')
                cliente_2024 = cliente_vendas[cliente_vendas['data_faturamento'].dt.year == 2024]
                print(f"Registros de 2024: {len(cliente_2024)}")
                
                # Verificar qual coluna de valor está sendo usada
                colunas_valor = ['valor_faturado', 'valor_liquido', 'valor', 'ROL', 'rol']
                for col in colunas_valor:
                    if col in cliente_2024.columns:
                        total_valor = cliente_2024[col].sum()
                        print(f"Total {col} em 2024: {total_valor:,.2f}")
                
                # Mostrar alguns registros
                print("\nPrimeiros 5 registros de 2024:")
                colunas_exibir = ['data_faturamento', 'valor_faturado', 'material']
                colunas_disponiveis = [col for col in colunas_exibir if col in cliente_2024.columns]
                if colunas_disponiveis:
                    print(cliente_2024[colunas_disponiveis].head())
    except Exception as e:
        print(f"Erro ao verificar tabela vendas: {e}")
    
    # 3. Testar cálculo de KPIs
    print("\n3. TESTE DE CÁLCULO DE KPIs:")
    try:
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Filtrar para 2024
        if 'data_faturamento' in df_vendas.columns:
            df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
            df_vendas_2024 = df_vendas[df_vendas['data_faturamento'].dt.year == 2024]
            print(f"Total de registros de vendas em 2024: {len(df_vendas_2024)}")
            
            # Calcular KPIs
            df_kpis = kpis.calculate_kpis_por_cliente(df_vendas_2024, df_cotacoes)
            
            # Encontrar cliente 782080
            cliente_kpi = df_kpis[df_kpis['cod_cliente'] == 782080]
            if not cliente_kpi.empty:
                print(f"KPI calculado para cliente 782080:")
                print(f"  total_comprado_valor: {cliente_kpi['total_comprado_valor'].iloc[0]:,.2f}")
                print(f"  total_comprado_qtd: {cliente_kpi['total_comprado_qtd'].iloc[0]:,.2f}")
                print(f"  mix_produtos: {cliente_kpi['mix_produtos'].iloc[0]}")
            else:
                print("Cliente 782080 não encontrado nos KPIs")
    except Exception as e:
        print(f"Erro ao calcular KPIs: {e}")
    
    # 4. Comparar diferenças
    print("\n4. ANÁLISE DE DIFERENÇAS:")
    print("Valor esperado (planilha): 487.339,01")
    print("Valor calculado (dashboard): 453.724,68")
    diferenca = 487339.01 - 453724.68
    print(f"Diferença: {diferenca:,.2f}")
    print(f"Percentual de diferença: {(diferenca/487339.01)*100:.2f}%")

if __name__ == "__main__":
    investigar_cliente_782080()
