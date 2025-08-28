# utils/visualizations.py

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

def create_bubble_chart(df_matrix, color_scale='Viridis'):
    """
    Cria gráfico de bolhas para análise cliente x produto
    
    Args:
        df_matrix: DataFrame com dados da matriz
        color_scale: Escala de cores
    
    Returns:
        plotly.graph_objects.Figure
    """
    if df_matrix.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum dado disponível para exibir",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(
            title="Gráfico de Bolhas - Clientes vs Produtos",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig
    
    # Preparar dados
    df_plot = df_matrix.copy()
    df_plot['cliente_nome'] = df_plot['cliente'].str.slice(0, 20) + '...' if 'cliente' in df_plot.columns else df_plot['cod_cliente'].astype(str)
    df_plot['material_str'] = df_plot['material'].astype(str)
    
    # Normalizar tamanhos das bolhas
    size_min, size_max = 5, 50
    if df_plot['quantidade'].max() > 0:
        df_plot['bubble_size'] = size_min + (df_plot['quantidade'] - df_plot['quantidade'].min()) / (df_plot['quantidade'].max() - df_plot['quantidade'].min()) * (size_max - size_min)
    else:
        df_plot['bubble_size'] = size_min
    
    # Criar gráfico
    fig = px.scatter(
        df_plot,
        x='material_str',
        y='cliente_nome',
        size='bubble_size',
        color='pct_nao_comprado',
        color_continuous_scale=color_scale,
        hover_data={
            'quantidade': ':,.0f',
            'quantidade_faturada': ':,.0f',
            'pct_nao_comprado': ':.1f',
            'bubble_size': False,
            'material_str': False,
            'cliente_nome': False
        },
        labels={
            'material_str': 'Material',
            'cliente_nome': 'Cliente',
            'pct_nao_comprado': '% Não Comprado'
        }
    )
    
    fig.update_traces(
        hovertemplate=
        '<b>%{y}</b><br>' +
        'Material: %{x}<br>' +
        'Qtd Cotada: %{customdata[0]}<br>' +
        'Qtd Comprada: %{customdata[1]}<br>' +
        '% Não Comprado: %{customdata[2]:.1f}%' +
        '<extra></extra>'
    )
    
    fig.update_layout(
        title="Análise de Bolhas - Clientes vs Produtos",
        xaxis_title="Produtos (Material)",
        yaxis_title="Clientes",
        height=600,
        showlegend=False,
        xaxis=dict(tickangle=45),
        coloraxis_colorbar=dict(title="% Não Comprado")
    )
    
    return fig

