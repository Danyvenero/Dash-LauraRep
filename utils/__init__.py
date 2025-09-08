"""
Módulo utils - Utilitários para o Dashboard WEG
"""

from .db import (
    init_db, 
    get_connection, 
    save_dataset, 
    load_vendas_data, 
    load_cotacoes_data, 
    load_produtos_cotados_data,
    get_setting, 
    save_setting, 
    verify_user,
    SENTINEL_ALL,
    _norm_year
)

from .data_loader import DataLoader
from .kpis import KPICalculator
from .visualizations import VisualizationGenerator
from .security import (
    SecurityManager, 
    require_auth, 
    is_authenticated, 
    login_user, 
    logout_user,
    get_current_user_id,
    rate_limiter,
    check_file_security
)

__all__ = [
    'init_db',
    'get_connection', 
    'save_dataset',
    'load_vendas_data',
    'load_cotacoes_data', 
    'load_produtos_cotados_data',
    'get_setting',
    'save_setting',
    'verify_user',
    'SENTINEL_ALL',
    '_norm_year',
    'DataLoader',
    'KPICalculator', 
    'VisualizationGenerator',
    'SecurityManager',
    'require_auth',
    'is_authenticated',
    'login_user',
    'logout_user',
    'get_current_user_id',
    'rate_limiter',
    'check_file_security'
]
