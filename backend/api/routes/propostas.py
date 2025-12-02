"""
Rotas para análise de propostas
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.routes.auth import get_current_user
from backend.api.models.database import get_db_connection
from utils.db import get_clean_vendas_as_df, get_clean_cotacoes_as_df
from utils import kpis

router = APIRouter()


@router.get("/comparativo")
async def get_comparativo_propostas(
    ano_inicio: int = Query(2020, ge=2020, le=2025),
    ano_fim: int = Query(2025, ge=2020, le=2025),
    mes_inicio: int = Query(1, ge=1, le=12),
    mes_fim: int = Query(12, ge=1, le=12),
    top_n: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Retorna dados comparativos de propostas vs vendas"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    if df_cotacoes.empty:
        return {
            "clientes": [],
            "resumo": {
                "total_cotado": 0,
                "total_comprado": 0,
                "taxa_conversao": 0
            }
        }
    
    # Filtrar por período
    if 'data' in df_cotacoes.columns:
        df_cotacoes['ano'] = pd.to_datetime(df_cotacoes['data']).dt.year
        df_cotacoes['mes'] = pd.to_datetime(df_cotacoes['data']).dt.month
        df_cotacoes = df_cotacoes[
            (df_cotacoes['ano'] >= ano_inicio) & 
            (df_cotacoes['ano'] <= ano_fim) &
            (df_cotacoes['mes'] >= mes_inicio) &
            (df_cotacoes['mes'] <= mes_fim)
        ]
    
    # Agrupar por cliente
    cotacoes_por_cliente = df_cotacoes.groupby(['cod_cliente', 'cliente']).agg({
        'quantidade': 'sum'
    }).reset_index()
    
    if not df_vendas.empty:
        vendas_por_cliente = df_vendas.groupby('cod_cliente').agg({
            'quantidade_faturada': 'sum',
            'valor_faturado': 'sum'
        }).reset_index()
        
        # Merge
        comparativo = pd.merge(
            cotacoes_por_cliente,
            vendas_por_cliente,
            on='cod_cliente',
            how='left'
        )
        comparativo['quantidade_faturada'] = comparativo['quantidade_faturada'].fillna(0)
        comparativo['valor_faturado'] = comparativo['valor_faturado'].fillna(0)
        comparativo['pct_conversao'] = (
            (comparativo['quantidade_faturada'] / comparativo['quantidade']) * 100
        ).fillna(0)
    else:
        comparativo = cotacoes_por_cliente.copy()
        comparativo['quantidade_faturada'] = 0
        comparativo['valor_faturado'] = 0
        comparativo['pct_conversao'] = 0
    
    # Top N
    comparativo = comparativo.sort_values('quantidade', ascending=False).head(top_n)
    
    # Resumo
    total_cotado = comparativo['quantidade'].sum()
    total_comprado = comparativo['quantidade_faturada'].sum()
    taxa_conversao = (total_comprado / total_cotado * 100) if total_cotado > 0 else 0
    
    return {
        "clientes": comparativo.to_dict('records'),
        "resumo": {
            "total_cotado": float(total_cotado),
            "total_comprado": float(total_comprado),
            "taxa_conversao": round(taxa_conversao, 2)
        }
    }


@router.get("/heatmap")
async def get_heatmap_propostas(
    ano_inicio: int = Query(2020, ge=2020, le=2025),
    ano_fim: int = Query(2025, ge=2020, le=2025),
    top_clientes: int = Query(15, ge=5, le=50),
    top_produtos: int = Query(20, ge=5, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Retorna dados para heatmap cliente x produto"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    if df_cotacoes.empty:
        return {
            "data": [],
            "clientes": [],
            "produtos": []
        }
    
    # Filtrar por período
    if 'data' in df_cotacoes.columns:
        df_cotacoes['ano'] = pd.to_datetime(df_cotacoes['data']).dt.year
        df_cotacoes = df_cotacoes[
            (df_cotacoes['ano'] >= ano_inicio) & 
            (df_cotacoes['ano'] <= ano_fim)
        ]
    
    # Top clientes e produtos
    top_clientes_list = df_cotacoes.groupby(['cod_cliente', 'cliente'])['quantidade'].sum().nlargest(top_clientes).index
    top_produtos_list = df_cotacoes.groupby('material')['quantidade'].sum().nlargest(top_produtos).index
    
    # Filtrar
    df_filtered = df_cotacoes[
        df_cotacoes[['cod_cliente', 'cliente']].apply(tuple, axis=1).isin(top_clientes_list) &
        df_cotacoes['material'].isin(top_produtos_list)
    ]
    
    # Calcular % não comprado
    if not df_vendas.empty:
        vendas_matrix = df_vendas.groupby(['cod_cliente', 'material']).agg({
            'quantidade_faturada': 'sum'
        }).reset_index()
        
        matrix = pd.merge(
            df_filtered.groupby(['cod_cliente', 'cliente', 'material']).agg({'quantidade': 'sum'}).reset_index(),
            vendas_matrix,
            on=['cod_cliente', 'material'],
            how='left'
        )
        matrix['quantidade_faturada'] = matrix['quantidade_faturada'].fillna(0)
        matrix['pct_nao_comprado'] = (
            ((matrix['quantidade'] - matrix['quantidade_faturada']) / matrix['quantidade']) * 100
        ).clip(0, 100)
    else:
        matrix = df_filtered.groupby(['cod_cliente', 'cliente', 'material']).agg({'quantidade': 'sum'}).reset_index()
        matrix['pct_nao_comprado'] = 100
    
    # Preparar para heatmap
    pivot = matrix.pivot_table(
        index='cliente',
        columns='material',
        values='pct_nao_comprado',
        aggfunc='mean'
    ).fillna(0)
    
    return {
        "data": pivot.values.tolist(),
        "clientes": pivot.index.tolist(),
        "produtos": [str(p) for p in pivot.columns.tolist()]
    }


@router.get("/sugestao-estoque")
async def get_sugestao_estoque(
    current_user: dict = Depends(get_current_user)
):
    """Retorna sugestão de lista de compra para estoque"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    if df_vendas.empty or df_cotacoes.empty:
        return []
    
    sugestoes = kpis.generate_purchase_list(df_vendas, df_cotacoes)
    
    return sugestoes.to_dict('records') if not sugestoes.empty else []
