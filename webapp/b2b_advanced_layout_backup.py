"""
Layout B2B Avançado Integrado - Versão Otimizada
Sistema completo de recomendações com UX aprimorada
"""

import dash
from dash import html, dcc, dash_table, callback, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import numpy as np

# Importações dos sistemas implementados
from utils.recommendation_actions import RecommendationActionHandler
from utils.ml_feedback_learning import MLFeedbackLearningSystem, FeedbackMetrics
from utils.advanced_export_system import AdvancedExportSystem
from utils.ux_optimizations import (
    create_loading_skeleton, 
    create_enhanced_filter_section,
    create_performance_metrics_card,
    create_smart_insights_section,
    CUSTOM_CSS
)


def create_overview_content():
    """Cria conteúdo de overview para B2B"""
    return html.Div([
        html.H4("📊 Visão Geral do Sistema B2B"),
        html.P("Dashboard em desenvolvimento...")
    ])


def create_gaps_content():
    """Cria conteúdo de análise de gaps"""
    return html.Div([
        html.H4("🎯 Análise de Gaps de Mercado"),
        html.P("Análise de oportunidades em desenvolvimento...")
    ])


def create_seasonality_content():
    """Cria conteúdo de análise de sazonalidade"""
    return html.Div([
        html.H4("📅 Análise de Sazonalidade"),
        html.P("Análise temporal em desenvolvimento...")
    ])


def create_empty_state():
    """Cria estado vazio para o dashboard"""
    return html.Div([
        html.H4("💫 Sistema B2B Inicializando"),
        html.P("Carregando dados...")
    ])


def create_b2b_filters_section():
    """Cria seção de filtros avançados para B2B com UX otimizada"""
    return create_enhanced_filter_section()  # Usa o componente otimizado


def create_b2b_modals():
                        placeholder="Selecionar materiais...",
                        multi=True,
                        className="mb-3"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Período de Análise:", className="fw-bold"),
                    dcc.DatePickerRange(
                        id="filter-b2b-periodo",
                        display_format="DD/MM/YYYY",
                        className="mb-3"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Confidence Mínima:", className="fw-bold"),
                    dcc.Slider(
                        id="filter-b2b-confidence",
                        min=0,
                        max=100,
                        value=70,
                        marks={i: f"{i}%" for i in range(0, 101, 25)},
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="mb-3"
                    )
                ], width=3)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Filtros de Prioridade:", className="fw-bold"),
                    dbc.Checklist(
                        id="filter-b2b-priority",
                        options=[
                            {"label": "🔥 Alta Prioridade", "value": "alta"},
                            {"label": "⚡ Sazonalidade Ativa", "value": "sazonal"},
                            {"label": "📈 Alto Potencial ROI", "value": "roi"},
                            {"label": "🎯 Gaps Críticos", "value": "gaps"}
                        ],
                        value=["alta"],
                        inline=True,
                        className="mb-3"
                    )
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Hierarquia Produto - Nível 1:", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-hier-produto-1",
                        placeholder="Carregando categorias...",
                        multi=True,
                        className="mb-3",
                        options=[
                            {"label": "Carregando...", "value": "loading"}
                        ]
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Hierarquia Produto - Nível 2:", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-hier-produto-2",
                        placeholder="Selecionar subcategoria...",
                        multi=True,
                        className="mb-3"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Hierarquia Produto - Nível 3:", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-hier-produto-3",
                        placeholder="Selecionar produto...",
                        multi=True,
                        className="mb-3"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Unidade de Negócio:", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-unidade-negocio",
                        placeholder="Carregando unidades...",
                        multi=True,
                        className="mb-3",
                        options=[
                            {"label": "Carregando...", "value": "loading"}
                        ]
                    )
                ], width=3)
            ])
        ], className="py-2")
    ], className="mb-4")


