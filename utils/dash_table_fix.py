#!/usr/bin/env python3
"""
Correção para Erro de Carregamento do dash_table
Implementa fallbacks e carregamento otimizado para evitar chunk loading errors
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_safe_data_table(table_id, columns, data=None, **kwargs):
    """
    Cria um DataTable com fallback em caso de erro de carregamento
    """
    try:
        # Primeiro, tenta importar o dash_table
        from dash import dash_table
        
        # Configurações padrão otimizadas
        default_config = {
            "id": table_id,
            "columns": columns,
            "data": data or [],
            "page_size": 25,
            "page_action": "native",
            "sort_action": "native", 
            "filter_action": "native",
            "style_cell": {
                'textAlign': 'left',
                'fontSize': '14px',
                'fontFamily': 'system-ui, -apple-system, sans-serif',
                'padding': '12px 8px',
                'border': '1px solid #dee2e6',
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '1.4'
            },
            "style_header": {
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'color': '#495057',
                'border': '1px solid #dee2e6',
                'textAlign': 'center',
                'fontSize': '13px'
            },
            "style_data": {
                'backgroundColor': '#ffffff',
                'color': '#495057',
                'border': '1px solid #dee2e6'
            },
            "style_data_conditional": [
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': '#e3f2fd',
                    'border': '1px solid #1976d2'
                }
            ],
            # Configurações para evitar problemas de carregamento
            "css": [
                {
                    'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner',
                    'rule': 'overflow: auto !important; max-height: 70vh;'
                }
            ],
            "export_format": "xlsx",
            "export_headers": "display",
            # Configurações de performance
            "virtualization": True,
            "page_current": 0,
            "derived_virtual_data": data or [],
            "derived_virtual_selected_rows": []
        }
        
        # Mescla configurações personalizadas
        config = {**default_config, **kwargs}
        
        logger.info(f"Criando DataTable {table_id} com {len(data or [])} registros")
        
        return dash_table.DataTable(**config)
        
    except ImportError as e:
        logger.error(f"Erro ao importar dash_table: {e}")
        return create_table_fallback(table_id, columns, data)
    except Exception as e:
        logger.error(f"Erro ao criar DataTable {table_id}: {e}")
        return create_table_fallback(table_id, columns, data)

def create_table_fallback(table_id, columns, data):
    """
    Cria uma tabela HTML simples como fallback
    """
    try:
        # Criar cabeçalho
        header_cells = [html.Th(col.get('name', col.get('id', ''))) for col in columns]
        header = html.Thead(html.Tr(header_cells))
        
        # Criar linhas de dados
        rows = []
        if data:
            for i, row in enumerate(data[:100]):  # Limita a 100 registros para performance
                cells = [html.Td(str(row.get(col['id'], ''))) for col in columns]
                rows.append(html.Tr(cells, className="table-row"))
        else:
            # Linha vazia se não houver dados
            empty_cells = [html.Td("Carregando...", colSpan=len(columns), className="text-center text-muted")]
            rows.append(html.Tr(empty_cells))
        
        body = html.Tbody(rows)
        
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong("Modo de Compatibilidade: "),
                "Tabela carregada em modo simplificado devido a problema com componentes avançados."
            ], color="warning", className="mb-3"),
            
            html.Div([
                html.Table([header, body], 
                          className="table table-striped table-hover table-sm",
                          id=f"{table_id}-fallback")
            ], className="table-responsive", style={"maxHeight": "500px", "overflowY": "auto"})
        ], id=table_id)
        
    except Exception as e:
        logger.error(f"Erro ao criar fallback para {table_id}: {e}")
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                html.Strong("Erro: "),
                f"Não foi possível carregar a tabela. {str(e)}"
            ], color="danger"),
            html.P("Por favor, recarregue a página ou contate o suporte técnico.", className="text-muted")
        ], id=table_id)

def create_loading_table_placeholder(table_id):
    """
    Cria um placeholder de carregamento para tabelas
    """
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    dbc.Spinner(
                        html.Div([
                            html.H6("Carregando dados...", className="text-muted mb-2"),
                            html.P("Por favor, aguarde enquanto os dados são processados.", 
                                  className="small text-muted")
                        ], className="text-center"),
                        color="primary",
                        type="border"
                    )
                ], className="d-flex justify-content-center align-items-center", 
                   style={"minHeight": "200px"})
            ])
        ])
    ], id=table_id, className="mb-4")

def create_optimized_products_layout():
    """
    Versão otimizada do layout de produtos com tratamento de erros
    """
    try:
        from dash.dash_table.Format import Format, Scheme
        from dash.dash_table import FormatTemplate
        
        logger.info("Criando layout otimizado de produtos")
        
        return html.Div([
            # Controles melhorados
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6([
                                html.I(className="fas fa-filter me-2"),
                                "Filtros de Visualização"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Top Produtos:", className="fw-bold"),
                                    dbc.Input(
                                            id="filter-top-produtos", 
                                            type="number", 
                                            value=0, 
                                            min=0, 
                                            max=10000,
                                        className="mb-2"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Modo de Exibição:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="produtos-display-mode",
                                        options=[
                                            {"label": "📊 Tabela Completa", "value": "full"},
                                            {"label": "⚡ Tabela Rápida", "value": "fast"},
                                            {"label": "📋 Lista Simples", "value": "simple"}
                                        ],
                                        value="full",
                                        clearable=False
                                    )
                                ], width=6)
                            ])
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-download me-1"),
                            "CSV"
                        ], id="btn-download-csv-produtos", color="primary", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-file-pdf me-1"),
                            "PDF"
                        ], id="btn-pdf-cliente", color="success", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-rocket me-1"),
                            "B2B"
                        ], id="btn-b2b-redirect", color="info", size="sm")
                    ], className="w-100")
                ], width=4, className="d-flex align-items-end")
            ], className="mb-4"),
            
            # Status e alertas
            html.Div(id="produtos-status-container"),
            
            # Gráficos otimizados
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6([
                                html.I(className="fas fa-chart-scatter me-2"),
                                "Matriz Clientes × Produtos"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(
                                dcc.Graph(
                                    id="grafico-bolhas-produtos",
                                    config={'displayModeBar': True, 'responsive': True}
                                ),
                                type="default"
                            )
                        ])
                    ])
                ], width=12, lg=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6([
                                html.I(className="fas fa-chart-bar me-2"),
                                "Análise de Pareto"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(
                                dcc.Graph(
                                    id="grafico-pareto-produtos",
                                    config={'displayModeBar': True, 'responsive': True}
                                ),
                                type="default"
                            )
                        ])
                    ])
                ], width=12, lg=6)
            ], className="mb-4"),
            
            # Seção da tabela com tratamento de erro robusto
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H6([
                                html.I(className="fas fa-table me-2"),
                                "Análise Detalhada de Produtos"
                            ], className="mb-0")
                        ], width=8),
                        dbc.Col([
                            dbc.Badge(
                                id="produtos-table-status",
                                color="info",
                                className="ms-2"
                            )
                        ], width=4, className="text-end")
                    ])
                ]),
                dbc.CardBody([
                    # Filtros da tabela
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Filtrar por Material:", className="fw-bold"),
                            dcc.Input(
                                id="filter-material-search",
                                type="text",
                                placeholder="Digite para buscar por código ou descrição (ex.: motor -disjuntor, 14402)",
                                debounce=False,
                                className="mb-2",
                                style={"width": "100%"}
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Registros por página:", className="fw-bold"),
                            dcc.Dropdown(
                                id="table-page-size-produtos",
                                options=[
                                    {"label": "10 registros", "value": 10},
                                    {"label": "25 registros", "value": 25},
                                    {"label": "50 registros", "value": 50},
                                    {"label": "100 registros", "value": 100}
                                ],
                                value=25,
                                clearable=False
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    # Controles da tabela
                    dbc.Row([
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-check me-1"),
                                    "Selecionar Todos"
                                ], id="btn-select-all-produtos", color="outline-primary", size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-times me-1"),
                                    "Desmarcar"
                                ], id="btn-deselect-all-produtos", color="outline-secondary", size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-eraser me-1"),
                                    "Limpar Filtros"
                                ], id="btn-clear-filters-produtos", color="outline-warning", size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-sync me-1"),
                                    "Atualizar"
                                ], id="btn-refresh-produtos", color="outline-info", size="sm")
                            ])
                        ], width=12)
                    ], className="mb-3"),
                    
                    # Container da tabela com fallback
                    html.Div([
                        dcc.Loading(
                            html.Div(id="tabela-analise-produtos-container"),
                            type="default"
                        )
                    ])
                ])
            ])
        ], className="container-fluid")
        
    except Exception as e:
        logger.error(f"Erro ao criar layout de produtos: {e}")
        traceback.print_exc()
        
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                html.Strong("Erro no Sistema: "),
                "Não foi possível carregar a página de produtos. ",
                html.Br(),
                f"Detalhes técnicos: {str(e)}"
            ], color="danger"),
            dbc.Card([
                dbc.CardBody([
                    html.H5("🔧 Soluções Recomendadas"),
                    html.Ul([
                        html.Li("Recarregue a página (Ctrl+F5 ou Cmd+R)"),
                        html.Li("Limpe o cache do navegador"),
                        html.Li("Tente acessar em modo privado/incógnito"),
                        html.Li("Verifique sua conexão com a internet")
                    ]),
                    html.Hr(),
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-home me-1"),
                            "Voltar ao Início"
                        ], href="/app/overview", color="primary"),
                        dbc.Button([
                            html.I(className="fas fa-rocket me-1"),
                            "Ir para B2B Avançado"
                        ], href="/app/b2b-advanced", color="success")
                    ])
                ])
            ])
        ])

if __name__ == "__main__":
    print("✅ Módulo de correção de dash_table carregado com sucesso!")
    print("📋 Funções disponíveis:")
    print("   - create_safe_data_table(): DataTable com fallback automático")
    print("   - create_table_fallback(): Tabela HTML de emergência")
    print("   - create_loading_table_placeholder(): Placeholder de carregamento")
    print("   - create_optimized_products_layout(): Layout otimizado de produtos")