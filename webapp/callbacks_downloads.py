# webapp/callbacks_downloads.py

import dash
from dash import html, dcc, Input, Output, State, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime
from io import StringIO, BytesIO
import base64

from webapp import app
from utils import db, kpis, report

@app.callback(
    Output("download-csv-kpis-cliente", "data"),
    Input("btn-csv-kpis-cliente", "n_clicks"),
    State("store-kpis-cliente-filtered", "data"),
    prevent_initial_call=True,
)
def download_kpis_cliente_csv(n_clicks, json_data):
    """Download da tabela de KPIs por cliente em CSV"""
    if not n_clicks or not json_data:
        raise exceptions.PreventUpdate
    
    try:
        df = pd.read_json(StringIO(json_data), orient='split')
        return dcc.send_data_frame(
            df.to_csv, 
            f"kpis_por_cliente_{datetime.now().date()}.csv", 
            index=False
        )
    except Exception as e:
        print(f"Erro no download CSV KPIs: {e}")
        raise exceptions.PreventUpdate

@app.callback(
    Output("download-lista-sugestao", "data"),
    Input("btn-gerar-lista", "n_clicks"),
    State('filtro-ano-propostas', 'value'),
    State('filtro-mes-propostas', 'value'),
    prevent_initial_call=True
)
def generate_suggestion_list(n_clicks, ano_filtro, mes_filtro):
    """Gera lista de sugestão de compra baseada em análise de gaps"""
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    try:
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Filtrar por período se especificado
        if ano_filtro and isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
            if 'data' in df_cotacoes.columns:
                df_cotacoes_filtered = df_cotacoes[
                    (pd.to_datetime(df_cotacoes['data']).dt.year >= ano_filtro[0]) &
                    (pd.to_datetime(df_cotacoes['data']).dt.year <= ano_filtro[1])
                ]
            else:
                df_cotacoes_filtered = df_cotacoes
                
            if mes_filtro and isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
                if 'data' in df_cotacoes_filtered.columns:
                    df_cotacoes_filtered = df_cotacoes_filtered[
                        (pd.to_datetime(df_cotacoes_filtered['data']).dt.month >= mes_filtro[0]) &
                        (pd.to_datetime(df_cotacoes_filtered['data']).dt.month <= mes_filtro[1])
                    ]
        else:
            df_cotacoes_filtered = df_cotacoes
        
        # Analisar produtos mais cotados vs menos vendidos
        cotacoes_summary = df_cotacoes_filtered.groupby('material').agg({
            'quantidade': 'sum',
            'cod_cliente': 'nunique'
        }).reset_index()
        cotacoes_summary.columns = ['material', 'qtd_cotada_total', 'num_clientes_cotaram']
        
        if not df_vendas.empty:
            vendas_summary = df_vendas.groupby('material').agg({
                'quantidade_faturada': 'sum',
                'cod_cliente': 'nunique'
            }).reset_index()
            vendas_summary.columns = ['material', 'qtd_vendida_total', 'num_clientes_compraram']
            
            # Merge para calcular gaps
            gap_analysis = pd.merge(cotacoes_summary, vendas_summary, on='material', how='left')
            gap_analysis['qtd_vendida_total'] = gap_analysis['qtd_vendida_total'].fillna(0)
            gap_analysis['num_clientes_compraram'] = gap_analysis['num_clientes_compraram'].fillna(0)
        else:
            gap_analysis = cotacoes_summary.copy()
            gap_analysis['qtd_vendida_total'] = 0
            gap_analysis['num_clientes_compraram'] = 0
        
        # Calcular métricas de oportunidade
        gap_analysis['gap_quantidade'] = gap_analysis['qtd_cotada_total'] - gap_analysis['qtd_vendida_total']
        gap_analysis['taxa_conversao'] = np.where(
            gap_analysis['qtd_cotada_total'] > 0,
            (gap_analysis['qtd_vendida_total'] / gap_analysis['qtd_cotada_total']) * 100,
            0
        )
        gap_analysis['oportunidade_score'] = (
            gap_analysis['gap_quantidade'] * 0.4 +
            gap_analysis['num_clientes_cotaram'] * 0.3 +
            (100 - gap_analysis['taxa_conversao']) * 0.3
        )
        
        # Classificar e filtrar top oportunidades
        gap_analysis = gap_analysis.sort_values('oportunidade_score', ascending=False)
        top_opportunities = gap_analysis.head(50)
        
        # Preparar lista de sugestão
        suggestion_list = top_opportunities[[
            'material', 'qtd_cotada_total', 'qtd_vendida_total', 'gap_quantidade',
            'num_clientes_cotaram', 'num_clientes_compraram', 'taxa_conversao', 'oportunidade_score'
        ]].copy()
        
        suggestion_list.columns = [
            'Material', 'Qtd_Cotada_Total', 'Qtd_Vendida_Total', 'Gap_Quantidade',
            'Clientes_Cotaram', 'Clientes_Compraram', 'Taxa_Conversao_%', 'Score_Oportunidade'
        ]
        
        # Adicionar recomendação de estoque sugerido
        suggestion_list['Estoque_Sugerido'] = (
            suggestion_list['Gap_Quantidade'] * 0.3  # 30% do gap como sugestão conservadora
        ).round(0).astype(int)
        
        # Adicionar prioridade
        suggestion_list['Prioridade'] = pd.cut(
            suggestion_list['Score_Oportunidade'],
            bins=3,
            labels=['Baixa', 'Média', 'Alta']
        )
        
        # Criar arquivo Excel com múltiplas abas
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Aba principal com lista de sugestão
            suggestion_list.to_excel(writer, sheet_name='Lista_Sugestao', index=False)
            
            # Aba com análise detalhada
            gap_analysis.to_excel(writer, sheet_name='Analise_Completa', index=False)
            
            # Aba com resumo por prioridade
            if 'Prioridade' in suggestion_list.columns:
                priority_summary = suggestion_list.groupby('Prioridade').agg({
                    'Material': 'count',
                    'Gap_Quantidade': 'sum',
                    'Estoque_Sugerido': 'sum'
                }).reset_index()
                priority_summary.columns = ['Prioridade', 'Num_Produtos', 'Gap_Total', 'Estoque_Total_Sugerido']
                priority_summary.to_excel(writer, sheet_name='Resumo_Prioridades', index=False)
        
        output.seek(0)
        
        return dcc.send_bytes(
            output.getvalue(),
            f"lista_sugestao_estoque_{datetime.now().date()}.xlsx"
        )
        
    except Exception as e:
        print(f"Erro na geração da lista de sugestão: {e}")
        raise exceptions.PreventUpdate