def create_b2b_modals():
    """Cria modais para ações do sistema B2B"""
    return html.Div([
        # Modal de exportação
        dbc.Modal([
            dbc.ModalHeader("🚀 Exportação Avançada"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("📊 Relatório Executivo", className="text-primary"),
                                html.P("Sumário executivo com KPIs principais, insights estratégicos e recomendações prioritárias."),
                                dbc.Button(
                                    "Gerar PDF Executivo",
                                    id="btn-export-executive-pdf",
                                    color="primary",
                                    className="w-100"
                                )
                            ])
                        ])
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("📈 Análise Detalhada", className="text-success"),
                                html.P("Dados completos com análises, gráficos e métricas detalhadas para análise técnica."),
                                dbc.Button(
                                    "Gerar Excel Completo",
                                    id="btn-export-detailed-excel",
                                    color="success",
                                    className="w-100"
                                )
                            ])
                        ])
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("📦 Pacote Completo", className="text-info"),
                                html.P("Todos os formatos: PDF executivo + Excel detalhado + gráficos PNG."),
                                dbc.Button(
                                    "Download Pacote ZIP",
                                    id="btn-export-complete-package",
                                    color="info",
                                    className="w-100"
                                )
                            ])
                        ])
                    ], width=12)
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Fechar", id="btn-close-export-modal", color="secondary")
            ])
        ], id="modal-b2b-export", size="lg", is_open=False),
        
        # Modal de feedback detalhado
        dbc.Modal([
            dbc.ModalHeader("💡 Feedback Detalhado"),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Tipo de Feedback:", className="fw-bold"),
                            dcc.Dropdown(
                                id="feedback-type-detailed",
                                options=[
                                    {"label": "👍 Recomendação Útil", "value": "positive"},
                                    {"label": "👎 Recomendação Inadequada", "value": "negative"},
                                    {"label": "❓ Necessita Mais Informações", "value": "neutral"},
                                    {"label": "🚀 Já Implementado", "value": "implemented"}
                                ],
                                placeholder="Selecionar tipo..."
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Prioridade:", className="fw-bold"),
                            dcc.Dropdown(
                                id="feedback-priority",
                                options=[
                                    {"label": "🔥 Alta", "value": "high"},
                                    {"label": "⚡ Média", "value": "medium"},
                                    {"label": "📝 Baixa", "value": "low"}
                                ],
                                value="medium"
                            )
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Comentários Adicionais:", className="fw-bold"),
                            dbc.Textarea(
                                id="feedback-comments",
                                placeholder="Compartilhe suas observações, sugestões ou contexto adicional...",
                                rows=4
                            )
                        ], width=12)
                    ], className="mb-3"),
                    html.Div(id="feedback-material-context")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Enviar Feedback", id="btn-submit-detailed-feedback", color="primary"),
                dbc.Button("Cancelar", id="btn-cancel-feedback", color="secondary")
            ])
        ], id="modal-b2b-feedback", size="lg", is_open=False)
    ])


