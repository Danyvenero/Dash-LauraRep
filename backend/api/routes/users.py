"""
Rotas de gestão de usuários
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.models.schemas import UserResponse, UserCreateRequest
from backend.api.routes.auth import get_current_user
from backend.api.models.database import get_db_connection
from utils.db import get_all_users, delete_user, add_user

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(get_current_user)):
    """Lista todos os usuários (apenas para admin)"""
    # TODO: Adicionar verificação de permissão admin
    users = get_all_users()
    
    return [
        UserResponse(
            id=user[0],
            username=user[1],
            created_at=user[2],
            is_active=True  # Assumindo que todos estão ativos por padrão
        )
        for user in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo usuário"""
    success = add_user(request.username, request.password)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Nome de usuário já está em uso"
        )
    
    # Buscar o usuário criado
    from utils.db import get_user_by_username
    user = get_user_by_username(request.username)
    
    return UserResponse(
        id=user['id'],
        username=user['username'],
        created_at=user['created_at'],
        is_active=user.get('is_active', True)
    )


@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um usuário"""
    if user_id == current_user['id']:
        raise HTTPException(
            status_code=400,
            detail="Não é possível deletar seu próprio usuário"
        )
    
    delete_user(user_id)
    return {"message": "Usuário deletado com sucesso"}
