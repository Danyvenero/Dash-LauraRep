"""
Módulo de layouts da aplicação
Integração com interface de chat para preparação do agente de IA
"""

from dash import html, dcc
from dash import dash_table
import dash_bootstrap_components as dbc
from webapp.auth import require_login, create_user_info_component, create_login_layout
from webapp.chat_interface import create_chat_interface
from webapp.b2b_advanced_layout import create_advanced_b2b_layout
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
                    marks={year: {'label': str(year), 'style': {'color': 'white', 'fontSize': '11px'}} 
                          for year in range(2018, datetime.datetime.now().year + 1, 1)},
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
                    max=1095,
                    value=[0, 1095],
                    marks={0: '0', 365: '1 ano', 730: '2 anos', 1095: '3 anos'},
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
                    dcc.Link("🚀 B2B Analytics Avançado", href="/app/b2b-advanced", className="sidebar-menu-item")
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
        # Placeholder simples para visão geral (pode ser expandido conforme necessário)
        dbc.Alert("Selecione um menu para iniciar a análise.", color="light")
    ])

@require_login
def create_clients_layout():
    """Cria layout da página de clientes"""
    return html.Div([
        # Tabela de KPIs por cliente
        html.Div([
            html.Div(id="tabela-kpis-clientes-container", children=[
                dash_table.DataTable(
                    id='tabela-kpis-clientes',
                    columns=[
                        {"name": "Código", "id": "cod_cliente"},
                        {"name": "Cliente", "id": "cliente"},
                        {"name": "Total Vendas", "id": "total_vendas", "type": "numeric", "format": {"specifier": ",.2f"}},
                        {"name": "Primeira Compra", "id": "primeira_compra"},
                        {"name": "Última Compra", "id": "ultima_compra"},
                        {"name": "Freq. Compras", "id": "frequencia_compra", "type": "numeric"},
                        {"name": "Dias sem Compra", "id": "dias_sem_compra", "type": "numeric"},
                        {"name": "Mix Produtos", "id": "mix_produtos", "type": "numeric"},
                        {"name": "% Mix", "id": "percentual_mix", "type": "numeric"},
                        {"name": "Prod. Cotados", "id": "produtos_cotados", "type": "numeric"},
                        {"name": "Prod. Comprados", "id": "produtos_comprados", "type": "numeric"},
                        {"name": "% Não Comprado", "id": "perc_nao_comprado", "type": "numeric"}
                    ],
                    data=[],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    export_format="csv",
                    export_headers="display"
                )
            ])
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
        # Tabela de Análise de Produtos (mover para antes dos gráficos)
        html.Div([
            html.H5("Análise Detalhada de Produtos", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Filtrar por Material:", className="small"),
                    dcc.Input(
                        id="filter-material-search",
                        type="text",
                        placeholder="Digite para buscar (ex.: motor -disjuntor, code:1440, 14402)",
                        style={'width': '100%', 'fontSize': '14px'}
                    ),
                    html.Div([
                        html.A(
                            "Como filtrar? Ver exemplos",
                            id="material-search-help-toggle",
                            n_clicks=0,
                            className="small",
                            style={"cursor": "pointer"}
                        ),
                        dbc.Collapse(
                            dbc.Card(dbc.CardBody([
                                html.Strong("Operadores suportados:"),
                                html.Ul([
                                    html.Li('"frase exata" — busca exatamente a frase'),
                                    html.Li('−termo — exclui itens com o termo (ex.: -disjuntor)'),
                                    html.Li('code:abc — só no código (material)'),
                                    html.Li('desc:xyz — só na descrição (produto)'),
                                    html.Li('^ini — começa com; fim$ — termina com'),
                                    html.Li('a|b — OR (qualquer um); AND é implícito entre termos')
                                ], className="mb-2"),
                                html.Strong("Exemplos úteis:"),
                                html.Ul([
                                    html.Li('motor -disjuntor'),
                                    html.Li('code:1440 desc:motor'),
                                    html.Li('^mot tor$'),
                                    html.Li('"motor 1cv" | "motor 2cv"'),
                                ], className="mb-0")
                            ]), className="mt-2"),
                            id="material-search-help",
                            is_open=False
                        ),
                        # (removido) checkbox 'Aplicar seleção do dropdown'
                    ])
                ], width=12)
            ], className="mb-3"),
            
            dbc.Row([
                # Limite de itens (vazio = todos)
                dbc.Col([
                    html.Label("Máx. de itens (opcional):", className="small"),
                    dbc.Input(
                        id="filter-top-produtos",
                        type="number",
                        value=None,
                        placeholder="",
                        style={"maxWidth": "220px"}
                    ),
                    html.Div(className="mt-2"),
                    html.Label("Tamanho da página:", className="small"),
                    dcc.Dropdown(
                        id="table-page-size-produtos",
                        options=[
                            {"label": "10", "value": 10},
                            {"label": "25", "value": 25},
                            {"label": "50", "value": 50},
                            {"label": "100", "value": 100}
                        ],
                        value=25,
                        clearable=False,
                        style={"maxWidth": "220px"}
                    )
                ], width=12, md=3),
                dbc.Col([
                    html.Label("Pesos RFM (Recência / Frequência / Valor)", className="small"),
                    dbc.Row([
                        dbc.Col([
                            html.Small("Recência"),
                            dcc.Slider(
                                id="rfm-weight-r", min=0, max=100, step=5, value=40,
                                marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                                tooltip={"placement": "bottom", "always_visible": False},
                                className="w-100"
                            )
                        ], width=12, md=4),
                        dbc.Col([
                            html.Small("Frequência"),
                            dcc.Slider(
                                id="rfm-weight-f", min=0, max=100, step=5, value=30,
                                marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                                tooltip={"placement": "bottom", "always_visible": False},
                                className="w-100"
                            )
                        ], width=12, md=4),
                        dbc.Col([
                            html.Small("Valor"),
                            dcc.Slider(
                                id="rfm-weight-m", min=0, max=100, step=5, value=30,
                                marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                                tooltip={"placement": "bottom", "always_visible": False},
                                className="w-100"
                            )
                        ], width=12, md=4)
                    ]),
                    html.Small("Dica: os pesos são normalizados para somarem 100% automaticamente.", className="text-muted"),
                    html.Br(),
                    html.Small(id="rfm-weights-display", className="text-muted")
                ], width=12, md=9)
            ], className="mb-3"),

            # Botões de ação abaixo dos sliders RFM
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("📥 Download CSV", id="btn-download-csv-produtos", color="primary"),
                        dbc.Button("📄 PDF por Cliente", id="btn-pdf-cliente", color="success"),
                        dbc.Button("🚀 B2B Analytics", id="btn-b2b-redirect", 
                                 color="info", href="/app/b2b-advanced", external_link=True)
                    ], className="d-flex justify-content-end")
                ], width=12, className="d-flex align-items-center justify-content-end")
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
            
            # Container para tabela de produtos - será preenchido por callback
            html.Div(id="tabela-analise-produtos-container", children=[
                dbc.Card([
                    dbc.CardBody([
                        dbc.Spinner([
                            html.H6("Carregando dados dos produtos...", className="text-muted mb-2"),
                            html.P("Aguarde enquanto processamos as informações.", className="small text-muted")
                        ], color="primary", type="border", spinnerClassName="text-center")
                    ])
                ], className="mb-4")
            ])
        ], className="graph-container mb-4"),

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
        html.Div(id="insights-ia-produtos", className="mb-4"),
        
        # Componentes de download
        dcc.Download(id="download-csv-produtos"),
        dcc.Download(id="download-pdf-produtos")
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
    elif pathname == '/app/products' or pathname == '/produtos':
        return create_main_layout()
    elif pathname == '/app/funnel':
        return create_main_layout()
    elif pathname == '/app/chat':
        return create_main_layout()
    elif pathname == '/app/purchase-suggestions':
        # Redireciona para B2B Analytics unificado
        return create_advanced_b2b_layout()
    elif pathname == '/app/b2b-advanced':
        return create_advanced_b2b_layout()
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
