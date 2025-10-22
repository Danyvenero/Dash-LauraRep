"""
Módulo de layouts da aplicação
Integração com interface de chat para preparação do agente de IA
"""

from dash import html, dcc
from dash import dash_table
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from webapp.auth import require_login, create_user_info_component, create_login_layout
from webapp.chat_interface import create_chat_interface
from webapp.b2b_advanced_layout import create_advanced_b2b_layout
from utils import is_authenticated
from utils.table_styles import (
    TABLE_STYLE_HEADER_PRIMARY,
    TABLE_STYLE_CELL_DEFAULT,
    TABLE_STYLE_TABLE_FULL_WIDTH,
)
from utils.aggrid_config import build_column_defs, default_col_def, default_grid_options
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
                    value=None,
                    min=1,
                    max=1500,
                    placeholder="Todos",
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
            dbc.Alert("Selecione um menu para iniciar a análise.", color="light"),

            # Gráfico de Pareto de Produtos (movido da página de Produtos)
            html.Div([
                html.H5("Análise de Pareto - Produtos", className="mb-3"),
                dcc.Graph(id="grafico-pareto-produtos")
            ], className="graph-container mb-4")
    ])

@require_login
def create_clients_layout():
    """Cria layout da página de clientes"""
    return html.Div([
        # Controles superiores (RFV e paginação/exportação)
        dbc.Row([
            dbc.Col([
                html.Label("Peso R (Recência)", className="small mb-1"),
                dcc.Slider(id="slider-r-weight", min=0, max=1, step=0.05, value=0.33,
                           tooltip={"always_visible": False}, marks=None)
            ], md=4),
            dbc.Col([
                html.Label("Peso F (Frequência)", className="small mb-1"),
                dcc.Slider(id="slider-f-weight", min=0, max=1, step=0.05, value=0.33,
                           tooltip={"always_visible": False}, marks=None)
            ], md=4),
            dbc.Col([
                html.Label("Peso M (Monetário)", className="small mb-1"),
                dcc.Slider(id="slider-v-weight", min=0, max=1, step=0.05, value=0.34,
                           tooltip={"always_visible": False}, marks=None)
            ], md=4),
        ], className="g-3 mb-3"),

        # Tip text e exibição dos pesos normalizados (como na página de produtos)
        dbc.Row([
            dbc.Col([
                html.Small("Dica: os pesos são normalizados para somarem 100% automaticamente.", className="text-muted"),
                html.Br(),
                html.Small(id="clients-rfv-weights-display", className="text-muted")
            ], md=12)
        ], className="mb-2"),

        dbc.Row([
            dbc.Col([
                html.Label("Tamanho da página", className="small mb-1"),
                dcc.Dropdown(
                    id="clients-page-size",
                    options=[
                        {"label": "Todos", "value": "all"},
                        {"label": "10", "value": 10},
                        {"label": "25", "value": 25},
                        {"label": "50", "value": 50},
                        {"label": "100", "value": 100}
                    ],
                    value=10,
                    clearable=False,
                    style={"width": "120px"}
                )
            ], md=2),
            dbc.Col([
                html.Small(id="clients-counter", className="text-muted")
            ], md=10, className="d-flex align-items-end")
        ], className="mb-2"),

        # Botões de controle e ação na mesma linha, alinhados pelas bases
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("✅ Selecionar Todos", id="btn-select-all-clientes", color="secondary", outline=True, size="sm"),
                    dbc.Button("❌ Desmarcar Todos", id="btn-deselect-all-clientes", color="secondary", outline=True, size="sm"),
                    dbc.Button("�️ Limpar Filtros", id="btn-clear-filters-clientes", color="warning", outline=True, size="sm")
                ])
            ], md=6, className="d-flex justify-content-start"),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("📥 Exportar Excel", id="btn-export-excel-clientes", color="primary"),
                    dbc.Button("📄 PDF por Cliente", id="btn-pdf-cliente-clientes", color="success"),
                    dbc.Button("� B2B Analytics", id="btn-b2b-redirect-clientes", color="info", href="/app/b2b-advanced", external_link=True)
                ])
            ], md=6, className="d-flex justify-content-end")
        ], className="mb-3 align-items-end"),

        # Seleção de colunas visíveis (mesma UX da página de produtos)
        dbc.Row([
            dbc.Col([
                html.Label("Colunas visíveis na tabela", className="mb-1 fw-semibold"),
                dcc.Dropdown(
                    id="clientes-column-select",
                    multi=True,
                    placeholder="Selecione as colunas (vazio = todas)",
                    options=[
                        {"label": "Código", "value": "cod_cliente"},
                        {"label": "Cliente", "value": "cliente"},
                        {"label": "RFV Score", "value": "rfv_score"},
                        {"label": "RFV Classe", "value": "rfv_class"},
                        {"label": "Total Vendas", "value": "total_vendas"},
                        {"label": "Última Compra", "value": "ultima_compra"},
                        {"label": "Freq. Compras", "value": "frequencia_compra"},
                        {"label": "Freq. Média (dias)", "value": "frequencia_media_compra"},
                        {"label": "Dias sem Compra", "value": "dias_sem_compra"},
                        {"label": "Mix Produtos", "value": "mix_produtos"},
                        {"label": "% Mix", "value": "percentual_mix"},
                        {"label": "Prod. Cotados", "value": "produtos_cotados"},
                        {"label": "Prod. Comprados", "value": "produtos_comprados"},
                        {"label": "% Não Comprado", "value": "perc_nao_comprado"},
                    ],
                    style={"maxWidth": "100%"},
                    clearable=True,
                ),
                html.Div([
                    dbc.Button("Salvar preset de colunas", id="btn-save-clientes-col-preset", color="primary", outline=True, size="sm", className="mt-2 me-2"),
                    dbc.Button("Reset para padrão", id="btn-reset-clientes-col-preset", color="secondary", outline=True, size="sm", className="mt-2 me-2"),
                    html.Small("Dica: deixe vazio para exibir todas as colunas.", className="text-muted d-block mt-1")
                ]),
                dcc.Store(id="clientes-column-preset", storage_type="local")
            ], width=12)
        ], className="mb-2"),

        # Tabela de KPIs por cliente
        html.Div([
            html.Div(id="tabela-kpis-clientes-container", children=[
                dag.AgGrid(
                    id='tabela-kpis-clientes',
                    rowData=[],
                    columnDefs=build_column_defs(
                        [
                            "cod_cliente",
                            "cliente",
                            "rfv_score",
                            "rfv_class",
                            "total_vendas",
                            "ultima_compra",
                            "frequencia_compra",
                            "frequencia_media_compra",
                            "dias_sem_compra",
                            "mix_produtos",
                            "percentual_mix",
                            "produtos_cotados",
                            "produtos_comprados",
                            "perc_nao_comprado",
                        ],
                        numeric_cols=[
                            "rfv_score",
                            "total_vendas",
                            "frequencia_compra",
                            "frequencia_media_compra",
                            "dias_sem_compra",
                            "mix_produtos",
                            "percentual_mix",
                            "produtos_cotados",
                            "produtos_comprados",
                            "perc_nao_comprado",
                        ],
                        formats={
                            "total_vendas": "currency",
                            "percentual_mix": "percent",
                            "perc_nao_comprado": "percent",
                            "rfv_score": "int",
                            "frequencia_compra": "int",
                            "frequencia_media_compra": "int",
                            "dias_sem_compra": "int",
                            "mix_produtos": "int",
                            "produtos_cotados": "int",
                            "produtos_comprados": "int",
                        },
                        display_names={
                            "cod_cliente": "Código",
                            "cliente": "Cliente",
                            "rfv_score": "RFV Score",
                            "rfv_class": "RFV Classe",
                            "total_vendas": "Total Vendas",
                            "ultima_compra": "Última Compra",
                            "frequencia_compra": "Freq. Compras",
                            "frequencia_media_compra": "Freq. Média (dias)",
                            "dias_sem_compra": "Dias sem Compra",
                            "mix_produtos": "Mix Produtos",
                            "percentual_mix": "% Mix",
                            "produtos_cotados": "Prod. Cotados",
                            "produtos_comprados": "Prod. Comprados",
                            "perc_nao_comprado": "% Não Comprado",
                        },
                    ),
                    defaultColDef=default_col_def(),
                    dashGridOptions=default_grid_options(paginationPageSize=10),
                    getRowStyle={
                        "function": (
                            "params => {"
                            " const d = params && params.data ? params.data : {};"
                            " const v = Number(d.dias_sem_compra);"
                            " if (isNaN(v)) return null;"
                            " if (v <= 30) return {backgroundColor:'rgba(40,167,69,0.12)', color:'#155724'};"
                            " if (v > 30 && v <= 90) return {backgroundColor:'rgba(255,193,7,0.18)', color:'#7a6b00'};"
                            " if (v > 90 && v <= 180) return {backgroundColor:'rgba(253,126,20,0.18)', color:'#7a3f00'};"
                            " if (v > 180) return {backgroundColor:'rgba(220,53,69,0.18)', color:'#7a1e24'};"
                            " return null;"
                            " }"
                        )
                    },
                    style={"width": "100%"}
                )
            ])
    ], className="mb-4"),
    # Store local para persistir estado do grid (Clientes)
    dcc.Store(id="clientes-grid-state", storage_type="local"),

        # Gráfico de status dos clientes
        html.Div([
            html.H5("Distribuição de Status dos Clientes", className="mb-3"),
            dcc.Graph(id="grafico-status-clientes")
        ], className="graph-container"),

        # Gráfico diagnóstico adicional
        html.Div([
            html.H5("Diagnóstico: % Não Comprado x % Mix", className="mb-3"),
            dcc.Graph(id="grafico-clientes-diagnostico")
        ], className="graph-container"),

        # Gráfico de Pareto por Cliente
        html.Div([
            html.H5("Análise de Pareto - Clientes", className="mb-3"),
            dcc.Graph(id="grafico-pareto-clientes")
        ], className="graph-container"),

        # Componentes de download para clientes
        dcc.Download(id="download-csv-clientes"),
        dcc.Download(id="download-xlsx-clientes"),
        dcc.Download(id="download-pdf-clientes")
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
                ], width=12, md=6),
                # Nova coluna: janela de meses para cálculo de "Meses Cotados Sem Compra"
                dbc.Col([
                    html.Label("Janela (meses)", className="small"),
                    dcc.Dropdown(
                        id="produtos-meses-janela",
                        options=[
                            {"label": "6", "value": 6},
                            {"label": "12", "value": 12},
                            {"label": "18", "value": 18},
                            {"label": "24", "value": 24},
                            {"label": "36", "value": 36},
                            {"label": "48", "value": 48},
                            {"label": "60", "value": 60}
                        ],
                        value=12,
                        clearable=False,
                        style={"maxWidth": "220px"}
                    ),
                    html.Small("Define a janela temporal para 'Meses Cotados Sem Compra'.", className="text-muted")
                ], width=12, md=3),
                dbc.Col([], width=12, md=3)
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

            # Seleção de colunas visíveis (persistente, fora do container substituído)
            dbc.Row([
                dbc.Col([
                    html.Label("Colunas visíveis na tabela", className="mb-1 fw-semibold"),
                    dcc.Dropdown(
                        id="produtos-column-select",
                        multi=True,
                        placeholder="Selecione as colunas (vazio = todas)",
                        options=[
                            {"label": "Material", "value": "material"},
                            {"label": "Produto", "value": "produto"},
                            {"label": "Oportunidade", "value": "oportunidade_score"},
                            {"label": "Status", "value": "status_oportunidade"},
                            {"label": "Prioridade (Venda)", "value": "prioridade_score"},
                            {"label": "Prioridade (Venda) Cat.", "value": "prioridade_venda_cat"},
                            {"label": "Prioridade (Cotação)", "value": "q_prioridade_score"},
                            {"label": "Prioridade (Cotação) Cat.", "value": "q_prioridade_cat"},
                            {"label": "Recorrência/Mês (Vendas)", "value": "recorrencia_mensal"},
                            {"label": "Recorrência Cotação/Mês", "value": "q_recorrencia_mensal"},
                            {"label": "Recência (Venda) Dias", "value": "recency_days"},
                            {"label": "Recência (Cotação) Dias", "value": "q_recency_days"},
                            {"label": "Freq. Compra (Dias)", "value": "freq_media_compra_dias"},
                            {"label": "Freq. Cotação (Dias)", "value": "freq_media_cotacao_dias"},
                            {"label": "Obs. Freq. Compra", "value": "obs_freq_compra"},
                            {"label": "Faturamento Total", "value": "faturamento_total"},
                            {"label": "Valor Cotado Total", "value": "valor_cotado_total"},
                            {"label": "Quantidade", "value": "quantidade_total"},
                            {"label": "Qtd Cotada Total", "value": "qtd_cotada_total"},
                            {"label": "Conversão Valor (%)", "value": "conversao_valor_percent"},
                            {"label": "Gap Freq (%)", "value": "freq_gap_pct"},
                            {"label": "Gap Recência (%)", "value": "recency_gap_pct"},
                            {"label": "Gap Valor (%)", "value": "valor_gap_pct"},
                            {"label": "Meses Cotados Sem Compra (janela)", "value": "meses_cotados_sem_compra"},
                            {"label": "Qtd Comprada vs Cotada (%)", "value": "pct_qtd_comprada_vs_cotada"},
                        ],
                        style={"maxWidth": "100%"},
                        clearable=True,
                    ),
                    html.Div([
                        dbc.Button("Salvar preset de colunas", id="btn-save-col-preset", color="primary", outline=True, size="sm", className="mt-2 me-2"),
                        dbc.Button("Reset para padrão", id="btn-reset-col-preset", color="secondary", outline=True, size="sm", className="mt-2 me-2"),
                        html.Small("Dica: deixe vazio para exibir todas as colunas.", className="text-muted d-block mt-1")
                    ]),
                    dcc.Store(id="produtos-column-preset", storage_type="local")
                ], width=12)
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

        # --- Oportunidades por Cliente (Onda A+B) ---
        html.Div([
            html.H5("Oportunidades por Cliente", className="mb-3"),
            html.Small("Selecione exatamente um cliente no filtro global para personalizar as oportunidades.", className="text-muted d-block mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Label("Peso da Frequência nas Cotações (0 = só valor, 1 = só frequência)", className="small"),
                    dcc.Slider(id="peso-freq-cotacao", min=0.0, max=1.0, step=0.1, value=0.5,
                               tooltip={"always_visible": False}, className="w-100"),
                    html.Small(id="opportunities-weight-hint", className="text-muted d-block mt-1")
                ], md=4),
                dbc.Col([
                    html.Label("Filtrar por Motivo", className="small"),
                    dcc.Dropdown(
                        id="opportunities-bucket-filter",
                        options=[
                            {"label": "Todos", "value": "all"},
                            {"label": "Cotou e não compra", "value": "Cotou e não compra"},
                            {"label": "Mercado forte, cliente fora", "value": "Mercado forte, cliente fora"},
                            {"label": "Baixa penetração", "value": "Baixa penetração"}
                        ],
                        value="all",
                        clearable=False
                    )
                ], md=4),
                dbc.Col([
                    html.Label("Modo de Frequência", className="small"),
                    dcc.RadioItems(
                        id="opportunities-freq-mode",
                        options=[
                            {"label": "Ocorrências", "value": "occurrences"},
                            {"label": "Ponderada por Quantidade", "value": "quantity"}
                        ],
                        value="occurrences",
                        labelStyle={"marginRight": "12px"},
                        inputStyle={"marginRight": "6px"},
                        className="small"
                    )
                ], md=4)
            ], className="mb-2"),
            html.Div(id="opportunities-summary", className="text-muted mb-2"),
            dag.AgGrid(
                id='opportunities-table',
                rowData=[],
                columnDefs=[],
                defaultColDef=default_col_def(),
                dashGridOptions=default_grid_options(paginationPageSize=25),
                style={"width": "100%"}
            )
        ], className="graph-container mb-4"),

        # Gráfico de bolhas
        html.Div([
            html.H5("Matriz Clientes × Produtos", className="mb-3"),
            dcc.Graph(id="grafico-bolhas-produtos")
        ], className="graph-container mb-4"),
        
        # Insights da IA
        html.Div(id="insights-ia-produtos", className="mb-4"),
        
        # Componentes de download
        dcc.Download(id="download-csv-produtos"),
        dcc.Download(id="download-pdf-produtos"),
        # Store local para persistir estado do grid (Produtos)
        dcc.Store(id="produtos-grid-state", storage_type="local"),
        # Disparador inicial persistente (fora do container substituído pelo callback)
        dcc.Interval(id="produtos-initial-trigger", interval=250, n_intervals=0, max_intervals=1)
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
