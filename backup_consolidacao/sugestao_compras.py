"""
Página de Sugestão Inteligente de Compras
Sistema B2B Laura Representações - WEG
Implementação completa conforme especificações do prompt
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, MATCH, ALL
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from utils.ml_recommendations import SmartPurchaseRecommendations
from utils.db import get_connection as get_db_connection
import dash_bootstrap_components as dbc

# Registrar a página
dash.register_page(__name__, path="/sugestao-compras", name="Sugestão de Compras")

def create_recommendations_table(recommendations_data):
    """
    Cria tabela de recomendações conforme especificação:
    material, descricao, qtd_sugerida, motivo_da_sugestao, probabilidade_recompra, 
    nivel_confianca, cobertura_dias
    """
    if not recommendations_data or len(recommendations_data) == 0:
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Nenhuma recomendação disponível para os filtros selecionados."
            ], color="info")
        ])
    
    # Preparar dados para a tabela
    table_data = []
    for i, rec in enumerate(recommendations_data):
        table_data.append({
            'id': i,
            'material': rec.get('material', 'N/A'),
            'descricao': rec.get('descricao', rec.get('produto', 'Produto não identificado')),
            'qtd_sugerida': rec.get('qtd_sugerida', rec.get('qtd_potencial', 0)),
            'motivo_da_sugestao': rec.get('motivo_da_sugestao', rec.get('justificativa', 'Análise automática')),
            'probabilidade_recompra': f"{rec.get('probabilidade_recompra', rec.get('score_oportunidade', 0)):.1f}%",
            'nivel_confianca': rec.get('nivel_confianca', 'MÉDIA'),
            'cobertura_dias': rec.get('cobertura_dias', 'N/A'),
            'valor_potencial': f"R$ {rec.get('valor_potencial', 0):,.2f}",
            'tipo_gap': rec.get('gap_type', rec.get('tipo', 'OPORTUNIDADE'))
        })
    
    # Definir colunas da tabela
    columns = [
        {"name": "Material", "id": "material", "type": "text"},
        {"name": "Descrição", "id": "descricao", "type": "text"},
        {"name": "Qtd. Sugerida", "id": "qtd_sugerida", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Motivo da Sugestão", "id": "motivo_da_sugestao", "type": "text"},
        {"name": "Probabilidade", "id": "probabilidade_recompra", "type": "text"},
        {"name": "Confiança", "id": "nivel_confianca", "type": "text"},
        {"name": "Cobertura", "id": "cobertura_dias", "type": "text"},
        {"name": "Valor Potencial", "id": "valor_potencial", "type": "text"},
        {"name": "Ações", "id": "acoes", "presentation": "markdown"}
    ]
    
    # Adicionar coluna de ações com IDs para callbacks
    for row in table_data:
        row_id = row['id']
        row['acoes'] = f"cotacao-{row_id} | irrelevante-{row_id} | like-{row_id} | dislike-{row_id}"
    
    return html.Div([
        dash_table.DataTable(
            id="recommendations-table",
            data=table_data,
            columns=columns,
            style_cell={
                'textAlign': 'left',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '14px',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': '#1f77b4',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{nivel_confianca} = ALTA'},
                    'backgroundColor': '#d4edda',
                    'border': '2px solid #28a745'
                },
                {
                    'if': {'filter_query': '{nivel_confianca} = BAIXA'},
                    'backgroundColor': '#f8d7da',
                    'border': '2px solid #dc3545'
                }
            ],
            page_size=10,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            export_headers="display",
            row_selectable="multi",
            selected_rows=[]
        ),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.P("Ações para itens selecionados:", className="fw-bold mb-2"),
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-file-invoice me-1"), "Gerar Cotação"],
                        id="btn-bulk-cotacao",
                        color="primary",
                        disabled=True
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-down me-1"), "Marcar Irrelevante"],
                        id="btn-bulk-irrelevante", 
                        color="warning",
                        disabled=True
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-up me-1"), "Feedback Positivo"],
                        id="btn-bulk-like",
                        color="success", 
                        disabled=True
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-download me-1"), "Exportar PDF"],
                        id="btn-bulk-export-pdf",
                        color="info",
                        disabled=True
                    )
                ])
            ])
        ], className="mt-3")
    ])

def create_kpi_cards(summary_data):
    """Cria cards de KPIs principais"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{summary_data.get('total_oportunidades', 0)}", className="card-title text-primary"),
                    html.P("Oportunidades Identificadas", className="card-text")
                ])
            ], color="light", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"R$ {summary_data.get('valor_potencial', 0):,.0f}", className="card-title text-success"),
                    html.P("Valor Potencial Total", className="card-text")
                ])
            ], color="light", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{summary_data.get('score_medio', 0):.1f}%", className="card-title text-warning"),
                    html.P("Score Médio de Confiança", className="card-text")
                ])
            ], color="light", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{summary_data.get('alertas_criticos', 0)}", className="card-title text-danger"),
                    html.P("Alertas Críticos", className="card-text")
                ])
            ], color="light", outline=True)
        ], width=3)
    ], className="mb-4")

