# webapp/layouts.py

from dash import dcc, html
import dash_bootstrap_components as dbc

# --- LAYOUTS COMPARTILHADOS ---

sidebar_layout = html.Div(
    [
        html.H2("Laura Rep.", className="display-6"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Visão Geral", href="/app/overview", active="exact"),
                dbc.NavLink("KPIs por Cliente", href="/app/kpis-cliente", active="exact"),
                dbc.NavLink("KPIs de Propostas", href="/app/kpis-propostas", active="exact"),
                dbc.NavLink("Produtos (Bolhas)", href="/app/produtos", active="exact"),
                dbc.NavLink("Funil & Ações", href="/app/funil", active="exact"),
                dbc.NavLink("Configurações", href="/app/config", active="exact"),
                html.Hr(),
                dbc.NavLink("Sair (Logout)", href="/logout", active="exact"),
            ],
            vertical=True, pills=True,
        ),
        html.Hr(),
        html.Div([
            dcc.Upload(id="upload-vendas", children=dbc.Button("Upload Vendas (Anual)", color="primary", className="me-1"), multiple=True),
            dcc.Upload(id="upload-cotacoes", children=dbc.Button("Upload Cotações (Materiais + Ano)", color="secondary", className="me-1"), multiple=True),
            html.Div(id="upload-msgs", className="mt-2")
        ]),
    ],
    id="sidebar",
)

login_layout = dbc.Container([
    dbc.Row(dbc.Col(dbc.Card([
        html.H2("Login | Dashboard WEG", className="card-title text-center"),
        dbc.CardBody([
            dbc.Input(id="username", placeholder="Usuário", type="text", className="mb-3"),
            dbc.Input(id="password", placeholder="Senha", type="password", className="mb-3"),
            dbc.Button("Entrar", id="login-button", color="primary", n_clicks=0, className="w-100"),
            html.Div(id="login-error", className="mt-3"),
            html.Div(dcc.Link("Não tem uma conta? Cadastre-se", href="/cadastro"), className="text-center mt-3")
        ]),
    ], body=True, style={"maxWidth": "400px"}), width=12, className="d-flex justify-content-center"),
    className="align-items-center", style={"height": "100vh"})
], fluid=True)

cadastro_layout = dbc.Container([
    dbc.Row(dbc.Col(dbc.Card([
        html.H2("Cadastro de Usuário", className="card-title text-center"),
        dbc.CardBody([
            dbc.Input(id="cadastro-username", placeholder="Escolha um nome de usuário", type="text", className="mb-3"),
            dbc.Input(id="cadastro-password", placeholder="Crie uma senha", type="password", className="mb-3"),
            dbc.Input(id="cadastro-password-confirm", placeholder="Confirme a senha", type="password", className="mb-3"),
            dbc.Button("Cadastrar", id="cadastro-button", color="success", n_clicks=0, className="w-100"),
            html.Div(id="cadastro-msg", className="mt-3"),
            html.Div(dcc.Link("Já tem uma conta? Faça o login", href="/"), className="text-center mt-3")
        ]),
    ], body=True, style={"maxWidth": "400px"}), width=12, className="d-flex justify-content-center"),
    className="align-items-center", style={"height": "100vh"})
], fluid=True)

# --- LAYOUTS DAS PÁGINAS DE ANÁLISE ---

visao_geral_layout = dbc.Container([
    html.H1("Visão Geral"),
    html.P("Principais indicadores de performance comercial.", className="lead"),
    html.Hr(),
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Entrada de Pedidos"), dbc.CardBody([html.H4(id="kpi-entrada-pedidos", className="card-title"), html.P("Soma de 'Vlr. Entrada'", className="card-text text-muted")])]), md=4),
        dbc.Col(dbc.Card([dbc.CardHeader("Valor em Carteira"), dbc.CardBody([html.H4(id="kpi-valor-carteira", className="card-title"), html.P("Soma de 'Vlr. Carteira'", className="card-text text-muted")])]), md=4),
        dbc.Col(dbc.Card([dbc.CardHeader("Faturamento (ROL)"), dbc.CardBody([html.H4(id="kpi-faturamento", className="card-title"), html.P("Soma de 'Vlr. ROL'", className="card-text text-muted")])]), md=4),
    ])
], fluid=True)

