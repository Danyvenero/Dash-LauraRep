"""
Rotas de upload de arquivos
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import sys
import os
import base64
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.models.schemas import UploadResponse
from backend.api.routes.auth import get_current_user
from utils.data_loader import parse_upload_content, generate_fingerprint, read_raw_vendas, read_raw_materiais_cotados
from utils.db import check_raw_fingerprint_exists, insert_raw_df
from utils import etl

router = APIRouter()


@router.post("/vendas", response_model=UploadResponse)
async def upload_vendas(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload de arquivo de vendas"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    # Ler arquivo
    contents = await file.read()
    file_bytes_io = io.BytesIO(contents)
    
    # Gerar fingerprint
    fingerprint = generate_fingerprint(file_bytes_io)
    
    # Verificar se já existe
    if check_raw_fingerprint_exists(fingerprint, 'raw_vendas'):
        return UploadResponse(
            success=False,
            message="Este arquivo já foi carregado anteriormente.",
            fingerprint=fingerprint
        )
    
    # Ler dados
    try:
        df = read_raw_vendas(file_bytes_io)
        if df.empty:
            raise HTTPException(status_code=400, detail="Arquivo vazio ou inválido")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Inserir no banco
    records_inserted = insert_raw_df(
        df, 
        'raw_vendas', 
        file.filename, 
        fingerprint, 
        current_user['id']
    )
    
    # Executar ETL
    try:
        etl.transform_vendas()
    except Exception as e:
        # Log do erro mas não falha o upload
        print(f"Erro no ETL: {e}")
    
    return UploadResponse(
        success=True,
        message=f"Arquivo carregado com sucesso. {records_inserted} registros inseridos.",
        records_inserted=records_inserted,
        fingerprint=fingerprint
    )


@router.post("/cotacoes", response_model=UploadResponse)
async def upload_cotacoes(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload de arquivo de cotações"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    # Ler arquivo
    contents = await file.read()
    file_bytes_io = io.BytesIO(contents)
    
    # Gerar fingerprint
    fingerprint = generate_fingerprint(file_bytes_io)
    
    # Verificar se já existe
    if check_raw_fingerprint_exists(fingerprint, 'raw_materiais_cotados'):
        return UploadResponse(
            success=False,
            message="Este arquivo já foi carregado anteriormente.",
            fingerprint=fingerprint
        )
    
    # Ler dados
    try:
        df = read_raw_materiais_cotados(file_bytes_io)
        if df.empty:
            raise HTTPException(status_code=400, detail="Arquivo vazio ou inválido")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")
    
    # Inserir no banco
    records_inserted = insert_raw_df(
        df, 
        'raw_materiais_cotados', 
        file.filename, 
        fingerprint, 
        current_user['id']
    )
    
    # Executar ETL
    try:
        etl.transform_cotacoes()
    except Exception as e:
        print(f"Erro no ETL: {e}")
    
    return UploadResponse(
        success=True,
        message=f"Arquivo carregado com sucesso. {records_inserted} registros inseridos.",
        records_inserted=records_inserted,
        fingerprint=fingerprint
    )
