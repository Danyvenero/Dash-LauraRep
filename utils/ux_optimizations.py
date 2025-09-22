#!/usr/bin/env python3
"""
Otimizações de Performance e UX para Sistema B2B
Implementa melhorias na interface e feedback visual
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go

def create_loading_skeleton():
    """Cria um skeleton loading mais elegante"""
    return dbc.Card([
        dbc.CardBody([
            # Header skeleton
            dbc.Row([
                dbc.Col([
                    html.Div(className="placeholder-glow", children=[
                        html.Span(className="placeholder col-6 bg-secondary"),
                        html.Span(className="placeholder col-4 bg-secondary ms-2"),
                    ])
                ], width=12)
            ], className="mb-3"),
            
            # Content skeleton
            dbc.Row([
                dbc.Col([
                    html.Div(className="placeholder-glow", children=[
                        html.Span(className="placeholder col-8 bg-light"),
                        html.Span(className="placeholder col-6 bg-light"),
                        html.Span(className="placeholder col-10 bg-light"),
                    ])
                ], width=8),
                dbc.Col([
                    html.Div(className="placeholder-glow", children=[
                        html.Span(className="placeholder col-12 bg-light", style={"height": "120px"}),
                    ])
                ], width=4),
            ])
        ])
    ], className="mb-3 shadow-sm")

def create_enhanced_filter_section():
    """Cria seção de filtros com melhor UX"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-filter me-2 text-primary"),
                "Filtros Inteligentes"
            ], className="mb-0"),
            dbc.Badge("Beta", color="warning", className="ms-2")
        ]),
        dbc.CardBody([
            # Status do carregamento
            dbc.Alert(
                id="filter-status-alert",
                children=[
                    html.I(className="fas fa-sync-alt fa-spin me-2"),
                    "Carregando filtros..."
                ],
                color="info",
                className="mb-3",
                style={"display": "none"}
            ),
            
            # Componente para carregamento automático dos filtros
            dcc.Interval(
                id="filter-loader-interval",
                interval=1000,  # 1 segundo - mais rápido para melhor UX
                n_intervals=0,
                max_intervals=5  # Mais tentativas
            ),
            
            # Filtros em layout responsivo
            dbc.Row([
                dbc.Col([
                    dbc.Label("Cliente(s):", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-cliente",
                        placeholder="🔍 Selecione um ou mais clientes...",
                        multi=True,
                        className="mb-3",
                        style={"minHeight": "38px"}
                    )
                ], width=12, lg=6),
                
                dbc.Col([
                    dbc.Label("Unidade de Negócio:", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-b2b-unidade-negocio",
                        placeholder="🏢 Carregando unidades...",
                        multi=True,
                        className="mb-3",
                        style={"minHeight": "38px"}
                    )
                ], width=12, lg=6),
            ]),
            
            # Filtros hierárquicos em accordion
            dbc.Accordion([
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Produto - Nível 1:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filter-b2b-hier-produto-1",
                                placeholder="🏷️ Carregando categorias...",
                                multi=True,
                                className="mb-3"
                            )
                        ], width=12, lg=4),
                        
                        dbc.Col([
                            dbc.Label("Produto - Nível 2:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filter-b2b-hier-produto-2",
                                placeholder="Selecione Nível 1 primeiro",
                                multi=True,
                                className="mb-3",
                                disabled=False  # Será controlado por callback
                            )
                        ], width=12, lg=4),
                        
                        dbc.Col([
                            dbc.Label("Produto - Nível 3:", className="fw-bold"),
                            dcc.Dropdown(
                                id="filter-b2b-hier-produto-3",
                                placeholder="Selecione Nível 2 primeiro",
                                multi=True,
                                className="mb-3",
                                disabled=False  # Será controlado por callback
                            )
                        ], width=12, lg=4),
                    ])
                ], title="🎯 Filtros de Produto Hierárquicos", item_id="hierarchy-filters")
            ], start_collapsed=False, className="mb-3"),
            
            # Botões de ação
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-search me-2"),
                            "Aplicar Filtros"
                        ], id="btn-apply-filters", color="primary", size="sm"),
                        
                        dbc.Button([
                            html.I(className="fas fa-undo me-2"),
                            "Limpar"
                        ], id="btn-clear-filters", color="outline-secondary", size="sm"),
                        
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Salvar"
                        ], id="btn-save-filters", color="outline-success", size="sm"),
                    ])
                ], width="auto"),
                
                dbc.Col([
                    dbc.Progress(
                        id="filter-progress",
                        value=0,
                        style={"height": "4px", "display": "none"}
                    )
                ], width=True)
            ], className="align-items-center"),
            
            # Alert para feedback
            dbc.Alert(
                id="alert-filters-saved",
                is_open=False,
                duration=3000,
                color="success"
            )
        ])
    ], className="shadow-sm mb-4")