kpis_cliente_layout = dbc.Container([

    html.H1("KPIs por Cliente"),
    html.P("Análise detalhada do comportamento de compra e cotação de cada cliente.", className="lead"),
    html.Hr(),
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.Label("Filtrar por Ano de Faturamento (intervalo)"),
                        dcc.RangeSlider(id='filtro-ano-kpis-cliente', min=2020, max=2025, step=1, value=[2024,2024], marks={str(y): str(y) for y in range(2020, 2026)}, tooltip={"placement": "bottom", "always_visible": True}),
                        html.Label("Filtrar por Mês de Faturamento (intervalo)", style={"marginTop": "1em"}),
                        dcc.RangeSlider(id='filtro-mes-kpis-cliente', min=1, max=12, step=1, value=[1,12], marks={str(m): str(m) for m in range(1, 13)}, tooltip={"placement": "bottom", "always_visible": True})
                    ]), md=4
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Filtrar por Cliente (código ou nome)"),
                        dcc.Dropdown(id="filtro-cliente", placeholder="Selecione um ou mais clientes...", multi=True)
                    ]), md=5
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Faixa de Dias Sem Compra"),
                        dcc.RangeSlider(id='filtro-dias-sem-compra', min=0, max=1000, step=10, value=[0, 1000], marks=None, tooltip={"placement": "bottom", "always_visible": True})
                    ]), md=3
                ),
            ]),
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.Label("Filtrar por Canal de Vendas"),
                        dcc.Dropdown(id="filtro-canal-vendas", placeholder="Selecione...", multi=True)
                    ]), md=4
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Filtrar por Hierarquia de Produto (1, 2 ou 3)"),
                        dcc.Dropdown(id="filtro-hierarquia-produto", placeholder="Selecione uma ou mais hierarquias...", multi=True)
                    ]), md=5
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Filtrar Top N Clientes (por valor total comprado)"),
                        dbc.Input(id="filtro-top-n-clientes", type="number", min=1, max=100, step=1, value=20, placeholder="Top N Clientes")
                    ]), md=3
                ),
            ], className="mt-3"),
        ]),
        className="mb-4"
    ),
    dbc.Row([
        dbc.Col(dbc.Button("Download CSV da Tabela", id="btn-csv-kpis-cliente", color="secondary"), width="auto")
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="tabela-kpis-cliente-container")), width=12)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(html.H4("Gráfico: Valor Faturado x Dias sem Compra"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="grafico-scatter-kpis-cliente")), width=12)
    ], className="mb-4"),
    html.Hr(),
    dbc.Row([
        dbc.Col(html.H4("Evolução Histórica Anual (Clientes Filtrados)"), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Div([
            html.Label("Selecione os Indicadores para o Gráfico"),
            dcc.Dropdown(
                id='dropdown-historico-kpis',
                options=[
                    {'label': 'Valor Total Faturado', 'value': 'total_comprado_valor'},
                    {'label': 'Quantidade Faturada', 'value': 'total_comprado_qtd'},
                    {'label': 'Mix de Produtos Comprados', 'value': 'mix_produtos'},
                    {'label': 'Percentual de Mix de Produtos (%)', 'value': 'pct_mix_produtos'}
                ],
                value=['total_comprado_valor'],
                multi=True
            )
        ]), md=12)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="grafico-historico-kpis")), width=12)
    ])
], fluid=True)