def create_advanced_b2b_layout():
    """
    Cria layout avançado B2B com todas as funcionalidades implementadas
    
    Funcionalidades COMPLETAS:
    1. Análise de Gaps de Mercado (W% e Q%)
    2. Detecção de Sazonalidade
    3. KPIs Comerciais Avançados
    4. Benchmark de Mercado
    5. Sistema de Alertas Inteligentes
    6. Insights Acionáveis
    7. Exportação Avançada (PDF/Excel/ZIP)
    8. Sistema de Feedback e Aprendizado ML
    9. Filtros Avançados com Salvamento
    10. Interface Completa de Recomendações
    """
    
    return dbc.Container([
        # Stores para dados
        dcc.Store(id="store-b2b-recommendations-data"),
        dcc.Store(id="store-b2b-analytics-data"),
        dcc.Store(id="store-b2b-export-data"),
        
        # Header da página
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-lightbulb me-3"),
                    "Sugestão Inteligente de Compras"
                ], className="text-primary mb-0"),
                html.P("Sistema B2B de Recomendações - Laura Representações", className="text-muted")
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync me-1"),
                        "Atualizar Dados"
                    ], id="btn-refresh-b2b-data", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Exportar"
                    ], id="btn-export-b2b-data", color="success", size="sm")
                ])
            ], width=4, className="text-end")
        ], className="mb-4"),
        
        # Loading skeleton para feedback visual
        html.Div(id="b2b-loading-container", children=create_loading_skeleton(), style={"display": "none"}),
        
        # Seção de Filtros Avançados
        create_b2b_filters_section(),
        
        # KPIs principais com UX otimizada
        create_performance_metrics_card(),
        
        # Insights inteligentes
        create_smart_insights_section(),
        
        # NOVA SEÇÃO: Análise de Gaps de Compra
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-search me-2"),
                            "Análise de Gaps de Compra"
                        ], className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-chart-line me-1"), "Analisar Gaps"],
                            id="btn-analyze-gaps",
                            color="warning",
                            size="sm"
                        )
                    ], width=4, className="text-end")
                ])
            ]),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    html.Strong("O que são Gaps de Compra?"),
                    html.Br(),
                    "Produtos que possuem importante demanda (cotações/orçamentos) mas que não foram efetivamente comprados por todos os clientes ou por clientes específicos."
                ], color="info", className="mb-3"),
                
                html.Div(id="gaps-analysis-container", children=[
                    html.P([
                        html.I(className="fas fa-play me-2"),
                        "Clique em 'Analisar Gaps' para identificar oportunidades de venda."
                    ], className="text-muted text-center")
                ])
            ])
        ], className="mb-4"),
        
        # NOVA SEÇÃO: Análise de Conversão e Cross-Selling
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Análise de Conversão e Cross-Selling"
                        ], className="mb-0")
                    ], width=6),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="fas fa-percentage me-1"), "Analisar Conversão"],
                                id="btn-analyze-conversion",
                                color="info",
                                size="sm"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-shopping-cart me-1"), "Cross-Selling"],
                                id="btn-analyze-cross-selling",
                                color="success",
                                size="sm"
                            )
                        ])
                    ], width=6, className="text-end")
                ])
            ]),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-lightbulb me-2"),
                    html.Strong("Análise Estratégica de Vendas:"),
                    html.Br(),
                    html.Strong("Conversão: "), "Identifica produtos com alta demanda (cotações) mas baixa conversão em vendas.",
                    html.Br(),
                    html.Strong("Cross-Selling: "), "Detecta produtos frequentemente comprados juntos para estratégias de venda cruzada."
                ], color="primary", className="mb-3"),
                
                dbc.Tabs([
                    dbc.Tab(label="📊 Taxa de Conversão", tab_id="tab-conversion-analysis"),
                    dbc.Tab(label="🛒 Oportunidades Cross-Selling", tab_id="tab-cross-selling-analysis")
                ], id="segmentation-analysis-tabs", active_tab="tab-conversion-analysis"),
                
                html.Div(id="segmentation-analysis-content", className="mt-3", children=[
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="conversion-analysis-container", children=[
                                html.P([
                                    html.I(className="fas fa-play me-2"),
                                    "Clique em 'Analisar Conversão' para identificar produtos com baixa taxa de conversão."
                                ], className="text-muted text-center")
                            ])
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="cross-selling-analysis-container", children=[
                                html.P([
                                    html.I(className="fas fa-play me-2"),
                                    "Clique em 'Cross-Selling' para descobrir oportunidades de venda cruzada."
                                ], className="text-muted text-center")
                            ])
                        ], width=12)
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Tabela de recomendações
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-table me-2"),
                    "Recomendações de Compra"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Div(id="b2b-recommendations-table-container"),
                html.Hr(),
                html.P([
                    html.Strong("Explicabilidade: "),
                    "Cada sugestão é baseada em análise de gaps de mercado, sazonalidade histórica, "
                    "padrões de recompra e benchmarking com clientes similares. "
                    "Confidence ≥70% indica alta confiabilidade estatística."
                ], className="text-muted small")
            ])
        ], className="mb-4"),
        
        # Seção de gráficos analíticos
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-chart-line me-2"),
                    "Análises de Apoio à Decisão"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📊 Penetração de Mercado", tab_id="tab-b2b-penetracao"),
                    dbc.Tab(label="📅 Sazonalidade", tab_id="tab-b2b-sazonalidade"),
                    dbc.Tab(label="🎯 Gaps & Oportunidades", tab_id="tab-b2b-gaps"),
                    dbc.Tab(label="💰 ROI Estimado", tab_id="tab-b2b-roi")
                ], id="b2b-analytics-tabs", active_tab="tab-b2b-penetracao"),
                html.Div(id="b2b-analytics-content", className="mt-3")
            ])
        ], className="mb-4"),
        
        # Alertas inteligentes
        html.Div(id="b2b-intelligent-alerts-container"),
        
        # Painel de Monitoramento de Aprendizado ML
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-brain me-2"),
                            "Sistema de Aprendizado ML"
                        ], className="mb-0")
                    ], width=6),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-sync me-1"), "Executar Ciclo de Aprendizado"],
                            id="btn-b2b-run-learning-cycle",
                            color="info",
                            size="sm"
                        )
                    ], width=6, className="text-end")
                ]),
                # Alerta de feedback do aprendizado
                dbc.Alert(id="b2b-learning-feedback", is_open=False, dismissable=True, className="mt-3")
            ]),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📊 Métricas de Feedback", tab_id="tab-b2b-feedback-metrics"),
                    dbc.Tab(label="⚙️ Pesos do Algoritmo", tab_id="tab-b2b-ml-weights"),
                    dbc.Tab(label="📈 Performance de Materiais", tab_id="tab-b2b-material-performance")
                ], id="b2b-learning-tabs", active_tab="tab-b2b-feedback-metrics"),
                html.Div(id="b2b-learning-content", className="mt-3")
            ])
        ], className="mb-4"),
        
        # Modais para ações
        create_b2b_modals(),
        
        # Toast para feedback
        dbc.Toast(
            id="b2b-feedback-toast",
            header="Feedback Registrado",
            is_open=False,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
        
    ], fluid=True)