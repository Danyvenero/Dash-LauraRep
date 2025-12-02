"""
Rotas de cotações
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.models.schemas import CotacaoResponse
from backend.api.routes.auth import get_current_user
from backend.api.models.database import get_db_connection
from utils.db import get_clean_cotacoes_as_df

router = APIRouter()


@router.get("/", response_model=List[CotacaoResponse])
async def get_cotacoes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cod_cliente: Optional[str] = None,
    material: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Lista cotações com paginação e filtros"""
    df = get_clean_cotacoes_as_df()
    
    if df.empty:
        return []
    
    # Aplicar filtros
    if cod_cliente:
        df = df[df['cod_cliente'] == cod_cliente]
    if material:
        df = df[df['material'] == material]
    
    # Paginação
    df = df.iloc[skip:skip+limit]
    
    result = df.to_dict('records')
    return [CotacaoResponse(**row) for row in result]


@router.get("/stats")
async def get_cotacoes_stats(
    current_user: dict = Depends(get_current_user)
):
    """Retorna estatísticas gerais de cotações"""
    df = get_clean_cotacoes_as_df()
    
    if df.empty:
        return {
            "total_cotacoes": 0,
            "total_clientes": 0,
            "total_produtos": 0,
            "quantidade_total": 0
        }
    
    return {
        "total_cotacoes": len(df),
        "total_clientes": df['cod_cliente'].nunique(),
        "total_produtos": df['material'].nunique(),
        "quantidade_total": float(df['quantidade'].sum()) if 'quantidade' in df.columns else 0
    }