@app.callback(
    Output("download-pdf-individual", "data"),
    Input("btn-pdf-individual", "n_clicks"),
    State("selected-client-code", "data"),
    prevent_initial_call=True
)
def generate_individual_client_pdf(n_clicks, client_code):
    """Gera relatório PDF para cliente específico"""
    if not n_clicks or not client_code:
        raise exceptions.PreventUpdate
    
    try:
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Filtrar dados do cliente
        client_vendas = df_vendas[df_vendas['cod_cliente'] == client_code] if not df_vendas.empty else pd.DataFrame()
        client_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'] == client_code] if not df_cotacoes.empty else pd.DataFrame()
        
        # Obter nome do cliente
        if not client_vendas.empty and 'cliente' in client_vendas.columns:
            client_name = client_vendas['cliente'].iloc[0]
        elif not client_cotacoes.empty and 'cliente' in client_cotacoes.columns:
            client_name = client_cotacoes['cliente'].iloc[0]
        else:
            client_name = f"Cliente {client_code}"
        
        # Criar gráfico para o PDF
        charts_data = None
        if not client_vendas.empty and 'data_faturamento' in client_vendas.columns:
            monthly_sales = client_vendas.groupby(
                pd.to_datetime(client_vendas['data_faturamento']).dt.to_period('M')
            )['valor_faturado'].sum()
            
            if not monthly_sales.empty:
                chart_b64 = report.create_chart_for_pdf(monthly_sales, 'bar')
                if chart_b64:
                    charts_data = {'image_base64': chart_b64}
        
        # Gerar PDF
        pdf_bytes = report.generate_client_pdf(client_vendas, client_name, charts_data)
        
        return dcc.send_bytes(
            pdf_bytes,
            f"relatorio_{client_name.replace(' ', '_')}_{datetime.now().date()}.pdf"
        )
        
    except Exception as e:
        print(f"Erro na geração do PDF individual: {e}")
        raise exceptions.PreventUpdate
