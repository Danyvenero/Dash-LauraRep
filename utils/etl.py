# utils/etl.py

import pandas as pd
from utils import db
import numpy as np

def transform_vendas():
    print("Iniciando ETL de Vendas...")
    df_raw = db.get_raw_data_as_df('raw_vendas')
    if df_raw.empty:
        print("Nenhum dado bruto de vendas para processar.")
        return 0
    
    df_raw.replace('#', pd.NA, inplace=True)
    
    df_raw.rename(columns={
        'ID_Cli': 'cod_cliente', 'Cliente': 'cliente', 'Material': 'material', 'Produto': 'produto',
        'Unidade de Negócio': 'unidade_negocio', 'Data': 'data_entrada', 
        'Data Faturamento': 'data_faturamento', 'Qtd. Entrada': 'quantidade_entrada', 
        'Qtd. Carteira': 'quantidade_carteira', 'Qtd. ROL': 'quantidade_faturada', 
        'Vlr. Entrada': 'valor_entrada', 'Vlr. Carteira': 'valor_carteira', 'Vlr. ROL': 'valor_faturado',
        'Canal Distribuição': 'canal_distribuicao',
        'Cód. Cliente': 'cod_cliente', 'Data Fat.': 'data_faturamento'  # Adicionar mapeamentos alternativos
    }, inplace=True)

    final_cols = [
        'cod_cliente', 'cliente', 'material', 'produto', 'unidade_negocio', 
        'canal_distribuicao',
        'data_entrada', 'data_faturamento', 'quantidade_entrada', 'quantidade_carteira', 
        'quantidade_faturada', 'valor_entrada', 'valor_carteira', 'valor_faturado'
    ]
    df_clean = pd.DataFrame(columns=final_cols)
    for col in final_cols:
        if col in df_raw.columns:
            df_clean[col] = df_raw[col]

    numeric_cols = [
        'quantidade_entrada', 'quantidade_carteira', 'quantidade_faturada',
        'valor_entrada', 'valor_carteira', 'valor_faturado'
    ]
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    date_cols = ['data_entrada', 'data_faturamento']
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce', dayfirst=True)
    
    if 'cod_cliente' in df_clean.columns:
        df_clean['cod_cliente'] = df_clean['cod_cliente'].astype(str)
    
    df_clean.dropna(subset=['cod_cliente'], inplace=True)
    
    db.truncate_table('vendas')
    rows_inserted = db.save_clean_df(df_clean, 'vendas')
    print(f"ETL de Vendas concluído. {rows_inserted} registros inseridos.")
    return rows_inserted

def transform_cotacoes():
    print("Iniciando ETL de Cotações...")
    df_materiais = db.get_raw_data_as_df('raw_materiais_cotados')
    df_propostas = db.get_raw_data_as_df('raw_propostas_anuais')
    if df_materiais.empty or df_propostas.empty:
        print("Dados brutos de materiais ou propostas insuficientes para processar.")
        return 0

    df_propostas = df_propostas[~df_propostas['Status da Cotação'].isin(['Perdido', 'Cancelado'])]
    df_propostas.rename(columns={'Número da Cotação': 'Cotação'}, inplace=True)
    df_materiais['Cotação'] = df_materiais['Cotação'].astype(str)
    df_propostas['Cotação'] = df_propostas['Cotação'].astype(str)
    df_propostas_datas = df_propostas[['Cotação', 'Data de Criação']].drop_duplicates()
    df_merged = pd.merge(df_materiais, df_propostas_datas, on='Cotação', how='left')
    df_merged.rename(columns={'Cod. Cliente': 'cod_cliente', 'Cliente': 'cliente', 'Material': 'material', 'Data de Criação': 'data', 'Quantidade': 'quantidade'}, inplace=True)
    final_cols = ['cod_cliente', 'cliente', 'material', 'data', 'quantidade']
    df_clean = df_merged[[col for col in final_cols if col in df_merged.columns]].copy()
    df_clean['data'] = pd.to_datetime(df_clean['data'], errors='coerce', dayfirst=True)
    df_clean['quantidade'] = pd.to_numeric(df_clean['quantidade'], errors='coerce')
    df_clean.dropna(subset=['data', 'cod_cliente', 'material', 'quantidade'], inplace=True)
    db.truncate_table('cotacoes')
    rows_inserted = db.save_clean_df(df_clean, 'cotacoes')
    print(f"ETL de Cotações concluído. {rows_inserted} registros inseridos.")
    return rows_inserted

def run_full_etl():
    vendas_count = transform_vendas()
    cotacoes_count = transform_cotacoes()
    return f"Processo concluído! Vendas: {vendas_count} registros. Cotações: {cotacoes_count} registros."