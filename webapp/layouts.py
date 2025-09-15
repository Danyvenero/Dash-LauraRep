"""
Módulo de layouts da aplicação
Integração com interface de chat para preparação do agente de IA
"""

from dash import html, dcc, dash_table
from dash.dash_table.Format import Format, Scheme
from dash.dash_table import FormatTemplate
import dash_bootstrap_components as dbc
from webapp.auth import require_login, create_user_info_component, create_login_layout
from webapp.chat_interface import create_chat_interface
from utils import is_authenticated
import datetime

def create_sidebar():
    """Cria sidebar da aplicação"""
    return html.Div([
        # Header da sidebar
        html.Div([
            html.H4("Dashboard WEG", className="text-white mb-1"),
            html.P("Laura Representações", className="text-light small mb-0")
        ], className="sidebar-header"),
        
        # Filtros globais
        html.Div([
            html.H6("Filtros Globais", className="text-white mb-3"),
            
            # Filtro de Ano
            html.Div([
                html.Label("Ano:", className="text-white small"),
                dcc.RangeSlider(
                    id='global-filtro-ano',
                    min=2018,
                    max=datetime.datetime.now().year + 1,
                    step=1,
                    value=[2018, datetime.datetime.now().year],
                    marks={year: str(year) for year in range(2018, datetime.datetime.now().year + 1, 1)},
                    tooltip={"placement": "bottom", "always_visible": True},
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # Filtro de Mês
            html.Div([
                html.Label("Mês:", className="text-white small"),
                dcc.RangeSlider(
                    id='global-filtro-mes',
                    min=1,
                    max=12,
                    step=1,
                    value=[1, 12],
                    marks={i: str(i) for i in range(1, 13)},
                    tooltip={"placement": "bottom", "always_visible": True},
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # Filtro de Unidade de Negócios
            # html.Div([
            #     html.Label("BU:", className="text-white small"),
            #     dcc.Dropdown(
            #         id='global-filtro-bu',
            #         options=[],
            #         value=None,
            #         multi=True,
            #         placeholder="Selecione as BUs...",
            #         className="mb-3"
            #     )
            # ], className="mb-3"),

            # Filtro de Cliente
            html.Div([
                html.Label("Cliente:", className="text-white small"),
                dcc.Dropdown(
                    id='global-filtro-cliente',
                    options=[],
                    value=None,
                    multi=True,
                    placeholder="Selecione clientes...",
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # Filtro de Hierarquia de Produto
            html.Div([
                html.Label("Hierarquia Produto:", className="text-white small"),
                dcc.Dropdown(
                    id='global-filtro-hierarquia',
                    options=[],
                    value=None,
                    multi=True,
                    placeholder="Selecione hierarquias...",
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # Filtro de Canal
            html.Div([
                html.Label("Canal:", className="text-white small"),
                dcc.Dropdown(
                    id='global-filtro-canal',
                    options=[],
                    value=None,
                    multi=True,
                    placeholder="Selecione canais...",
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # TOP Clientes
            html.Div([
                html.Label("TOP Clientes:", className="text-white small"),
                dbc.Input(
                    id='global-filtro-top-clientes',
                    type="number",
                    value=10,
                    min=1,
                    max=1500,
                    className="mb-3"
                )
            ], className="mb-3"),
            
            # Dias sem compra
            html.Div([
                html.Label("Dias sem compra:", className="text-white small"),
                dcc.RangeSlider(
                    id='global-filtro-dias-sem-compra',
                    min=0,
                    max=365,
                    value=[0, 365],
                    marks={0: '0', 90: '90', 180: '180', 365: '365+'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], className="mb-4")
        ], className="px-3"),
        
        # Menu de navegação
        html.Div([
            html.H6("Menu", className="text-white mb-3"),
            html.Ul([
                html.Li([
                    dcc.Link("📊 Visão Geral", href="/app/overview", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("👥 Clientes", href="/app/clients", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("📦 Mix de Produtos", href="/app/products", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("🎯 Funil & Ações", href="/app/funnel", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("🤖 Assistente IA", href="/app/chat", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("🎯 Insights IA", href="/app/insights", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("📊 Analytics Avançados", href="/app/analytics", className="sidebar-menu-item")
                ]),
                html.Li([
                    dcc.Link("⚙️ Configurações", href="/app/config", className="sidebar-menu-item")
                ])
            ], className="sidebar-menu")
        ], className="px-3")
    ], className="sidebar")

def create_main_layout():
    """Cria layout principal da aplicação"""
    return html.Div([
        create_sidebar(),
        html.Div([
            # Header superior
            html.Div([
                html.Div([
                    html.H4("Dashboard WEG", id="page-title", className="mb-0"),
                    create_user_info_component()
                ], className="d-flex justify-content-between align-items-center")
            ], className="bg-white p-3 mb-4 shadow-sm"),
            
            # Conteúdo da página
            html.Div(id="page-main-content")
        ], className="main-content")
    ])

@require_login
def create_overview_layout():
    """Cria layout da página de visão geral"""
    return html.Div([
        # KPIs principais
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-entrada-pedidos", className="kpi-value text-primary"),
                        html.P("Entrada de Pedidos", className="kpi-label"),
                        html.P(id="kpi-entrada-variacao", className="kpi-change")
                    ])
                ], className="kpi-card")
            ], width=12, md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-valor-carteira", className="kpi-value text-info"),
                        html.P("Valor Carteira", className="kpi-label"),
                        html.P(id="kpi-carteira-variacao", className="kpi-change")
                    ])
                ], className="kpi-card")
            ], width=12, md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(id="kpi-faturamento", className="kpi-value text-success"),
                        html.P("Faturamento", className="kpi-label"),
                        html.P(id="kpi-faturamento-variacao", className="kpi-change")
                    ])
                ], className="kpi-card")
            ], width=12, md=4)
        ], className="mb-4"),
        
        # KPIs por Unidade de Negócio
        html.Div([
            html.H5("Faturamento por Unidade de Negócio", className="mb-3"),
            dbc.Row(id="kpis-unidades-negocio", className="mb-4")
        ]),
        
        # Gráfico de evolução
        html.Div([
            html.H5("Evolução de Vendas", className="mb-3"),
            dcc.Graph(id="grafico-evolucao-vendas")
        ], className="graph-container")
    ])

@require_login
def create_clients_layout():
    """Cria layout da página de clientes"""
    return html.Div([
        # Controles da tabela
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("📥 Download CSV", id="btn-download-csv-clientes", color="primary", outline=True),
                    dbc.Button("✅ Selecionar Todos", id="btn-select-all-clientes", color="secondary", outline=True),
                    dbc.Button("❌ Desmarcar Todos", id="btn-deselect-all-clientes", color="secondary", outline=True),
                    dbc.Button("🗑️ Limpar Filtros", id="btn-clear-filters-clientes", color="warning", outline=True)
                ])
            ], width=12, md=8),
            dbc.Col([
                html.Label("Tamanho da página:", className="small"),
                dcc.Dropdown(
                    id="table-page-size-clientes",
                    options=[
                        {"label": "5", "value": 5},
                        {"label": "10", "value": 10},
                        {"label": "25", "value": 25},
                        {"label": "50", "value": 50},
                        {"label": "100", "value": 100}
                    ],
                    value=5,
                    clearable=False
                )
            ], width=12, md=4)
        ], className="mb-3"),
        
        # Tabela de KPIs por cliente
        html.Div([
            dash_table.DataTable(
                id="tabela-kpis-clientes",
                columns=[
                    {"name": "Código", "id": "cod_cliente", "type": "text"},
                    {"name": "Cliente", "id": "cliente", "type": "text"},
                    {"name": "Dias sem Compra", "id": "dias_sem_compra", "type": "numeric"},
                    {"name": "Freq. Média (dias)", "id": "frequencia_media_compra", "type": "numeric"},
                    {"name": "Mix Produtos", "id": "mix_produtos", "type": "numeric"},
                    {"name": "% Mix", "id": "percentual_mix", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Cotados", "id": "produtos_cotados", "type": "numeric"},
                    {"name": "Comprados", "id": "produtos_comprados", "type": "numeric"},
                    {"name": "% Não Comprado", "id": "perc_nao_comprado", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "UN", "id": "unidades_negocio", "type": "text"}
                ],
                data=[],
                filter_action="native",
                sort_action="native",
                page_action="native",
                page_current=0,
                page_size=25,
                row_selectable="multi",
                selected_rows=[],
                style_cell={
                    'textAlign': 'left', 
                    'fontSize': '12px',
                    'fontFamily': 'Arial, sans-serif',
                    'padding': '8px',
                    'border': '1px solid #ddd'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'color': '#333',
                    'border': '1px solid #ddd',
                    'textAlign': 'center'
                },
                style_data={
                    'backgroundColor': '#ffffff',
                    'color': '#333',
                    'border': '1px solid #ddd'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    },
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#e3f2fd',
                        'border': '1px solid #1976d2'
                    },
                    {
                        'if': {'column_id': 'cod_cliente'},
                        'fontWeight': 'bold',
                        'width': '80px'
                    },
                    {
                        'if': {'column_id': 'cliente'},
                        'width': '200px'
                    },
                    {
                        'if': {'filter_query': '{dias_sem_compra} > 365'},
                        'backgroundColor': '#ffebee',
                        'color': '#f5697e',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{dias_sem_compra} > 90 && {dias_sem_compra} <= 365'},
                        'backgroundColor': '#fff8e1',
                        'color': '#fac002',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{dias_sem_compra} <= 90'},
                        'backgroundColor': '#e8f5e8',
                        'color': '#456945',
                        'fontWeight': 'bold'
                    }
                ]
            )
        ], className="mb-4"),
        
        # Gráfico de status dos clientes
        html.Div([
            html.H5("Distribuição de Status dos Clientes", className="mb-3"),
            dcc.Graph(id="grafico-status-clientes")
        ], className="graph-container"),
        
        # Componente de download para clientes
        dcc.Download(id="download-csv-clientes")
    ])