kpis_propostas_layout = dbc.Container([
    html.H1("KPIs de Propostas e Análise de Gaps"),
    html.P("Identifique oportunidades de venda analisando o que seus clientes cotam vs. o que eles e o mercado compram.", className="lead"),
        dbc.Row([
            dbc.Col([
                # Filtros exclusivos da página de propostas
                html.Div([
                    html.Label("Filtrar por Ano de Proposta (intervalo)"),
                    dcc.RangeSlider(id='filtro-ano-propostas', min=2020, max=2025, step=1, value=[2020,2025], marks={str(y): str(y) for y in range(2020, 2026)}, tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Filtrar por Mês de Proposta (intervalo)", style={"marginTop": "1em"}),
                    dcc.RangeSlider(id='filtro-mes-propostas', min=1, max=12, step=1, value=[1,12], marks={str(m): str(m) for m in range(1, 13)}, tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Filtrar por Cliente (código ou nome)", style={"marginTop": "1em"}),
                    dcc.Dropdown(id="filtro-cliente-propostas", placeholder="Selecione um ou mais clientes...", multi=True),
                    html.Label("Filtrar Top N Clientes (por valor total comprado)", style={"marginTop": "1em"}),
                    dbc.Input(id="filtro-top-n-clientes-propostas", type="number", min=1, max=100, step=1, value=20, placeholder="Top N Clientes")
                ])
            ], width=12)
        ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            # Radiobuttons acima do gráfico
            dcc.RadioItems(
                id='tipo-grafico-propostas',
                options=[
                    {'label': 'Comparativo (Barra)', 'value': 'barra'},
                    {'label': 'Heatmap', 'value': 'heatmap'}
                ],
                value='barra',
                inline=True,
                style={"marginBottom": "1em"}
            ),
            # Gráfico
            dcc.Loading(
                id="loading-grafico-propostas",
                type="default",
                children=[dcc.Graph(id='grafico-propostas')]
            )
        ], width=12)
    ]),
    dbc.Row([dbc.Col(dcc.Loading(html.Div(id="tabela-propostas-container")), width=12)], className="mb-4"),
    html.Hr(),
    dbc.Row([
        dbc.Col(html.H4("Sugestão de Lista de Compra para Estoque"), width="auto"),
        dbc.Col(dbc.Button("Gerar e Baixar Lista (.xlsx)", id="btn-gerar-lista", color="success"), width="auto"),
    ], className="mb-3", align="center"),
    dcc.Download(id="download-lista-sugestao")
], fluid=True)


produtos_layout = dbc.Container([
    html.H1("Produtos (Bolhas)"),
    html.P("Análise visual de clientes vs produtos com métricas de cotação e compra.", className="lead"),
    html.Hr(),
    
    # Filtros
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Ano de Referência"),
                    dcc.Dropdown(
                        id="filtro-ano-produtos",
                        options=[
                            {"label": "Todos", "value": "__ALL__"},
                            {"label": "2023", "value": 2023},
                            {"label": "2024", "value": 2024},
                            {"label": "2025", "value": 2025}
                        ],
                        value="__ALL__"
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Unidade de Negócio"),
                    dcc.Dropdown(
                        id="filtro-un-produtos",
                        placeholder="Selecione...",
                        multi=True
                    )
                ], md=3),
                dbc.Col([
                    html.Label("Top N Produtos"),
                    dbc.Input(
                        id="filtro-top-produtos",
                        type="number",
                        value=20,
                        min=5,
                        max=100
                    )
                ], md=2),
                dbc.Col([
                    html.Label("Top N Clientes"),
                    dbc.Input(
                        id="filtro-top-clientes-produtos",
                        type="number",
                        value=15,
                        min=5,
                        max=50
                    )
                ], md=2),
                dbc.Col([
                    html.Label("Paleta de Cores"),
                    dcc.Dropdown(
                        id="filtro-paleta-cores",
                        options=[
                            {"label": "Viridis", "value": "Viridis"},
                            {"label": "Blues", "value": "Blues"},
                            {"label": "Reds", "value": "Reds"},
                            {"label": "RdYlBu", "value": "RdYlBu"}
                        ],
                        value="Viridis"
                    )
                ], md=2)
            ])
        ])
    ], className="mb-4"),
    
    # Gráfico de bolhas
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                dcc.Graph(id="grafico-bolhas-produtos", style={"height": "600px"})
            )
        ], width=12)
    ]),
    
    # Botões de ação
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Download CSV", id="btn-csv-produtos", color="secondary"),
                dbc.Button("Gerar PDF por Cliente", id="btn-pdf-produtos", color="primary"),
            ])
        ])
    ], className="mt-3"),
    
    dcc.Download(id="download-csv-produtos"),
    dcc.Download(id="download-pdf-produtos")
    
], fluid=True)