def create_filters_section():
    """Cria seção de filtros avançados conforme especificado"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("🔍 Filtros Avançados de Segmentação", className="card-title"),
            
            # Linha 1: Filtros principais
            dbc.Row([
                dbc.Col([
                    html.Label("Cliente:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-cliente",
                        placeholder="Selecione o cliente...",
                        multi=False
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Tipo de Cliente:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-tipo-cliente",
                        options=[
                            {"label": "Revenda", "value": "revenda"},
                            {"label": "Usuário Final", "value": "usuario_final"},
                            {"label": "Todos", "value": "todos"}
                        ],
                        value="todos"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Região:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-regiao",
                        options=[
                            {"label": "Sul", "value": "sul"},
                            {"label": "Sudeste", "value": "sudeste"},
                            {"label": "Nordeste", "value": "nordeste"},
                            {"label": "Norte", "value": "norte"},
                            {"label": "Centro-Oeste", "value": "centro_oeste"},
                            {"label": "Todas", "value": "todas"}
                        ],
                        value="todas"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Nível de Confiança:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-confianca",
                        options=[
                            {"label": "≥ 80% (Muito Alta)", "value": 80},
                            {"label": "≥ 70% (Alta)", "value": 70},
                            {"label": "≥ 50% (Média)", "value": 50},
                            {"label": "≥ 30% (Baixa)", "value": 30},
                            {"label": "Todos", "value": 0}
                        ],
                        value=70
                    )
                ], width=3)
            ], className="mb-3"),
            
            # Linha 2: Filtros temporais e valor
            dbc.Row([
                dbc.Col([
                    html.Label("Período de Análise:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-periodo",
                        options=[
                            {"label": "Últimos 3 meses", "value": 3},
                            {"label": "Últimos 6 meses", "value": 6},
                            {"label": "Últimos 12 meses", "value": 12},
                            {"label": "Últimos 24 meses", "value": 24},
                            {"label": "Customizado", "value": "custom"}
                        ],
                        value=12
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Faixa de Valor (R$):", className="form-label"),
                    dcc.RangeSlider(
                        id="filter-valor-range",
                        min=0,
                        max=100000,
                        step=1000,
                        value=[1000, 50000],
                        marks={
                            0: "0",
                            25000: "25k",
                            50000: "50k",
                            75000: "75k",
                            100000: "100k+"
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Tipo de Gap:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-gap-type",
                        options=[
                            {"label": "Todos os Tipos", "value": "todos"},
                            {"label": "Oportunidades Críticas", "value": "critico"},
                            {"label": "Oportunidades Normais", "value": "oportunidade"},
                            {"label": "Gaps Sazonais", "value": "sazonal"},
                            {"label": "Benchmark", "value": "benchmark"}
                        ],
                        value="todos",
                        multi=True
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Categoria de Produto:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-categoria",
                        placeholder="Selecione categorias...",
                        multi=True
                    )
                ], width=3)
            ], className="mb-3"),
            
            # Linha 3: Filtros de benchmark e comparação
            dbc.Row([
                dbc.Col([
                    html.Label("Comparar com:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-benchmark",
                        options=[
                            {"label": "Clientes Similares", "value": "similares"},
                            {"label": "Top Performers", "value": "top_performers"},
                            {"label": "Mesmo Segmento", "value": "segmento"},
                            {"label": "Mercado Geral", "value": "mercado"}
                        ],
                        value="similares"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Frequência de Compra:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-frequencia",
                        options=[
                            {"label": "Clientes Ativos (Compra regular)", "value": "ativo"},
                            {"label": "Clientes Esporádicos", "value": "esporadico"},
                            {"label": "Clientes Inativos", "value": "inativo"},
                            {"label": "Todos", "value": "todos"}
                        ],
                        value="todos"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Sazonalidade:", className="form-label"),
                    dcc.Dropdown(
                        id="filter-sazonalidade",
                        options=[
                            {"label": "Considerar Padrões Sazonais", "value": "sim"},
                            {"label": "Ignorar Sazonalidade", "value": "nao"},
                            {"label": "Apenas Produtos Sazonais", "value": "apenas"}
                        ],
                        value="sim"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Score Mínimo:", className="form-label"),
                    dcc.Slider(
                        id="filter-score-minimo",
                        min=0,
                        max=100,
                        step=5,
                        value=50,
                        marks={i: f"{i}%" for i in range(0, 101, 25)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=3)
            ], className="mb-3"),
            
            # Linha 4: Filtros personalizados salvos e ações
            dbc.Row([
                dbc.Col([
                    html.Label("Filtros Salvos:", className="form-label"),
                    dcc.Dropdown(
                        id="saved-filters",
                        placeholder="Carregar filtro salvo...",
                        options=[]
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Nome do Filtro:", className="form-label"),
                    dbc.Input(
                        id="filter-name-input",
                        placeholder="Ex: Clientes Sul Alta Confiança",
                        type="text"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Ações:", className="form-label"),
                    html.Br(),
                    dbc.ButtonGroup([
                        dbc.Button(
                            "💾 Salvar Filtro",
                            id="btn-save-filter",
                            color="info",
                            size="sm"
                        ),
                        dbc.Button(
                            "🗑️ Excluir",
                            id="btn-delete-filter",
                            color="danger",
                            size="sm"
                        ),
                        dbc.Button(
                            "🔄 Limpar Tudo",
                            id="btn-clear-filters",
                            color="secondary",
                            size="sm"
                        )
                    ])
                ], width=4)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Linha 5: Botões principais
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "🔄 Atualizar Recomendações", 
                        id="btn-update-recommendations",
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "📊 Gerar Relatório Completo", 
                        id="btn-generate-report",
                        color="success",
                        className="me-2"
                    ),
                    dbc.Button(
                        "📤 Exportar Seleção", 
                        id="btn-export-selection",
                        color="info",
                        className="me-2"
                    )
                ], width=8),
                dbc.Col([
                    dbc.DropdownMenu([
                        dbc.DropdownMenuItem("📄 Relatório Executivo PDF", id="btn-exec-pdf"),
                        dbc.DropdownMenuItem("📊 Análise Detalhada Excel", id="btn-detailed-excel"),
                        dbc.DropdownMenuItem("📦 Pacote Completo ZIP", id="btn-complete-package"),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem("⏰ Agendar Relatórios", id="btn-schedule-reports")
                    ], 
                    label="📋 Exportação Avançada",
                    color="secondary",
                    size="sm"
                    )
                ], width=4, className="text-end")
            ]),
            
            # Indicadores de filtros ativos
            html.Div(id="active-filters-indicators", className="mt-3")
        ])
    ], className="mb-4")

# Layout principal da página
layout = dbc.Container([
    dcc.Store(id="store-recommendations-data"),
    dcc.Store(id="store-analytics-data"),
    dcc.Store(id="store-export-data"),
    
    # Cabeçalho
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-lightbulb me-3"),
                "Sugestão Inteligente de Compras"
            ], className="text-primary mb-0"),
            html.P("Sistema B2B de Recomendações - Laura Representações", className="text-muted")
        ])
    ], className="mb-4"),
    
    # Seção de filtros
    create_filters_section(),
    
    # KPIs principais
    html.Div(id="kpi-cards-container"),
    
    # Tabela de recomendações
    dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-table me-2"),
                "Recomendações de Compra"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="recommendations-table-container"),
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
                dbc.Tab(label="📊 Penetração de Mercado", tab_id="tab-penetracao"),
                dbc.Tab(label="📅 Sazonalidade", tab_id="tab-sazonalidade"),
                dbc.Tab(label="🎯 Gaps & Oportunidades", tab_id="tab-gaps"),
                dbc.Tab(label="💰 ROI Estimado", tab_id="tab-roi")
            ], id="analytics-tabs", active_tab="tab-penetracao"),
            html.Div(id="analytics-content", className="mt-3")
        ])
    ], className="mb-4"),
    
    # Alertas inteligentes
    html.Div(id="intelligent-alerts-container"),
    
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
                        id="btn-run-learning-cycle",
                        color="info",
                        size="sm"
                    )
                ], width=6, className="text-end")
            ])
        ]),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(label="📊 Métricas de Feedback", tab_id="tab-feedback-metrics"),
                dbc.Tab(label="⚙️ Pesos do Algoritmo", tab_id="tab-ml-weights"),
                dbc.Tab(label="📈 Performance de Materiais", tab_id="tab-material-performance")
            ], id="learning-tabs", active_tab="tab-feedback-metrics"),
            html.Div(id="learning-content", className="mt-3")
        ])
    ], className="mb-4"),
    
    # Modais para ações
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Gerar Cotação")),
        dbc.ModalBody([
            html.P("Cotação será gerada automaticamente com base na recomendação selecionada."),
            html.Div(id="modal-cotacao-content")
        ]),
        dbc.ModalFooter([
            dbc.Button("Confirmar", id="btn-confirm-cotacao", color="success"),
            dbc.Button("Cancelar", id="btn-cancel-cotacao", color="secondary")
        ])
    ], id="modal-cotacao", is_open=False),
    
    # Modal para agendamento de relatórios
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("⏰ Agendar Relatórios Automáticos")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Frequência:", className="form-label"),
                    dcc.Dropdown(
                        id="schedule-frequency",
                        options=[
                            {"label": "Diário", "value": "daily"},
                            {"label": "Semanal", "value": "weekly"},
                            {"label": "Mensal", "value": "monthly"}
                        ],
                        value="weekly"
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Formato:", className="form-label"),
                    dcc.Dropdown(
                        id="schedule-format",
                        options=[
                            {"label": "PDF Executivo", "value": "pdf"},
                            {"label": "Excel Detalhado", "value": "excel"},
                            {"label": "Pacote Completo", "value": "complete"}
                        ],
                        value="pdf"
                    )
                ], width=6)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Clientes (múltipla seleção):", className="form-label"),
                    dcc.Dropdown(
                        id="schedule-clients",
                        multi=True,
                        placeholder="Selecione os clientes..."
                    )
                ])
            ]),
            dbc.Alert(
                "Os relatórios serão gerados automaticamente conforme agendamento e enviados por email.",
                color="info",
                className="mt-3"
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Agendar", id="btn-confirm-schedule", color="success"),
            dbc.Button("Cancelar", id="btn-cancel-schedule", color="secondary")
        ])
    ], id="modal-schedule", is_open=False),
    
    # Toast para feedback
    dbc.Toast(
        id="feedback-toast",
        header="Feedback Registrado",
        is_open=False,
        dismissable=True,
        duration=3000,
        style={"position": "fixed", "top": 66, "right": 10, "width": 350}
    )
    
], fluid=True)

# Import das ações interativas
from utils.recommendation_actions import RecommendationActionHandler, create_download_link
from utils.ml_feedback_learning import MLFeedbackLearningSystem
from utils.advanced_export_system import AdvancedExportSystem, create_download_link_advanced

# Instância global do handler
action_handler = RecommendationActionHandler()
learning_system = MLFeedbackLearningSystem()
export_system = AdvancedExportSystem()

# Callbacks para funcionalidade
@callback(
    [Output("filter-cliente", "options"),
     Output("store-analytics-data", "data")],
    [Input("btn-update-recommendations", "n_clicks")],
    prevent_initial_call=False
)
def load_initial_data(n_clicks):
    """Carrega dados iniciais e popula filtros"""
    try:
        # Carregar lista de clientes
        conn = get_db_connection()
        clientes_query = """
        SELECT DISTINCT cod_cliente, COUNT(*) as vendas
        FROM vendas 
        WHERE cod_cliente IS NOT NULL
        GROUP BY cod_cliente
        ORDER BY vendas DESC
        LIMIT 100
        """
        clientes_df = pd.read_sql(clientes_query, conn)
        conn.close()
        
        cliente_options = [
            {"label": f"Cliente {row['cod_cliente']} ({row['vendas']} vendas)", 
             "value": row['cod_cliente']} 
            for _, row in clientes_df.iterrows()
        ]
        
        # Dados analíticos iniciais
        analytics_data = {
            "last_update": datetime.now().isoformat(),
            "total_clientes": len(clientes_df),
            "clientes_ativos": len(clientes_df[clientes_df['vendas'] >= 5])
        }
        
        return cliente_options, analytics_data
        
    except Exception as e:
        print(f"Erro ao carregar dados iniciais: {e}")
        return [], {}

@callback(
    [Output("recommendations-table-container", "children"),
     Output("kpi-cards-container", "children"),
     Output("store-recommendations-data", "data")],
    [Input("btn-update-recommendations", "n_clicks"),
     Input("filter-cliente", "value"),
     Input("filter-confianca", "value")],
    prevent_initial_call=True
)
def update_recommendations(n_clicks, selected_cliente, min_confidence):
    """Atualiza recomendações baseado nos filtros"""
    if not selected_cliente:
        return [
            dbc.Alert("Selecione um cliente para ver as recomendações.", color="warning")
        ], [], {}
    
    try:
        # Executar análise completa
        recommender = SmartPurchaseRecommendations()
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente=selected_cliente,
            contexto_comercial={'tipo_analise': 'completa'},
            export_format='completo'
        )
        
        # Extrair recomendações dos gaps
        recommendations = []
        if 'analises' in resultado and 'gaps_mercado' in resultado['analises']:
            gaps_data = resultado['analises']['gaps_mercado']
            for gap in gaps_data.get('gaps', []):
                if gap.get('score_oportunidade', 0) >= min_confidence:
                    recommendations.append({
                        'material': gap['material'],
                        'descricao': gap.get('produto', 'Produto WEG'),
                        'qtd_sugerida': gap.get('qtd_potencial', 0),
                        'motivo_da_sugestao': f"Gap de mercado: {gap['w_percent']:.1f}% penetração na base",
                        'probabilidade_recompra': gap['score_oportunidade'],
                        'nivel_confianca': 'ALTA' if gap['score_oportunidade'] >= 80 else 'MÉDIA' if gap['score_oportunidade'] >= 60 else 'BAIXA',
                        'cobertura_dias': 'N/A',
                        'valor_potencial': gap.get('valor_potencial', 0),
                        'gap_type': gap.get('gap_type', 'OPORTUNIDADE')
                    })
        
        # Preparar dados de resumo
        summary_data = {
            'total_oportunidades': len(recommendations),
            'valor_potencial': sum(r.get('valor_potencial', 0) for r in recommendations),
            'score_medio': np.mean([r.get('probabilidade_recompra', 0) for r in recommendations]) if recommendations else 0,
            'alertas_criticos': len(resultado.get('analises', {}).get('alertas', {}).get('alertas', {}).get('criticos', []))
        }
        
        # Criar componentes
        table = create_recommendations_table(recommendations)
        kpi_cards = create_kpi_cards(summary_data)
        
        return table, kpi_cards, recommendations
        
    except Exception as e:
        print(f"Erro ao atualizar recomendações: {e}")
        return [
            dbc.Alert(f"Erro ao carregar recomendações: {str(e)}", color="danger")
        ], [], {}

@callback(
    Output("analytics-content", "children"),
    [Input("analytics-tabs", "active_tab"),
     Input("store-recommendations-data", "data"),
     Input("filter-cliente", "value")]
)
def update_analytics_content(active_tab, recommendations_data, selected_cliente):
    """Atualiza conteúdo dos gráficos analíticos"""
    if not recommendations_data:
        return dbc.Alert("Selecione um cliente para ver as análises.", color="info")
    
    if active_tab == "tab-penetracao":
        # Gráfico de penetração de mercado aprimorado
        df = pd.DataFrame(recommendations_data)
        if not df.empty:
            # Top 15 materiais por score
            top_materials = df.nlargest(15, 'probabilidade_recompra')
            
            # Gráfico de barras com cores graduadas
            fig = px.bar(
                top_materials, 
                x='material', 
                y='probabilidade_recompra',
                title=f"📊 Penetração de Mercado - Top 15 Oportunidades (Cliente: {selected_cliente})",
                labels={'probabilidade_recompra': 'Score de Oportunidade (%)', 'material': 'Material WEG'},
                color='probabilidade_recompra',
                color_continuous_scale='RdYlGn',
                text='probabilidade_recompra'
            )
            
            fig.update_traces(
                texttemplate='%{text:.1f}%', 
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}%<br>Valor Potencial: R$ %{customdata:,.0f}<extra></extra>',
                customdata=top_materials['valor_potencial']
            )
            
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45,
                showlegend=False,
                title_x=0.5,
                xaxis_title="Material",
                yaxis_title="Score de Oportunidade (%)"
            )
            
            # Adicionar linha de meta (70%)
            fig.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="Meta Confiança (70%)")
            
            return dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig),
                    dbc.Alert([
                        html.Strong("💡 Insights: "), 
                        f"Identificadas {len(df[df['probabilidade_recompra'] >= 70])} oportunidades de alta confiança (≥70%). ",
                        f"Valor total potencial: R$ {df['valor_potencial'].sum():,.0f}"
                    ], color="info", className="mt-3")
                ])
            ])
        
    elif active_tab == "tab-sazonalidade":
        # Simulação de análise de sazonalidade
        try:
            conn = get_db_connection()
            sazonalidade_query = """
            SELECT 
                strftime('%m', data_emissao) as mes,
                COUNT(*) as vendas,
                SUM(vlr_entrada) as valor_total
            FROM vendas 
            WHERE cod_cliente = ?
            AND data_emissao >= date('now', '-12 months')
            GROUP BY strftime('%m', data_emissao)
            ORDER BY mes
            """
            
            sazon_df = pd.read_sql(sazonalidade_query, conn, params=[selected_cliente])
            conn.close()
            
            if not sazon_df.empty:
                # Converter mês numérico para nome
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                sazon_df['mes_nome'] = sazon_df['mes'].astype(int).map(lambda x: meses[x-1])
                
                # Criar gráfico de linhas duplo
                fig = go.Figure()
                
                # Linha de vendas
                fig.add_trace(go.Scatter(
                    x=sazon_df['mes_nome'],
                    y=sazon_df['vendas'],
                    mode='lines+markers',
                    name='Quantidade de Vendas',
                    line=dict(color='#1f77b4', width=3),
                    yaxis='y'
                ))
                
                # Linha de valor
                fig.add_trace(go.Scatter(
                    x=sazon_df['mes_nome'],
                    y=sazon_df['valor_total'],
                    mode='lines+markers',
                    name='Valor Total (R$)',
                    line=dict(color='#ff7f0e', width=3),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title=f"📅 Análise de Sazonalidade - Últimos 12 Meses (Cliente: {selected_cliente})",
                    xaxis_title="Mês",
                    yaxis=dict(title="Quantidade de Vendas", side="left"),
                    yaxis2=dict(title="Valor Total (R$)", side="right", overlaying="y"),
                    height=400,
                    title_x=0.5
                )
                
                return dcc.Graph(figure=fig)
            else:
                return dbc.Alert("Dados insuficientes para análise de sazonalidade.", color="warning")
                
        except Exception as e:
            print(f"Erro na análise de sazonalidade: {e}")
            return dbc.Alert("Erro ao carregar dados de sazonalidade.", color="danger")
        
    elif active_tab == "tab-gaps":
        # Matriz de oportunidades aprimorada
        df = pd.DataFrame(recommendations_data)
        if not df.empty:
            # Criar scatter plot com sizing e cores
            fig = px.scatter(
                df,
                x='probabilidade_recompra',
                y='valor_potencial',
                size='qtd_sugerida',
                color='nivel_confianca',
                hover_data={'material': True, 'motivo_da_sugestao': True},
                title="🎯 Matriz de Oportunidades: Score vs Valor Potencial",
                labels={
                    'probabilidade_recompra': 'Score de Oportunidade (%)', 
                    'valor_potencial': 'Valor Potencial (R$)',
                    'nivel_confianca': 'Nível de Confiança'
                },
                color_discrete_map={
                    'ALTA': '#28a745',
                    'MÉDIA': '#ffc107', 
                    'BAIXA': '#dc3545'
                }
            )
            
            fig.update_traces(
                hovertemplate='<b>%{hovertext}</b><br>Score: %{x:.1f}%<br>Valor: R$ %{y:,.0f}<br>Qtd: %{marker.size:,.0f}<extra></extra>'
            )
            
            fig.update_layout(
                height=500,
                title_x=0.5
            )
            
            # Adicionar quadrantes de decisão
            fig.add_vline(x=70, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_hline(y=df['valor_potencial'].median(), line_dash="dash", line_color="gray", opacity=0.5)
            
            # Análise de quadrantes
            alta_conf_alto_valor = len(df[(df['probabilidade_recompra'] >= 70) & 
                                        (df['valor_potencial'] >= df['valor_potencial'].median())])
            
            return dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig),
                    dbc.Alert([
                        html.Strong("🎯 Análise de Quadrantes: "),
                        f"{alta_conf_alto_valor} oportunidades no quadrante IDEAL (alta confiança + alto valor). ",
                        "Focar investimentos neste quadrante para máximo ROI."
                    ], color="success", className="mt-3")
                ])
            ])
            
    elif active_tab == "tab-roi":
        # Análise de ROI estimado
        df = pd.DataFrame(recommendations_data)
        if not df.empty:
            # Calcular métricas de ROI
            df['roi_estimado'] = (df['valor_potencial'] * df['probabilidade_recompra'] / 100) - (df['valor_potencial'] * 0.1)  # Assumindo 10% de custo
            df['payback_meses'] = (df['valor_potencial'] * 0.1) / (df['valor_potencial'] / 12)  # Payback aproximado
            
            # Gauge Chart para ROI médio
            roi_medio = df['roi_estimado'].mean()
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = roi_medio,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "ROI Médio Estimado (R$)"},
                delta = {'reference': 0},
                gauge = {
                    'axis': {'range': [None, df['roi_estimado'].max()]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, df['roi_estimado'].max() * 0.3], 'color': "lightgray"},
                        {'range': [df['roi_estimado'].max() * 0.3, df['roi_estimado'].max() * 0.7], 'color': "yellow"},
                        {'range': [df['roi_estimado'].max() * 0.7, df['roi_estimado'].max()], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': df['roi_estimado'].max() * 0.8
                    }
                }
            ))
            
            fig.update_layout(height=400)
            
            # Tabela de ROI por material
            roi_top = df.nlargest(10, 'roi_estimado')[['material', 'roi_estimado', 'payback_meses', 'probabilidade_recompra']]
            
            return dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig)
                ], width=6),
                dbc.Col([
                    html.H6("💰 Top 10 ROI por Material"),
                    dash_table.DataTable(
                        data=roi_top.to_dict('records'),
                        columns=[
                            {"name": "Material", "id": "material"},
                            {"name": "ROI Est. (R$)", "id": "roi_estimado", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Payback (meses)", "id": "payback_meses", "type": "numeric", "format": {"specifier": ".1f"}},
                            {"name": "Confiança (%)", "id": "probabilidade_recompra", "type": "numeric", "format": {"specifier": ".1f"}}
                        ],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                        page_size=10
                    )
                ], width=6)
            ])
    
    return html.Div()

# Callbacks para ações interativas dos botões
@callback(
    [Output("btn-bulk-cotacao", "disabled"),
     Output("btn-bulk-irrelevante", "disabled"),
     Output("btn-bulk-like", "disabled"),
     Output("btn-bulk-export-pdf", "disabled")],
    [Input("recommendations-table", "selected_rows")]
)
def enable_action_buttons(selected_rows):
    """Habilita botões de ação quando há itens selecionados"""
    has_selection = selected_rows and len(selected_rows) > 0
    return not has_selection, not has_selection, not has_selection, not has_selection

@callback(
    [Output("modal-cotacao", "is_open"),
     Output("modal-cotacao-content", "children")],
    [Input("btn-bulk-cotacao", "n_clicks")],
    [State("recommendations-table", "selected_rows"),
     State("store-recommendations-data", "data"),
     State("modal-cotacao", "is_open")],
    prevent_initial_call=True
)
def handle_bulk_cotacao(n_clicks, selected_rows, recommendations_data, is_open):
    """Gerencia cotação em lote"""
    if not n_clicks or not selected_rows or not recommendations_data:
        return is_open, []
    
    selected_recs = [recommendations_data[i] for i in selected_rows if i < len(recommendations_data)]
    
    if selected_recs:
        modal_content = []
        for i, rec in enumerate(selected_recs):
            quotation_data = action_handler.generate_quotation_data(rec)
            
            modal_content.extend([
                html.H6(f"📋 Cotação {i+1}: {rec.get('material', 'N/A')}", className="text-primary"),
                dbc.Row([
                    dbc.Col([
                        html.P([html.Strong("Número: "), quotation_data.get('numero_cotacao', 'N/A')]),
                        html.P([html.Strong("Quantidade: "), f"{quotation_data.get('quantidade_sugerida', 0):,.0f}"]),
                        html.P([html.Strong("Preço Ref.: "), quotation_data.get('preco_referencia', 'N/A')])
                    ])
                ]),
                html.Hr() if i < len(selected_recs) - 1 else html.Div()
            ])
        
        return True, modal_content
    
    return is_open, []

@callback(
    [Output("feedback-toast", "is_open"),
     Output("feedback-toast", "children")],
    [Input("btn-bulk-like", "n_clicks"),
     Input("btn-bulk-irrelevante", "n_clicks")],
    [State("recommendations-table", "selected_rows"),
     State("store-recommendations-data", "data"),
     State("filter-cliente", "value")],
    prevent_initial_call=True
)
def handle_bulk_feedback(n_likes, n_irrelevantes, selected_rows, recommendations_data, client_code):
    """Gerencia feedback em lote com integração ao sistema de aprendizado"""
    ctx = dash.callback_context
    if not ctx.triggered or not selected_rows or not recommendations_data:
        return False, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    feedback_type = "like" if button_id == "btn-bulk-like" else "not_relevant"
    
    success_count = 0
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for row_idx in selected_rows:
        if row_idx < len(recommendations_data):
            recommendation = recommendations_data[row_idx]
            rec_id = f"{recommendation.get('material', 'unknown')}_{row_idx}"
            
            # Salvar feedback tradicional
            success = action_handler.save_feedback(
                recommendation_id=rec_id,
                feedback_type=feedback_type,
                client_code=client_code,
                additional_data={'recommendation': recommendation}
            )
            
            # Integrar com sistema de aprendizado ML
            if success:
                learning_success = learning_system.process_user_feedback(
                    recommendation_id=rec_id,
                    feedback_type=feedback_type,
                    client_code=client_code,
                    material=recommendation.get('material', 'unknown'),
                    confidence_score=recommendation.get('probabilidade_recompra', 0),
                    value_potential=recommendation.get('valor_potencial', 0),
                    session_id=session_id
                )
                if learning_success:
                    success_count += 1
    
    message = f"Feedback registrado para {success_count} de {len(selected_rows)} itens. Sistema ML atualizado! 🤖"
    return True, message

@callback(
    Output("btn-export-selection", "href"),
    [Input("btn-bulk-export-pdf", "n_clicks")],
    [State("recommendations-table", "selected_rows"),
     State("store-recommendations-data", "data")],
    prevent_initial_call=True
)
def export_selected_recommendations(n_clicks, selected_rows, recommendations_data):
    """Exporta recomendações selecionadas para PDF"""
    if not n_clicks or not selected_rows or not recommendations_data:
        return ""
    
    try:
        selected_recs = [recommendations_data[i] for i in selected_rows if i < len(recommendations_data)]
        
        if not selected_recs:
            return ""
        
        # Para múltiplas recomendações, usar Excel ao invés de PDF
        excel_data = action_handler.export_recommendations_excel(selected_recs)
        download_url = create_download_link(
            excel_data, 
            f"recomendacoes_selecionadas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        return download_url
    except Exception as e:
        print(f"Erro ao exportar seleção: {e}")
        return ""

@callback(
    Output("intelligent-alerts-container", "children"),
    [Input("store-recommendations-data", "data"),
     Input("filter-cliente", "value")]
)
def generate_intelligent_alerts(recommendations_data, selected_cliente):
    """Gera alertas inteligentes baseados nas recomendações"""
    if not recommendations_data or not selected_cliente:
        return []
    
    df = pd.DataFrame(recommendations_data)
    alerts = []
    
    # Alerta 1: Oportunidades críticas de alta confiança
    high_conf_high_value = df[(df['probabilidade_recompra'] >= 80) & (df['valor_potencial'] >= 10000)]
    if not high_conf_high_value.empty:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-fire me-2"),
                html.Strong("🔥 OPORTUNIDADE CRÍTICA: "),
                f"{len(high_conf_high_value)} materiais com alta confiança (≥80%) e alto valor (≥R$ 10k). ",
                f"Valor total: R$ {high_conf_high_value['valor_potencial'].sum():,.0f}. ",
                "Ação recomendada: Contato imediato!"
            ], color="danger", dismissable=True)
        )
    
    # Alerta 2: Padrão de sazonalidade
    try:
        conn = get_db_connection()
        current_month = datetime.now().month
        seasonal_query = """
        SELECT COUNT(*) as vendas_mes_atual
        FROM vendas 
        WHERE cod_cliente = ?
        AND strftime('%m', data_emissao) = ?
        AND data_emissao >= date('now', '-12 months')
        """
        
        cursor = conn.execute(seasonal_query, [selected_cliente, f"{current_month:02d}"])
        seasonal_data = cursor.fetchone()
        conn.close()
        
        if seasonal_data and seasonal_data[0] > 5:
            alerts.append(
                dbc.Alert([
                    html.I(className="fas fa-calendar-alt me-2"),
                    html.Strong("📅 PADRÃO SAZONAL: "),
                    f"Cliente historicamente ativo neste mês ({seasonal_data[0]} compras nos últimos 12 meses). ",
                    "Momento ideal para abordagem comercial!"
                ], color="info", dismissable=True)
            )
    except Exception as e:
        print(f"Erro no alerta sazonal: {e}")
    
    # Alerta 3: Concentração de oportunidades
    top_5_value = df.nlargest(5, 'valor_potencial')['valor_potencial'].sum()
    total_value = df['valor_potencial'].sum()
    concentration_pct = (top_5_value / total_value) * 100 if total_value > 0 else 0
    
    if concentration_pct > 70:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-bullseye me-2"),
                html.Strong("🎯 CONCENTRAÇÃO ESTRATÉGICA: "),
                f"{concentration_pct:.1f}% do valor potencial concentrado em apenas 5 materiais. ",
                "Estratégia: Focar esforços nos top performers para máxima eficiência!"
            ], color="warning", dismissable=True)
        )
    
    # Alerta 4: Oportunidades de baixo risco
    low_risk_high_prob = df[(df['probabilidade_recompra'] >= 75) & (df['valor_potencial'] <= 5000)]
    if len(low_risk_high_prob) >= 3:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-shield-alt me-2"),
                html.Strong("🛡️ BAIXO RISCO: "),
                f"{len(low_risk_high_prob)} oportunidades de baixo risco (≤R$ 5k) com alta probabilidade (≥75%). ",
                "Ideais para construir relacionamento e testar receptividade!"
            ], color="success", dismissable=True)
        )
    
    # Alerta 5: Diversificação de portfólio
    unique_gaps = df['motivo_da_sugestao'].unique()
    if len(unique_gaps) >= 3:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-chart-pie me-2"),
                html.Strong("📊 PORTFÓLIO DIVERSIFICADO: "),
                f"Identificados {len(unique_gaps)} tipos diferentes de gaps de mercado. ",
                "Oportunidade para ampliar penetração em múltiplas frentes!"
            ], color="primary", dismissable=True)
        )
    
    if not alerts:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Nenhum alerta crítico identificado. Continue monitorando as recomendações."
            ], color="light")
        )
    
    return html.Div([
        html.H5([
            html.I(className="fas fa-bell me-2"),
            "Alertas Inteligentes"
        ], className="text-primary mb-3"),
        html.Div(alerts)
    ])

@callback(
    Output("learning-content", "children"),
    [Input("learning-tabs", "active_tab"),
     Input("btn-run-learning-cycle", "n_clicks")]
)
def update_learning_content(active_tab, n_clicks):
    """Atualiza conteúdo do painel de aprendizado"""
    if active_tab == "tab-feedback-metrics":
        # Métricas de feedback
        try:
            metrics = learning_system.analyze_feedback_patterns(30)
            
            return dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metrics.total_feedbacks}", className="text-primary"),
                            html.P("Total de Feedbacks (30d)", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metrics.positive_rate:.1%}", className="text-success"),
                            html.P("Taxa de Aprovação", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metrics.relevance_rate:.1%}", className="text-info"),
                            html.P("Taxa de Relevância", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metrics.avg_confidence_adjustment:+.3f}", className="text-warning"),
                            html.P("Ajuste Médio de Confiança", className="card-text")
                        ])
                    ])
                ], width=3)
            ])
            
        except Exception as e:
            return dbc.Alert(f"Erro ao carregar métricas: {e}", color="danger")
    
    elif active_tab == "tab-ml-weights":
        # Pesos atuais do algoritmo
        try:
            weights = learning_system.ml_weights
            
            weights_data = [
                {"peso": "Análise de Gaps", "valor": f"{weights['gap_analysis_weight']:.3f}", "descrição": "Peso para análise de gaps de mercado"},
                {"peso": "Sazonalidade", "valor": f"{weights['seasonality_weight']:.3f}", "descrição": "Peso para padrões sazonais"},
                {"peso": "Benchmark", "valor": f"{weights['benchmark_weight']:.3f}", "descrição": "Peso para comparação com clientes similares"},
                {"peso": "Performance Histórica", "valor": f"{weights['historical_performance_weight']:.3f}", "descrição": "Peso para histórico de performance"},
                {"peso": "Similaridade de Cliente", "valor": f"{weights['client_similarity_weight']:.3f}", "descrição": "Peso para similaridade entre clientes"},
                {"peso": "Threshold Confiança", "valor": f"{weights['confidence_threshold']:.1f}%", "descrição": "Limite mínimo de confiança"},
                {"peso": "Taxa de Aprendizado", "valor": f"{weights['feedback_learning_rate']:.3f}", "descrição": "Velocidade de adaptação do algoritmo"}
            ]
            
            return dash_table.DataTable(
                data=weights_data,
                columns=[
                    {"name": "Parâmetro", "id": "peso"},
                    {"name": "Valor Atual", "id": "valor"},
                    {"name": "Descrição", "id": "descrição"}
                ],
                style_cell={'textAlign': 'left', 'fontSize': '14px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{peso} contains "Threshold"'},
                        'backgroundColor': '#fff3cd',
                        'border': '1px solid #ffeaa7'
                    }
                ]
            )
            
        except Exception as e:
            return dbc.Alert(f"Erro ao carregar pesos: {e}", color="danger")
    
    elif active_tab == "tab-material-performance":
        # Performance de materiais
        try:
            conn = get_db_connection()
            performance_query = """
                SELECT material, recommendation_count, positive_feedback_count, 
                       negative_feedback_count, conversion_rate, avg_confidence_score
                FROM material_performance_history
                WHERE recommendation_count >= 2
                ORDER BY conversion_rate DESC
                LIMIT 20
            """
            
            performance_df = pd.read_sql(performance_query, conn)
            conn.close()
            
            if not performance_df.empty:
                performance_data = performance_df.to_dict('records')
                
                return dash_table.DataTable(
                    data=performance_data,
                    columns=[
                        {"name": "Material", "id": "material"},
                        {"name": "Recomendações", "id": "recommendation_count", "type": "numeric"},
                        {"name": "Feedback +", "id": "positive_feedback_count", "type": "numeric"},
                        {"name": "Feedback -", "id": "negative_feedback_count", "type": "numeric"},
                        {"name": "Taxa Conversão", "id": "conversion_rate", "type": "numeric", "format": {"specifier": ".1%"}},
                        {"name": "Confiança Média", "id": "avg_confidence_score", "type": "numeric", "format": {"specifier": ".1f"}}
                    ],
                    style_cell={'textAlign': 'left', 'fontSize': '14px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{conversion_rate} > 0.7'},
                            'backgroundColor': '#d4edda',
                            'border': '1px solid #28a745'
                        },
                        {
                            'if': {'filter_query': '{conversion_rate} < 0.3'},
                            'backgroundColor': '#f8d7da',
                            'border': '1px solid #dc3545'
                        }
                    ],
                    page_size=10,
                    sort_action="native"
                )
            else:
                return dbc.Alert("Nenhum dado de performance disponível ainda.", color="info")
                
        except Exception as e:
            return dbc.Alert(f"Erro ao carregar performance: {e}", color="danger")
    
    return html.Div()

@callback(
    Output("btn-run-learning-cycle", "children"),
    [Input("btn-run-learning-cycle", "n_clicks")],
    prevent_initial_call=True
)
def run_learning_cycle(n_clicks):
    """Executa ciclo de aprendizado manual"""
    if not n_clicks:
        return [html.I(className="fas fa-sync me-1"), "Executar Ciclo de Aprendizado"]
    
    try:
        success = learning_system.run_daily_learning_cycle()
        if success:
            return [html.I(className="fas fa-check me-1"), "✅ Ciclo Executado"]
        else:
            return [html.I(className="fas fa-info me-1"), "ℹ️ Nenhum Ajuste"]
    except Exception as e:
        return [html.I(className="fas fa-times me-1"), "❌ Erro"]

# Callbacks para exportação avançada
@callback(
    [Output("modal-schedule", "is_open"),
     Output("schedule-clients", "options")],
    [Input("btn-schedule-reports", "n_clicks"),
     Input("btn-cancel-schedule", "n_clicks")],
    [State("modal-schedule", "is_open"),
     State("store-analytics-data", "data")],
    prevent_initial_call=True
)
def toggle_schedule_modal(n_open, n_cancel, is_open, analytics_data):
    """Controla abertura/fechamento do modal de agendamento"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-schedule-reports":
        # Carregar lista de clientes para agendamento
        try:
            conn = get_db_connection()
            clients_query = """
            SELECT DISTINCT cod_cliente, COUNT(*) as vendas
            FROM vendas 
            WHERE cod_cliente IS NOT NULL
            GROUP BY cod_cliente
            HAVING vendas >= 10
            ORDER BY vendas DESC
            LIMIT 50
            """
            clients_df = pd.read_sql(clients_query, conn)
            conn.close()
            
            client_options = [
                {"label": f"Cliente {row['cod_cliente']} ({row['vendas']} vendas)", 
                 "value": row['cod_cliente']} 
                for _, row in clients_df.iterrows()
            ]
            
            return True, client_options
        except Exception as e:
            print(f"Erro ao carregar clientes: {e}")
            return True, []
    
    return False, []