@require_login
def create_products_layout():
    """Cria layout da página de produtos"""
    return html.Div([
        # Controles
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Filtros de Visualização", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Top Produtos:", className="small"),
                                dbc.Input(id="filter-top-produtos", type="number", value=20, min=5, max=50)
                            ], width=6),
                            dbc.Col([
                                html.Label("Paleta de Cores:", className="small"),
                                dcc.Dropdown(
                                    id="filter-color-scale",
                                    options=[
                                        {"label": "WEG Blue", "value": "weg_blue"},
                                        {"label": "Performance", "value": "performance"},
                                        {"label": "Viridis", "value": "viridis"},
                                        {"label": "Plasma", "value": "plasma"}
                                    ],
                                    value="weg_blue"
                                )
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12, md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("📥 Download CSV", id="btn-download-csv-produtos", color="primary"),
                    dbc.Button("📄 PDF por Cliente", id="btn-pdf-cliente", color="success"),
                    dbc.Button("🤖 Sugestões IA", id="btn-sugestoes-ia", color="info")
                ], className="mb-2 d-flex justify-content-end")
            ], width=12, md=4, className="d-flex align-items-center justify-content-end")
        ], className="mb-4"),
        
        # Gráfico de bolhas
        html.Div([
            html.H5("Matriz Clientes × Produtos", className="mb-3"),
            dcc.Graph(id="grafico-bolhas-produtos")
        ], className="graph-container mb-4"),
        
        # Gráfico de Pareto
        html.Div([
            html.H5("Análise de Pareto - Produtos", className="mb-3"),
            dcc.Graph(id="grafico-pareto-produtos")
        ], className="graph-container mb-4"),
        
        # Tabela de Análise de Produtos
        html.Div([
            html.H5("Análise Detalhada de Produtos", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Filtrar por Material:", className="small"),
                    dcc.Dropdown(
                        id="filter-material-table",
                        placeholder="Todos os materiais",
                        multi=True,
                        searchable=True,
                        clearable=True,
                        style={'fontSize': '14px'},
                        options=[]  # Será populado dinamicamente pelo callback
                    )
                ], width=12, md=6),
                dbc.Col([
                    html.Label("Tamanho da página:", className="small"),
                    dcc.Dropdown(
                        id="table-page-size-produtos",
                        options=[
                            {"label": "10", "value": 10},
                            {"label": "25", "value": 25},
                            {"label": "50", "value": 50},
                            {"label": "100", "value": 100}
                        ],
                        value=25
                    )
                ], width=12, md=6)
            ], className="mb-3"),
            
            # Botões de controle da tabela
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("✅ Selecionar Todos", id="btn-select-all-produtos", color="secondary", outline=True, size="sm"),
                        dbc.Button("❌ Desmarcar Todos", id="btn-deselect-all-produtos", color="secondary", outline=True, size="sm"),
                        dbc.Button("🗑️ Limpar Filtros", id="btn-clear-filters-produtos", color="warning", outline=True, size="sm")
                    ], className="mb-2")
                ], width=12, className="d-flex justify-content-start")
            ], className="mb-2"),
            
            dash_table.DataTable(
                id="tabela-analise-produtos",
                columns=[
                    {"name": "Material", "id": "material", "type": "text"},
                    {"name": "Produto", "id": "produto", "type": "text"},
                    {"name": "Hierarquia", "id": "hierarquia", "type": "text"},
                    {"name": "Recorrência Compra", "id": "recorrencia_compra", "type": "numeric", "format": {"specifier": ",.0f"}},
                    {"name": "Recorrência Cotação", "id": "recorrencia_cotacao", "type": "numeric", "format": {"specifier": ",.0f"}},
                    {"name": "Taxa Conversão (%)", "id": "taxa_conversao", "type": "numeric", "format": {"specifier": ",.1f"}},
                    {"name": "Qty Média Cotada", "id": "qty_media_cotada", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Valor Médio", "id": "valor_medio", "type": "numeric", "format": FormatTemplate.money(2)},
                    {"name": "Faturamento Total", "id": "faturamento_total", "type": "numeric", "format": FormatTemplate.money(2)}
                ],
                data=[],  # Dados serão carregados pelo callback
                page_size=25,
                page_action="native",
                sort_action="native",
                filter_action="native",
                row_selectable="multi",
                selected_rows=[],
                style_cell={
                    'textAlign': 'left',
                    'fontSize': '12px',
                    'fontFamily': 'Arial, sans-serif',
                    'padding': '8px',
                    'border': '1px solid #ddd'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'color': '#333',
                    'border': '1px solid #ddd',
                    'textAlign': 'center'
                },
                style_data={
                    'backgroundColor': '#ffffff',
                    'color': '#333',
                    'border': '1px solid #ddd'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    },
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#e3f2fd',
                        'border': '1px solid #1976d2'
                    },
                    {
                        'if': {'column_id': 'material'},
                        'fontWeight': 'bold',
                        'width': '100px'
                    },
                    {
                        'if': {'column_id': 'produto'},
                        'width': '200px'
                    },
                    {
                        'if': {'column_id': 'hierarquia'},
                        'width': '120px',
                        'color': '#666'
                    }
                ]
            )
        ], className="graph-container mb-4"),
        
        # Insights da IA
        html.Div(id="insights-ia-produtos", className="mb-4"),
        
        # Componentes de download
        dcc.Download(id="download-csv-produtos"),
        dcc.Download(id="download-pdf-produtos"),
        
        # Modal de Sugestões IA
        dbc.Modal([
            dbc.ModalHeader("🤖 Sugestões de Inteligência Artificial"),
            dbc.ModalBody([
                html.Div(id="conteudo-sugestoes-ia")
            ]),
            dbc.ModalFooter([
                dbc.Button("Fechar", id="btn-fechar-modal-ia", className="ms-auto", n_clicks=0)
            ])
        ], id="modal-sugestoes-ia", size="lg", is_open=False)
    ])

