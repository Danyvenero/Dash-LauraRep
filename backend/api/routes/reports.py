"""
Rotas de relatórios e exportações
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import sys
import os
import pandas as pd
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.routes.auth import get_current_user
from backend.api.models.database import get_db_connection
from utils.db import get_clean_vendas_as_df, get_clean_cotacoes_as_df
from utils import kpis

router = APIRouter()


@router.get("/csv/kpis-cliente")
async def export_kpis_cliente_csv(
    current_user: dict = Depends(get_current_user)
):
    """Exporta KPIs por cliente em CSV"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    df_kpis = kpis.calculate_kpis_por_cliente(df_vendas, df_cotacoes)
    
    if df_kpis.empty:
        raise HTTPException(status_code=404, detail="Nenhum dado disponível")
    
    # Converter para CSV
    output = io.StringIO()
    df_kpis.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kpis_cliente.csv"}
    )


@router.get("/csv/funil-lista-a")
async def export_funil_lista_a_csv(
    current_user: dict = Depends(get_current_user)
):
    """Exporta Lista A do funil em CSV"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    funil_data = kpis.calculate_funil_metrics(df_vendas, df_cotacoes)
    lista_a = funil_data['lista_a']
    
    if lista_a.empty:
        raise HTTPException(status_code=404, detail="Nenhum dado disponível")
    
    output = io.StringIO()
    lista_a.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=funil_lista_a.csv"}
    )


@router.get("/csv/funil-lista-b")
async def export_funil_lista_b_csv(
    current_user: dict = Depends(get_current_user)
):
    """Exporta Lista B do funil em CSV"""
    df_vendas = get_clean_vendas_as_df()
    df_cotacoes = get_clean_cotacoes_as_df()
    
    funil_data = kpis.calculate_funil_metrics(df_vendas, df_cotacoes)
    lista_b = funil_data['lista_b']
    
    if lista_b.empty:
        raise HTTPException(status_code=404, detail="Nenhum dado disponível")
    
    output = io.StringIO()
    lista_b.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=funil_lista_b.csv"}
    )
