"""
Pydantic Schemas para validação de dados
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Autenticação ============
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


# ============ Vendas ============
class VendaBase(BaseModel):
    cod_cliente: str
    cliente: Optional[str] = None
    material: str
    produto: Optional[str] = None
    unidade_negocio: Optional[str] = None
    canal_distribuicao: Optional[str] = None
    data_entrada: Optional[datetime] = None
    data_faturamento: Optional[datetime] = None
    quantidade_entrada: Optional[float] = None
    quantidade_carteira: Optional[float] = None
    quantidade_faturada: Optional[float] = None
    valor_entrada: Optional[float] = None
    valor_carteira: Optional[float] = None
    valor_faturado: Optional[float] = None


class VendaResponse(VendaBase):
    id: int

    class Config:
        from_attributes = True


# ============ Cotações ============
class CotacaoBase(BaseModel):
    cod_cliente: str
    cliente: Optional[str] = None
    material: str
    data: datetime
    quantidade: float


class CotacaoResponse(CotacaoBase):
    id: int

    class Config:
        from_attributes = True


# ============ KPIs ============
class KPIGeralResponse(BaseModel):
    entrada_pedidos: str
    valor_carteira: str
    faturamento: str


class KPIClienteResponse(BaseModel):
    cod_cliente: str
    cliente: str
    ultima_compra: Optional[datetime]
    total_comprado_valor: float
    total_comprado_qtd: float
    mix_produtos: int
    unidades_negocio: int
    dias_sem_compra: int
    total_cotado_qtd: float
    pct_mix_produtos: float
    pct_nao_comprado: float


class FiltrosKPICliente(BaseModel):
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None
    mes_inicio: Optional[int] = None
    mes_fim: Optional[int] = None
    clientes: Optional[List[str]] = None
    dias_sem_compra_min: Optional[int] = None
    dias_sem_compra_max: Optional[int] = None
    canal_vendas: Optional[List[str]] = None
    hierarquia_produto: Optional[List[int]] = None
    top_n: Optional[int] = 20


# ============ Upload ============
class UploadResponse(BaseModel):
    success: bool
    message: str
    records_inserted: Optional[int] = None
    fingerprint: Optional[str] = None


# ============ Produtos ============
class ProdutoMatrixResponse(BaseModel):
    cod_cliente: str
    cliente: str
    material: str
    quantidade: float
    quantidade_faturada: float
    pct_nao_comprado: float


# ============ Funil ============
class FunilMetricsResponse(BaseModel):
    total_clientes_cotaram: int
    total_clientes_compraram: int
    taxa_conversao_geral: float
    lista_a: List[Dict[str, Any]]
    lista_b: List[Dict[str, Any]]


# ============ Usuários ============
class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    is_active: bool


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


# ============ Relatórios ============
class ReportRequest(BaseModel):
    tipo: str  # 'csv', 'pdf', 'excel'
    filtros: Optional[Dict[str, Any]] = None
    cliente_id: Optional[str] = None
