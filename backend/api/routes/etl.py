"""
Rotas para ETL e processamento de dados
"""

from fastapi import APIRouter, Depends, HTTPException
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.routes.auth import get_current_user
from utils import etl

router = APIRouter()


@router.post("/run")
async def run_etl(current_user: dict = Depends(get_current_user)):
    """Executa o processo ETL completo"""
    try:
        result = etl.run_full_etl()
        return {
            "success": True,
            "message": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar ETL: {str(e)}"
        )


@router.post("/wipe")
async def wipe_data(current_user: dict = Depends(get_current_user)):
    """Limpa todos os dados brutos e processados"""
    try:
        from utils.db import wipe_all_transaction_data
        success = wipe_all_transaction_data()
        
        if success:
            return {
                "success": True,
                "message": "Todos os dados foram limpos com sucesso"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Erro ao limpar dados"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao limpar dados: {str(e)}"
        )
