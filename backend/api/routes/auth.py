"""
Rotas de autenticação
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.api.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.api.models.database import get_db_connection
from utils.db import get_user_by_username, add_user
from utils.security import check_password, hash_password

router = APIRouter()

# Configuração JWT
SECRET_KEY = "uma-chave-secreta-muito-forte-deve-ser-usada-aqui-em-producao-mude-isso"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT e retorna o usuário"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_active FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
    if user is None:
        raise credentials_exception
    
    return {"id": user[0], "username": user[1], "is_active": user[2]}


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint de login"""
    user = get_user_by_username(form_data.username)
    
    if not user or not check_password(user['password_hash'], form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['id']},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user['id'],
        username=user['username']
    )


@router.post("/register")
async def register(request: RegisterRequest):
    """Endpoint de cadastro de usuário"""
    success = add_user(request.username, request.password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já está em uso"
        )
    
    return {"message": "Usuário criado com sucesso"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Retorna informações do usuário atual"""
    return current_user


@router.post("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verifica se um token é válido"""
    try:
        await get_current_user(token)
        return {"valid": True}
    except HTTPException:
        return {"valid": False}