@require_login
def create_analytics_layout():
    """Cria layout da página de Analytics Avançados"""
    return html.Div([
        # Header com seletor de análise
        dbc.Row([
            dbc.Col([
                html.H4("📊 Analytics Avançados", className="mb-0"),
                html.P("Análises estatísticas e insights inteligentes", className="text-muted small")
            ], width=8),
            dbc.Col([
                dcc.Dropdown(
                    id="analytics-tipo-analise",
                    options=[
                        {"label": "🎯 Gaps de Oportunidade", "value": "gaps"},
                        {"label": "⚠️ Alertas de Inatividade", "value": "inatividade"},
                        {"label": "📈 Análise de Sazonalidade", "value": "sazonalidade"},
                        {"label": "📋 Demanda de Cotações", "value": "cotacoes"}
                    ],
                    value="gaps",
                    placeholder="Selecione o tipo de análise"
                )
            ], width=4)
        ], className="mb-4"),
        
        # Área de conteúdo dinâmico
        html.Div(id="analytics-content"),
        
        # Componentes de download
        dcc.Download(id="download-analytics-csv"),
        dcc.Download(id="download-analytics-pdf"),
        
        # Stores para dados
        dcc.Store(id="analytics-data-store"),
        dcc.Store(id="analytics-config-store")
    ])