@callback(
    Output("store-export-data", "data"),
    [Input("btn-exec-pdf", "n_clicks"),
     Input("btn-detailed-excel", "n_clicks"),
     Input("btn-complete-package", "n_clicks")],
    [State("filter-cliente", "value")],
    prevent_initial_call=True
)
def handle_advanced_exports(n_pdf, n_excel, n_package, client_code):
    """Gerencia exportações avançadas"""
    ctx = dash.callback_context
    if not ctx.triggered or not client_code:
        return {}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "btn-exec-pdf":
            # Gerar PDF executivo
            resultado = export_system.recommender.run_complete_b2b_analysis(
                cod_cliente=client_code,
                contexto_comercial={'tipo_analise': 'executive_summary'},
                export_format='completo'
            )
            
            # Preparar recomendações
            recommendations = []
            if 'analises' in resultado and 'gaps_mercado' in resultado['analises']:
                gaps_data = resultado['analises']['gaps_mercado']
                for gap in gaps_data.get('gaps', []):
                    recommendations.append({
                        'material': gap['material'],
                        'descricao': gap.get('produto', 'Produto WEG'),
                        'qtd_sugerida': gap.get('qtd_potencial', 0),
                        'motivo_da_sugestao': f"Gap de mercado: {gap['w_percent']:.1f}% penetração",
                        'probabilidade_recompra': gap['score_oportunidade'],
                        'nivel_confianca': 'ALTA' if gap['score_oportunidade'] >= 80 else 'MÉDIA' if gap['score_oportunidade'] >= 60 else 'BAIXA',
                        'valor_potencial': gap.get('valor_potencial', 0)
                    })
            
            pdf_data = export_system.generate_executive_summary_pdf(client_code, recommendations)
            if pdf_data:
                download_url = create_download_link_advanced(
                    pdf_data,
                    f"relatorio_executivo_{client_code}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "application/pdf"
                )
                return {"type": "pdf", "url": download_url, "filename": f"relatorio_executivo_{client_code}.pdf"}
        
        elif button_id == "btn-detailed-excel":
            # Gerar Excel detalhado
            resultado = export_system.recommender.run_complete_b2b_analysis(
                cod_cliente=client_code,
                contexto_comercial={'tipo_analise': 'detailed_analysis'},
                export_format='completo'
            )
            
            excel_data = export_system.generate_detailed_excel_report(client_code, resultado)
            if excel_data:
                download_url = create_download_link_advanced(
                    excel_data,
                    f"analise_detalhada_{client_code}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                return {"type": "excel", "url": download_url, "filename": f"analise_detalhada_{client_code}.xlsx"}
        
        elif button_id == "btn-complete-package":
            # Gerar pacote completo
            package_data = export_system.generate_complete_export_package(client_code)
            if package_data:
                download_url = create_download_link_advanced(
                    package_data,
                    f"pacote_completo_{client_code}_{datetime.now().strftime('%Y%m%d')}.zip",
                    "application/zip"
                )
                return {"type": "package", "url": download_url, "filename": f"pacote_completo_{client_code}.zip"}
        
        return {"error": "Erro ao gerar exportação"}
        
    except Exception as e:
        print(f"Erro na exportação avançada: {e}")
        return {"error": str(e)}

# Callbacks para filtros avançados
@callback(
    [Output("active-filters-indicators", "children"),
     Output("filter-categoria", "options")],
    [Input("filter-cliente", "value"),
     Input("filter-confianca", "value"),
     Input("filter-periodo", "value"),
     Input("filter-valor-range", "value"),
     Input("filter-gap-type", "value"),
     Input("filter-benchmark", "value")]
)
def update_filter_indicators(cliente, confianca, periodo, valor_range, gap_type, benchmark):
    """Atualiza indicadores de filtros ativos e opções de categoria"""
    # Indicadores de filtros ativos
    indicators = []
    
    if cliente:
        indicators.append(
            dbc.Badge(f"Cliente: {cliente}", color="primary", className="me-2")
        )
    
    if confianca and confianca > 0:
        indicators.append(
            dbc.Badge(f"Confiança ≥ {confianca}%", color="success", className="me-2")
        )
    
    if periodo and periodo != 12:
        indicators.append(
            dbc.Badge(f"Período: {periodo} meses", color="info", className="me-2")
        )
    
    if valor_range and (valor_range[0] > 0 or valor_range[1] < 100000):
        indicators.append(
            dbc.Badge(f"Valor: R$ {valor_range[0]:,} - R$ {valor_range[1]:,}", color="warning", className="me-2")
        )
    
    if gap_type and gap_type != ["todos"]:
        gap_labels = {"critico": "Críticos", "oportunidade": "Oportunidades", "sazonal": "Sazonais", "benchmark": "Benchmark"}
        gap_text = ", ".join([gap_labels.get(g, g) for g in gap_type if g != "todos"])
        if gap_text:
            indicators.append(
                dbc.Badge(f"Gaps: {gap_text}", color="secondary", className="me-2")
            )
    
    # Carregar categorias de produto
    categoria_options = []
    try:
        conn = get_db_connection()
        cat_query = """
        SELECT DISTINCT 
            CASE 
                WHEN material LIKE '1%' THEN 'Motores'
                WHEN material LIKE '2%' THEN 'Inversores'
                WHEN material LIKE '3%' THEN 'Soft-Starters'
                WHEN material LIKE '4%' THEN 'Automação'
                WHEN material LIKE '5%' THEN 'Painéis'
                ELSE 'Outros'
            END as categoria
        FROM vendas
        WHERE categoria != 'Outros'
        """
        
        cat_df = pd.read_sql(cat_query, conn)
        conn.close()
        
        categoria_options = [
            {"label": cat, "value": cat} 
            for cat in cat_df['categoria'].unique()
        ]
        
    except Exception as e:
        print(f"Erro ao carregar categorias: {e}")
    
    if indicators:
        filter_display = html.Div([
            html.Strong("Filtros Ativos: "),
            html.Span(indicators),
            dbc.Button(
                "❌ Limpar",
                id="btn-clear-active-filters",
                size="sm",
                color="light",
                className="ms-2"
            )
        ])
    else:
        filter_display = dbc.Alert("Nenhum filtro específico ativo", color="light", className="mb-0")
    
    return filter_display, categoria_options

@callback(
    Output("saved-filters", "options"),
    [Input("btn-save-filter", "n_clicks"),
     Input("btn-delete-filter", "n_clicks")],
    [State("filter-name-input", "value"),
     State("saved-filters", "value"),
     State("filter-cliente", "value"),
     State("filter-confianca", "value"),
     State("filter-periodo", "value"),
     State("filter-valor-range", "value")],
    prevent_initial_call=True
)
def manage_saved_filters(n_save, n_delete, filter_name, selected_filter, cliente, confianca, periodo, valor_range):
    """Gerencia filtros salvos (salvar/excluir)"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        conn = get_db_connection()
        
        # Criar tabela de filtros salvos se não existir
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                filter_config TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        if button_id == "btn-save-filter" and filter_name:
            # Salvar novo filtro
            filter_config = {
                "cliente": cliente,
                "confianca": confianca,
                "periodo": periodo,
                "valor_range": valor_range
            }
            
            conn.execute("""
                INSERT OR REPLACE INTO saved_filters (name, filter_config)
                VALUES (?, ?)
            """, (filter_name, json.dumps(filter_config)))
            
        elif button_id == "btn-delete-filter" and selected_filter:
            # Excluir filtro selecionado
            conn.execute("""
                DELETE FROM saved_filters WHERE name = ?
            """, (selected_filter,))
        
        # Carregar filtros salvos
        cursor = conn.execute("""
            SELECT name, usage_count FROM saved_filters 
            ORDER BY usage_count DESC, created_at DESC
        """)
        
        saved_filters = cursor.fetchall()
        conn.commit()
        conn.close()
        
        return [
            {"label": f"{name} (usado {count}x)", "value": name}
            for name, count in saved_filters
        ]
        
    except Exception as e:
        print(f"Erro ao gerenciar filtros salvos: {e}")
        return []

@callback(
    [Output("filter-cliente", "value"),
     Output("filter-confianca", "value"),
     Output("filter-periodo", "value"),
     Output("filter-valor-range", "value")],
    [Input("saved-filters", "value"),
     Input("btn-clear-filters", "n_clicks")],
    prevent_initial_call=True
)
def load_or_clear_filters(selected_filter, n_clear):
    """Carrega filtro salvo ou limpa todos os filtros"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, 70, 12, [1000, 50000]
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-clear-filters":
        # Limpar todos os filtros
        return None, 0, 12, [0, 100000]
    
    elif button_id == "saved-filters" and selected_filter:
        # Carregar filtro salvo
        try:
            conn = get_db_connection()
            
            cursor = conn.execute("""
                SELECT filter_config FROM saved_filters WHERE name = ?
            """, (selected_filter,))
            
            result = cursor.fetchone()
            
            if result:
                # Incrementar contador de uso
                conn.execute("""
                    UPDATE saved_filters 
                    SET usage_count = usage_count + 1 
                    WHERE name = ?
                """, (selected_filter,))
                
                conn.commit()
                config = json.loads(result[0])
                
                return (
                    config.get("cliente"),
                    config.get("confianca", 70),
                    config.get("periodo", 12),
                    config.get("valor_range", [1000, 50000])
                )
            
            conn.close()
            
        except Exception as e:
            print(f"Erro ao carregar filtro salvo: {e}")
    
    return None, 70, 12, [1000, 50000]

if __name__ == "__main__":
    pass