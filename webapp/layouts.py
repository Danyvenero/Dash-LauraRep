"""
Módulo de layouts da aplicação
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from webapp.auth import require_login, create_user_info_component, create_login_layout
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
                    dcc.Link("🤖 Insights IA", href="/app/insights", className="sidebar-menu-item")
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
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{dias_sem_compra} > 365'},
                        'backgroundColor': '#ffebee',
                        #'color': 'black',
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
        ], className="graph-container")
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
        
        # Insights da IA
        html.Div(id="insights-ia-produtos", className="mb-4")
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
    elif pathname == '/app/insights':
        return create_main_layout()
    elif pathname == '/app/config':
        return create_main_layout()
    else:
        return html.Div([
            html.H1("404 - Página não encontrada"),
            dcc.Link("Voltar ao início", href="/app/overview")
        ])
