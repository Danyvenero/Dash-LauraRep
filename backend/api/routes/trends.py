"""
Rotas para análise de tendências e sazonalidade
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.routes.auth import get_current_user
from utils.db import get_clean_vendas_as_df

router = APIRouter()


@router.get("/mensal")
async def get_trends_mensal(
    meses: int = Query(12, ge=1, le=24),
    current_user: dict = Depends(get_current_user)
):
    """Retorna tendência mensal dos últimos N meses"""
    df_vendas = get_clean_vendas_as_df()
    
    if df_vendas.empty:
        return []
    
    # Filtrar últimos N meses
    df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'])
    data_limite = pd.Timestamp.now() - pd.DateOffset(months=meses)
    df_filtered = df_vendas[df_vendas['data_faturamento'] >= data_limite]
    
    # Agrupar por mês
    df_filtered['ano_mes'] = df_filtered['data_faturamento'].dt.to_period('M').astype(str)
    
    trends = df_filtered.groupby('ano_mes').agg({
        'valor_entrada': 'sum',
        'valor_carteira': 'sum',
        'valor_faturado': 'sum',
    }).reset_index()
    
    trends.columns = ['mes', 'entrada', 'carteira', 'faturamento']
    trends = trends.sort_values('mes')
    
    return trends.to_dict('records')


@router.get("/sazonalidade")
async def get_sazonalidade(
    ano_inicio: int = Query(2020, ge=2020),
    ano_fim: int = Query(2025, le=2025),
    current_user: dict = Depends(get_current_user)
):
    """Retorna análise de sazonalidade por mês"""
    df_vendas = get_clean_vendas_as_df()
    
    if df_vendas.empty:
        return {
            "meses": [],
            "media_mensal": [],
            "desvio_padrao": []
        }
    
    # Filtrar por período
    df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'])
    df_vendas['ano'] = df_vendas['data_faturamento'].dt.year
    df_vendas['mes'] = df_vendas['data_faturamento'].dt.month
    
    df_filtered = df_vendas[
        (df_vendas['ano'] >= ano_inicio) & 
        (df_vendas['ano'] <= ano_fim)
    ]
    
    # Agrupar por mês
    sazonalidade = df_filtered.groupby('mes').agg({
        'valor_faturado': ['mean', 'std', 'sum']
    }).reset_index()
    
    sazonalidade.columns = ['mes', 'media', 'desvio', 'total']
    
    meses_nomes = [
        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
    ]
    
    sazonalidade['mes_nome'] = sazonalidade['mes'].apply(lambda x: meses_nomes[x-1])
    sazonalidade = sazonalidade.sort_values('mes')
    
    return {
        "meses": sazonalidade['mes_nome'].tolist(),
        "media_mensal": sazonalidade['media'].fillna(0).tolist(),
        "desvio_padrao": sazonalidade['desvio'].fillna(0).tolist(),
        "total_mensal": sazonalidade['total'].fillna(0).tolist()
    }