def create_performance_metrics_card():
    """Card com métricas de performance do sistema"""
    return dbc.Card([
        dbc.CardHeader([
            html.H6([
                html.I(className="fas fa-tachometer-alt me-2 text-success"),
                "Performance do Sistema"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P("Tempo de Carregamento", className="text-muted mb-1"),
                    html.H5("< 3s", className="text-success mb-0")
                ], width=4),
                dbc.Col([
                    html.P("Registros Processados", className="text-muted mb-1"),
                    html.H5("56.7K", className="text-info mb-0")
                ], width=4),
                dbc.Col([
                    html.P("Cache Hit Rate", className="text-muted mb-1"),
                    html.H5("94%", className="text-warning mb-0")
                ], width=4),
            ])
        ])
    ], className="border-left-success shadow-sm")

def create_smart_insights_section():
    """Seção de insights inteligentes"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-lightbulb me-2 text-warning"),
                "Insights Inteligentes"
            ], className="mb-0"),
            dbc.Badge("AI Powered", color="info", className="ms-2")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.I(className="fas fa-chart-line me-2"),
                        html.Strong("Oportunidade Detectada: "),
                        "Cliente X tem potencial 23% maior em produtos da categoria Y"
                    ], color="success", className="border-left-success")
                ], width=12),
                
                dbc.Col([
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Atenção: "),
                        "Queda de 15% nas vendas da categoria Z no último trimestre"
                    ], color="warning", className="border-left-warning")
                ], width=12),
                
                dbc.Col([
                    dbc.Alert([
                        html.I(className="fas fa-star me-2"),
                        html.Strong("Sucesso: "),
                        "Taxa de conversão de recomendações: 78% acima da média"
                    ], color="info", className="border-left-info")
                ], width=12),
            ])
        ])
    ], className="shadow-sm")

# CSS personalizado para melhorar o visual
CUSTOM_CSS = """
.border-left-success {
    border-left: 4px solid #28a745 !important;
}

.border-left-warning {
    border-left: 4px solid #ffc107 !important;
}

.border-left-info {
    border-left: 4px solid #17a2b8 !important;
}

.placeholder {
    display: inline-block;
    min-height: 1em;
    vertical-align: middle;
    cursor: wait;
    background-color: currentColor;
    opacity: .5;
}

.placeholder.col-6 {
    width: 50%;
}

.placeholder.col-4 {
    width: 33.3333333333%;
}

.placeholder.col-8 {
    width: 66.6666666667%;
}

.placeholder.col-10 {
    width: 83.3333333333%;
}

.placeholder.col-12 {
    width: 100%;
}

.placeholder-glow .placeholder {
    animation: placeholder-glow 2s ease-in-out infinite alternate;
}

@keyframes placeholder-glow {
    50% {
        opacity: .2;
    }
}

.shadow-sm {
    box-shadow: 0 .125rem .25rem rgba(0,0,0,.075)!important;
}

/* Melhorias nos dropdowns */
.Select-control {
    transition: all 0.2s ease-in-out;
}

.Select-control:hover {
    box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

/* Animações suaves */
.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
"""

if __name__ == "__main__":
    print("✅ Componentes de otimização UX criados com sucesso!")
    print("📋 Componentes disponíveis:")
    print("   - create_loading_skeleton(): Skeleton loading elegante")
    print("   - create_enhanced_filter_section(): Filtros com melhor UX")
    print("   - create_performance_metrics_card(): Métricas de performance")
    print("   - create_smart_insights_section(): Insights inteligentes")
    print("   - CUSTOM_CSS: Estilos personalizados")