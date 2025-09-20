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
    get_latest_dataset,
    SENTINEL_ALL,
    _norm_year
)

from .data_loader import DataLoader
from .kpis import KPICalculator
from .visualizations import VisualizationGenerator
from .advanced_analytics import AdvancedAnalytics
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

def load_all_data():
    """
    Carrega todos os dados necessários para o sistema ML
    
    Returns:
        tuple: (vendas_df, cotacoes_df, produtos_df)
    """
    try:
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data() 
        produtos_df = load_produtos_cotados_data()
        
        return vendas_df, cotacoes_df, produtos_df
        
    except Exception as e:
        print(f"⚠️ Erro ao carregar dados: {e}")
        import pandas as pd
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

__all__ = [
    'init_db',
    'get_connection', 
    'save_dataset',
    'load_vendas_data',
    'load_cotacoes_data', 
    'load_produtos_cotados_data',
    'load_all_data',
    'get_setting',
    'save_setting',
    'verify_user',
    'get_latest_dataset',
    'SENTINEL_ALL',
    '_norm_year',
    'DataLoader',
    'KPICalculator',
    'VisualizationGenerator',
    'AdvancedAnalytics',
    'SecurityManager',
    'require_auth',
    'is_authenticated',
    'login_user',
    'logout_user',
    'get_current_user_id',
    'rate_limiter',
    'check_file_security'
]