def create_funnel_chart(funil_data):
    """
    Cria gráfico de funil de conversão
    """
    if funil_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum dado disponível",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Calcular estágios do funil
    total_cotaram = len(funil_data)
    total_compraram = len(funil_data[funil_data['quantidade_faturada'] > 0])
    
    # Faixas de conversão
    alta_conversao = len(funil_data[funil_data['conversao_pct'] >= 70])
    media_conversao = len(funil_data[(funil_data['conversao_pct'] >= 30) & (funil_data['conversao_pct'] < 70)])
    baixa_conversao = len(funil_data[funil_data['conversao_pct'] < 30])
    
    fig = go.Figure()
    
    # Funil principal
    fig.add_trace(go.Funnel(
        y=['Clientes que Cotaram', 'Compraram Algo', 'Alta Conversão (≥70%)', 'Média Conversão (30-70%)', 'Baixa Conversão (<30%)'],
        x=[total_cotaram, total_compraram, alta_conversao, media_conversao, baixa_conversao],
        textinfo="value+percent initial",
        marker=dict(
            color=['lightblue', 'lightgreen', 'green', 'orange', 'red'],
            line=dict(color='white', width=2)
        )
    ))
    
    fig.update_layout(
        title="Funil de Conversão de Clientes",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_scatter_kpis(df_kpis):
    """
    Cria gráfico scatter para KPIs por cliente
    """
    if df_kpis.empty:
        return go.Figure()
    
    fig = px.scatter(
        df_kpis,
        x='total_comprado_valor',
        y='pct_nao_comprado',
        size='mix_produtos',
        color='dias_sem_compra',
        hover_data=['cliente', 'total_comprado_qtd', 'unidades_negocio'],
        labels={
            'total_comprado_valor': 'Valor Total Comprado (R$)',
            'pct_nao_comprado': '% Não Comprado',
            'mix_produtos': 'Mix de Produtos',
            'dias_sem_compra': 'Dias sem Compra'
        },
        color_continuous_scale='Reds_r'
    )
    
    fig.update_layout(
        title="Análise de Performance por Cliente",
        height=500
    )
    
    return fig

def create_historical_evolution(df_vendas, indicators):
    """
    Cria gráfico de evolução histórica dos KPIs
    """
    if df_vendas.empty or not indicators:
        return go.Figure()
    
    # Agrupar por ano
    df_vendas['ano'] = pd.to_datetime(df_vendas['data_faturamento']).dt.year
    
    historical_data = df_vendas.groupby('ano').agg({
        'valor_faturado': 'sum',
        'quantidade_faturada': 'sum',
        'material': 'nunique',
        'cod_cliente': 'nunique'
    }).reset_index()
    
    historical_data['pct_mix_produtos'] = (historical_data['material'] / historical_data['material'].max()) * 100
    
    # Mapear indicadores
    indicator_map = {
        'total_comprado_valor': ('valor_faturado', 'Valor Faturado (R$)'),
        'total_comprado_qtd': ('quantidade_faturada', 'Quantidade Faturada'),
        'mix_produtos': ('material', 'Mix de Produtos'),
        'pct_mix_produtos': ('pct_mix_produtos', 'Mix de Produtos (%)')
    }
    
    fig = go.Figure()
    
    for indicator in indicators:
        if indicator in indicator_map:
            col_name, label = indicator_map[indicator]
            fig.add_trace(go.Scatter(
                x=historical_data['ano'],
                y=historical_data[col_name],
                mode='lines+markers',
                name=label,
                line=dict(width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title="Evolução Histórica dos Indicadores",
        xaxis_title="Ano",
        yaxis_title="Valor",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_comparative_chart(df_propostas, chart_type='barra'):
    """
    Cria gráfico comparativo para análise de propostas
    """
    if df_propostas.empty:
        return go.Figure()
    
    if chart_type == 'heatmap':
        # Preparar dados para heatmap
        pivot_data = df_propostas.pivot_table(
            index='cliente',
            columns='material',
            values='pct_nao_comprado',
            aggfunc='mean'
        ).fillna(0)
        
        fig = px.imshow(
            pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            color_continuous_scale='RdYlBu_r',
            labels=dict(color="% Não Comprado")
        )
        
        fig.update_layout(
            title="Heatmap: % Não Comprado por Cliente x Produto",
            height=600
        )
        
    else:  # barra
        # Agrupar por cliente
        client_summary = df_propostas.groupby('cliente').agg({
            'quantidade': 'sum',
            'quantidade_faturada': 'sum'
        }).reset_index()
        
        client_summary['pct_conversao'] = np.where(
            client_summary['quantidade'] > 0,
            (client_summary['quantidade_faturada'] / client_summary['quantidade']) * 100,
            0
        )
        
        client_summary = client_summary.sort_values('quantidade', ascending=True).tail(15)
        
        fig = px.bar(
            client_summary,
            x='pct_conversao',
            y='cliente',
            orientation='h',
            color='pct_conversao',
            color_continuous_scale='RdYlGn',
            labels={
                'pct_conversao': 'Taxa de Conversão (%)',
                'cliente': 'Cliente'
            }
        )
        
        fig.update_layout(
            title="Taxa de Conversão por Cliente (Top 15)",
            height=600
        )
    
    return fig

def create_status_indicators(df_kpis, thresholds=None):
    """
    Cria indicadores visuais de status por cliente
    """
    if thresholds is None:
        thresholds = {
            'dias_sem_compra': {'bom': 30, 'medio': 90, 'ruim': 180},
            'pct_nao_comprado': {'bom': 20, 'medio': 50, 'ruim': 80},
            'mix_produtos': {'bom': 5, 'medio': 3, 'ruim': 1}
        }
    
    def get_status_color(value, metric):
        thresh = thresholds.get(metric, {})
        if metric == 'dias_sem_compra' or metric == 'pct_nao_comprado':
            # Menor é melhor
            if value <= thresh.get('bom', 0):
                return '🟢'
            elif value <= thresh.get('medio', 0):
                return '🟡'
            else:
                return '🔴'
        else:
            # Maior é melhor
            if value >= thresh.get('bom', 0):
                return '🟢'
            elif value >= thresh.get('medio', 0):
                return '🟡'
            else:
                return '🔴'
    
    status_indicators = []
    for _, row in df_kpis.iterrows():
        indicators = {
            'cliente': row.get('cliente', 'N/A'),
            'dias_status': get_status_color(row.get('dias_sem_compra', 999), 'dias_sem_compra'),
            'conversao_status': get_status_color(row.get('pct_nao_comprado', 100), 'pct_nao_comprado'),
            'mix_status': get_status_color(row.get('mix_produtos', 0), 'mix_produtos')
        }
        status_indicators.append(indicators)
    
    return status_indicators
