"""
Módulo para criação de visualizações e gráficos
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.db import SENTINEL_ALL

class VisualizationGenerator:
    """Classe para geração de visualizações"""
    
    def __init__(self):
        # Paleta de cores WEG
        self.weg_colors = {
            'primary': '#003366',
            'secondary': '#0066cc',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        self.color_scales = {
            'weg_blue': ['#e6f3ff', '#cce7ff', '#99d6ff', '#66c5ff', '#33b4ff', '#0099ff', '#0080cc', '#006699', '#004d66', '#003366'],
            'performance': ['#dc3545', '#ffc107', '#28a745'],
            'heatmap': px.colors.sequential.Blues
        }
    
    def create_evolution_chart(self, vendas_df: pd.DataFrame, filters: Dict = None) -> go.Figure:
        """Cria gráfico de evolução de vendas"""
        
        if vendas_df.empty or 'data_faturamento' not in vendas_df.columns:
            return self._create_empty_chart("Sem dados para exibir")
        
        # Aplica filtros
        df_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        
        if df_filtered.empty:
            return self._create_empty_chart("Nenhum dado encontrado com os filtros aplicados")
        
        # Agrupa por mês
        df_monthly = (df_filtered.groupby(df_filtered['data_faturamento'].dt.to_period('M'))
                     .agg({
                         'vlr_entrada': 'sum',
                         'vlr_carteira': 'sum',
                         'vlr_rol': 'sum'
                     }).reset_index())
        
        df_monthly['data_faturamento'] = df_monthly['data_faturamento'].astype(str)
        
        fig = go.Figure()
        
        # Linha de Entrada de Pedidos
        fig.add_trace(go.Scatter(
            x=df_monthly['data_faturamento'],
            y=df_monthly['vlr_entrada'],
            mode='lines+markers',
            name='Entrada de Pedidos',
            line=dict(color=self.weg_colors['primary'], width=3),
            marker=dict(size=8)
        ))
        
        # Linha de Carteira
        fig.add_trace(go.Scatter(
            x=df_monthly['data_faturamento'],
            y=df_monthly['vlr_carteira'],
            mode='lines+markers',
            name='Carteira',
            line=dict(color=self.weg_colors['secondary'], width=3),
            marker=dict(size=8)
        ))
        
        # Linha de Faturamento
        fig.add_trace(go.Scatter(
            x=df_monthly['data_faturamento'],
            y=df_monthly['vlr_rol'],
            mode='lines+markers',
            name='Faturamento',
            line=dict(color=self.weg_colors['success'], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Evolução de Vendas',
            xaxis_title='Período',
            yaxis_title='Valor (R$)',
            hovermode='x unified',
            template='plotly_white',
            font=dict(family="Arial", size=12),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_bubble_chart(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame, 
                           produtos_cotados_df: pd.DataFrame, 
                           top_produtos: int = 20, top_clientes: int = 20,
                           color_scale: str = 'weg_blue', filters: Dict = None) -> go.Figure:
        """Cria gráfico de bolhas clientes × produtos"""
        
        # Aplica filtros
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        cotacoes_filtered = self._apply_filters(cotacoes_df, filters, is_cotacoes=True) if filters else cotacoes_df
        
        if vendas_filtered.empty and cotacoes_filtered.empty:
            return self._create_empty_chart("Sem dados para o gráfico de bolhas")
        
        # Cria matriz cliente × produto
        df_matrix = self._create_client_product_matrix(vendas_filtered, cotacoes_filtered, produtos_cotados_df)
        
        if df_matrix.empty:
            return self._create_empty_chart("Matriz cliente × produto vazia")
        
        # Filtra top clientes e produtos
        top_clients_list = df_matrix.groupby('cod_cliente')['qtd_cotada'].sum().nlargest(top_clientes).index
        top_products_list = df_matrix.groupby('material')['qtd_cotada'].sum().nlargest(top_produtos).index
        
        df_matrix = df_matrix[
            (df_matrix['cod_cliente'].isin(top_clients_list)) &
            (df_matrix['material'].isin(top_products_list))
        ]
        
        if df_matrix.empty:
            return self._create_empty_chart("Sem dados após aplicar filtros de top clientes/produtos")
        
        fig = go.Figure()
        
        # Adiciona bolhas
        fig.add_trace(go.Scatter(
            x=df_matrix['cod_cliente'],
            y=df_matrix['material'],
            mode='markers',
            marker=dict(
                size=df_matrix['qtd_cotada'] / df_matrix['qtd_cotada'].max() * 50 + 10,
                color=df_matrix['perc_nao_comprado'],
                colorscale=self.color_scales.get(color_scale, 'Blues'),
                showscale=True,
                colorbar=dict(title="% Não Comprado"),
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            text=df_matrix.apply(lambda row: 
                f"Cliente: {row['cliente']}<br>"
                f"Material: {row['material']}<br>"
                f"Qtd Cotada: {row['qtd_cotada']}<br>"
                f"% Não Comprado: {row['perc_nao_comprado']:.1f}%", axis=1),
            hovertemplate='%{text}<extra></extra>',
            name='Produtos Cotados'
        ))
        
        fig.update_layout(
            title='Matriz Clientes × Produtos (Bolhas)',
            xaxis_title='Código Cliente',
            yaxis_title='Material',
            template='plotly_white',
            height=600,
            font=dict(family="Arial", size=12)
        )
        
        return fig
    
    def create_pareto_chart(self, vendas_df: pd.DataFrame, filters: Dict = None) -> go.Figure:
        """Cria gráfico de Pareto de produtos"""
        
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        
        if vendas_filtered.empty or 'material' not in vendas_filtered.columns:
            return self._create_empty_chart("Sem dados para análise de Pareto")
        
        # Agrupa por produto
        df_pareto = (vendas_filtered.groupby(['material', 'produto'])['qtd_rol']
                    .sum()
                    .reset_index()
                    .sort_values('qtd_rol', ascending=False))
        
        # Calcula percentual acumulado
        df_pareto['perc_individual'] = (df_pareto['qtd_rol'] / df_pareto['qtd_rol'].sum()) * 100
        df_pareto['perc_acumulado'] = df_pareto['perc_individual'].cumsum()
        
        # Limita a 20 produtos
        df_pareto = df_pareto.head(20)
        
        fig = go.Figure()
        
        # Barras
        fig.add_trace(go.Bar(
            x=df_pareto['material'],
            y=df_pareto['qtd_rol'],
            name='Quantidade Vendida',
            marker_color=self.weg_colors['primary'],
            yaxis='y'
        ))
        
        # Linha do percentual acumulado
        fig.add_trace(go.Scatter(
            x=df_pareto['material'],
            y=df_pareto['perc_acumulado'],
            mode='lines+markers',
            name='% Acumulado',
            line=dict(color=self.weg_colors['danger'], width=3),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Análise de Pareto - Produtos',
            xaxis_title='Material',
            yaxis=dict(title='Quantidade Vendida', side='left'),
            yaxis2=dict(title='% Acumulado', side='right', overlaying='y', range=[0, 100]),
            template='plotly_white',
            height=500,
            font=dict(family="Arial", size=12),
            showlegend=True
        )
        
        return fig
    
    def create_unit_comparison_chart(self, vendas_df: pd.DataFrame, filters: Dict = None) -> go.Figure:
        """Cria gráfico de comparação por unidade de negócio"""
        
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        
        if vendas_filtered.empty or 'unidade_negocio' not in vendas_filtered.columns:
            return self._create_empty_chart("Sem dados de unidades de negócio")
        
        # Agrupa por unidade de negócio
        df_units = (vendas_filtered.groupby('unidade_negocio')['vlr_rol']
                   .sum()
                   .reset_index()
                   .sort_values('vlr_rol', ascending=True))
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_units['vlr_rol'],
            y=df_units['unidade_negocio'],
            orientation='h',
            marker_color=self.weg_colors['secondary'],
            text=df_units['vlr_rol'].apply(lambda x: f'R$ {x:,.0f}'),
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Faturamento por Unidade de Negócio',
            xaxis_title='Faturamento (R$)',
            yaxis_title='Unidade de Negócio',
            template='plotly_white',
            height=400,
            font=dict(family="Arial", size=12)
        )
        
        return fig
    
    def create_client_status_chart(self, client_kpis_df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de status dos clientes"""
        
        if client_kpis_df.empty:
            return self._create_empty_chart("Sem dados de clientes")
        
        # Classifica clientes por status
        def classify_client_status(row):
            if row['dias_sem_compra'] > 365:
                return 'Inativo (>1 ano)'
            elif row['dias_sem_compra'] > 90:
                return 'Em Risco (90-365 dias)'
            else:
                return 'Ativo (<90 dias)'
        
        client_kpis_df['status'] = client_kpis_df.apply(classify_client_status, axis=1)
        
        # Conta por status
        status_counts = client_kpis_df['status'].value_counts()
        
        colors = [self.weg_colors['success'], self.weg_colors['warning'], self.weg_colors['danger']]
        
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            marker_colors=colors[:len(status_counts)]
        )])
        
        fig.update_layout(
            title='Distribuição de Status dos Clientes',
            template='plotly_white',
            font=dict(family="Arial", size=12),
            showlegend=True
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Cria gráfico vazio com mensagem"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color=self.weg_colors['dark'])
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict, is_cotacoes: bool = False) -> pd.DataFrame:
        """Aplica filtros aos dados (método auxiliar)"""
        # Este método seria implementado de forma similar ao do módulo KPIs
        # Por brevidade, retorna o DataFrame original
        return df
    
    def _create_client_product_matrix(self, vendas_df: pd.DataFrame, 
                                    cotacoes_df: pd.DataFrame,
                                    produtos_cotados_df: pd.DataFrame) -> pd.DataFrame:
        """Cria matriz cliente × produto"""
        
        if cotacoes_df.empty or produtos_cotados_df.empty:
            return pd.DataFrame()
        
        # Merge cotações com produtos cotados
        df_merged = pd.merge(
            cotacoes_df[['numero_cotacao', 'cod_cliente', 'cliente', 'material', 'data']],
            produtos_cotados_df[['cotacao', 'material', 'quantidade']],
            left_on=['numero_cotacao', 'material'],
            right_on=['cotacao', 'material'],
            how='inner'
        )
        
        if df_merged.empty:
            return pd.DataFrame()
        
        # Agrupa por cliente e material
        df_matrix = (df_merged.groupby(['cod_cliente', 'cliente', 'material'])
                    .agg({'quantidade': 'sum'})
                    .reset_index())
        
        df_matrix = df_matrix.rename(columns={'quantidade': 'qtd_cotada'})
        
        # Verifica o que foi comprado
        if not vendas_df.empty:
            vendas_summary = (vendas_df.groupby(['cod_cliente', 'material'])['qtd_rol']
                            .sum()
                            .reset_index())
            vendas_summary = vendas_summary.rename(columns={'qtd_rol': 'qtd_comprada'})
            
            df_matrix = pd.merge(df_matrix, vendas_summary, 
                               on=['cod_cliente', 'material'], 
                               how='left')
            df_matrix['qtd_comprada'] = df_matrix['qtd_comprada'].fillna(0)
        else:
            df_matrix['qtd_comprada'] = 0
        
        # Calcula percentual não comprado
        df_matrix['perc_nao_comprado'] = (
            (df_matrix['qtd_cotada'] - df_matrix['qtd_comprada']) / 
            df_matrix['qtd_cotada'] * 100
        ).clip(0, 100)
        
        return df_matrix