@require_login
def create_config_layout():
    """Cria layout da página de configurações"""
    return html.Div([
        # Upload de arquivos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📁 Carregar Dados"),
                    dbc.CardBody([
                        html.Div([
                            html.H6("Upload de Arquivos Excel"),
                            html.P("Selecione os arquivos de vendas, cotações e materiais cotados:", 
                                  className="text-muted small"),
                            
                            dcc.Upload(
                                id='upload-vendas',
                                children=html.Div([
                                    '📊 Arraste ou clique para upload de Vendas'
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=True
                            ),
                            
                            dcc.Upload(
                                id='upload-cotacoes',
                                children=html.Div([
                                    '💼 Arraste ou clique para upload de Cotações'
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=True
                            ),
                            
                            dcc.Upload(
                                id='upload-materiais',
                                children=html.Div([
                                    '🔧 Arraste ou clique para upload de Materiais Cotados'
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=True
                            ),
                            
                            html.Div(id="upload-status", className="mt-3"),
                            
                            dbc.Button(
                                "📂 Carregar Dados Salvos",
                                id="btn-load-saved-data",
                                color="secondary",
                                className="mt-3"
                            )
                        ])
                    ])
                ])
            ], width=12, md=6),
            
            # Configurações de thresholds
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⚙️ Configurações de Thresholds"),
                    dbc.CardBody([
                        html.H6("Thresholds por Unidade de Negócio"),
                        html.P("Configure os limites para classificação de performance:", 
                              className="text-muted small"),
                        
                        html.Div(id="threshold-inputs"),
                        
                        dbc.Button(
                            "💾 Salvar Configurações",
                            id="btn-save-thresholds",
                            color="success",
                            className="mt-3"
                        ),
                        
                        html.Div(id="threshold-status", className="mt-3")
                    ])
                ])
            ], width=12, md=6)
        ], className="mb-4"),
        
        # Seção de limpeza de dados
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🗑️ Gerenciamento de Dados"),
                    dbc.CardBody([
                        html.H6("Limpeza Seletiva de Dados"),
                        html.P("Limpe dados específicos do banco de dados. Esta ação é irreversível.", 
                              className="text-muted small"),
                        
                        # Estatísticas atuais dos dados
                        html.Div(id="data-stats", className="mb-3"),
                        
                        dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Atenção: A limpeza de dados é permanente e não pode ser desfeita."
                        ], color="warning", className="mb-3"),
                        
                        # Botões de limpeza
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-chart-line me-2"), "Limpar Vendas"],
                                    id="btn-clear-vendas",
                                    color="danger",
                                    outline=True,
                                    className="w-100 mb-2"
                                )
                            ], width=12, md=4),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-file-contract me-2"), "Limpar Cotações"],
                                    id="btn-clear-cotacoes",
                                    color="danger",
                                    outline=True,
                                    className="w-100 mb-2"
                                )
                            ], width=12, md=4),
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-tools me-2"), "Limpar Materiais"],
                                    id="btn-clear-materiais",
                                    color="danger",
                                    outline=True,
                                    className="w-100 mb-2"
                                )
                            ], width=12, md=4)
                        ]),
                        
                        # Botão para limpeza total
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className="fas fa-trash-alt me-2"), "Limpar Todos os Dados"],
                                    id="btn-clear-all-data",
                                    color="danger",
                                    className="w-100 mt-2"
                                )
                            ], width=12)
                        ]),
                        
                        html.Div(id="clear-data-status", className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Log de atividades
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Log de Atividades"),
                    dbc.CardBody([
                        html.Div(id="activity-log")
                    ])
                ])
            ], width=12)
        ]),
        
        # Modais de confirmação para limpeza de dados
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Limpeza de Vendas")),
            dbc.ModalBody([
                html.P("Tem certeza que deseja limpar TODOS os dados de vendas?"),
                html.P("Esta ação é irreversível e removerá todos os registros de vendas do banco de dados.", 
                       className="text-danger")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancel-vendas", className="ms-auto", n_clicks=0),
                dbc.Button("Confirmar Limpeza", id="modal-confirm-vendas", color="danger", className="ms-2", n_clicks=0)
            ])
        ], id="modal-confirm-clear-vendas", is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Limpeza de Cotações")),
            dbc.ModalBody([
                html.P("Tem certeza que deseja limpar TODOS os dados de cotações?"),
                html.P("Esta ação é irreversível e removerá todos os registros de cotações do banco de dados.", 
                       className="text-danger")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancel-cotacoes", className="ms-auto", n_clicks=0),
                dbc.Button("Confirmar Limpeza", id="modal-confirm-cotacoes", color="danger", className="ms-2", n_clicks=0)
            ])
        ], id="modal-confirm-clear-cotacoes", is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Limpeza de Materiais")),
            dbc.ModalBody([
                html.P("Tem certeza que deseja limpar TODOS os dados de materiais cotados?"),
                html.P("Esta ação é irreversível e removerá todos os registros de materiais cotados do banco de dados.", 
                       className="text-danger")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancel-materiais", className="ms-auto", n_clicks=0),
                dbc.Button("Confirmar Limpeza", id="modal-confirm-materiais", color="danger", className="ms-2", n_clicks=0)
            ])
        ], id="modal-confirm-clear-materiais", is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmar Limpeza Total")),
            dbc.ModalBody([
                html.P("ATENÇÃO: Tem certeza que deseja limpar TODOS OS DADOS?"),
                html.P("Esta ação irá remover:", className="text-danger fw-bold"),
                html.Ul([
                    html.Li("Todos os dados de vendas"),
                    html.Li("Todos os dados de cotações"),
                    html.Li("Todos os dados de materiais cotados"),
                    html.Li("Todos os datasets cadastrados")
                ], className="text-danger"),
                html.P("Esta ação é completamente irreversível!", className="text-danger fw-bold")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="modal-cancel-all", className="ms-auto", n_clicks=0),
                dbc.Button("CONFIRMAR LIMPEZA TOTAL", id="modal-confirm-all", color="danger", className="ms-2", n_clicks=0)
            ])
        ], id="modal-confirm-clear-all", is_open=False)
    ])

