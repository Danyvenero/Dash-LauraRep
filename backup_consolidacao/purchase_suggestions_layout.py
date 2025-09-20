"""
Layout da página de Sugestões Inteligentes de Compra
Dashboard Laura Representações - WEG
"""

import dash
from dash import html, dcc, dash_table, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

def create_purchase_suggestions_layout():
    """
    Cria layout da página de Sugestões Inteligentes de Compra
    
    Funcionalidades:
    1. Filtros avançados (cliente, período, classificação ABC-XYZ)
    2. Tabela interativa com sugestões rankeadas
    3. Gráficos de análise (distribuição ABC-XYZ, timeline)
    4. Sistema de feedback (👍/👎) para cada sugestão
    5. Exportação para Excel/PDF
    6. Métricas de performance do modelo ML
    """
    
    return dbc.Container([
        # Header da página
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-brain me-2"),
                    "Sugestões Inteligentes de Compra"
                ], className="text-primary mb-0"),
                html.P("Sistema ML para recomendações de estoque personalizadas", 
                      className="text-muted")
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-brain me-1"),
                        "Treinar Modelo ML"
                    ], id="btn-train-ml", color="info", outline=True, size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Exportar Excel"
                    ], id="btn-export-excel", color="success", outline=True, size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-file-pdf me-1"),
                        "Relatório PDF"
                    ], id="btn-export-pdf", color="danger", outline=True, size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Atualizar"
                    ], id="btn-refresh-suggestions", color="primary", outline=True, size="sm",
                       title="🔄 Atualiza as sugestões com os filtros atuais sem treinar novamente o modelo ML")
                ], className="float-end")
            ], width=4)
        ], className="mb-4"),
        
        # Alertas de feedback de exportação
        html.Div([
            dbc.Alert(id="alert-export-excel", is_open=False, dismissable=True, className="mb-2"),
            dbc.Alert(id="alert-export-pdf", is_open=False, dismissable=True, className="mb-2"),
            # ✅ ALERTA PARA STATUS DO MODELO ML
            dbc.Alert(id="alert-model-status", is_open=False, dismissable=True, className="mb-2")
        ]),
        
        # Filtros e controles
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Hierarquia de Produtos - Multi-seleção (PRIMEIRO)
                    dbc.Col([
                        html.Label("Categoria de Produtos:", className="form-label fw-bold"),
                        html.Div([
                            dcc.Tabs(id="tabs-hierarchy", value="tab-hier1", children=[
                                dcc.Tab(label="Nível 1", value="tab-hier1"),
                                dcc.Tab(label="Nível 2", value="tab-hier2"),
                                dcc.Tab(label="Nível 3", value="tab-hier3"),
                            ]),
                            html.Div(id="dropdown-hierarchy-container", className="mt-2"),
                            html.Small([
                                html.I(className="fas fa-layer-group me-1"),
                                "Selecione categorias específicas ou deixe vazio para todos"
                            ], className="text-muted")
                        ])
                    ], width=3),  # Primeira coluna para hierarquia
                    
                    # Cliente - Multi-seleção com busca (SEGUNDO)
                    dbc.Col([
                        html.Label("Cliente:", className="form-label fw-bold"),
                        html.Div([
                            dcc.Dropdown(
                                id="dropdown-cliente-suggestions",
                                placeholder="🔍 Digite código ou nome do cliente...",
                                multi=True,  # Permite multi-seleção
                                searchable=True,  # Permite busca
                                clearable=True,  # Botão limpar
                                className="mb-2",
                                style={"fontSize": "14px"}
                            ),
                            html.Small([
                                html.I(className="fas fa-info-circle me-1"),
                                "Pode selecionar múltiplos clientes ou deixar vazio para todos"
                            ], className="text-muted")
                        ])
                    ], width=3),  # Segunda coluna para clientes
                    
                    # Período de análise
                    dbc.Col([
                        html.Label("Período de Análise:", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id="dropdown-periodo-suggestions",
                            options=[
                                {"label": "Últimos 3 meses", "value": 3},
                                {"label": "Últimos 6 meses", "value": 6},
                                {"label": "Último ano", "value": 12},
                                {"label": "Últimos 2 anos", "value": 24}
                            ],
                            value=6,
                            className="mb-2"
                        )
                    ], width=2),
                    
                    # Classificação ABC
                    dbc.Col([
                        html.Label("ABC:", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id="dropdown-abc-suggestions",
                            options=[
                                {"label": "Todas", "value": "ALL"},
                                {"label": "Classe A", "value": "A"},
                                {"label": "Classe B", "value": "B"},
                                {"label": "Classe C", "value": "C"}
                            ],
                            value="ALL",
                            className="mb-2"
                        )
                    ], width=2),
                    
                    # Classificação XYZ
                    dbc.Col([
                        html.Label("XYZ:", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id="dropdown-xyz-suggestions",
                            options=[
                                {"label": "Todas", "value": "ALL"},
                                {"label": "X (estável)", "value": "X"},
                                {"label": "Y (moderada)", "value": "Y"},
                                {"label": "Z (variável)", "value": "Z"}
                            ],
                            value="ALL",
                            className="mb-2"
                        )
                    ], width=2)
                ],
                className="mb-3"
            ),
            
            # Segunda linha de filtros
            dbc.Row([
                # Top N sugestões
                dbc.Col([
                    html.Label("Top N Sugestões:", className="form-label fw-bold"),
                    dcc.Input(
                        id="input-top-n-suggestions",
                        type="number",
                        value=20,
                        min=5,
                        max=100,
                        className="form-control mb-2"
                    )
                ], width=2),
                
                # Botão aplicar filtros
                dbc.Col([
                    html.Label("", className="form-label"),
                    html.Br(),
                    dbc.Button([
                        html.I(className="fas fa-search me-1"),
                        "Aplicar"
                    ], id="btn-apply-filters-suggestions", color="primary", className="w-100")
                ], width=2)
            ])
        ])
        ], className="mb-4"),
        
        # Métricas e KPIs
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-total-suggestions", className="text-primary mb-0"),
                        html.P("Sugestões Geradas", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-valor-total", className="text-success mb-0"),
                        html.P("Valor Total Sugerido", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-confianca-media", className="text-info mb-0"),
                        html.P("Confiança Média", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-classe-a", className="text-warning mb-0"),
                        html.P("Produtos Classe A", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-feedback-positivo", className="text-success mb-0"),
                        html.P("Taxa Aprovação", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-modelo-status", className="text-primary mb-0"),
                        html.P("Status do Modelo", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=2)
        ], className="mb-4"),
        
        # Gráficos de análise
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Distribuição ABC-XYZ"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="graph-abc-xyz-distribution")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Probabilidade de Recompra"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="graph-probability-distribution")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Tabela principal de sugestões
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-list me-2"),
                            "Sugestões de Compra Rankeadas"
                        ], className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Switch(
                            id="switch-show-details",
                            label="Mostrar detalhes",
                            value=False,
                            className="float-end"
                        )
                    ], width=4)
                ])
            ]),
            dbc.CardBody([
                html.Div(id="div-suggestions-table"),
                
                # Área de loading
                dcc.Loading(
                    id="loading-suggestions",
                    type="default",
                    children=[html.Div(id="loading-output-suggestions")]
                )
            ])
        ], className="mb-4"),
        
        # Modal para treinamento ML
        dbc.Modal([
            dbc.ModalHeader([
                html.H4([
                    html.I(className="fas fa-brain me-2"),
                    "Treinamento do Modelo ML"
                ])
            ]),
            dbc.ModalBody([
                html.Div(id="modal-body-training-progress"),
                dcc.Interval(
                    id="interval-training-progress",
                    interval=2000,  # 2 segundos
                    n_intervals=0,
                    disabled=True
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Fechar", id="btn-close-training-modal", color="secondary"),
                dbc.Button([
                    html.I(className="fas fa-play me-1"),
                    "Iniciar Treinamento"
                ], id="btn-start-training", color="primary")
            ])
        ], id="modal-training", size="lg"),
        
        # Modal para detalhes da sugestão
        dbc.Modal([
            dbc.ModalHeader([
                html.H4([
                    html.I(className="fas fa-info-circle me-2"),
                    "Detalhes da Sugestão"
                ])
            ]),
            dbc.ModalBody(id="modal-body-suggestion-details"),
            dbc.ModalFooter([
                dbc.Button("Fechar", id="btn-close-modal", color="secondary")
            ])
        ], id="modal-suggestion-details", size="lg"),
        
        # Toast para feedback
        html.Div([
            dbc.Toast(
                id="toast-feedback",
                header="Feedback Registrado",
                is_open=False,
                dismissable=True,
                duration=3000,
                icon="success",
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 9999}
            )
        ]),
        
        # Stores para dados
        dcc.Store(id="store-suggestions-data"),
        dcc.Store(id="store-current-filters"),
        dcc.Store(id="store-feedback-stats"),
        dcc.Store(id="store-training-status"),
        dcc.Store(id="store-hierarchy-data")  # Para armazenar dados de hierarquia
        
    ], fluid=True)