funil_layout = dbc.Container([
    html.H1("Funil & Ações"),
    html.P("Identifique clientes que precisam de atenção especial e ações comerciais.", className="lead"),
    html.Hr(),
    
    # Filtros
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Período de Análise"),
                    dcc.Dropdown(
                        id="filtro-periodo-funil",
                        options=[
                            {"label": "Últimos 12 meses", "value": 12},
                            {"label": "Últimos 6 meses", "value": 6},
                            {"label": "Últimos 3 meses", "value": 3},
                            {"label": "Ano atual", "value": "current_year"}
                        ],
                        value=12
                    )
                ], md=4),
                dbc.Col([
                    html.Label("Threshold % Conversão Baixa"),
                    dbc.Input(
                        id="threshold-conversao-baixa",
                        type="number",
                        value=20,
                        min=0,
                        max=100,
                        step=5
                    )
                ], md=4),
                dbc.Col([
                    html.Label("Dias sem Compra (Risco)"),
                    dbc.Input(
                        id="threshold-dias-risco",
                        type="number",
                        value=90,
                        min=30,
                        max=365,
                        step=10
                    )
                ], md=4)
            ])
        ])
    ], className="mb-4"),
    
    # Métricas do funil
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📊 Resumo do Funil")),
                dbc.CardBody([
                    html.Div(id="metricas-funil")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Listas de ação
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🎯 Lista A - Baixa Conversão, Alto Volume", className="mb-0"),
                    html.Small("Clientes que cotam muito mas compram pouco", className="text-muted")
                ]),
                dbc.CardBody([
                    html.Div(id="lista-a-container"),
                    dbc.Button("Download Lista A (CSV)", id="btn-download-lista-a", 
                             color="warning", size="sm", className="mt-2")
                ])
            ])
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("⚠️ Lista B - Risco de Inatividade", className="mb-0"),
                    html.Small("Clientes com muito tempo sem comprar", className="text-muted")
                ]),
                dbc.CardBody([
                    html.Div(id="lista-b-container"),
                    dbc.Button("Download Lista B (CSV)", id="btn-download-lista-b", 
                             color="danger", size="sm", className="mt-2")
                ])
            ])
        ], md=6)
    ]),
    
    # Gráfico de funil
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📈 Análise Visual do Funil")),
                dbc.CardBody([
                    dcc.Loading(
                        dcc.Graph(id="grafico-funil", style={"height": "400px"})
                    )
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Downloads
    dcc.Download(id="download-lista-a"),
    dcc.Download(id="download-lista-b")
    
], fluid=True)

config_layout = dbc.Container([
    dcc.Location(id='config-url', refresh=True),
    html.H1("Gestão de Dados"),
    html.P("Esta área permite a gestão de usuários e a exclusão de dados carregados.", className="lead"),
    html.Div(id='config-feedback-msg'),
    dcc.ConfirmDialog(id='confirm-delete-user', message='Você tem certeza que quer excluir este usuário?'),
    dcc.ConfirmDialog(id='confirm-wipe-db', message='PERIGO: Esta ação é irreversível e apagará TODOS os dados. Deseja continuar?'),
    dcc.Store(id='store-user-to-delete', data=None),
    dbc.Card([dbc.CardHeader(html.H4("Gestão de Usuários")), dbc.CardBody(id="user-management-table-container")], className="mb-4"),
    dbc.Card([
        dbc.CardHeader(html.H4("Ações Perigosas")),
        dbc.CardBody([
            html.P("Cuidado: As ações abaixo não podem ser desfeitas."),
            dbc.Button("Limpar Todos os Dados Brutos e Processados", id="wipe-db-button", color="danger"),
            html.Hr(),
            html.P("Execute o processo de transformação para atualizar os dashboards com os últimos dados carregados."),
            dbc.Button("Processar Dados Brutos e Atualizar Análises", id="run-etl-button", color="primary", className="mt-2")
        ])
    ], color="danger", outline=True)
], fluid=True)

# --- ESTRUTURA PRINCIPAL DA APLICAÇÃO ---
app_layout = html.Div([
    sidebar_layout,
    html.Div([
        html.Div(visao_geral_layout, id='page-overview-content', style={'display': 'block'}),
        html.Div(kpis_cliente_layout, id='page-kpis-cliente-content', style={'display': 'none'}),
        html.Div(kpis_propostas_layout, id='page-kpis-propostas-content', style={'display': 'none'}),
        html.Div(produtos_layout, id='page-produtos-content', style={'display': 'none'}),
        html.Div(funil_layout, id='page-funil-content', style={'display': 'none'}),
        html.Div(config_layout, id='page-config-content', style={'display': 'none'}),
    ], className="content")
])

# --- LAYOUT RAIZ ---
main_layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Download(id="download-csv-kpis-cliente"),
    dcc.Store(id='store-kpis-cliente-filtered', storage_type='session'),
    html.Div(id="page-content")
])