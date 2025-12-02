"""
Rotas de KPIs
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.models.schemas import (
    KPIGeralResponse, 
    KPIClienteResponse, 
    FiltrosKPICliente
)
from backend.api.routes.auth import get_current_user
from backend.api.models.database import get_db_connection
from utils.db import get_clean_vendas_as_df, get_clean_cotacoes_as_df
from utils import kpis

router = APIRouter()


@router.get("/gerais", response_model=KPIGeralResponse)
async def get_kpis_gerais(current_user: dict = Depends(get_current_user)):
    """Retorna KPIs gerais"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    kpis_result = kpis.calculate_kpis_gerais(df_vendas, df_cotacoes)
    
    return KPIGeralResponse(**kpis_result)


@router.post("/cliente", response_model=List[KPIClienteResponse])
async def get_kpis_cliente(
    filtros: FiltrosKPICliente,
    current_user: dict = Depends(get_current_user)
):
    """Retorna KPIs por cliente com filtros"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    if df_vendas.empty:
        return []
    
    # Aplicar filtros
    if filtros.ano_inicio or filtros.ano_fim:
        df_vendas['ano'] = pd.to_datetime(df_vendas['data_faturamento']).dt.year
        if filtros.ano_inicio:
            df_vendas = df_vendas[df_vendas['ano'] >= filtros.ano_inicio]
        if filtros.ano_fim:
            df_vendas = df_vendas[df_vendas['ano'] <= filtros.ano_fim]
    
    if filtros.mes_inicio or filtros.mes_fim:
        df_vendas['mes'] = pd.to_datetime(df_vendas['data_faturamento']).dt.month
        if filtros.mes_inicio:
            df_vendas = df_vendas[df_vendas['mes'] >= filtros.mes_inicio]
        if filtros.mes_fim:
            df_vendas = df_vendas[df_vendas['mes'] <= filtros.mes_fim]
    
    if filtros.clientes:
        df_vendas = df_vendas[df_vendas['cod_cliente'].isin(filtros.clientes)]
        df_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'].isin(filtros.clientes)]
    
    # Calcular KPIs
    df_kpis = kpis.calculate_kpis_por_cliente(df_vendas, df_cotacoes)
    
    if df_kpis.empty:
        return []
    
    # Aplicar filtros adicionais
    if filtros.dias_sem_compra_min is not None:
        df_kpis = df_kpis[df_kpis['dias_sem_compra'] >= filtros.dias_sem_compra_min]
    if filtros.dias_sem_compra_max is not None:
        df_kpis = df_kpis[df_kpis['dias_sem_compra'] <= filtros.dias_sem_compra_max]
    
    # Top N
    if filtros.top_n:
        df_kpis = df_kpis.head(filtros.top_n)
    
    # Converter para lista de dicts
    result = df_kpis.to_dict('records')
    
    return [KPIClienteResponse(**row) for row in result]


@router.get("/funil")
async def get_funil_metrics(
    periodo_meses: int = Query(12, ge=1, le=24),
    threshold_conversao: float = Query(20, ge=0, le=100),
    threshold_dias_risco: int = Query(90, ge=30, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Retorna métricas do funil de conversão"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    funil_data = kpis.calculate_funil_metrics(
        df_vendas, 
        df_cotacoes, 
        periodo_meses=periodo_meses,
        threshold_conversao=threshold_conversao,
        threshold_dias_risco=threshold_dias_risco
    )
    
    # Converter DataFrames para listas de dicts
    funil_data['lista_a'] = funil_data['lista_a'].to_dict('records') if not funil_data['lista_a'].empty else []
    funil_data['lista_b'] = funil_data['lista_b'].to_dict('records') if not funil_data['lista_b'].empty else []
    
    return funil_data


@router.get("/produtos/matrix")
async def get_produtos_matrix(
    top_produtos: int = Query(20, ge=5, le=100),
    top_clientes: int = Query(15, ge=5, le=50),
    ano: Optional[int] = None,
    unidade_negocio: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retorna matriz de produtos vs clientes para gráfico de bolhas"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    # Aplicar filtros
    if ano:
        df_vendas['ano'] = pd.to_datetime(df_vendas['data_faturamento']).dt.year
        df_vendas = df_vendas[df_vendas['ano'] == ano]
        df_cotacoes['ano'] = pd.to_datetime(df_cotacoes['data']).dt.year
        df_cotacoes = df_cotacoes[df_cotacoes['ano'] == ano]
    
    if unidade_negocio:
        df_vendas = df_vendas[df_vendas['unidade_negocio'].isin(unidade_negocio)]
    
    matrix = kpis.calculate_produtos_matrix(
        df_vendas, 
        df_cotacoes, 
        top_produtos=top_produtos,
        top_clientes=top_clientes
    )
    
    if matrix.empty:
        return []
    
    return matrix.to_dict('records')