def create_suggestions_table(df_suggestions, show_details=False):
    """
    Cria tabela interativa de sugestões com botões de feedback
    
    Args:
        df_suggestions: DataFrame com sugestões
        show_details: Se deve mostrar colunas detalhadas
    
    Returns:
        DataTable component
    """
    if df_suggestions.empty:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Nenhuma sugestão encontrada com os filtros aplicados."
        ], color="warning")
    
    # Colunas básicas
    columns = [
        {
            "name": "Material", 
            "id": "material",
            "type": "text"
        },
        {
            "name": "Produto", 
            "id": "produto",
            "type": "text"
        },
        {
            "name": "Cliente", 
            "id": "cliente",
            "type": "text"
        },
        {
            "name": "Qtd. Sugerida", 
            "id": "quantidade_sugerida",
            "type": "numeric",
            "format": {"specifier": ",.0f"}
        },
        {
            "name": "Safety Stock", 
            "id": "safety_stock",
            "type": "numeric",
            "format": {"specifier": ",.0f"}
        },
        {
            "name": "Classificação", 
            "id": "classificacao",
            "type": "text"
        },
        {
            "name": "Prob. Recompra", 
            "id": "prob_recompra",
            "type": "numeric",
            "format": {"specifier": ".1%"}
        },
        {
            "name": "Confiança", 
            "id": "confianca",
            "type": "numeric",
            "format": {"specifier": ".0f"}
        },
        {
            "name": "Priority Score", 
            "id": "priority_score",
            "type": "numeric",
            "format": {"specifier": ".1f"}
        }
    ]
    
    # Colunas detalhadas
    if show_details:
        detail_columns = [
            {
                "name": "Demanda Média/Mês", 
                "id": "demanda_media_mensal",
                "type": "numeric",
                "format": {"specifier": ",.1f"}
            },
            {
                "name": "Valor Médio/Mês", 
                "id": "valor_medio_mensal",
                "type": "numeric",
                "format": {"specifier": ",.2f"}
            },
            {
                "name": "Coef. Variação", 
                "id": "coef_variacao",
                "type": "numeric",
                "format": {"specifier": ".2f"}
            },
            {
                "name": "Histórico (meses)", 
                "id": "historico_meses",
                "type": "numeric"
            },
            {
                "name": "Cobertura (dias)", 
                "id": "cobertura_dias",
                "type": "numeric"
            }
        ]
        columns.extend(detail_columns)
    
    # Adiciona coluna de ações
    columns.append({
        "name": "Ações", 
        "id": "acoes",
        "type": "text"
    })
    
    # Prepara dados para exibição
    display_data = df_suggestions.copy()
    
    # Garante que todas as colunas necessárias existem
    required_columns = {
        'material': 'N/A',
        'produto': 'Produto não informado',
        'cliente': 'Cliente não informado',
        'quantidade_sugerida': 0,
        'safety_stock': 0,
        'classificacao': 'N/A',
        'confianca': 0,
        'priority_score': 0,
        'prob_recompra': 0.0
    }
    
    for col, default_val in required_columns.items():
        if col not in display_data.columns:
            display_data[col] = default_val
    
    # Adiciona coluna de probabilidade se não existir
    if 'prob_recompra' not in display_data.columns or display_data['prob_recompra'].isna().all():
        # Usa heurística baseada no priority_score
        display_data['prob_recompra'] = display_data['priority_score'] / 100
    
    # Cria botões de ação maiores e mais visíveis
    display_data['acoes'] = display_data.apply(lambda row: 
        f"👍 Bom  👎 Ruim  ℹ️ Info", 
        axis=1
    )
    
    return dash_table.DataTable(
        id="table-suggestions",
        columns=columns,
        data=display_data.to_dict('records'),
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            # Prioridade 1: Produtos de alta prioridade (Classe A + alta confiança)
            {
                'if': {
                    'filter_query': '{classificacao} contains A && {confianca} > 70',
                    'column_id': ['material', 'produto', 'quantidade_sugerida', 'valor_estimado']
                },
                'backgroundColor': '#d1f2eb',  # Verde claro
                'color': '#00695c',
                'fontWeight': 'bold',
            },
            # Prioridade 2: Produtos classe A (mesmo com confiança média)
            {
                'if': {
                    'filter_query': '{classificacao} contains A',
                    'column_id': ['material', 'produto', 'classificacao']
                },
                'backgroundColor': '#fff3cd',  # Amarelo claro
                'color': '#856404',
            },
            # Prioridade 3: Alta probabilidade de recompra (independente da classe)
            {
                'if': {
                    'filter_query': '{prob_recompra} >= 0.7',
                    'column_id': ['prob_recompra']
                },
                'backgroundColor': '#d4edda',  # Verde claro
                'color': '#155724',
            },
            # Destaque negativo: Baixa confiança (necessita atenção)
            {
                'if': {
                    'filter_query': '{confianca} <= 50',
                    'column_id': ['confianca']
                },
                'backgroundColor': '#f8d7da',  # Vermelho claro
                'color': '#721c24',
            },
            # Destaque para alto valor estimado (acima de R$ 1000)
            {
                'if': {
                    'filter_query': '{valor_estimado} > 1000',
                    'column_id': ['valor_estimado']
                },
                'backgroundColor': '#e7f3ff',  # Azul claro
                'color': '#0056b3',
                'fontWeight': 'bold',
            }
        ],
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in display_data.to_dict('records')
        ],
        css=[{
            'selector': '.dash-table-tooltip',
            'rule': 'background-color: grey; font-family: monospace; color: white'
        }]
    )

