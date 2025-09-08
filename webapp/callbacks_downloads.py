"""
Callbacks para Downloads do Dashboard WEG
"""

import pandas as pd
import io
import base64
from datetime import datetime
from dash import Input, Output, callback, dcc
from flask import session
import openpyxl

from utils import (
    load_vendas_data, 
    load_cotacoes_data, 
    load_produtos_cotados_data,
    get_current_user_id,
    require_auth,
    SENTINEL_ALL
)


@callback(
    Output('download-excel', 'data'),
    Input('btn-download-excel', 'n_clicks'),
    prevent_initial_call=True
)
@require_auth
def download_excel_report(n_clicks):
    """
    Gera e baixa relatório em Excel com todos os dados
    """
    if not n_clicks:
        return None
    
    try:
        # Carrega todos os dados
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_df = load_produtos_cotados_data()
        
        # Cria arquivo Excel em memória
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Aba de vendas
            if not vendas_df.empty:
                vendas_df.to_excel(writer, sheet_name='Vendas', index=False)
            
            # Aba de cotações
            if not cotacoes_df.empty:
                cotacoes_df.to_excel(writer, sheet_name='Cotações', index=False)
            
            # Aba de produtos cotados
            if not produtos_df.empty:
                produtos_df.to_excel(writer, sheet_name='Produtos Cotados', index=False)
        
        output.seek(0)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_weg_report_{timestamp}.xlsx"
        
        return dcc.send_bytes(output.getvalue(), filename)
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório Excel: {e}")
        return None


@callback(
    Output('download-csv', 'data'),
    Input('btn-download-csv', 'n_clicks'),
    prevent_initial_call=True
)
@require_auth
def download_csv_report(n_clicks):
    """
    Gera e baixa relatório em CSV com dados de vendas
    """
    if not n_clicks:
        return None
    
    try:
        # Carrega dados de vendas
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            print("⚠️ Não há dados de vendas para download")
            return None
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vendas_weg_{timestamp}.csv"
        
        return dcc.send_data_frame(vendas_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório CSV: {e}")
        return None


@callback(
    Output('download-cotacoes-csv', 'data'),
    Input('btn-download-cotacoes-csv', 'n_clicks'),
    prevent_initial_call=True
)
@require_auth
def download_cotacoes_csv(n_clicks):
    """
    Gera e baixa relatório CSV com dados de cotações
    """
    if not n_clicks:
        return None
    
    try:
        # Carrega dados de cotações
        cotacoes_df = load_cotacoes_data()
        
        if cotacoes_df.empty:
            print("⚠️ Não há dados de cotações para download")
            return None
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cotacoes_weg_{timestamp}.csv"
        
        return dcc.send_data_frame(cotacoes_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório de cotações CSV: {e}")
        return None


def register_download_callbacks(app):
    """
    Registra todos os callbacks de download
    """
    print("✅ Callbacks de download registrados com sucesso")
    return True