@require_login
def create_chat_layout():
    """Cria layout da página do assistente de IA"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-robot me-2"),
                    "Assistente de IA - Preparação para o Futuro"
                ], className="mb-4"),
                
                # Informações sobre o desenvolvimento
                dbc.Alert([
                    html.H5([
                        html.I(className="fas fa-info-circle me-2"),
                        "Sobre esta Funcionalidade"
                    ]),
                    html.P([
                        "Este é o início do nosso agente de IA conversacional! Atualmente funciona com comandos estruturados, ",
                        "mas será evoluído para entender perguntas em linguagem natural."
                    ]),
                    html.Hr(),
                    html.Strong("Roadmap de Evolução:"),
                    html.Ul([
                        html.Li("Fase 1 (Atual): Comandos estruturados"),
                        html.Li("Fase 2 (Q1 2026): NLP básico em português"),
                        html.Li("Fase 3 (Q2-Q3 2026): IA conversacional completa"),
                        html.Li("Fase 4 (Q4 2026): Agente proativo com insights automáticos")
                    ])
                ], color="info", className="mb-4"),
                
                # Interface do chat
                create_chat_interface()
            ], width=12, lg=8),
            
            dbc.Col([
                # Painel de informações técnicas
                dbc.Card([
                    dbc.CardHeader(html.H5("🔧 Informações Técnicas")),
                    dbc.CardBody([
                        html.H6("Status Atual"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.I(className="fas fa-check-circle text-success me-2"),
                                "Sistema heurístico operacional"
                            ], className="border-0"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-check-circle text-success me-2"),
                                "Comandos estruturados funcionais"
                            ], className="border-0"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-spinner text-warning me-2"),
                                "NLP em desenvolvimento"
                            ], className="border-0"),
                            dbc.ListGroupItem([
                                html.I(className="fas fa-clock text-info me-2"),
                                "LLM integration planejada"
                            ], className="border-0")
                        ], flush=True, className="mb-3"),
                        
                        html.H6("Próximas Funcionalidades"),
                        html.Ul([
                            html.Li("Perguntas em linguagem natural"),
                            html.Li("Geração automática de relatórios"),
                            html.Li("Análises personalizadas sob demanda"),
                            html.Li("Insights proativos baseados em dados"),
                            html.Li("Integração com ferramentas externas")
                        ], className="small"),
                        
                        html.Hr(),
                        html.Small([
                            "📖 Documentação completa: ",
                            html.A("ROADMAP_AGENTE_IA.md", href="#", className="text-decoration-none")
                        ], className="text-muted")
                    ])
                ], className="mb-4"),
                
                # Estatísticas de uso
                dbc.Card([
                    dbc.CardHeader(html.H5("📊 Estatísticas")),
                    dbc.CardBody([
                        html.P("Funcionalidade em desenvolvimento.", className="text-muted"),
                        html.Small("Em breve: estatísticas de uso, análises mais solicitadas, e métricas de performance.")
                    ])
                ])
            ], width=12, lg=4)
        ])
    ])

def get_layout(pathname):
    """Retorna layout baseado no pathname"""
    if not is_authenticated() and pathname != '/login':
        return create_login_layout()
    
    if pathname == '/login':
        return create_login_layout()
    elif pathname == '/app/overview' or pathname == '/app' or pathname == '/':
        return create_main_layout()
    elif pathname == '/app/clients':
        return create_main_layout()
    elif pathname == '/app/products':
        return create_main_layout()
    elif pathname == '/app/funnel':
        return create_main_layout()
    elif pathname == '/app/chat':
        return create_main_layout()
    elif pathname == '/app/insights':
        return create_main_layout()
    elif pathname == '/app/config':
        return create_main_layout()
    elif pathname == '/app/analytics':
        return create_main_layout()
    else:
        return html.Div([
            html.H1("404 - Página não encontrada"),
            dcc.Link("Voltar ao início", href="/app/overview")
        ])