def create_abc_xyz_chart(df_suggestions):
    """Cria gráfico de distribuição ABC-XYZ"""
    if df_suggestions.empty:
        return {}
    
    # Conta distribuição
    abc_xyz_counts = df_suggestions['classificacao'].value_counts()
    
    # Cores personalizadas para cada classe
    color_map = {
        'AX': '#1f77b4', 'AY': '#ff7f0e', 'AZ': '#2ca02c',
        'BX': '#d62728', 'BY': '#9467bd', 'BZ': '#8c564b',
        'CX': '#e377c2', 'CY': '#7f7f7f', 'CZ': '#bcbd22'
    }
    
    colors = [color_map.get(classe, '#17becf') for classe in abc_xyz_counts.index]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=abc_xyz_counts.index,
            values=abc_xyz_counts.values,
            hole=0.3,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Distribuição ABC-XYZ das Sugestões",
        showlegend=True,
        height=300,
        margin=dict(t=50, b=10, l=10, r=10)
    )
    
    return fig

def create_probability_chart(df_suggestions):
    """Cria gráfico de distribuição de probabilidades"""
    if df_suggestions.empty or 'prob_recompra' not in df_suggestions.columns:
        return {}
    
    # Histograma de probabilidades
    fig = px.histogram(
        df_suggestions,
        x='prob_recompra',
        nbins=20,
        title="Distribuição de Probabilidades de Recompra",
        labels={
            'prob_recompra': 'Probabilidade de Recompra',
            'count': 'Número de Produtos'
        }
    )
    
    fig.update_layout(
        height=300,
        margin=dict(t=50, b=50, l=50, r=50),
        xaxis_title="Probabilidade de Recompra",
        yaxis_title="Número de Produtos"
    )
    
    # Adiciona linhas de referência
    fig.add_vline(x=0.3, line_dash="dash", line_color="orange", 
                 annotation_text="Baixa", annotation_position="top")
    fig.add_vline(x=0.7, line_dash="dash", line_color="green", 
                 annotation_text="Alta", annotation_position="top")
    
    return fig