"""
Callbacks principais da aplicação com performance otimizada
Integração com AI Framework para preparação evolutiva
"""

from dash import Input, Output, State, callback_context, dash_table, html, dcc
import dash
import pandas as pd
import dash_bootstrap_components as dbc
import logging
from webapp import app
from webapp.auth import authenticated_callback
from utils import (
    load_vendas_data,
    load_cotacoes_data,
    load_produtos_cotados_data,
    AdvancedAnalytics,
    apply_filters,
    determine_hierarchy_level,
    get_setting,
    save_setting,
    delete_setting,
)
from utils.opportunity import compute_client_opportunities
from utils.aggrid_config import build_column_defs, default_col_def, default_grid_options

# OBS: As implementações de apply_filters e determine_hierarchy_level foram movidas para utils.filters
# para servir como ponto único de verdade e evitar divergências entre módulos.

# Registrar callbacks do chat (mantém comportamento anterior)
try:
    from webapp.chat_interface import register_chat_callbacks
    register_chat_callbacks(app)
    print("✅ Callbacks do chat registrados com sucesso")
except Exception as e:
    print(f"⚠️ Erro ao registrar callbacks do chat: {e}")

# Callback para mostrar conteúdo baseado na página
@app.callback(
    Output('page-main-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def display_page_content(pathname):
    """Mostra o conteúdo correto baseado na URL"""
    print(f"🔄 DISPLAY_PAGE_CONTENT executado para: {pathname}")
    
    try:
        if pathname == '/app/chat':
            from webapp.layouts import create_chat_layout
            layout = create_chat_layout()
        elif pathname == '/app/overview' or pathname == '/app' or pathname == '/':
            from webapp.layouts import create_overview_layout
            layout = create_overview_layout()
        elif pathname == '/app/clients':
            from webapp.layouts import create_clients_layout
            layout = create_clients_layout()
            
            # CORREÇÃO ESPECÍFICA: Verificar se o layout de clientes é válido
            if layout is None:
                print(f"❌ Layout de clientes retornado é None")
                return html.Div([
                    dbc.Alert("Erro: Layout de clientes não encontrado", color="danger")
                ])
            
            print("✅ Layout de clientes validado com sucesso")
            return layout
        elif pathname == '/app/products' or pathname == '/produtos':
            from webapp.layouts import create_products_layout
            from utils.component_validator import safe_component_return
            try:
                layout = create_products_layout()
                
                # CORREÇÃO ESPECÍFICA: Validação robusta do layout
                validated_layout = safe_component_return(
                    layout, 
                    "Erro ao carregar página de produtos"
                )
                
                print("✅ Layout de produtos validado com sucesso")
                return validated_layout
                
            except Exception as e:
                print(f"❌ Erro ao criar layout de produtos: {e}")
                import traceback
                traceback.print_exc()
                return html.Div([
                    dbc.Alert(f"Erro ao carregar página de produtos: {str(e)}", color="danger"),
                    html.P("Verifique os logs do servidor para mais detalhes.")
                ])
                
        elif pathname == '/app/funnel':
            from webapp.layouts import create_funnel_layout
            layout = create_funnel_layout()
        elif pathname == '/app/insights':
            from webapp.layouts import create_insights_layout
            layout = create_insights_layout()
        elif pathname == '/app/analytics':
            from webapp.layouts import create_analytics_layout
            layout = create_analytics_layout()
        elif pathname == '/app/config':
            from webapp.layouts import create_config_layout
            layout = create_config_layout()
        else:
            layout = html.Div([
                dbc.Alert("Página não encontrada", color="warning")
            ])
            
        # CORREÇÃO: Verificar se o layout é válido antes de retornar
        if layout is None:
            print(f"❌ Layout retornado é None para pathname: {pathname}")
            return html.Div([
                dbc.Alert("Erro: Layout não encontrado", color="danger")
            ])
            
        return layout
        
    except Exception as e:
        print(f"❌ Erro em display_page_content: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Erro ao carregar página: {str(e)}", color="danger")
        ])

# Callback para popular filtros globais
@app.callback(
    [Output('global-filtro-cliente', 'options'),
     Output('global-filtro-hierarquia', 'options'),
     Output('global-filtro-canal', 'options')],
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_filter_options(pathname):
    """Atualiza opções dos filtros globais"""
    print(f"🔄 update_filter_options executado para pathname: {pathname}")
    try:
        # Carrega dados
        vendas_df = load_vendas_data()
        print(f"📊 Dados carregados: {len(vendas_df)} registros de vendas")
        
        if vendas_df.empty:
            print("❌ Nenhum dado de vendas encontrado")
            return [], [], []
        
        # Opções de clientes (robusto a colunas ausentes)
        cliente_options = []
        try:
            dfc = vendas_df.copy()
            # Normalizar possíveis colunas
            if 'cod_cliente' in dfc.columns:
                dfc['cod_cliente'] = dfc['cod_cliente'].astype(str).str.strip()
            # Se não houver 'cliente', tentar encontrar uma alternativa comum
            nome_col = 'cliente' if 'cliente' in dfc.columns else None
            for alt in ['nome_cliente', 'cliente_nome', 'razao_social']:
                if nome_col is None and alt in dfc.columns:
                    nome_col = alt
            if 'cod_cliente' in dfc.columns:
                base_cols = ['cod_cliente'] + ([nome_col] if nome_col else [])
                clientes_unique = dfc[base_cols].dropna(subset=['cod_cliente']).drop_duplicates('cod_cliente')
                for _, row in clientes_unique.iterrows():
                    code = str(row['cod_cliente'])
                    name = str(row[nome_col]) if (nome_col and pd.notna(row.get(nome_col))) else ''
                    label = f"{code} -- {name}" if name else code
                    cliente_options.append({'label': label, 'value': code})
            elif nome_col:
                for val in sorted(set(dfc[nome_col].dropna().astype(str))):
                    cliente_options.append({'label': val, 'value': val})
        except Exception as _e_cli:
            print(f"⚠️ Falha ao montar opções de cliente: {_e_cli}")
        print(f"✅ Clientes: {len(cliente_options)} opções")
        
        # Opções de hierarquia de produto (deduplicadas / ordenadas)
        hierarquia_options = []
        try:
            seen = set()
            for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
                if col in vendas_df.columns:
                    vals = [str(v) for v in vendas_df[col].dropna().unique()]
                    for v in vals:
                        if v not in seen:
                            seen.add(v)
            hierarquia_options = [{'label': v, 'value': v} for v in sorted(seen)]
        except Exception as _e_h:
            print(f"⚠️ Falha ao montar hierarquia: {_e_h}")
        print(f"✅ Hierarquia: {len(hierarquia_options)} opções")
        
        # Opções de canal (suporta 'canal_distribuicao' e fallback 'canal')
        canal_options = []
        try:
            if 'canal_distribuicao' in vendas_df.columns:
                unique_canais = sorted(set(vendas_df['canal_distribuicao'].dropna().astype(str)))
                canal_options = [{'label': c, 'value': c} for c in unique_canais]
            elif 'canal' in vendas_df.columns:
                unique_canais = sorted(set(vendas_df['canal'].dropna().astype(str)))
                canal_options = [{'label': c, 'value': c} for c in unique_canais]
        except Exception as _e_c:
            print(f"⚠️ Falha ao montar canais: {_e_c}")
        print(f"✅ Canais: {len(canal_options)} opções")
        
        return cliente_options, hierarquia_options, canal_options
        
    except Exception as e:
        print(f"❌ Erro ao atualizar filtros: {e}")
        import traceback
        traceback.print_exc()
        return [], [], []

# Callback para analytics
@app.callback(
    Output('analytics-content', 'children'),
    [Input('analytics-tipo-analise', 'value'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value')],
    prevent_initial_call=False
)
def update_analytics_content(tipo_analise, filtro_ano, filtro_mes, filtro_cliente, 
                           filtro_hierarquia, filtro_canal, filtro_top_clientes):
    """Atualiza o conteúdo da página de analytics baseado no tipo de análise selecionado"""
    print(f"🔥 UPDATE_ANALYTICS_CONTENT EXECUTADO!")
    print(f"🔥 Tipo análise: {tipo_analise}")
    print(f"🔥 Filtros: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    
    # Set default analysis type if none selected
    if not tipo_analise:
        tipo_analise = "gaps"
        print(f"🔥 Usando tipo padrão: {tipo_analise}")
    
    try:
        from utils import AdvancedAnalytics
        
        # Carregar dados
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        print(f"📊 Analytics Debug - Vendas: {len(df_vendas) if df_vendas is not None else 0} registros")
        print(f"📊 Analytics Debug - Cotações: {len(df_cotacoes) if df_cotacoes is not None else 0} registros")
        
        # Aplicar filtros aos dados
        df_vendas_filtrado = apply_filters(
            df_vendas, filtro_ano, filtro_mes, filtro_cliente, 
            filtro_hierarquia, filtro_canal, filtro_top_clientes
        ) if df_vendas is not None and not df_vendas.empty else df_vendas
        
        df_cotacoes_filtrado = apply_filters(
            df_cotacoes, filtro_ano, filtro_mes, filtro_cliente, 
            filtro_hierarquia, filtro_canal, filtro_top_clientes
        ) if df_cotacoes is not None and not df_cotacoes.empty else df_cotacoes
        
        print(f"📊 Analytics Debug - Vendas filtradas: {len(df_vendas_filtrado) if df_vendas_filtrado is not None else 0} registros")
        print(f"📊 Analytics Debug - Cotações filtradas: {len(df_cotacoes_filtrado) if df_cotacoes_filtrado is not None else 0} registros")
        
        # Inicializar o analisador com dados originais
        analytics = AdvancedAnalytics(df_vendas, df_cotacoes)
        
        if tipo_analise == "gaps":
            return create_gaps_analysis_content(analytics, df_vendas_filtrado, df_cotacoes_filtrado)
        elif tipo_analise == "inatividade":
            return create_inactivity_analysis_content(analytics, df_vendas_filtrado)
        elif tipo_analise == "sazonalidade":
            return create_seasonality_analysis_content(analytics, df_vendas_filtrado)
        elif tipo_analise == "cotacoes":
            return create_quotation_demand_content(analytics, df_cotacoes_filtrado)
        else:
            return html.Div([
                dbc.Alert("Tipo de análise não reconhecido.", color="warning")
            ])
            
    except Exception as e:
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro ao carregar análise: {str(e)}"
            ], color="danger")
        ])

def create_gaps_analysis_content(analytics, df_vendas_filtrado=None, df_cotacoes_filtrado=None):
    """Cria conteúdo para análise de gaps de oportunidade - versão completa"""
    try:
        # Sliders de pesos (UI)
        weight_controls = dbc.Row([
            dbc.Col([
                html.Label("Peso Recência (R)", className="small"),
                dcc.Slider(id="gaps-weight-r", min=0, max=100, step=5, value=30,
                           marks={0:'0', 30:'30', 50:'50', 70:'70', 100:'100'})
            ], width=4),
            dbc.Col([
                html.Label("Peso Frequência (F)", className="small"),
                dcc.Slider(id="gaps-weight-f", min=0, max=100, step=5, value=40,
                           marks={0:'0', 40:'40', 50:'50', 70:'70', 100:'100'})
            ], width=4),
            dbc.Col([
                html.Label("Peso Valor (M)", className="small"),
                dcc.Slider(id="gaps-weight-m", min=0, max=100, step=5, value=30,
                           marks={0:'0', 30:'30', 50:'50', 70:'70', 100:'100'})
            ], width=4)
        ], className="mb-2")
        weight_reset = dbc.Row([
            dbc.Col(dbc.Button("Restaurar pesos 30/40/30", id='gaps-weights-reset', color='secondary', outline=True, size='sm'), width='auto')
        ], className='mb-3')

        # Dica inicial de pesos normalizados (30/40/30)
        r0, f0, m0 = 30, 40, 30
        s0 = max(r0 + f0 + m0, 1)
        hint_initial = html.Div([
            html.P("Dica: os pesos são normalizados para somarem 100% automaticamente.", className="text-muted small mb-1"),
            html.P(f"Pesos normalizados: R={r0/s0*100:.0f}%, F={f0/s0*100:.0f}%, M={m0/s0*100:.0f}%", className="text-muted small mb-0")
        ], id='gaps-weights-hint', className='mb-3')

        # Configurações avançadas (penalidades/impulsos)
        advanced_cfg = dbc.Card([
            dbc.CardHeader([
                html.Strong("Configurações avançadas"),
                html.Span(" – ajuste penalidades e impulso de prioridade de cotações", className="text-muted small"),
                dbc.Button([
                    html.I(className="fas fa-question-circle me-2"),
                    "Ajuda"
                ], id='gaps-help-open', color='info', outline=True, size='sm', className='float-end')
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Início penalização conversão (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-conv-start', type='number', min=0, max=1, step=0.05, value=0.6, className='form-control'),
                        dbc.Tooltip("Taxa de conversão a partir da qual começamos a penalizar (0–1). Ex.: 0.6 = 60%.", target='gaps-pen-conv-start', placement='right')
                    ], width=4),
                    dbc.Col([
                        html.Label("Amplitude penalização conv (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-conv-span', type='number', min=0, max=1, step=0.05, value=0.4, className='form-control'),
                        dbc.Tooltip("Intervalo de conversão até atingir penalização máxima (0–1). Ex.: 0.4 cobre até 100%.", target='gaps-pen-conv-span', placement='right')
                    ], width=4),
                    dbc.Col([
                        html.Label("Penalização máx. conv (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-conv-max', type='number', min=0, max=1, step=0.05, value=0.4, className='form-control'),
                        dbc.Tooltip("Intensidade máxima da penalização por alta conversão (0–1).", target='gaps-pen-conv-max', placement='right')
                    ], width=4)
                ], className='mb-2'),
                dbc.Row([
                    dbc.Col([
                        html.Label("Penalização máx. vendas recentes (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-recent-max', type='number', min=0, max=1, step=0.05, value=0.2, className='form-control'),
                        dbc.Tooltip("Intensidade máxima da penalização por vendas muito recentes (0–1).", target='gaps-pen-recent-max', placement='right')
                    ], width=4),
                    dbc.Col([
                        html.Label("Impulso prioridade cotações máx. (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-boost-max', type='number', min=0, max=1, step=0.05, value=0.15, className='form-control'),
                        dbc.Tooltip("Impulso máximo para materiais com cotações recentes/prioridade (0–1).", target='gaps-pen-boost-max', placement='right')
                    ], width=4),
                    dbc.Col([
                        html.Label("Piso de momentum (0–1)", className="small"),
                        dcc.Input(id='gaps-pen-momentum-floor', type='number', min=0, max=1, step=0.05, value=0.5, className='form-control'),
                        dbc.Tooltip("Piso de momentum: mínimo de impulso para evitar zerar incremental (0–1).", target='gaps-pen-momentum-floor', placement='right')
                    ], width=4)
                ]),
                dbc.Row([
                    dbc.Col(html.P("Dica: use valores entre 0 e 1. Ex.: 0.6 = 60%.", className="text-muted small mt-2 mb-0"), width=8),
                    dbc.Col(dbc.Button("Restaurar padrões", id='gaps-pen-reset', color='secondary', outline=True, size='sm', className='float-end mt-1'), width=4)
                ], className='mt-1')
            ])
        ], className='mb-3')

        # Modal de ajuda da análise de gaps
        gaps_help_modal = dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Como usar a Análise de Gaps")),
            dbc.ModalBody([
                html.P("Esta seção ajuda a priorizar produtos por potencial de crescimento baseado em padrões de compra (Q‑RFV) e sinais recentes (cotações)."),
                html.H6("Pesos (R/F/M)", className="mt-3"),
                html.Ul([
                    html.Li([html.Strong("R – Recência:"), " privilegia itens com clientes que compraram há mais tempo."]),
                    html.Li([html.Strong("F – Frequência:"), " destaca itens comprados com menos regularidade que o esperado."],),
                    html.Li([html.Strong("M – Valor:"), " foca itens com maior oportunidade de receita."])
                ], className='mb-2'),
                html.P("Os pesos são normalizados automaticamente. O padrão recomendado é 30/40/30 (R/F/M)." , className='text-muted small'),
                html.H6("Penalidades e Impulso", className="mt-3"),
                html.Ul([
                    html.Li([html.Strong("Conversão alta:"), " reduz score quando o item já converte bem – menos gap a capturar."]),
                    html.Li([html.Strong("Vendas muito recentes:"), " reduz score para evitar ‘recompras’ imediatas."]),
                    html.Li([html.Strong("Impulso por cotações:"), " aumenta score quando há interesse recente ou prioridade."])
                ]),
                html.H6("Interpretação do Score", className="mt-3"),
                html.Ul([
                    html.Li([html.Strong("Alto (≥ 70):"), " priorize ação (campanhas, follow‑ups, propostas)."]),
                    html.Li([html.Strong("Médio (40–69):"), " investigue causas (preço, estoque, timing) e segmente."]),
                    html.Li([html.Strong("Baixo (< 40):"), " oportunidade limitada agora ou dados insuficientes."])
                ]),
                html.H6("Dicas rápidas", className="mt-3"),
                html.Ul([
                    html.Li("Use ‘Comparar (Overlay)’ para ver Padrão (cinza) vs Ajuste Atual (colorido)."),
                    html.Li("Clique em ‘Aplicar Visualização’ para fixar a escolha em toda a página."),
                    html.Li("Passe o mouse nos pontos para ver explicações (recência, conversão, penalidades, base).")
                ], className='mb-0')
            ]),
            dbc.ModalFooter(
                dbc.Button("Fechar", id='gaps-help-close', color='secondary')
            )
        ], id='gaps-help-modal', is_open=False)

        # Primeiro cálculo com pesos padrão; callback abaixo atualizará dinamicamente
        gaps_data = analytics.calculate_opportunity_gaps(
            vendas_df=df_vendas_filtrado,
            cotacoes_df=df_cotacoes_filtrado,
            weights={"r": 30, "f": 40, "m": 30}
        )
        # Garante DataFrame
        if gaps_data is None:
            gaps_data = pd.DataFrame()
        # Normaliza colunas esperadas e tipos
        expected_cols = ['produto', 'gap_score', 'gap_category', 'cliente_count', 'current_revenue', 'potential_revenue']
        for col in expected_cols:
            if col not in gaps_data.columns:
                if col in ['gap_score', 'cliente_count', 'current_revenue', 'potential_revenue']:
                    gaps_data[col] = 0
                elif col == 'gap_category':
                    # Deriva de score se possível
                    if 'gap_score' in gaps_data.columns:
                        gaps_data[col] = pd.cut(gaps_data['gap_score'], bins=[-1, 40, 70, 100], labels=['Baixo', 'Médio', 'Alto']).astype(str)
                    else:
                        gaps_data[col] = 'Desconhecido'
                elif col == 'produto':
                    gaps_data[col] = 'N/A'
        # Coerção numérica segura
        for num_col in ['gap_score', 'cliente_count', 'current_revenue', 'potential_revenue']:
            if num_col in gaps_data.columns:
                gaps_data[num_col] = pd.to_numeric(gaps_data[num_col], errors='coerce').fillna(0)
        
        # Adicionar colunas Material e Quantidade Sugerida
        if 'material' not in gaps_data.columns and df_vendas_filtrado is not None:
            try:
                if 'produto' in df_vendas_filtrado.columns and 'material' in df_vendas_filtrado.columns:
                    material_map = df_vendas_filtrado.groupby('produto')['material'].first().to_dict()
                    gaps_data['material'] = gaps_data['produto'].map(material_map).fillna('N/A')
                else:
                    gaps_data['material'] = 'N/A'
            except Exception:
                gaps_data['material'] = 'N/A'
        elif 'material' not in gaps_data.columns:
            gaps_data['material'] = 'N/A'
        
        if 'quantidade_sugerida' not in gaps_data.columns and df_vendas_filtrado is not None:
            try:
                if 'produto' in df_vendas_filtrado.columns and 'qtd_rol' in df_vendas_filtrado.columns:
                    qty_map = df_vendas_filtrado.groupby('produto')['qtd_rol'].mean().to_dict()
                    gaps_data['quantidade_sugerida'] = gaps_data['produto'].map(qty_map).fillna(1).round(0).astype(int)
                else:
                    gaps_data['quantidade_sugerida'] = 1
            except Exception:
                gaps_data['quantidade_sugerida'] = 1
        elif 'quantidade_sugerida' not in gaps_data.columns:
            gaps_data['quantidade_sugerida'] = 1
        
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Gráfico principal com fallback seguro caso colunas faltem
        try:
            hover_cols = [
                'produto', 'current_revenue', 'conversion_rate', 'nao_comprado_pct',
                'v_recency_days', 'q_recency_days', 'freq_gap', 'recency_gap', 'valor_gap',
                'penalty_recent_sales', 'penalty_high_conv', 'gap_score_base'
            ]
            hover_cols = [c for c in hover_cols if c in gaps_data.columns]
            fig = px.scatter(
                gaps_data, 
                x='potential_revenue', 
                y='gap_score',
                size='cliente_count',
                color='gap_category',
                hover_data=hover_cols,
                title="Gaps de Oportunidade por Produto",
                labels={
                    'potential_revenue': 'Receita Potencial (R$)',
                    'gap_score': 'Score do Gap',
                    'cliente_count': 'Número de Clientes'
                }
            )
        except Exception:
            # Fallback simples
            fig = go.Figure()
            fig.update_layout(title="Gaps de Oportunidade por Produto", template="plotly_white")
        
        fig.update_layout(
            showlegend=True,
            height=500,
            template="plotly_white",
            xaxis=dict(
                autorange=True,
                fixedrange=False,
                title="Receita Potencial (R$)"
            ),
            yaxis=dict(
                autorange=True,
                fixedrange=False,
                title="Score do Gap"
            ),
            dragmode="zoom",
            selectdirection="d"
        )

        # Linhas de corte horizontais no scatter (y=40 e y=70)
        try:
            for yval, color in [(40, '#f57c00'), (70, '#c62828')]:
                fig.add_shape(type='line', x0=0, x1=1, y0=yval, y1=yval, xref='paper', yref='y',
                              line=dict(color=color, dash='dash'))
        except Exception:
            pass

        # Escala dinâmica do eixo X (Receita Potencial): usa log se amplitude for muito grande
        scale_label = 'Linear'
        try:
            if 'potential_revenue' in gaps_data.columns:
                vals = pd.to_numeric(gaps_data['potential_revenue'], errors='coerce').dropna()
                if not vals.empty:
                    min_pos = vals[vals > 0].min() if (vals > 0).any() else None
                    max_val = vals.max()
                    if min_pos is not None and max_val / max(min_pos, 1e-9) > 100:
                        fig.update_xaxes(type='log', tickprefix='R$ ', tickformat=',.0f', showexponent='none')
                        scale_label = 'Log'
                    else:
                        fig.update_xaxes(type='linear', tickprefix='R$ ', tickformat=',.0f')
        except Exception:
            pass
        # Atualiza o título indicando a escala
        fig.update_layout(title=f"Gaps de Oportunidade por Produto – Escala: {scale_label}")

        # Distribuição inicial de score: histograma com linhas de corte e quantis
        import numpy as np
        try:
            dist_fig = px.histogram(gaps_data, x='gap_score', nbins=20, histnorm='percent', title='Distribuição do Score de Gap (%)')
        except Exception:
            dist_fig = go.Figure()
            dist_fig.update_layout(title='Distribuição do Score de Gap (%)')
        dist_fig.update_layout(template='plotly_white', height=300, bargap=0.05, xaxis_title='Score de Gap', yaxis_title='% de Produtos')
        if not gaps_data.empty and 'gap_score' in gaps_data.columns:
            qs = gaps_data['gap_score'].dropna()
            q50 = float(qs.median()) if not qs.empty else None
            q25 = float(qs.quantile(0.25)) if not qs.empty else None
            q75 = float(qs.quantile(0.75)) if not qs.empty else None
            for xval, color in [(40, '#f57c00'), (70, '#c62828')]:
                dist_fig.add_shape(type='line', x0=xval, x1=xval, y0=0, y1=1, xref='x', yref='paper', line=dict(color=color, dash='dash'))
            for xval, color in [(q25, '#6c757d'), (q50, '#0d6efd'), (q75, '#6c757d')]:
                if xval is not None:
                    dist_fig.add_shape(type='line', x0=xval, x1=xval, y0=0, y1=1, xref='x', yref='paper', line=dict(color=color, dash='dot'))

        # Mini-resumo por categoria (contagem e %)
        total_rows = int(len(gaps_data))
        def _count_pct(cat):
            if 'gap_category' in gaps_data.columns and total_rows > 0:
                c = int((gaps_data['gap_category'].astype(str) == cat).sum())
                p = 100.0 * c / total_rows
                return c, p
            return 0, 0.0
        alto_c, alto_p = _count_pct('Alto')
        medio_c, medio_p = _count_pct('Médio')
        baixo_c, baixo_p = _count_pct('Baixo')
        summary_children = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Alto", className="text-danger small mb-1"), html.H4(f"{alto_c} ({alto_p:.1f}%)", className="mb-0")])) , width=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Médio", className="text-warning small mb-1"), html.H4(f"{medio_c} ({medio_p:.1f}%)", className="mb-0")])) , width=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Baixo", className="text-secondary small mb-1"), html.H4(f"{baixo_c} ({baixo_p:.1f}%)", className="mb-0")])) , width=2),
        ], className="mb-2")
        
        # Estatísticas de score (mediana e IQR)
        qs_stats = gaps_data['gap_score'].dropna() if 'gap_score' in gaps_data.columns else pd.Series(dtype=float)
        if qs_stats.empty:
            med_score = 0.0
            q1 = 0.0
            q3 = 0.0
            iqr = 0.0
        else:
            med_score = float(qs_stats.median())
            q1 = float(qs_stats.quantile(0.25))
            q3 = float(qs_stats.quantile(0.75))
            iqr = float(q3 - q1)

        # KPIs container (dynamic)
        mean_base_initial = gaps_data['gap_score_base'].mean() if 'gap_score_base' in gaps_data.columns and not gaps_data.empty else None
        kpi_row = dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(gaps_data):,}", className="text-primary mb-0"),
                            html.P("Produtos Analisados", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{gaps_data['gap_score'].mean():.2f}", className="text-warning mb-0"),
                            html.P("Score Médio", className="text-muted small mb-1"),
                            html.Small((f"Base: {mean_base_initial:.2f}" if mean_base_initial is not None else ""), className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {gaps_data.get('incremental_revenue', pd.Series()).sum():,.0f}", className="text-info mb-0"),
                            html.P("Receita Incremental Total", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {gaps_data['potential_revenue'].sum():,.0f}", className="text-success mb-0"),
                            html.P("Receita Potencial Total", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
            ], className="mb-3")

        stats_row = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Mediana do Score", className="text-muted small mb-1"),
                        html.H4(f"{med_score:.2f}", className="mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("IQR do Score (Q3-Q1)", className="text-muted small mb-1"),
                        html.H4(f"{iqr:.2f}", className="mb-0")
                    ])
                ])
            ], width=3),
        ], className="mb-2")

        kpis_children = html.Div([kpi_row, stats_row])

        # Badge inicial: Incremental penalizado por conversão/recência
        try:
            incr_total = float(gaps_data.get('incremental_revenue', pd.Series(dtype=float)).sum()) if 'incremental_revenue' in gaps_data.columns else 0.0
        except Exception:
            incr_total = 0.0
        try:
            pot_total = float(gaps_data['potential_revenue'].sum()) if 'potential_revenue' in gaps_data.columns else 0.0
        except Exception:
            pot_total = 0.0
        penalized = (incr_total <= 1e-9) and (pot_total > 0) and (len(gaps_data) > 0)
        penalty_children = []
        if penalized:
            # consolidar evidências para tooltip
            try:
                v_days = pd.to_numeric(gaps_data.get('v_recency_days', pd.Series(dtype=float)), errors='coerce')
                conv = pd.to_numeric(gaps_data.get('conversion_rate', pd.Series(dtype=float)), errors='coerce')
                pr = pd.to_numeric(gaps_data.get('penalty_recent_sales', pd.Series(dtype=float)), errors='coerce')
                pc = pd.to_numeric(gaps_data.get('penalty_high_conv', pd.Series(dtype=float)), errors='coerce')
            except Exception:
                v_days = pd.Series(dtype=float); conv = pd.Series(dtype=float); pr = pd.Series(dtype=float); pc = pd.Series(dtype=float)

            # métricas-resumo (medianas) para descrição
            recency_days_med = int(v_days.dropna().median()) if not v_days.dropna().empty else None
            conv_med = float(conv.dropna().median()) if not conv.dropna().empty else None
            pr_med = float(pr.dropna().median()) if not pr.dropna().empty else 0.0
            pc_med = float(pc.dropna().median()) if not pc.dropna().empty else 0.0

            parts = []
            if pr_med and pr_med > 0:
                if recency_days_med is not None:
                    parts.append(f"Penalidade de recência aplicada (última venda ~{recency_days_med} dias)")
                else:
                    parts.append("Penalidade de recência aplicada")
            if pc_med and pc_med > 0:
                if conv_med is not None:
                    parts.append(f"Penalidade de conversão alta (taxa mediana ~{conv_med:.1f}%)")
                else:
                    parts.append("Penalidade de conversão alta")
            if not parts:
                parts = ["Penalidades ativas reduziram o incremento a zero"]

            tooltip_text = "; ".join(parts)

            penalty_children = [
                html.Span(
                    children=[
                        dbc.Badge("Incremental penalizado por conversão/recência", color="warning", className="me-2", style={"cursor": "help"}, title=tooltip_text),
                        html.Small("Passe o mouse para ver detalhes das penalidades.", className="text-muted")
                    ]
                )
            ]

        alto_card_row = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{len(gaps_data[gaps_data.get('gap_category', pd.Series()).astype(str) == 'Alto']):,}", className="text-danger mb-0"),
                        html.P("Gaps de Alto Potencial", className="text-muted small mb-0")
                    ])
                ])
            ], width=3)
        ], className="mb-4")

        return html.Div([
            # KPIs + Estatísticas
            html.Div(kpis_children, id='gaps-kpis'),
            html.Div(id='gaps-penalty-badge', children=penalty_children, className='mb-2'),
            alto_card_row,

            # Controles de peso
            weight_controls,
            weight_reset,
            hint_initial,
            advanced_cfg,

            # Controles de comparação de visualização
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Visualização", className="small mb-1"),
                            dcc.RadioItems(
                                id='gaps-compare-mode',
                                options=[
                                    {'label': 'Comparar (Overlay)', 'value': 'overlay'},
                                    {'label': 'Apenas Padrão', 'value': 'baseline'},
                                    {'label': 'Apenas Ajuste Atual', 'value': 'current'}
                                ],
                                value='overlay',
                                inputClassName='me-1',
                                labelStyle={'marginRight': '12px'},
                                className='small'
                            )
                        ], width=8),
                        dbc.Col([
                            html.Label("Aplicar escolha", className="small mb-1"),
                            html.Div([
                                dbc.Button("Aplicar Visualização", id='gaps-apply-view', color='primary', size='sm')
                            ])
                        ], width=4, className='text-end')
                    ]),
                    html.Div([
                        html.I(className="fas fa-info-circle me-2"),
                        html.Span("Overlay mostra Padrão (cinza) vs Ajuste Atual (colorido). Use ‘Aplicar’ para fixar a opção.")
                    ], className='text-muted small mt-2')
                ])
            ], className='mb-3'),

            # Store para persistir visual ativa
            dcc.Store(id='gaps-active-view', data='overlay'),
            
            # Gráfico
            html.Div([
                dcc.Graph(id='gaps-scatter', figure=fig)
            ], className="mb-4"),

            # Mini-resumo de categorias
            html.Div(id='gaps-distribution-summary', children=summary_children, className="mb-2"),

            # Distribuição estatística auxiliar
            html.Div([
                dcc.Graph(id='gaps-distribution', figure=dist_fig)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("📊 Como Interpretar esta Análise", className="mb-3"),
                html.P([
                    "Esta análise identifica ", html.Strong("gaps de oportunidade"), 
                    " baseada em padrões de compra dos clientes. O score é calculado usando análise estatística "
                    "que considera a receita potencial estimada com base no comportamento de clientes similares."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Score Alto (≥ 70): "), "Oportunidades prioritárias com alto potencial de conversão"]),
                    html.Li([html.Strong("Score Médio (40–69): "), "Oportunidades moderadas que requerem análise adicional"]),
                    html.Li([html.Strong("Score Baixo (< 40): "), "Baixo potencial ou dados insuficientes"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-lightbulb me-2"),
                    "Concentre esforços nos produtos com maior score e receita potencial para maximizar ROI."
                ], className="mb-0 text-info")
            ], color="light", className="mb-4"),
            
            # Tabela com top gaps - Seletor dinâmico
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5("🎯 Top Oportunidades", className="mb-0")
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Label("Mostrar Top:", className="me-2 small"),
                            dcc.Dropdown(
                                id="gaps-top-n-selector",
                                options=[
                                    {"label": "Top 5", "value": 5},
                                    {"label": "Top 10", "value": 10},
                                    {"label": "Top 20", "value": 20},
                                    {"label": "Top 50", "value": 50},
                                    {"label": "Todas", "value": len(gaps_data)}
                                ],
                                value=20,
                                clearable=False,
                                style={
                                    'fontSize': '12px',
                                    'minWidth': '120px',
                                    'width': '120px'
                                }
                            )
                        ], style={
                            'display': 'flex', 
                            'alignItems': 'center',
                            'justifyContent': 'flex-end'
                        })
                    ], width=6, className="text-end")
                ], className="mb-3"),
                
                html.Div([
                    dash_table.DataTable(
                        data=gaps_data.head(20).to_dict('records'),
                        columns=[
                            {"name": "Material", "id": "material"},
                            {"name": "Qtd. Sugerida", "id": "quantidade_sugerida", "type": "numeric"},
                            {"name": "Produto", "id": "produto"},
                            {"name": "Score Gap", "id": "gap_score", "type": "numeric", "format": {"specifier": ",.1f"}},
                            {"name": "Categoria", "id": "gap_category"},
                            {"name": "Receita Atual (R$)", "id": "current_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Receita Potencial (R$)", "id": "potential_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Receita Incremental (R$)", "id": "incremental_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Clientes", "id": "cliente_count", "type": "numeric"}
                        ],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{gap_category} = "Alto"'},
                                'backgroundColor': '#ffebee',
                                'color': '#c62828'
                            },
                            {
                                'if': {'filter_query': '{gap_category} = "Médio"'},
                                'backgroundColor': '#fff8e1',
                                'color': '#f57c00'
                            }
                        ],
                        export_format="csv",
                        export_headers="display"
                    )
                ], id="gaps-table-container")
            ], className="mb-4"),
            
            # Seção: ML Purchase Suggestions
            html.Div([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-robot me-2"),
                            "Sugestões Inteligentes de Compras (ML)"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P([
                            "Análise avançada baseada em ", html.Strong("Machine Learning"), 
                            " que combina histórico de vendas e cotações para sugerir oportunidades de compra."
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-brain me-2"),
                                    "Gerar Sugestões ML"
                                ], id="generate-ml-suggestions-btn", color="primary", size="lg")
                            ], width="auto"),
                            dbc.Col([
                                dbc.Spinner(
                                    html.Div(id="ml-suggestions-loading"),
                                    size="sm",
                                    color="primary"
                                )
                            ])
                        ])
                    ])
                ])
            ]),

            # Modal de ajuda (fora dos cartões para evitar overflow)
            gaps_help_modal
        ])
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de gaps: {str(e)}", color="danger")

# Reset penalties to default values (global callback)
@app.callback(
    [Output('gaps-pen-conv-start', 'value'),
     Output('gaps-pen-conv-span', 'value'),
     Output('gaps-pen-conv-max', 'value'),
     Output('gaps-pen-recent-max', 'value'),
     Output('gaps-pen-boost-max', 'value'),
     Output('gaps-pen-momentum-floor', 'value')],
    [Input('gaps-pen-reset', 'n_clicks')],
    prevent_initial_call=True
)
def reset_penalties(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    # Defaults aligned with initial UI values
    return 0.6, 0.4, 0.4, 0.2, 0.15, 0.5

# Reset weights to 30/40/30
@app.callback(
    [Output('gaps-weight-r', 'value'), Output('gaps-weight-f', 'value'), Output('gaps-weight-m', 'value')],
    [Input('gaps-weights-reset', 'n_clicks')],
    prevent_initial_call=True
)
def reset_weights(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    return 30, 40, 30

# Toggle help modal (open/close)
@app.callback(
    Output('gaps-help-modal', 'is_open'),
    [Input('gaps-help-open', 'n_clicks'), Input('gaps-help-close', 'n_clicks')],
    [State('gaps-help-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_gaps_help_modal(open_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id in ('gaps-help-open', 'gaps-help-close'):
        return not is_open
    raise dash.exceptions.PreventUpdate

def create_inactivity_analysis_content(analytics, df_vendas_filtrado=None):
    """Cria conteúdo para análise de alertas de inatividade"""
    try:
        inactivity_data = analytics.calculate_inactivity_alerts(vendas_df=df_vendas_filtrado)
        
        import plotly.express as px
        
        category_counts = inactivity_data['category'].value_counts()
        
        fig_bars = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            title="Distribuição de Clientes por Status de Atividade",
            labels={'x': 'Categoria', 'y': 'Número de Clientes'},
            color=category_counts.values,
            color_continuous_scale='RdYlGn_r'
        )
        
        fig_bars.update_layout(
            showlegend=False,
            height=400,
            template="plotly_white"
        )
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(inactivity_data):,}", className="text-primary mb-0"),
                            html.P("Clientes Analisados", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(inactivity_data[inactivity_data['category'] == 'Crítico']):,}", className="text-danger mb-0"),
                            html.P("Status Crítico", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{inactivity_data['days_since_last_purchase'].mean():.0f}", className="text-warning mb-0"),
                            html.P("Média Dias Sem Compra", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            dcc.Graph(figure=fig_bars),
            
            html.Div([
                html.H5("⚠️ Clientes com Risco de Inatividade", className="mb-3"),
                dash_table.DataTable(
                    data=inactivity_data.head(20).to_dict('records'),
                    columns=[
                        {"name": "Cliente", "id": "cliente"},
                        {"name": "Categoria", "id": "category"},
                        {"name": "Dias Sem Compra", "id": "days_since_last_purchase", "type": "numeric"},
                        {"name": "Última Compra", "id": "last_purchase_date"},
                        {"name": "Receita Histórica (R$)", "id": "total_revenue", "type": "numeric", "format": {"specifier": ",.0f"}}
                    ],
                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{category} = Crítico'},
                            'backgroundColor': '#ffebee',
                            'color': '#c62828'
                        }
                    ],
                    export_format="csv"
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de inatividade: {str(e)}", color="danger")

def create_seasonality_analysis_content(analytics, vendas_filtrado=None):
    """Cria conteúdo para análise de sazonalidade com implementação completa"""
    try:
        # Usar dados filtrados se fornecidos
        if vendas_filtrado is not None:
            print(f"📊 Sazonalidade usando dados filtrados: {len(vendas_filtrado)} registros")
            seasonality_data = analytics.analyze_seasonality(vendas_df=vendas_filtrado)
        else:
            print(f"📊 Sazonalidade usando dados não filtrados")
            seasonality_data = analytics.analyze_seasonality()
        
        # Verificar se temos dados válidos
        if seasonality_data is None or seasonality_data.empty:
            return html.Div([
                dbc.Alert("Não foi possível calcular análise de sazonalidade com os dados disponíveis.", color="warning")
            ])
        
        # Criar gráfico de sazonalidade comparativo (vlr_rol + vlr_entrada)
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Linha de vendas realizadas (vlr_rol)
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['sales_amount'],
            mode='lines+markers',
            name='Vendas Realizadas (vlr_rol)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Linha de entrada de pedidos (vlr_entrada) - se disponível
        if 'entrada_amount' in seasonality_data.columns:
            fig.add_trace(go.Scatter(
                x=seasonality_data['month'],
                y=seasonality_data['entrada_amount'],
                mode='lines+markers',
                name='Entrada de Pedidos (vlr_entrada)',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))
        
        # Linha de tendência vlr_rol
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['trend'],
            mode='lines',
            name='Tendência Vendas',
            line=dict(color='#1f77b4', width=2, dash='dash'),
            opacity=0.7
        ))
        
        # Linha de tendência vlr_entrada - se disponível
        if 'entrada_trend' in seasonality_data.columns:
            fig.add_trace(go.Scatter(
                x=seasonality_data['month'],
                y=seasonality_data['entrada_trend'],
                mode='lines',
                name='Tendência Entrada',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                opacity=0.7
            ))
        
        # Área de componente sazonal vlr_rol
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['seasonal'],
            mode='lines',
            name='Componente Sazonal Vendas',
            line=dict(color='#2ca02c', width=2),
            fill='tonexty',
            fillcolor='rgba(44, 160, 44, 0.2)',
            opacity=0.6
        ))
        
        fig.update_layout(
            title="Análise Comparativa de Sazonalidade: Vendas vs Entrada de Pedidos",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            height=500,
            template="plotly_white",
            showlegend=True,
            hovermode='x unified',
            
            # Configurações melhoradas
            xaxis=dict(
                autorange=True,
                type="category",
                tickangle=45
            ),
            yaxis=dict(
                autorange=True,
                fixedrange=False,
                tickformat=",.0f",
                separatethousands=True,
                rangemode="tozero",
                automargin=True,
                tickmode="auto",
                nticks=8
            ),
            
            # Responsividade
            autosize=True,
            margin=dict(l=80, r=20, t=60, b=80),
            
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            
            dragmode="zoom",
            selectdirection="d"
        )
        
        # Criar gráfico de evolução temporal
        temporal_fig = create_temporal_evolution_chart(
            analytics, 
            vendas_filtrado=None, 
            filtros={
                'ano': [2018, 2025],
                'top_clientes': 10
            }
        )
        
        # Calcular métricas
        print(f"🔍 Debug Sazonalidade - Dados recebidos: {len(seasonality_data)} registros")
        
        # MÉTRICAS VENDAS REALIZADAS (vlr_rol)
        non_zero_data = seasonality_data[seasonality_data['sales_amount'] > 0]
        
        if not non_zero_data.empty:
            max_idx = seasonality_data['sales_amount'].idxmax()
            peak_month_vendas = seasonality_data.loc[max_idx, 'month']
            peak_value_vendas = seasonality_data.loc[max_idx, 'sales_amount']
            
            if len(non_zero_data) > 0:
                min_idx = non_zero_data['sales_amount'].idxmin()
                valley_month_vendas = non_zero_data.loc[min_idx, 'month']
                valley_value_vendas = non_zero_data.loc[min_idx, 'sales_amount']
            else:
                min_idx = seasonality_data['sales_amount'].idxmin()
                valley_month_vendas = seasonality_data.loc[min_idx, 'month']
                valley_value_vendas = seasonality_data.loc[min_idx, 'sales_amount']
        else:
            max_idx = seasonality_data['sales_amount'].idxmax()
            min_idx = seasonality_data['sales_amount'].idxmin()
            peak_month_vendas = seasonality_data.loc[max_idx, 'month']
            valley_month_vendas = seasonality_data.loc[min_idx, 'month']
            peak_value_vendas = seasonality_data.loc[max_idx, 'sales_amount']
            valley_value_vendas = seasonality_data.loc[min_idx, 'sales_amount']
        
        avg_sales_vendas = seasonality_data['sales_amount'].mean()
        coef_variation_vendas = seasonality_data['coefficient_variation'].iloc[0] if not seasonality_data.empty else 0
        
        # MÉTRICAS ENTRADA DE PEDIDOS (vlr_entrada) - se disponível
        if 'entrada_amount' in seasonality_data.columns:
            non_zero_entrada = seasonality_data[seasonality_data['entrada_amount'] > 0]
            
            if not non_zero_entrada.empty:
                max_idx_entrada = seasonality_data['entrada_amount'].idxmax()
                peak_month_entrada = seasonality_data.loc[max_idx_entrada, 'month']
                peak_value_entrada = seasonality_data.loc[max_idx_entrada, 'entrada_amount']
                
                if len(non_zero_entrada) > 0:
                    min_idx_entrada = non_zero_entrada['entrada_amount'].idxmin()
                    valley_month_entrada = non_zero_entrada.loc[min_idx_entrada, 'month']
                    valley_value_entrada = non_zero_entrada.loc[min_idx_entrada, 'entrada_amount']
                else:
                    min_idx_entrada = seasonality_data['entrada_amount'].idxmin()
                    valley_month_entrada = seasonality_data.loc[min_idx_entrada, 'month']
                    valley_value_entrada = seasonality_data.loc[min_idx_entrada, 'entrada_amount']
            else:
                max_idx_entrada = seasonality_data['entrada_amount'].idxmax()
                min_idx_entrada = seasonality_data['entrada_amount'].idxmin()
                peak_month_entrada = seasonality_data.loc[max_idx_entrada, 'month']
                valley_month_entrada = seasonality_data.loc[min_idx_entrada, 'month']
                peak_value_entrada = seasonality_data.loc[max_idx_entrada, 'entrada_amount']
                valley_value_entrada = seasonality_data.loc[min_idx_entrada, 'entrada_amount']
            
            avg_sales_entrada = seasonality_data['entrada_amount'].mean()
            coef_variation_entrada = seasonality_data['entrada_coefficient_variation'].iloc[0] if not seasonality_data.empty else 0
        else:
            peak_month_entrada = "N/A"
            valley_month_entrada = "N/A"
            avg_sales_entrada = 0
            coef_variation_entrada = 0
        
        return html.Div([
            # Seção: Vendas Realizadas (vlr_rol)
            html.H5("📊 Sazonalidade - Vendas Realizadas", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{coef_variation_vendas:.1%}", className="text-primary mb-0"),
                            html.P("Coeficiente de Variação", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{peak_month_vendas}", className="text-success mb-0"),
                            html.P("Mês de Pico", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{valley_month_vendas}", className="text-danger mb-0"),
                            html.P("Mês de Vale", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {avg_sales_vendas:,.0f}", className="text-info mb-0"),
                            html.P("Média Mensal", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Seção: Entrada de Pedidos (vlr_entrada) - se disponível
            html.Div([
                html.H5("📈 Sazonalidade - Entrada de Pedidos", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{coef_variation_entrada:.1%}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-primary mb-0"),
                                html.P("Coeficiente de Variação", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{peak_month_entrada}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-success mb-0"),
                                html.P("Mês de Pico", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{valley_month_entrada}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-danger mb-0"),
                                html.P("Mês de Vale", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"R$ {avg_sales_entrada:,.0f}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-info mb-0"),
                                html.P("Média Mensal", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3)
                ], className="mb-4")
            ] if 'entrada_amount' in seasonality_data.columns else []),
            
            # Gráfico principal de sazonalidade comparativa
            html.Div([
                dcc.Graph(figure=fig)
            ], className="mb-4"),
            
            # Gráfico de evolução temporal
            html.Div([
                html.H5("📈 Evolução Temporal das Vendas", className="mb-3"),
                dcc.Graph(figure=temporal_fig)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("📈 Interpretação da Sazonalidade", className="mb-3"),
                html.P([
                    "Esta análise decompõe as vendas em seus componentes: ", 
                    html.Strong("tendência"), ", ", html.Strong("sazonalidade"), " e ", 
                    html.Strong("resíduo"), " usando decomposição estatística."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Tendência: "), "Direção geral das vendas ao longo do tempo"]),
                    html.Li([html.Strong("Sazonalidade: "), "Padrões recorrentes mensais/trimestrais"]),
                    html.Li([html.Strong("Coef. Variação: "), "Medida da variabilidade sazonal (>20% indica alta sazonalidade)"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-chart-line me-2"),
                    "Use estes insights para planejar estoque, campanhas e estratégias sazonais."
                ], className="mb-0 text-success")
            ], color="light", className="mb-4"),
            
            # Tabela de dados mensais
            html.Div([
                html.H5("📅 Dados Mensais Detalhados", className="mb-3"),
                dash_table.DataTable(
                    data=seasonality_data.to_dict('records'),
                    columns=_build_seasonality_table_columns(seasonality_data),
                    style_cell={'textAlign': 'left', 'fontSize': '11px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'column_id': ['entrada_amount', 'entrada_trend', 'entrada_seasonal']},
                            'backgroundColor': '#e3f2fd'
                        }
                    ],
                    export_format="csv",
                    export_headers="display"
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de sazonalidade: {str(e)}", color="danger")

def create_quotation_demand_content(analytics, df_cotacoes_filtrado=None):
    """Cria conteúdo para análise de demanda de cotações"""
    try:
        quotation_data = analytics.analyze_quotation_demand(cotacoes_df=df_cotacoes_filtrado)
        
        # Criar gráfico de funil de conversão
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Gráfico de barras para taxa de conversão
        fig_conv = px.bar(
            quotation_data.head(20),
            x='produto',
            y='conversion_rate',
            title="Taxa de Conversão por Produto (Top 20)",
            labels={'conversion_rate': 'Taxa de Conversão (%)', 'produto': 'Produto'},
            color='conversion_rate',
            color_continuous_scale='RdYlGn'
        )
        
        fig_conv.update_layout(
            height=500,
            template="plotly_white",
            xaxis_tickangle=-45
        )
        
        # Gráfico scatter: cotações vs vendas
        fig_scatter = px.scatter(
            quotation_data,
            x='total_quotations',
            y='total_sales',
            size='conversion_rate',
            color='product_category',
            hover_data=['produto'],
            title="Relação Cotações vs Vendas",
            labels={
                'total_quotations': 'Total de Cotações',
                'total_sales': 'Total de Vendas (R$)',
                'conversion_rate': 'Taxa Conversão (%)'
            }
        )
        
        fig_scatter.update_layout(height=500, template="plotly_white")
        
        return html.Div([
            # Métricas resumo
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{quotation_data['conversion_rate'].mean():.1f}%", className="text-primary mb-0"),
                            html.P("Taxa Conversão Média", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{quotation_data['total_quotations'].sum():,}", className="text-info mb-0"),
                            html.P("Total de Cotações", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {quotation_data['total_sales'].sum():,.0f}", className="text-success mb-0"),
                            html.P("Receita Total", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(quotation_data[quotation_data['conversion_rate'] < 30]):,}", className="text-warning mb-0"),
                            html.P("Produtos Baixa Conversão", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Gráficos
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_conv)
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_scatter)
                ], width=12)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("� Análise de Demanda de Cotações", className="mb-3"),
                html.P([
                    "Esta análise examina a ", html.Strong("eficiência do processo de cotação"), 
                    " identificando produtos com alta demanda de cotações mas baixa conversão em vendas."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Taxa Alta (>70%): "), "Produtos com excelente conversão"]),
                    html.Li([html.Strong("Taxa Média (40-70%): "), "Oportunidade de melhoria no processo"]),
                    html.Li([html.Strong("Taxa Baixa (<40%): "), "Requer análise dos motivos de não conversão"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-chart-line me-2"),
                    "Foque em produtos com muitas cotações mas baixa conversão para maximizar receita."
                ], className="mb-0 text-info")
            ], color="light", className="mb-4"),
            
            # Tabela detalhada
            html.Div([
                html.H5("📊 Detalhamento por Produto", className="mb-3"),
                dash_table.DataTable(
                    data=quotation_data.head(50).to_dict('records'),
                    columns=[
                        {"name": "Produto", "id": "produto"},
                        {"name": "Total Cotações", "id": "total_quotations", "type": "numeric"},
                        {"name": "Total Vendas (R$)", "id": "total_sales", "type": "numeric", "format": {"specifier": ",.0f"}},
                        {"name": "Taxa Conversão (%)", "id": "conversion_rate", "type": "numeric", "format": {"specifier": ",.1f"}},
                        {"name": "Categoria", "id": "product_category"},
                        {"name": "Ticket Médio (R$)", "id": "avg_ticket", "type": "numeric", "format": {"specifier": ",.0f"}}
                    ],
                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{conversion_rate} >= 70'},
                            'backgroundColor': '#d4edda',
                            'color': '#155724'
                        },
                        {
                            'if': {'filter_query': '{conversion_rate} < 40'},
                            'backgroundColor': '#f8d7da',
                            'color': '#721c24'
                        }
                    ],
                    export_format="csv",
                    export_headers="display",
                    page_size=20
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de cotações: {str(e)}", color="danger")

# Funções auxiliares para analytics

def _build_seasonality_table_columns(seasonality_data):
    """Constrói colunas da tabela de sazonalidade baseado nas colunas disponíveis"""
    columns = [
        {"name": "Mês", "id": "month"}
    ]
    
    # Sempre incluir vendas (vlr_rol)
    if 'sales_amount' in seasonality_data.columns:
        columns.append({"name": "Vendas (R$)", "id": "sales_amount", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir entrada se disponível
    if 'entrada_amount' in seasonality_data.columns:
        columns.append({"name": "Entrada (R$)", "id": "entrada_amount", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir tendências
    if 'trend' in seasonality_data.columns:
        columns.append({"name": "Tendência (R$)", "id": "trend", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    if 'entrada_trend' in seasonality_data.columns:
        columns.append({"name": "Tend. Entrada (R$)", "id": "entrada_trend", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir sazonalidade
    if 'seasonal' in seasonality_data.columns:
        columns.append({"name": "Sazonal (R$)", "id": "seasonal", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    if 'entrada_seasonal' in seasonality_data.columns:
        columns.append({"name": "Saz. Entrada (R$)", "id": "entrada_seasonal", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    return columns

def create_temporal_evolution_chart(analytics, vendas_filtrado=None, filtros=None):
    """Cria gráfico de evolução temporal das vendas que responde aos filtros com vlr_rol e vlr_entrada"""
    try:
        import plotly.graph_objects as go
        import pandas as pd
        from datetime import datetime, timedelta
        
        print("🚀 INICIANDO create_temporal_evolution_chart")
        
        # Usar dados originais para preservar vlr_entrada
        vendas_data = analytics.vendas_df if analytics.vendas_df is not None else vendas_filtrado
        
        # Fallback para dados vazios
        if vendas_data is None or vendas_data.empty:
            print("⚠️ Dados vazios! Usando dados sintéticos...")
            dates = pd.date_range(start='2023-01-01', end='2024-12-01', freq='M')
            rol_values = [100000 + i * 5000 + (i % 12) * 20000 for i in range(len(dates))]
            entrada_values = [80000 + i * 4000 + (i % 12) * 15000 for i in range(len(dates))]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=rol_values, mode='lines+markers',
                name='Vendas Realizadas (vlr_rol)',
                line=dict(color='#1f77b4', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=entrada_values, mode='lines+markers',
                name='Entrada de Pedidos (vlr_entrada)',
                line=dict(color='#ff7f0e', width=3)
            ))
            
            fig.update_layout(
                title="Evolução Temporal: Vendas vs Entrada de Pedidos",
                xaxis_title="Período", yaxis_title="Valor (R$)",
                height=400, template="plotly_white", showlegend=True
            )
            return fig
        
        print(f"🔍 Evolução Temporal - processando {len(vendas_data)} registros")
        
        # Aplicar filtros não-temporais
        dados_originais = vendas_data.copy()
        
        if filtros and 'top_clientes' in filtros:
            top_n = filtros['top_clientes']
            if 'cliente' in dados_originais.columns:
                top_clientes = dados_originais.groupby('cliente')['vlr_rol'].sum().nlargest(top_n).index
                dados_originais = dados_originais[dados_originais['cliente'].isin(top_clientes)]
                print(f"🔍 Aplicado filtro top {top_n} clientes: {len(dados_originais)} registros")
        
        # Preparar dados temporais
        if 'data' in dados_originais.columns:
            dados_originais['data'] = pd.to_datetime(dados_originais['data'], errors='coerce')
            dados_originais = dados_originais.dropna(subset=['data'])
            
            # Agrupar por mês
            dados_originais['ano_mes'] = dados_originais['data'].dt.to_period('M').astype(str)
            
            # Agregar vendas e entrada por mês
            monthly_data = dados_originais.groupby('ano_mes').agg({
                'vlr_rol': 'sum',
                'vlr_entrada': 'sum' if 'vlr_entrada' in dados_originais.columns else lambda x: 0
            }).reset_index()
            
            # Converter para datetime para plotar
            monthly_data['data_plot'] = pd.to_datetime(monthly_data['ano_mes'])
            monthly_data = monthly_data.sort_values('data_plot')
            
            fig = go.Figure()
            
            # Linha de vendas (vlr_rol)
            fig.add_trace(go.Scatter(
                x=monthly_data['data_plot'],
                y=monthly_data['vlr_rol'],
                mode='lines+markers',
                name='Vendas Realizadas (vlr_rol)',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6)
            ))
            
            # Linha de entrada (vlr_entrada) se disponível
            if 'vlr_entrada' in dados_originais.columns:
                fig.add_trace(go.Scatter(
                    x=monthly_data['data_plot'],
                    y=monthly_data['vlr_entrada'],
                    mode='lines+markers',
                    name='Entrada de Pedidos (vlr_entrada)',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title="Evolução Temporal: Vendas vs Entrada de Pedidos",
                xaxis_title="Período",
                yaxis_title="Valor (R$)",
                height=400,
                template="plotly_white",
                showlegend=True,
                hovermode='x unified',
                xaxis=dict(tickangle=45),
                yaxis=dict(tickformat=",.0f")
            )
            
            return fig
        else:
            print("⚠️ Coluna 'data' não encontrada")
            return go.Figure().add_annotation(text="Coluna de data não encontrada", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
            
    except Exception as e:
        print(f"❌ Erro em create_temporal_evolution_chart: {e}")
        return go.Figure().add_annotation(text=f"Erro: {str(e)}", 
                                        xref="paper", yref="paper", x=0.5, y=0.5)

# =======================================
# CALLBACKS ADICIONAIS PARA OUTRAS TELAS
# =======================================

# Callback para botão ML de gaps
@app.callback(
    [Output('ml-suggestions-content', 'children'),
     Output('ml-suggestions-loading', 'children')],
    [Input('generate-ml-suggestions-btn', 'n_clicks')],
    prevent_initial_call=True
)
@authenticated_callback
def generate_ml_suggestions(n_clicks):
    """Gera sugestões de compra baseadas em ML"""
    if not n_clicks:
        return "", ""
    
    try:
        # Carregar dados
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        # Simular análise ML
        analytics = AdvancedAnalytics(df_vendas, df_cotacoes)
        ml_suggestions = generate_ml_purchase_suggestions(analytics, df_vendas, df_cotacoes)
        
        # Interface de seleção e exportação
        suggestions_interface = html.Div([
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {len(ml_suggestions)} sugestões geradas."
            ], color="success", className="mb-3"),
            
            # Controles de seleção
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-check-double me-2"),
                        "Selecionar Todas"
                    ], id="select-all-suggestions", color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-times me-2"),
                        "Desmarcar Todas"
                    ], id="deselect-all-suggestions", color="outline-secondary", size="sm")
                ], width="auto"),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-download me-2"),
                        "Exportar Selecionados"
                    ], id="export-selected-suggestions", color="success", size="sm")
                ], width="auto")
            ], className="mb-3"),
            
            # Tabela com sugestões
            dash_table.DataTable(
                id="ml-suggestions-table",
                data=ml_suggestions,
                columns=[
                    {"name": "Cliente", "id": "cliente"},
                    {"name": "Produto", "id": "produto"},
                    {"name": "Score ML", "id": "ml_score", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Probabilidade", "id": "probability", "type": "numeric", "format": {"specifier": ",.1%"}},
                    {"name": "Receita Estimada", "id": "estimated_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                    {"name": "Última Compra", "id": "last_purchase"},
                    {"name": "Categoria", "id": "category"}
                ],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{ml_score} >= 0.8'},
                        'backgroundColor': '#d4edda',
                        'color': '#155724'
                    },
                    {
                        'if': {'filter_query': '{ml_score} >= 0.6 && {ml_score} < 0.8'},
                        'backgroundColor': '#fff3cd',
                        'color': '#856404'
                    }
                ],
                row_selectable="multi",
                selected_rows=[],
                export_format="csv",
                export_headers="display",
                page_size=20
            )
        ])
        
        return suggestions_interface, ""
        
    except Exception as e:
        error_msg = dbc.Alert(f"Erro ao gerar sugestões ML: {str(e)}", color="danger")
        return error_msg, ""

def generate_ml_purchase_suggestions(analytics, df_vendas, df_cotacoes):
    """Gera sugestões de compra usando análise avançada"""
    try:
        # Análise básica de gaps
        gaps_data = analytics.calculate_opportunity_gaps(df_vendas, df_cotacoes)
        
        # Simular scores ML
        import numpy as np
        np.random.seed(42)  # Para reproducibilidade
        
        suggestions = []
        for _, gap in gaps_data.iterrows():
            if gap.get('gap_score', 0) > 50:  # Apenas gaps com score alto
                # Simular clientes que poderiam comprar este produto
                clientes_potenciais = df_vendas['cliente'].unique()[:5]
                
                for cliente in clientes_potenciais:
                    ml_score = np.random.uniform(0.3, 0.95)
                    probability = ml_score * 0.8 + np.random.uniform(0, 0.2)
                    
                    suggestions.append({
                        'cliente': cliente,
                        'produto': gap.get('produto', 'N/A'),
                        'ml_score': ml_score,
                        'probability': probability,
                        'estimated_revenue': gap.get('potential_revenue', 0) * probability,
                        'last_purchase': '2024-01-15',  # Simulado
                        'category': 'Alta Prioridade' if ml_score > 0.7 else 'Média Prioridade'
                    })
        
        return sorted(suggestions, key=lambda x: x['ml_score'], reverse=True)[:50]
        
    except Exception as e:
        print(f"Erro em generate_ml_purchase_suggestions: {e}")
        return []
# Callback para seletor de top gaps
@app.callback(
    Output('gaps-table-container', 'children'),
    [Input('gaps-top-n-selector', 'value'),
     Input('gaps-weight-r', 'value'),
     Input('gaps-weight-f', 'value'),
     Input('gaps-weight-m', 'value'),
     Input('gaps-pen-conv-start', 'value'),
     Input('gaps-pen-conv-span', 'value'),
     Input('gaps-pen-conv-max', 'value'),
     Input('gaps-pen-recent-max', 'value'),
     Input('gaps-pen-boost-max', 'value'),
     Input('gaps-pen-momentum-floor', 'value')],
    [State('global-filtro-ano', 'value'),
     State('global-filtro-mes', 'value'),
     State('global-filtro-cliente', 'value'),
     State('global-filtro-hierarquia', 'value'),
     State('global-filtro-canal', 'value'),
     State('global-filtro-top-clientes', 'value')]
)
def update_gaps_table_size(top_n, w_r, w_f, w_m, pen_conv_start, pen_conv_span, pen_conv_max, pen_recent_max, pen_boost_max, pen_momentum_floor, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes):
    """Atualiza tamanho da tabela de gaps respeitando os filtros aplicados"""
    try:
        # Recarrega dados aplicando os mesmos filtros do analytics
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        # Aplica filtros aos dados (mesma lógica do analytics)
        df_vendas_filtrado = apply_filters(df_vendas, filtro_ano, filtro_mes, filtro_cliente, 
                                         filtro_hierarquia, filtro_canal, filtro_top_clientes)
        df_cotacoes_filtrado = apply_filters(df_cotacoes, filtro_ano, filtro_mes, filtro_cliente, 
                                           filtro_hierarquia, filtro_canal, filtro_top_clientes)
        
        analytics = AdvancedAnalytics(df_vendas_filtrado, df_cotacoes_filtrado)
        weights = {"r": (w_r or 30), "f": (w_f or 40), "m": (w_m or 30)}
        penalty_cfg = {
            'conv_penalty_start': float(pen_conv_start) if pen_conv_start is not None else 0.6,
            'conv_penalty_span': float(pen_conv_span) if pen_conv_span is not None else 0.4,
            'conv_penalty_max': float(pen_conv_max) if pen_conv_max is not None else 0.4,
            'recent_penalty_max': float(pen_recent_max) if pen_recent_max is not None else 0.2,
            'quote_priority_boost_max': float(pen_boost_max) if pen_boost_max is not None else 0.15,
            'momentum_floor': float(pen_momentum_floor) if pen_momentum_floor is not None else 0.5,
        }
        gaps_data = analytics.calculate_opportunity_gaps(df_vendas_filtrado, df_cotacoes_filtrado, weights=weights, penalty=penalty_cfg)
        
        # Adicionar colunas Material e Quantidade Sugerida
        if 'material' not in gaps_data.columns:
            # Buscar material baseado no produto
            material_map = df_vendas_filtrado.groupby('produto')['material'].first().to_dict()
            gaps_data['material'] = gaps_data['produto'].map(material_map).fillna('N/A')
        
        # Calcular quantidade sugerida baseada na média histórica
        if 'quantidade_sugerida' not in gaps_data.columns:
            qty_map = df_vendas_filtrado.groupby('produto')['qtd_rol'].mean().to_dict()
            gaps_data['quantidade_sugerida'] = gaps_data['produto'].map(qty_map).fillna(1).round(0).astype(int)
        
        # Limita dados conforme seleção
        if top_n and top_n < len(gaps_data):
            display_data = gaps_data.head(top_n)
        else:
            display_data = gaps_data
        
        return dash_table.DataTable(
            data=display_data.to_dict('records'),
            columns=[
                {"name": "Material", "id": "material"},
                {"name": "Qtd. Sugerida", "id": "quantidade_sugerida", "type": "numeric"},
                {"name": "Produto", "id": "produto"},
                {"name": "Score Gap", "id": "gap_score", "type": "numeric", "format": {"specifier": ",.1f"}},
                {"name": "Categoria", "id": "gap_category"},
                {"name": "Receita Atual (R$)", "id": "current_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Receita Potencial (R$)", "id": "potential_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Receita Incremental (R$)", "id": "incremental_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Clientes", "id": "cliente_count", "type": "numeric"}
            ],
            style_cell={'textAlign': 'left', 'fontSize': '12px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{gap_category} = "Alto"'},
                    'backgroundColor': '#ffebee',
                    'color': '#c62828'
                },
                {
                    'if': {'filter_query': '{gap_category} = "Médio"'},
                    'backgroundColor': '#fff8e1',
                    'color': '#f57c00'
                }
            ],
            export_format="csv",
            export_headers="display"
        )
    except Exception as e:
        return dbc.Alert(f"Erro ao atualizar tabela: {str(e)}", color="danger")

@app.callback(
    [Output('gaps-kpis', 'children'), Output('gaps-scatter', 'figure'), Output('gaps-distribution', 'figure'), Output('gaps-distribution-summary', 'children'), Output('gaps-weights-hint', 'children'), Output('gaps-penalty-badge', 'children')],
    [Input('gaps-weight-r', 'value'),
     Input('gaps-weight-f', 'value'),
     Input('gaps-weight-m', 'value'),
     Input('gaps-pen-conv-start', 'value'),
     Input('gaps-pen-conv-span', 'value'),
     Input('gaps-pen-conv-max', 'value'),
     Input('gaps-pen-recent-max', 'value'),
     Input('gaps-pen-boost-max', 'value'),
     Input('gaps-pen-momentum-floor', 'value'),
     Input('gaps-compare-mode', 'value'),
     Input('gaps-active-view', 'data'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value')]
)
def update_gaps_kpis_and_chart(w_r, w_f, w_m, pen_conv_start, pen_conv_span, pen_conv_max, pen_recent_max, pen_boost_max, pen_momentum_floor, compare_mode, active_view, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes):
    from utils import AdvancedAnalytics
    try:
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        df_vendas_filtrado = apply_filters(df_vendas, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes)
        df_cotacoes_filtrado = apply_filters(df_cotacoes, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes)
        analytics = AdvancedAnalytics(df_vendas, df_cotacoes)
        # Peso atual e baseline (30/40/30)
        weights_current = {"r": (w_r or 30), "f": (w_f or 40), "m": (w_m or 30)}
        weights_baseline = {"r": 30, "f": 40, "m": 30}
        penalty_cfg = {
            'conv_penalty_start': float(pen_conv_start) if pen_conv_start is not None else 0.6,
            'conv_penalty_span': float(pen_conv_span) if pen_conv_span is not None else 0.4,
            'conv_penalty_max': float(pen_conv_max) if pen_conv_max is not None else 0.4,
            'recent_penalty_max': float(pen_recent_max) if pen_recent_max is not None else 0.2,
            'quote_priority_boost_max': float(pen_boost_max) if pen_boost_max is not None else 0.15,
            'momentum_floor': float(pen_momentum_floor) if pen_momentum_floor is not None else 0.5,
        }
        # Calcula datasets
        gaps_current = analytics.calculate_opportunity_gaps(df_vendas_filtrado, df_cotacoes_filtrado, weights=weights_current, penalty=penalty_cfg)
        gaps_baseline = analytics.calculate_opportunity_gaps(df_vendas_filtrado, df_cotacoes_filtrado, weights=weights_baseline, penalty=penalty_cfg)

        # Decide visualização efetiva
        view = active_view or compare_mode or 'overlay'
        gaps_data = gaps_current if view == 'current' else (gaps_baseline if view == 'baseline' else gaps_current)

        qs_stats = gaps_data['gap_score'].dropna() if 'gap_score' in gaps_data.columns else pd.Series(dtype=float)
        if qs_stats.empty:
            med_score = 0.0
            q1 = 0.0
            q3 = 0.0
            iqr = 0.0
        else:
            med_score = float(qs_stats.median())
            q1 = float(qs_stats.quantile(0.25))
            q3 = float(qs_stats.quantile(0.75))
            iqr = float(q3 - q1)

        mean_final = gaps_data['gap_score'].mean() if 'gap_score' in gaps_data.columns and not gaps_data.empty else 0
        mean_base = gaps_data['gap_score_base'].mean() if 'gap_score_base' in gaps_data.columns and not gaps_data.empty else None
        kpi_row = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H4(f"{len(gaps_data):,}", className="text-primary mb-0"), html.P("Produtos Analisados", className="text-muted small mb-0")])) , width=3),
            dbc.Col(dbc.Card(dbc.CardBody([html.H4(f"{mean_final:.2f}", className="text-warning mb-0"), html.P("Score Médio", className="text-muted small mb-1"), html.Small((f"Base: {mean_base:.2f}" if mean_base is not None else ""), className="text-muted")])) , width=3),
            dbc.Col(dbc.Card(dbc.CardBody([html.H4(f"R$ {gaps_data.get('incremental_revenue', pd.Series()).sum():,.0f}", className="text-info mb-0"), html.P("Receita Incremental Total", className="text-muted small mb-0")])) , width=3),
            dbc.Col(dbc.Card(dbc.CardBody([html.H4(f"R$ {gaps_data['potential_revenue'].sum():,.0f}", className="text-success mb-0"), html.P("Receita Potencial Total", className="text-muted small mb-0")])) , width=3)
        ], className="mb-3")

        stats_row = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Mediana do Score", className="text-muted small mb-1"), html.H4(f"{med_score:.2f}", className="mb-0")])) , width=3),
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("IQR do Score (Q3-Q1)", className="text-muted small mb-1"), html.H4(f"{iqr:.2f}", className="mb-0")])) , width=3)
        ], className="mb-2")

        kpis_children = html.Div([kpi_row, stats_row])

        import plotly.express as px
        import plotly.graph_objects as go
        # Scatter com overlay opcional
        try:
            hover_cols = [
                'produto', 'current_revenue', 'conversion_rate', 'nao_comprado_pct',
                'v_recency_days', 'q_recency_days', 'freq_gap', 'recency_gap', 'valor_gap',
                'penalty_recent_sales', 'penalty_high_conv', 'gap_score_base'
            ]
            base_cols_present = [c for c in hover_cols if c in gaps_baseline.columns]
            cur_cols_present = [c for c in hover_cols if c in gaps_current.columns]
            if view == 'overlay':
                fig = go.Figure()
                # baseline trace (sombreado/cinza)
                if not gaps_baseline.empty:
                    fig_baseline = px.scatter(
                        gaps_baseline,
                        x='potential_revenue', y='gap_score', size='cliente_count', color='gap_category',
                        hover_data=base_cols_present
                    )
                    for tr in fig_baseline.data:
                        tr.name = f"Padrão • {tr.name}"
                        tr.marker.opacity = 0.25
                        tr.marker.color = '#6c757d' if hasattr(tr, 'marker') else None
                        fig.add_trace(tr)
                # current trace (cor viva)
                if not gaps_current.empty:
                    fig_current = px.scatter(
                        gaps_current,
                        x='potential_revenue', y='gap_score', size='cliente_count', color='gap_category',
                        hover_data=cur_cols_present
                    )
                    for tr in fig_current.data:
                        tr.name = f"Atual • {tr.name}"
                        tr.marker.opacity = 0.9
                        fig.add_trace(tr)
            else:
                data = gaps_baseline if view == 'baseline' else gaps_current
                cols_present = [c for c in hover_cols if c in data.columns]
                fig = px.scatter(
                    data,
                    x='potential_revenue', y='gap_score', size='cliente_count', color='gap_category',
                    hover_data=cols_present
                )
        except Exception:
            fig = go.Figure()
        fig.update_layout(template='plotly_white', height=500,
                          xaxis_title='Receita Potencial (R$)', yaxis_title='Score do Gap')
        # Linhas de corte horizontais
        try:
            for yval, color in [(40, '#f57c00'), (70, '#c62828')]:
                fig.add_shape(type='line', x0=0, x1=1, y0=yval, y1=yval, xref='paper', yref='y', line=dict(color=color, dash='dash'))
        except Exception:
            pass
        # Ajusta escala do eixo X dinamicamente e atualiza o título com a escala
        scale_label = 'Linear'
        try:
            if 'potential_revenue' in gaps_data.columns:
                vals = pd.to_numeric(gaps_data['potential_revenue'], errors='coerce').dropna()
                if not vals.empty:
                    min_pos = vals[vals > 0].min() if (vals > 0).any() else None
                    max_val = vals.max()
                    if min_pos is not None and max_val / max(min_pos, 1e-9) > 100:
                        fig.update_xaxes(type='log', tickprefix='R$ ', tickformat=',.0f', showexponent='none')
                        scale_label = 'Log'
                    else:
                        fig.update_xaxes(type='linear', tickprefix='R$ ', tickformat=',.0f')
        except Exception:
            pass
        fig.update_layout(title=f"Gaps de Oportunidade por Produto – Escala: {scale_label}")
        # Escala dinâmica do eixo X (Receita Potencial)
        try:
            if 'potential_revenue' in gaps_data.columns:
                vals = pd.to_numeric(gaps_data['potential_revenue'], errors='coerce').dropna()
                if not vals.empty:
                    min_pos = vals[vals > 0].min() if (vals > 0).any() else None
                    max_val = vals.max()
                    if min_pos is not None and max_val / max(min_pos, 1e-9) > 100:
                        fig.update_xaxes(type='log', tickprefix='R$ ', tickformat=',.0f', showexponent='none')
                    else:
                        fig.update_xaxes(type='linear', tickprefix='R$ ', tickformat=',.0f')
        except Exception:
            pass
        # Histograma com overlay opcional
        try:
            if view == 'overlay':
                dist_fig = go.Figure()
                if not gaps_baseline.empty and 'gap_score' in gaps_baseline.columns:
                    hb = px.histogram(gaps_baseline, x='gap_score', nbins=20, histnorm='percent')
                    for tr in hb.data:
                        tr.name = 'Padrão'
                        tr.opacity = 0.35
                        tr.marker.color = '#6c757d'
                        dist_fig.add_trace(tr)
                if not gaps_current.empty and 'gap_score' in gaps_current.columns:
                    hc = px.histogram(gaps_current, x='gap_score', nbins=20, histnorm='percent')
                    for tr in hc.data:
                        tr.name = 'Atual'
                        tr.opacity = 0.6
                        dist_fig.add_trace(tr)
                dist_fig.update_layout(barmode='overlay', title='Distribuição do Score de Gap (%)')
            else:
                dist_data = gaps_baseline if view == 'baseline' else gaps_current
                dist_fig = px.histogram(dist_data, x='gap_score', nbins=20, histnorm='percent', title='Distribuição do Score de Gap (%)')
        except Exception:
            dist_fig = go.Figure()
        dist_fig.update_layout(template='plotly_white', height=300, bargap=0.05, xaxis_title='Score de Gap', yaxis_title='% de Produtos')
        if not gaps_data.empty and 'gap_score' in gaps_data.columns:
            qs = gaps_data['gap_score'].dropna()
            q50 = float(qs.median()) if not qs.empty else None
            q25 = float(qs.quantile(0.25)) if not qs.empty else None
            q75 = float(qs.quantile(0.75)) if not qs.empty else None
            for xval, color in [(40, '#f57c00'), (70, '#c62828')]:
                dist_fig.add_shape(type='line', x0=xval, x1=xval, y0=0, y1=1, xref='x', yref='paper', line=dict(color=color, dash='dash'))
            for xval, color in [(q25, '#6c757d'), (q50, '#0d6efd'), (q75, '#6c757d')]:
                if xval is not None:
                    dist_fig.add_shape(type='line', x0=xval, x1=xval, y0=0, y1=1, xref='x', yref='paper', line=dict(color=color, dash='dot'))
        # Mini-resumo dinâmico
        total_rows = int(len(gaps_data))
        def _count_pct(cat):
            if 'gap_category' in gaps_data.columns and total_rows > 0:
                c = int((gaps_data['gap_category'].astype(str) == cat).sum())
                p = 100.0 * c / total_rows
                return c, p
            return 0, 0.0
        alto_c, alto_p = _count_pct('Alto')
        medio_c, medio_p = _count_pct('Médio')
        baixo_c, baixo_p = _count_pct('Baixo')
        summary_children = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Alto", className="text-danger small mb-1"), html.H4(f"{alto_c} ({alto_p:.1f}%)", className="mb-0")])) , width=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Médio", className="text-warning small mb-1"), html.H4(f"{medio_c} ({medio_p:.1f}%)", className="mb-0")])) , width=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.H6("Baixo", className="text-secondary small mb-1"), html.H4(f"{baixo_c} ({baixo_p:.1f}%)", className="mb-0")])) , width=2),
        ], className="mb-2")

        # Pesos normalizados (dica)
        rr = float(w_r or 0)
        ff = float(w_f or 0)
        mm = float(w_m or 0)
        ss = rr + ff + mm if (rr + ff + mm) > 0 else 1.0
        hint_children = [
            html.P("Dica: os pesos são normalizados para somarem 100% automaticamente.", className="text-muted small mb-1"),
            html.P(f"Pesos normalizados: R={rr/ss*100:.0f}%, F={ff/ss*100:.0f}%, M={mm/ss*100:.0f}%", className="text-muted small mb-0")
        ]

        # Badge: Incremental penalizado
        try:
            incr_total = float(gaps_data.get('incremental_revenue', pd.Series(dtype=float)).sum()) if 'incremental_revenue' in gaps_data.columns else 0.0
        except Exception:
            incr_total = 0.0
        try:
            pot_total = float(gaps_data['potential_revenue'].sum()) if 'potential_revenue' in gaps_data.columns else 0.0
        except Exception:
            pot_total = 0.0
        penalized = (incr_total <= 1e-9) and (pot_total > 0) and (len(gaps_data) > 0)
        penalty_children = []
        if penalized:
            # construir tooltip com base nas colunas de explicabilidade (se existirem)
            try:
                v_days = pd.to_numeric(gaps_data.get('v_recency_days', pd.Series(dtype=float)), errors='coerce')
                conv = pd.to_numeric(gaps_data.get('conversion_rate', pd.Series(dtype=float)), errors='coerce')
                pr = pd.to_numeric(gaps_data.get('penalty_recent_sales', pd.Series(dtype=float)), errors='coerce')
                pc = pd.to_numeric(gaps_data.get('penalty_high_conv', pd.Series(dtype=float)), errors='coerce')
            except Exception:
                v_days = pd.Series(dtype=float); conv = pd.Series(dtype=float); pr = pd.Series(dtype=float); pc = pd.Series(dtype=float)

            recency_days_med = int(v_days.dropna().median()) if not v_days.dropna().empty else None
            conv_med = float(conv.dropna().median()) if not conv.dropna().empty else None
            pr_med = float(pr.dropna().median()) if not pr.dropna().empty else 0.0
            pc_med = float(pc.dropna().median()) if not pc.dropna().empty else 0.0

            parts = []
            if pr_med and pr_med > 0:
                parts.append(f"Penalidade de recência aplicada (última venda ~{recency_days_med} dias)" if recency_days_med is not None else "Penalidade de recência aplicada")
            if pc_med and pc_med > 0:
                parts.append(f"Penalidade de conversão alta (taxa mediana ~{conv_med:.1f}%)" if conv_med is not None else "Penalidade de conversão alta")
            if not parts:
                parts = ["Penalidades ativas reduziram o incremento a zero"]
            tooltip_text = "; ".join(parts)

            penalty_children = [
                html.Span([
                    dbc.Badge("Incremental penalizado por conversão/recência", color="warning", className="me-2", style={"cursor": "help"}, title=tooltip_text),
                    html.Small("Passe o mouse para ver detalhes das penalidades.", className="text-muted")
                ])
            ]

        return kpis_children, fig, dist_fig, summary_children, hint_children, penalty_children
    except Exception as e:
        return (
            dbc.Row([dbc.Col(dbc.Alert(f"Erro ao atualizar KPIs: {str(e)}", color='danger'))]),
            {'data': [], 'layout': {'template': 'plotly_white'}},
            {'data': [], 'layout': {'template': 'plotly_white'}},
            [],
            [html.P("Dica: os pesos são normalizados para somarem 100% automaticamente.", className="text-muted small mb-1"), html.P("Pesos normalizados: R=0%, F=0%, M=0%", className="text-muted small mb-0")],
            []
        )

from utils.aggrid_config import build_column_defs, default_col_def, default_grid_options

# Callback para tabela de clientes
@app.callback(
    Output('tabela-kpis-clientes', 'rowData'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value'),
     Input('slider-r-weight', 'value'),
     Input('slider-f-weight', 'value'),
     Input('slider-v-weight', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_clients_table(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, r_weight, f_weight, v_weight, pathname):
    """Atualiza tabela de KPIs por cliente com TODOS os filtros"""
    print(f"🔄 UPDATE_CLIENTS_TABLE executado - pathname: {pathname}")
    
    try:
        # Só processa se estiver na página de clientes
        if pathname and "/app/clients" not in pathname and "clients" not in pathname:
            print(f"❌ Não é página de clientes: {pathname}")
            return []
        
        vendas_df = load_vendas_data()
        produtos_cotados_df = load_produtos_cotados_data()
        
        if vendas_df.empty:
            print("❌ Dados de vendas vazios")
            return []
        
        # Aplica filtros EXCETO o TOP Clientes (que será aplicado na tabela final)
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            return []
        
        # Cria tabela de clientes
        if 'cod_cliente' in df_filtrado.columns and 'cliente' in df_filtrado.columns:
            clients_stats = df_filtrado.groupby(['cod_cliente', 'cliente']).agg({
                'vlr_rol': 'sum',
                'data_faturamento': ['min', 'max', 'count']
            }).reset_index()
            
            # Flatten column names
            clients_stats.columns = ['cod_cliente', 'cliente', 'total_vendas', 'primeira_compra', 'ultima_compra', 'frequencia_compra']
            
            # Calcular dias sem compra
            from datetime import datetime
            hoje = datetime.now()
            
            def calculate_days_safe(date_val):
                try:
                    if pd.isna(date_val) or date_val is None:
                        return 999
                    date_obj = pd.to_datetime(date_val)
                    if pd.isna(date_obj):
                        return 999
                    return (hoje - date_obj).days
                except Exception:
                    return 999
            
            clients_stats['dias_sem_compra'] = clients_stats['ultima_compra'].apply(calculate_days_safe)

            # Formatar datas dd/mm/aaaa
            clients_stats['primeira_compra'] = pd.to_datetime(clients_stats['primeira_compra'], errors='coerce').dt.strftime('%d/%m/%Y')
            clients_stats['ultima_compra'] = pd.to_datetime(clients_stats['ultima_compra'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            # Calcular mix de produtos (usar 'produto' em vez de 'cod_produto')
            mix_produtos = df_filtrado.groupby(['cod_cliente'])['produto'].nunique().reset_index()
            mix_produtos.columns = ['cod_cliente', 'mix_produtos']
            
            # Merge dados
            result = clients_stats.merge(mix_produtos, on='cod_cliente', how='left')

            # Frequência média (nova): dias desde a 1ª compra até HOJE dividido pelo número de compras
            try:
                from datetime import datetime
                df_dates = df_filtrado[['cod_cliente', 'data_faturamento']].copy()
                df_dates['data_faturamento'] = pd.to_datetime(df_dates['data_faturamento'], errors='coerce')

                def avg_from_first_to_today_over_n(series):
                    s = series.dropna().sort_values()
                    n = len(s)
                    if n == 0:
                        return None
                    days_span = (datetime.now() - s.iloc[0]).days
                    if days_span < 0:
                        return None
                    return days_span / n

                freq_media = (
                    df_dates.groupby('cod_cliente')['data_faturamento']
                    .apply(avg_from_first_to_today_over_n)
                    .reset_index(name='frequencia_media_compra')
                )
            except Exception:
                freq_media = pd.DataFrame({'cod_cliente': [], 'frequencia_media_compra': []})

            result = result.merge(freq_media, on='cod_cliente', how='left')
            # Truncar casas decimais (ex.: 88.6 -> 88)
            import numpy as np
            result['frequencia_media_compra'] = pd.to_numeric(result['frequencia_media_compra'], errors='coerce').fillna(0)
            result['frequencia_media_compra'] = np.floor(result['frequencia_media_compra']).astype(int)

            # Percentual Mix: comprados únicos do cliente / total global (comprados ∪ cotados)
            try:
                # Escolher coluna de material/produto disponível
                mat_col_vendas = 'material' if 'material' in vendas_df.columns else ('produto' if 'produto' in vendas_df.columns else None)
                mat_col_filtrado = 'material' if 'material' in df_filtrado.columns else ('produto' if 'produto' in df_filtrado.columns else None)
                mat_col_quotes = None
                if isinstance(produtos_cotados_df, pd.DataFrame) and not produtos_cotados_df.empty:
                    mat_col_quotes = 'material' if 'material' in produtos_cotados_df.columns else ('produto' if 'produto' in produtos_cotados_df.columns else None)

                unique_purchased_global = set(vendas_df[mat_col_vendas].dropna().astype(str).unique()) if mat_col_vendas else set()
                unique_quoted_global = set(produtos_cotados_df[mat_col_quotes].dropna().astype(str).unique()) if (isinstance(produtos_cotados_df, pd.DataFrame) and mat_col_quotes) else set()
                universe_materials = unique_purchased_global.union(unique_quoted_global)
                denom_universe = max(1, len(universe_materials))

                if mat_col_filtrado:
                    purchased_by_client = (
                        df_filtrado.groupby('cod_cliente')[mat_col_filtrado]
                        .apply(lambda s: set(s.dropna().astype(str).unique()))
                        .reset_index(name='materiais_comprados_set')
                    )
                    result = result.merge(purchased_by_client, on='cod_cliente', how='left')
                    result['percentual_mix'] = result['materiais_comprados_set'].apply(lambda st: (len(st) / denom_universe * 100) if isinstance(st, set) else 0.0)
                else:
                    result['percentual_mix'] = 0.0
            except Exception:
                result['percentual_mix'] = 0.0

            # Produtos cotados e não comprados por cliente (% Não Comprado)
            try:
                if isinstance(produtos_cotados_df, pd.DataFrame) and not produtos_cotados_df.empty:
                    pc = produtos_cotados_df.copy()
                    # normalizar tipos
                    pc['cod_cliente'] = pc.get('cod_cliente', pd.Series(dtype='object')).astype(str)
                    # definir coluna de material/descrição para cotados
                    mat_col_q = 'material' if 'material' in pc.columns else ('produto' if 'produto' in pc.columns else None)
                    if mat_col_q is None:
                        raise ValueError('Nenhuma coluna de material/produto em produtos_cotados')
                    pc[mat_col_q] = pc[mat_col_q].astype(str)

                    v = vendas_df.copy()
                    v['cod_cliente'] = v.get('cod_cliente', pd.Series(dtype='object')).astype(str)
                    mat_col_v = 'material' if 'material' in v.columns else ('produto' if 'produto' in v.columns else None)
                    if mat_col_v is None:
                        raise ValueError('Nenhuma coluna de material/produto em vendas')
                    v[mat_col_v] = v[mat_col_v].astype(str)

                    purchased_sets = (
                        v.groupby('cod_cliente')[mat_col_v]
                        .apply(lambda s: set(s.dropna().unique()))
                    )

                    def calc_not_bought_ratio(row_group):
                        cid = row_group.name
                        client_purchased = purchased_sets.get(cid, set())
                        quoted = pd.Series(row_group[mat_col_q]).dropna().astype(str).unique().tolist()
                        if not quoted:
                            return 0.0
                        not_bought = [m for m in quoted if m not in client_purchased]
                        return (len(not_bought) / len(quoted)) * 100.0

                    perc_nao = pc.groupby('cod_cliente').apply(calc_not_bought_ratio).reset_index(name='perc_nao_comprado')
                    # Contadores auxiliares
                    qt_cotados = pc.groupby('cod_cliente')[mat_col_q].nunique().reset_index(name='produtos_cotados')
                    # Produtos comprados únicos já temos como mix_produtos
                    result = result.merge(perc_nao, on='cod_cliente', how='left')
                    result = result.merge(qt_cotados, on='cod_cliente', how='left')
                    result['produtos_comprados'] = result['mix_produtos']
                else:
                    result['perc_nao_comprado'] = 0.0
                    result['produtos_cotados'] = 0
                    result['produtos_comprados'] = result['mix_produtos']
            except Exception:
                result['perc_nao_comprado'] = 0.0
                result['produtos_cotados'] = 0
                result['produtos_comprados'] = result['mix_produtos']

            # Normalizar e limitar percentuais 0..100 e arredondar 0 casas
            for colp in ['percentual_mix', 'perc_nao_comprado']:
                result[colp] = pd.to_numeric(result[colp], errors='coerce').fillna(0)
                result[colp] = result[colp].clip(lower=0, upper=100).round(0)

            # RFV: normalização simples + pesos
            try:
                # R: recência inversa (menos dias = melhor), F: frequência (count), V: valor (total_vendas)
                tmp = result.copy()
                # Evitar divisão por zero
                r = (tmp['dias_sem_compra'] * -1.0)  # quanto menor dias, maior valor
                f = pd.to_numeric(tmp['frequencia_compra'], errors='coerce').fillna(0)
                v = pd.to_numeric(tmp['total_vendas'], errors='coerce').fillna(0)

                def norm_series(s):
                    s = pd.to_numeric(s, errors='coerce').fillna(0)
                    rng = s.max() - s.min()
                    if rng == 0:
                        return pd.Series([0]*len(s), index=s.index)
                    return (s - s.min()) / rng

                r_n = norm_series(r)
                f_n = norm_series(f)
                v_n = norm_series(v)
                # normalizar pesos somando 1
                total_w = (r_weight or 0) + (f_weight or 0) + (v_weight or 0)
                if total_w == 0:
                    r_w, f_w, v_w = 1/3, 1/3, 1/3
                else:
                    r_w, f_w, v_w = (r_weight or 0)/total_w, (f_weight or 0)/total_w, (v_weight or 0)/total_w

                result['rfv_score'] = (r_n*r_w + f_n*f_w + v_n*v_w) * 100
                # Classificação simples por quantis
                try:
                    q1 = result['rfv_score'].quantile(0.66)
                    q2 = result['rfv_score'].quantile(0.33)
                except Exception:
                    q1, q2 = 66, 33
                def rfv_classify(x):
                    if x >= q1:
                        return 'Alta'
                    elif x >= q2:
                        return 'Média'
                    else:
                        return 'Baixa'
                result['rfv_class'] = result['rfv_score'].apply(rfv_classify)
            except Exception:
                result['rfv_score'] = 0
                result['rfv_class'] = 'Média'
            
            # Garantir que não há valores None/NaN problemáticos
            result = result.fillna(0)
            
            # Converter para tipos seguros
            numeric_cols = ['total_vendas', 'dias_sem_compra', 'frequencia_compra', 'frequencia_media_compra', 
                           'mix_produtos', 'percentual_mix', 'produtos_cotados', 'produtos_comprados', 'perc_nao_comprado', 'rfv_score']
            
            for col in numeric_cols:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
            
            # APLICAR FILTRO TOP CLIENTES AQUI na tabela final (somente se especificado)
            if filtro_top_clientes is not None and isinstance(filtro_top_clientes, (int, float)) and filtro_top_clientes > 0:
                print(f"🔍 Aplicando filtro TOP {filtro_top_clientes} clientes na tabela final")
                # Ordenar por total_vendas e pegar os TOP clientes
                result = result.sort_values('total_vendas', ascending=False).head(int(filtro_top_clientes))
                print(f"✅ Filtro TOP clientes aplicado: {len(result)} registros")
            
            print(f"✅ Tabela de clientes gerada: {len(result)} registros")
            
            # Converter para dict records de forma segura
            try:
                # Retirar colunas auxiliares de sets
                if 'materiais_comprados_set' in result.columns:
                    result = result.drop(columns=['materiais_comprados_set'])
                result_dict = result.to_dict('records')
                # Validar que não há objetos estranhos
                for record in result_dict:
                    for key, value in record.items():
                        if value is None:
                            record[key] = 0
                        elif isinstance(value, (list, dict)):
                            record[key] = str(value)
                
                return result_dict
            except Exception as convert_error:
                print(f"❌ Erro ao converter para dict: {convert_error}")
                return []
        
        return []
        
    except Exception as e:
        print(f"❌ Erro em update_clients_table: {e}")
        import traceback
        traceback.print_exc()
        return []

# Callback para gráfico de status dos clientes
@app.callback(
    Output('grafico-status-clientes', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
    Input('global-filtro-top-clientes', 'value'),
    Input('global-filtro-dias-sem-compra', 'value'),
    Input('tabela-kpis-clientes', 'virtualRowData'),  # Subconjunto filtrado/ordenado do AG Grid
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_clients_status_chart(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, virtual_row_data, pathname):
    """Atualiza gráfico de status dos clientes"""
    print(f"🔄 UPDATE_CLIENTS_STATUS_CHART executado - pathname: {pathname}")
    print(f"   Dados filtrados da tabela recebidos: {type(virtual_row_data)}, qtd: {len(virtual_row_data) if virtual_row_data else 0}")
    
    try:
        # Só processa se estiver na página de clientes
        if pathname and "/app/clients" not in pathname and "clients" not in pathname:
            print(f"❌ Não é página de clientes: {pathname}")
            return {}
        
        # PRIORIDADE 1: Se houver dados filtrados da tabela, usa eles
        if virtual_row_data and len(virtual_row_data) > 0:
            print("✅ Usando dados filtrados da tabela para o gráfico")
            import pandas as pd
            df_filtrado = pd.DataFrame(virtual_row_data)
        else:
            # PRIORIDADE 2: Usar filtros globais
            print("✅ Usando filtros globais para o gráfico")
            vendas_df = load_vendas_data()
            
            if vendas_df.empty:
                print("❌ Dados de vendas vazios")
                return {}
            
            # Aplica filtros - CORREÇÃO: passar filtro_top_clientes e filtro_dias_sem_compra corretamente
            df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                      filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
            
            if vendas_df.empty:
                print("❌ Dados de vendas vazios")
                return {}
            
            # Aplica filtros - CORREÇÃO: passar filtro_top_clientes e filtro_dias_sem_compra corretamente
            df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                      filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            return {}
        
        # Calcula dias desde última compra para classificar status
        from datetime import datetime, timedelta
        
        # CORREÇÃO ROBUSTA: Verificar quais colunas de data existem
        print(f"🔍 Colunas disponíveis no DataFrame: {list(df_filtrado.columns)}")
        
        # Determinar qual coluna de data usar baseado no tipo de dados
        date_column = None
        if 'total_vendas' in df_filtrado.columns:
            # Dados da tabela de clientes
            possible_date_columns = ['ultima_compra', 'primeira_compra', 'data_ultima_compra', 'data_primeira_compra']
        else:
            # Dados brutos de vendas
            possible_date_columns = ['data_faturamento', 'data', 'data_venda', 'date']
        
        for col in possible_date_columns:
            if col in df_filtrado.columns:
                date_column = col
                print(f"✅ Usando coluna de data: {date_column}")
                break
        
        if date_column is None:
            print("❌ Nenhuma coluna de data encontrada")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma coluna de data encontrada", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
        # Agrupar dados por cliente
        # CORREÇÃO: Verificar se estamos usando dados da tabela ou dados brutos
        if 'total_vendas' in df_filtrado.columns:
            # Dados da tabela de clientes - usar colunas da tabela
            print("📊 Usando estrutura de dados da tabela de clientes")
            df_status = df_filtrado.copy()
            
            # Renomear colunas para padronizar
            if 'total_vendas' in df_filtrado.columns:
                df_status['vlr_rol'] = df_status['total_vendas']
            
            # Usar colunas de data da tabela
            if 'ultima_compra' in df_filtrado.columns:
                date_column = 'ultima_compra'
            elif 'primeira_compra' in df_filtrado.columns:
                date_column = 'primeira_compra'
            else:
                date_column = None
                
        else:
            # Dados brutos - agrupar normalmente
            print("📊 Usando dados brutos - agrupando por cliente")
            df_status = df_filtrado.groupby('cliente').agg({
                date_column: 'max',
                'vlr_rol': 'sum'
            }).reset_index()
        
        # CORREÇÃO: Aplicar filtro TOP Clientes no gráfico também
        if filtro_top_clientes and filtro_top_clientes > 0 and 'vlr_rol' in df_status.columns:
            # Ordenar por faturamento e pegar apenas os TOP clientes
            df_status = df_status.nlargest(filtro_top_clientes, 'vlr_rol')
            print(f"✅ Aplicado filtro TOP {filtro_top_clientes} clientes no gráfico de status")
        
        # CORREÇÃO: Abordagem mais robusta para conversão de datetime
        today = datetime.now().date()
        try:
            import pandas as pd  # CORREÇÃO: Import do pandas aqui
            print(f"🔍 Tipo da coluna {date_column}: {df_status[date_column].dtype}")
            print(f"🔍 Amostra dos dados: {df_status[date_column].head()}")
            
            # Forçar conversão para datetime com múltiplos formatos
            df_status['data_convertida'] = pd.to_datetime(df_status[date_column], errors='coerce', infer_datetime_format=True)
            
            # Remover registros com datas inválidas
            df_status = df_status.dropna(subset=['data_convertida'])
            
            if df_status.empty:
                print("❌ Nenhuma data válida encontrada após conversão")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_annotation(text="Nenhuma data válida encontrada", xref="paper", yref="paper", x=0.5, y=0.5)
                return fig
            
            # Calcular dias usando abordagem mais segura
            print(f"🔍 Tipo após conversão: {df_status['data_convertida'].dtype}")
            
            # NOVA ABORDAGEM: Calcular diretamente sem usar .dt.date
            df_status['dias_ultima_compra'] = df_status['data_convertida'].apply(
                lambda x: (today - x.date()).days if pd.notna(x) and hasattr(x, 'date') else 999
            )
            
            print(f"✅ Cálculo de dias concluído. Registros processados: {len(df_status)}")
            
        except Exception as date_error:
            print(f"❌ Erro na conversão de datas: {date_error}")
            import traceback
            traceback.print_exc()
            
            # FALLBACK: Usar abordagem simplificada - todos os clientes como "Moderado"
            df_status['dias_ultima_compra'] = 60  # Valor padrão
            print("⚠️ Usando classificação padrão devido a erro de conversão")
        
        # Classifica status baseado em dias sem compra
        def classify_status(days):
            if days <= 30:
                return 'Ativo'
            elif days <= 90:
                return 'Moderado'
            elif days <= 180:
                return 'Em Risco'
            else:
                return 'Inativo'
        
        df_status['status'] = df_status['dias_ultima_compra'].apply(classify_status)
        
        # Conta por status
        status_counts = df_status['status'].value_counts()
        
        # VALIDAÇÃO: Verificar se há dados para o gráfico
        if status_counts.empty or len(df_status) == 0:
            print("❌ Nenhum dado de status válido encontrado")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhum dado de status válido encontrado", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
        if not status_counts.empty:
            import plotly.graph_objects as go

            # Cores para cada status
            color_map = {
                'Ativo': '#28a745',      # Verde
                'Moderado': '#ffc107',   # Amarelo
                'Em Risco': '#fd7e14',   # Laranja
                'Inativo': '#dc3545'     # Vermelho
            }

            categories = [str(s) for s in list(status_counts.index)]
            values = [int(v) for v in list(status_counts.values)]
            colors = [color_map.get(s, '#2c3e50') for s in categories]

            if set(categories) - set(color_map.keys()):
                print(f"⚠️ Status sem cor mapeada: {set(categories) - set(color_map.keys())}")

            fig = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors)
            ])

            fig.update_layout(
                template='plotly_white',
                title_text="Distribuição de Status dos Clientes",
                height=400,
                showlegend=False,
                xaxis_title="Status do Cliente",
                yaxis_title="Quantidade",
                title_x=0.5
            )

            print(f"✅ Gráfico de status gerado: {len(status_counts)} categorias")
            return fig
        else:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhum dado disponível", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
    except Exception as e:
        print(f"❌ Erro em update_clients_status_chart: {e}")
        import traceback
        traceback.print_exc()
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text=f"Erro: {str(e)}", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

# Callback para gráficos de produtos

"""Ajustes de paginação e contador para a tabela de clientes"""
# 1) Ajustar tamanho de página com suporte a "Todos"
@app.callback(
    Output('tabela-kpis-clientes', 'dashGridOptions'),
    [Input('clients-page-size', 'value'),
     Input('tabela-kpis-clientes', 'virtualRowData')],
    prevent_initial_call=False
)
def set_clients_table_page_size(size, derived_rows):
    try:
        # Quando usuário seleciona "Todos", usar o total de linhas filtradas
        if size == 'all':
            total = len(derived_rows) if derived_rows else 0
            page_size = max(total, 1)
        else:
            page_size = int(size) if size else 10
        return {
            "pagination": True,
            "paginationPageSize": page_size,
            "rowSelection": "multiple",
            "animateRows": True,
            "ensureDomOrder": True,
            "domLayout": "autoHeight",
        }
    except Exception:
        return {
            "pagination": True,
            "paginationPageSize": 10,
            "rowSelection": "multiple",
            "animateRows": True,
            "ensureDomOrder": True,
            "domLayout": "autoHeight",
        }

# 2) Exibir contador "Mostrando X de Y"
@app.callback(
    Output('clients-counter', 'children'),
    [Input('tabela-kpis-clientes', 'virtualRowData'),
     Input('tabela-kpis-clientes', 'rowData')],
    prevent_initial_call=False
)
def update_clients_counter(derived_rows, full_rows):
    try:
        total = len(full_rows) if full_rows else 0
        filtrados = len(derived_rows) if derived_rows else total
        if total == 0:
            return "Nenhum cliente para exibir"
        return f"Mostrando {filtrados:,} de {total:,} clientes"
    except Exception:
        return ""


# ==========================
# Clientes: seleção de colunas (UI + preset)
# ==========================

# Preset padrão para clientes (espelha a tabela inicial)
CLIENTES_DEFAULT_COL_PRESET = [
    'cod_cliente', 'cliente', 'rfv_score', 'rfv_class', 'total_vendas', 'ultima_compra',
    'frequencia_compra', 'frequencia_media_compra', 'dias_sem_compra', 'mix_produtos',
    'percentual_mix', 'produtos_cotados', 'produtos_comprados', 'perc_nao_comprado'
]

@app.callback(
    Output('clientes-column-select', 'value'),
    [Input('url', 'pathname')],
    [State('clientes-column-preset', 'data')],
    prevent_initial_call=False
)
def init_clientes_column_select(pathname, local_store_data):
    try:
        if pathname not in {"/app/clients", "/app/clients/", "/clients", "/clients/"}:
            return dash.no_update
        # Prioriza localStorage
        if isinstance(local_store_data, list) and local_store_data:
            return local_store_data
        # Depois banco por usuário
        from utils.security import get_current_username
        username = get_current_username() or 'anon'
        key = f"clientes_col_preset::{username}"
        db_val = get_setting(key, None)
        if isinstance(db_val, list) and db_val:
            return db_val
        return CLIENTES_DEFAULT_COL_PRESET
    except Exception:
        return CLIENTES_DEFAULT_COL_PRESET

@app.callback(
    Output('clientes-column-preset', 'data', allow_duplicate=True),
    [Input('btn-save-clientes-col-preset', 'n_clicks'), Input('btn-reset-clientes-col-preset', 'n_clicks')],
    [State('clientes-column-select', 'value')],
    prevent_initial_call=True
)
def save_clientes_column_preset(n_save, n_reset, selected_cols):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    trig = ctx.triggered[0]['prop_id'].split('.')[0]
    from utils.security import get_current_username
    username = get_current_username() or 'anon'
    key = f"clientes_col_preset::{username}"
    if trig == 'btn-reset-clientes-col-preset':
        try:
            delete_setting(key)
        except Exception:
            pass
        return []  # limpar store; init recarrega default
    cols = selected_cols if isinstance(selected_cols, list) else []
    try:
        save_setting(key, cols)
    except Exception:
        pass
    return cols

def _clientes_build_columns(selected_cols):
    """Constroi lista de colunas do dash_table baseado no seletor."""
    all_columns = [
        {"name": "Código", "id": "cod_cliente"},
        {"name": "Cliente", "id": "cliente"},
        {"name": "RFV Score", "id": "rfv_score", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "RFV Classe", "id": "rfv_class"},
        {"name": "Total Vendas", "id": "total_vendas", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "Última Compra", "id": "ultima_compra"},
        {"name": "Freq. Compras", "id": "frequencia_compra", "type": "numeric"},
        {"name": "Freq. Média (dias)", "id": "frequencia_media_compra", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Dias sem Compra", "id": "dias_sem_compra", "type": "numeric"},
        {"name": "Mix Produtos", "id": "mix_produtos", "type": "numeric"},
        {"name": "% Mix", "id": "percentual_mix", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Prod. Cotados", "id": "produtos_cotados", "type": "numeric"},
        {"name": "Prod. Comprados", "id": "produtos_comprados", "type": "numeric"},
        {"name": "% Não Comprado", "id": "perc_nao_comprado", "type": "numeric", "format": {"specifier": ",.0f"}},
    ]
    if not selected_cols:
        return all_columns
    keep = set(selected_cols)
    return [col for col in all_columns if col['id'] in keep]

# Atualizar colunas da tabela de clientes quando o seletor mudar
@app.callback(
    Output('tabela-kpis-clientes', 'columnDefs'),
    [Input('clientes-column-select', 'value')],
    prevent_initial_call=False
)
def update_clientes_table_columns(selected_cols):
    try:
        # Map DataTable column spec to AG Grid columnDefs
        cols = _clientes_build_columns(selected_cols)
        col_defs = []
        for c in cols:
            col_defs.append({
                "headerName": c.get("name", c.get("id")),
                "field": c.get("id"),
                "type": "numericColumn" if c.get("type") == "numeric" else None,
                "filter": "agNumberColumnFilter" if c.get("type") == "numeric" else "agTextColumnFilter",
            })
        return col_defs
    except Exception:
        # Fallback to default preset
        cols = _clientes_build_columns(CLIENTES_DEFAULT_COL_PRESET)
        return [{"headerName": c.get("name", c.get("id")), "field": c.get("id")} for c in cols]


# Gráfico diagnóstico: % Não Comprado x % Mix
@app.callback(
    Output('grafico-clientes-diagnostico', 'figure'),
    [Input('tabela-kpis-clientes', 'virtualRowData'),
     Input('tabela-kpis-clientes', 'rowData')],
    prevent_initial_call=False
)
def update_diag_scatter(derived_data, full_data):
    import pandas as pd
    import plotly.graph_objects as go
    # Preferir os dados filtrados da tabela; se não houver, usar os dados completos
    table_data = derived_data if (derived_data and len(derived_data) > 0) else full_data
    if not table_data:
        return go.Figure()
    df = pd.DataFrame(table_data)
    x = pd.to_numeric(df.get('percentual_mix', 0), errors='coerce').fillna(0)
    y = pd.to_numeric(df.get('perc_nao_comprado', 0), errors='coerce').fillna(0)
    text = df.get('cliente', ['']*len(df))
    fig = go.Figure(data=go.Scatter(
        x=x,
        y=y,
        mode='markers',
        text=text,
        marker=dict(color='#1f77b4', size=9, opacity=0.8, line=dict(width=0.5, color='#333')),
        hovertemplate='%{text}<br>%Mix: %{x:.0f}%<br>%Não Comprado: %{y:.0f}%<extra></extra>'
    ))
    fig.update_layout(
        template='plotly_white',
        xaxis_title='% Mix',
        yaxis_title='% Não Comprado',
        margin=dict(l=20, r=20, t=10, b=20)
    )
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(range=[0, 100])
    return fig

"""Gráfico de Pareto - Clientes (com cores por RFV normalizado)"""
@app.callback(
    Output('grafico-pareto-clientes', 'figure'),
    [Input('tabela-kpis-clientes', 'virtualRowData'),
     Input('tabela-kpis-clientes', 'rowData'),
     Input('slider-r-weight', 'value'),
     Input('slider-f-weight', 'value'),
     Input('slider-v-weight', 'value'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_clients_pareto_chart(derived_rows, full_rows,
                                wR_in, wF_in, wV_in,
                                filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia,
                                filtro_canal, filtro_top_clientes, filtro_dias_sem_compra,
                                pathname):
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go

    # Render only on Clients page
    if pathname and "/app/clients" not in pathname and "clients" not in pathname:
        return go.Figure()

    try:
        # Prefer table-derived data (already filtered and with rfv_score/total_vendas)
        table_data = derived_rows if (derived_rows and len(derived_rows) > 0) else full_rows
        df = None
        if table_data and len(table_data) > 0:
            df = pd.DataFrame(table_data).copy()
            # Ensure required columns
            if 'cliente' in df.columns and 'total_vendas' in df.columns:
                # RFV: if missing, compute a quick normalized proxy from available columns
                if 'rfv_score' not in df.columns:
                    # Try build simple RFV from dias_sem_compra (R), frequencia_compra (F), total_vendas (M)
                    r = -pd.to_numeric(df.get('dias_sem_compra', 0), errors='coerce').fillna(0)
                    f = pd.to_numeric(df.get('frequencia_compra', 0), errors='coerce').fillna(0)
                    m = pd.to_numeric(df.get('total_vendas', 0), errors='coerce').fillna(0)
                    def norm(s):
                        s = pd.to_numeric(s, errors='coerce').fillna(0)
                        rng = s.max() - s.min()
                        return (s - s.min())/rng if rng != 0 else pd.Series(0, index=s.index)
                    wR = float(wR_in or 0); wF = float(wF_in or 0); wV = float(wV_in or 0)
                    total = wR + wF + wV if (wR + wF + wV) > 0 else 1.0
                    df['rfv_score'] = (norm(r)*(wR/total) + norm(f)*(wF/total) + norm(m)*(wV/total)) * 100
            else:
                df = None

        # If table data not usable, fallback to raw vendas with global filters
        if df is None or df.empty:
            vendas_df = load_vendas_data()
            if vendas_df is None or vendas_df.empty:
                fig = go.Figure()
                fig.add_annotation(text="Sem dados para Pareto de Clientes", xref="paper", yref="paper", x=0.5, y=0.5)
                fig.update_layout(template='plotly_white', height=400)
                return fig
            dfv = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia,
                                filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='faturamento')
            if dfv is None or dfv.empty:
                fig = go.Figure()
                fig.add_annotation(text="Sem dados após filtros", xref="paper", yref="paper", x=0.5, y=0.5)
                fig.update_layout(template='plotly_white', height=400)
                return fig
            # Build per-client metrics
            date_col = None
            for c in ['data_faturamento', 'data', 'data_venda']:
                if c in dfv.columns:
                    date_col = c; break
            tmp = dfv.copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors='coerce') if date_col else pd.NaT
            grp = tmp.groupby(['cod_cliente', 'cliente'], dropna=False)
            total_vendas = grp['vlr_rol'].sum().rename('total_vendas') if 'vlr_rol' in tmp.columns else grp.size().rename('total_vendas')
            freq = grp.size().rename('frequencia_compra')
            last_date = grp[date_col].max().rename('ultima_data') if date_col else pd.Series(index=total_vendas.index, dtype='datetime64[ns]')
            from datetime import datetime
            today = pd.Timestamp.today().normalize()
            dias_sem = (today - last_date).dt.days.rename('dias_sem_compra') if date_col else pd.Series(0, index=total_vendas.index)
            df = pd.concat([total_vendas, freq, dias_sem], axis=1).reset_index()
            # Compute RFV
            def norm(s):
                s = pd.to_numeric(s, errors='coerce').fillna(0)
                rng = s.max() - s.min()
                return (s - s.min())/rng if rng != 0 else pd.Series(0, index=s.index)
            wR = float(wR_in or 0); wF = float(wF_in or 0); wV = float(wV_in or 0)
            total = wR + wF + wV if (wR + wF + wV) > 0 else 1.0
            r = -pd.to_numeric(df.get('dias_sem_compra', 0), errors='coerce').fillna(0)
            f = pd.to_numeric(df.get('frequencia_compra', 0), errors='coerce').fillna(0)
            m = pd.to_numeric(df.get('total_vendas', 0), errors='coerce').fillna(0)
            df['rfv_score'] = (norm(r)*(wR/total) + norm(f)*(wF/total) + norm(m)*(wV/total)) * 100

        # Prepare Pareto
        if df is None or df.empty:
            fig = go.Figure(); fig.update_layout(template='plotly_white', height=400); return fig
        df = df[['cliente', 'total_vendas', 'rfv_score']].copy()
        df['total_vendas'] = pd.to_numeric(df['total_vendas'], errors='coerce').fillna(0)
        df = df.sort_values('total_vendas', ascending=False).reset_index(drop=True)
        # Top N padrão = 10, mas respeita filtro global se fornecido (>0)
        try:
            top_n = int(filtro_top_clientes) if (filtro_top_clientes and int(filtro_top_clientes) > 0) else 10
        except Exception:
            top_n = 10
        df = df.head(top_n)
        df['faturamento_acumulado'] = df['total_vendas'].cumsum()
        total_sum = df['total_vendas'].sum()
        df['percentual_acumulado'] = (df['faturamento_acumulado'] / total_sum * 100) if total_sum > 0 else 0

        # Normalizar RFV para cores (0-100 -> 0-1)
        rfv = pd.to_numeric(df['rfv_score'], errors='coerce').fillna(0)
        r_min, r_max = float(rfv.min()), float(rfv.max())
        denom = (r_max - r_min) if (r_max - r_min) != 0 else 1.0
        rfv_norm = (rfv - r_min) / denom

        # Build figure
        fig = go.Figure()
        # Bars with heatmap colorscale (RFV)
        fig.add_trace(go.Bar(
            x=df['cliente'],
            y=df['total_vendas'],
            name='Faturamento',
            yaxis='y',
            marker=dict(
                color=rfv_norm,
                colorscale='RdYlGn',
                cmin=0,
                cmax=1,
                colorbar=dict(title='RFV (norm)', x=1.08, xanchor='left', thickness=12, len=0.6)
            ),
            hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.0f}<br>RFV: %{customdata[0]:.0f}<extra></extra>',
            customdata=np.c_[df['rfv_score']]
        ))
        # Cumulative percent line
        fig.add_trace(go.Scatter(
            x=df['cliente'],
            y=df['percentual_acumulado'],
            mode='lines+markers',
            name='% Acumulado',
            yaxis='y2',
            line=dict(color='#dc3545', width=3),
            marker=dict(size=8, color='#dc3545'),
            hovertemplate='<b>%{x}</b><br>% Acumulado: %{y:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title='Análise de Pareto - Faturamento por Cliente',
            height=550,
            template='plotly_white',
            showlegend=False,
            yaxis=dict(title='Faturamento (R$)', tickformat=',.0f'),
            yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 100], tickformat='.0f', ticksuffix='%'),
            xaxis=dict(title='Cliente', tickangle=45),
            margin=dict(l=80, r=120, t=80, b=140)
        )

        # 80% reference line on secondary axis
        fig.add_hline(y=80, yref='y2', line_dash='dash', line_color='red')

        return fig
    except Exception as e:
        import traceback
        print(f"❌ Erro no Pareto de Clientes: {e}")
        traceback.print_exc()
        fig = go.Figure()
        fig.add_annotation(text=f"Erro: {str(e)}", xref='paper', yref='paper', x=0.5, y=0.5)
        fig.update_layout(template='plotly_white', height=400)
        return fig

# Exportar linhas selecionadas para Excel
@app.callback(
    Output('download-xlsx-clientes', 'data'),
    Input('btn-export-excel-clientes', 'n_clicks'),
    State('tabela-kpis-clientes', 'virtualRowData'),
    State('tabela-kpis-clientes', 'selectedRows'),
    prevent_initial_call=True
)
def export_clients_xlsx(n_clicks, rows, selected_row_indices):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    import pandas as pd
    from dash import dcc
    if not rows:
        return dash.no_update
    df = pd.DataFrame(rows)
    try:
        # Se houver linhas selecionadas, exportar apenas as selecionadas (AG Grid fornece linhas completas, não índices)
        if isinstance(selected_row_indices, (list, tuple)) and len(selected_row_indices) > 0:
            try:
                import pandas as pd
                sel_df = pd.DataFrame(list(selected_row_indices))
                # Preferir chave primária 'cod_cliente' para cruzar
                if 'cod_cliente' in df.columns and 'cod_cliente' in sel_df.columns:
                    df = df[df['cod_cliente'].isin(sel_df['cod_cliente'])]
                else:
                    # Fallback: interseção por todas as colunas em comum
                    common = [c for c in sel_df.columns if c in df.columns]
                    if common:
                        df = df.merge(sel_df[common].drop_duplicates(), on=common, how='inner')
            except Exception:
                pass

        def to_xlsx(bytes_io):
            with pd.ExcelWriter(bytes_io, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Clientes')

        return dcc.send_bytes(to_xlsx, 'clientes.xlsx')
    except Exception as e:
        print(f"❌ Erro ao gerar Excel: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update

# Exibir pesos normalizados RFV (clientes)
@app.callback(
    Output('clients-rfv-weights-display', 'children'),
    [Input('slider-r-weight', 'value'),
     Input('slider-f-weight', 'value'),
     Input('slider-v-weight', 'value')],
    prevent_initial_call=False
)
def display_normalized_rfv_clients(wR_in, wF_in, wV_in):
    try:
        wR = float(wR_in or 0)
        wF = float(wF_in or 0)
        wV = float(wV_in or 0)
        total = wR + wF + wV
        if total <= 0:
            return "Pesos normalizados: R=0%, F=0%, M=0%"
        wR_n = wR / total
        wF_n = wF / total
        wV_n = wV / total
        return f"Pesos normalizados: R={wR_n*100:.0f}%, F={wF_n*100:.0f}%, M={wV_n*100:.0f}%"
    except Exception:
        return "Pesos normalizados: R=33%, F=33%, M=34%"

"""Download PDF por Cliente (Clientes)"""
@app.callback(
    Output('download-pdf-clientes', 'data'),
    Input('btn-pdf-cliente-clientes', 'n_clicks'),
    State('tabela-kpis-clientes', 'virtualRowData'),
    State('tabela-kpis-clientes', 'selectedRows'),
    prevent_initial_call=True
)
def download_pdf_clientes(n_clicks, derived_rows, selected_rows):
    """Gera um PDF simples com os dados dos clientes selecionados (ou todos os filtrados)."""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    from dash import dcc
    import pandas as pd
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    if not derived_rows:
        return dash.no_update

    df = pd.DataFrame(derived_rows)
    # Se houver seleção, filtrar pelas linhas selecionadas (AG Grid: linhas completas)
    if isinstance(selected_rows, (list, tuple)) and len(selected_rows) > 0:
        try:
            sel_df = pd.DataFrame(list(selected_rows))
            if 'cod_cliente' in df.columns and 'cod_cliente' in sel_df.columns:
                df = df[df['cod_cliente'].isin(sel_df['cod_cliente'])]
            else:
                common = [c for c in sel_df.columns if c in df.columns]
                if common:
                    df = df.merge(sel_df[common].drop_duplicates(), on=common, how='inner')
        except Exception:
            pass

    # Restringir colunas relevantes e formatar
    preferred_cols = [
        'cod_cliente', 'cliente', 'rfv_score', 'rfv_class', 'total_vendas',
        'ultima_compra', 'frequencia_compra', 'frequencia_media_compra',
        'dias_sem_compra', 'percentual_mix', 'perc_nao_comprado'
    ]
    cols = [c for c in preferred_cols if c in df.columns]
    if not cols:
        cols = list(df.columns)

    # Ordenar por maior faturamento se existir
    if 'total_vendas' in df.columns:
        df = df.sort_values('total_vendas', ascending=False)

    # Preparar PDF em memória
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=54, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatório por Cliente", styles['Title']))
    story.append(Paragraph("Laura Representações - WEG", styles['Normal']))
    story.append(Spacer(1, 12))

    # Tabela de dados (limitando a 200 linhas para manter tamanho razoável)
    max_rows = 200
    df_print = df[cols].head(max_rows).copy()

    # Formatações leves
    if 'total_vendas' in df_print.columns:
        df_print['total_vendas'] = pd.to_numeric(df_print['total_vendas'], errors='coerce').fillna(0.0).map(lambda x: f"R$ {x:,.2f}")
    if 'percentual_mix' in df_print.columns:
        df_print['percentual_mix'] = pd.to_numeric(df_print['percentual_mix'], errors='coerce').fillna(0.0).map(lambda x: f"{x:.0f}%")
    if 'perc_nao_comprado' in df_print.columns:
        df_print['perc_nao_comprado'] = pd.to_numeric(df_print['perc_nao_comprado'], errors='coerce').fillna(0.0).map(lambda x: f"{x:.0f}%")

    table_data = [
        [
            'Código', 'Cliente', 'RFV', 'Classe', 'Total Vendas', 'Última Compra',
            'Freq. Compras', 'Freq. Média (dias)', 'Dias s/ Compra', '% Mix', '% Não Compr.'
        ]
    ]
    for _, row in df_print.iterrows():
        table_data.append([
            row.get('cod_cliente', ''),
            row.get('cliente', ''),
            row.get('rfv_score', ''),
            row.get('rfv_class', ''),
            row.get('total_vendas', ''),
            row.get('ultima_compra', ''),
            row.get('frequencia_compra', ''),
            row.get('frequencia_media_compra', ''),
            row.get('dias_sem_compra', ''),
            row.get('percentual_mix', ''),
            row.get('perc_nao_comprado', '')
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total de clientes listados: {len(df_print)}", styles['Italic']))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Nome do arquivo
    filename = 'clientes_relatorio.pdf'

    return dcc.send_bytes(pdf_bytes, filename)

"""Unificar controles da tabela de clientes para evitar outputs duplicados"""
@app.callback(
    Output('tabela-kpis-clientes', 'selectedRows'),
    [Input('btn-select-all-clientes', 'n_clicks'),
     Input('btn-deselect-all-clientes', 'n_clicks')],
    State('tabela-kpis-clientes', 'rowData'),
    prevent_initial_call=True
)
def manage_clients_table_controls(select_clicks, deselect_clicks, table_data):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'btn-select-all-clientes' and select_clicks:
        # Seleciona todas as linhas: passar a lista inteira (AG Grid usa objetos, mas selectedRows recebe linhas, não índices)
        return table_data or []
    elif button_id == 'btn-deselect-all-clientes' and deselect_clicks:
        return []
    else:
        return dash.no_update

# Limpar filtros e ordenação do AG Grid (Clientes)
@app.callback(
    [Output('tabela-kpis-clientes', 'filterModel'),
     Output('tabela-kpis-clientes', 'sortModel')],
    Input('btn-clear-filters-clientes', 'n_clicks'),
    prevent_initial_call=True
)
def clear_clients_grid_filters(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    # Zera filtros e ordenação
    return {}, []

# Persistir estado do AG Grid (Clientes) no armazenamento local
@app.callback(
    Output('clientes-grid-state', 'data'),
    [
        Input('tabela-kpis-clientes', 'filterModel'),
        Input('tabela-kpis-clientes', 'sortModel'),
        Input('tabela-kpis-clientes', 'columnState'),
    ],
    prevent_initial_call=True
)
def persist_clients_grid_state(filter_model, sort_model, column_state):
    try:
        return {
            'filterModel': filter_model or {},
            'sortModel': sort_model or [],
            'columnState': column_state or []
        }
    except Exception:
        return {}

# Restaurar estado do AG Grid (Clientes) ao entrar na página
@app.callback(
    [
        Output('tabela-kpis-clientes', 'filterModel', allow_duplicate=True),
        Output('tabela-kpis-clientes', 'sortModel', allow_duplicate=True),
        Output('tabela-kpis-clientes', 'columnState', allow_duplicate=True),
    ],
    Input('url', 'pathname'),
    State('clientes-grid-state', 'data'),
    prevent_initial_call='initial_duplicate'
)
def restore_clients_grid_state(pathname, grid_state):
    try:
        is_clients = bool(pathname and '/app/clients' in pathname)
        if not is_clients or not isinstance(grid_state, dict):
            return dash.no_update, dash.no_update, dash.no_update
        return (
            grid_state.get('filterModel') or {},
            grid_state.get('sortModel') or [],
            grid_state.get('columnState') or []
        )
    except Exception:
        return dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('grafico-bolhas-produtos', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('filter-top-produtos', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_products_bubble_chart(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, top_produtos, pathname):
    """Atualiza APENAS o gráfico de bolhas na página de Produtos."""
    import plotly.graph_objects as go
    import numpy as np
    # Restringe execução à página de Produtos
    is_products_page = bool(pathname and ("/app/products" in pathname or "products" in pathname))
    if not is_products_page:
        from dash.exceptions import PreventUpdate
        raise PreventUpdate

    try:
        vendas_df = load_vendas_data()
        if vendas_df is None or vendas_df.empty:
            fig = go.Figure().add_annotation(text="Nenhum dado de vendas disponível", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                    filtro_hierarquia, filtro_canal, filtro_top_clientes, None)
        if df_filtrado is None or df_filtrado.empty:
            fig = go.Figure().add_annotation(text="Sem dados após filtros", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        # Determinar coluna de produto conforme hierarquia
        hierarchy_level, product_column = determine_hierarchy_level(df_filtrado, filtro_hierarquia)
        top_n_produtos = top_produtos if top_produtos and top_produtos > 0 else 20

        # Verificações de colunas necessárias
        if 'cliente' not in df_filtrado.columns or product_column not in df_filtrado.columns:
            missing = [c for c in ['cliente', product_column] if c not in df_filtrado.columns]
            fig = go.Figure().add_annotation(text=f"Colunas faltando: {', '.join(missing)}", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        # Determinar coluna de quantidade, se existir
        qty_col = next((c for c in ['qty_vendida', 'qtde', 'quantidade', 'qte'] if c in df_filtrado.columns), None)
        agg = {'vlr_rol': 'sum'}
        if qty_col:
            agg[qty_col] = 'sum'

        matriz = df_filtrado.groupby(['cliente', product_column]).agg(agg).reset_index()
        if matriz.empty:
            fig = go.Figure().add_annotation(text="Sem dados para matriz", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        num_top_clientes = filtro_top_clientes if filtro_top_clientes and filtro_top_clientes > 0 else 10
        top_clientes = matriz.groupby('cliente')['vlr_rol'].sum().nlargest(num_top_clientes).index
        top_produtos_viz = matriz.groupby(product_column)['vlr_rol'].sum().nlargest(top_n_produtos).index
        sel = matriz[(matriz['cliente'].isin(top_clientes)) & (matriz[product_column].isin(top_produtos_viz))]
        if sel.empty:
            fig = go.Figure().add_annotation(text="Sem dados após seleção Top N", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        # Estatísticas auxiliares para hover/cores
        produto_stats = df_filtrado.groupby(product_column).agg({
            'vlr_rol': ['sum', 'mean', 'count', 'std'],
            'cliente': 'nunique'
        }).reset_index()
        produto_stats.columns = [product_column, 'faturamento_total', 'faturamento_medio', 'freq_vendas', 'desvio_padrao', 'num_clientes']
        produto_stats['desvio_padrao'] = produto_stats['desvio_padrao'].fillna(0)
        total_clientes = df_filtrado['cliente'].nunique()
        produto_stats['penetracao_mercado'] = (produto_stats['num_clientes'] / max(total_clientes, 1)) * 100

        # zscore com fallback
        try:
            from scipy import stats as _stats
            produto_stats['demanda_relativa'] = _stats.zscore(produto_stats['faturamento_total'])
        except Exception:
            m = produto_stats['faturamento_total'].mean()
            s = produto_stats['faturamento_total'].std() or 1
            produto_stats['demanda_relativa'] = (produto_stats['faturamento_total'] - m) / s

        produto_stats['indice_oportunidade'] = produto_stats['faturamento_total'] / (produto_stats['penetracao_mercado'] + 1)
        mat = sel.merge(
            produto_stats[[product_column, 'faturamento_total', 'penetracao_mercado', 'demanda_relativa', 'indice_oportunidade']],
            on=product_column
        )
        mat['participacao_cliente'] = (mat['vlr_rol'] / mat['faturamento_total']).replace([np.inf, -np.inf], 0) * 100
        mat['score_oportunidade'] = mat['indice_oportunidade'] * (100 - mat['participacao_cliente']) / 100

        # Normalizações
        p5, p95 = np.percentile(mat['score_oportunidade'], 5), np.percentile(mat['score_oportunidade'], 95)
        mat['score_norm'] = np.clip(mat['score_oportunidade'], p5, p95)
        smin, smax = mat['score_norm'].min(), mat['score_norm'].max()
        mat['cor_score'] = 50 if smax <= smin else 100 * (mat['score_norm'] - smin) / (smax - smin)
        mat['vlr_rol_abs'] = mat['vlr_rol'].abs().replace(0, 1)
        mat['tamanho_log'] = np.log1p(mat['vlr_rol_abs'])
        tmin, tmax = mat['tamanho_log'].min(), mat['tamanho_log'].max()
        mat['tamanho_norm'] = 25 if tmax <= tmin else 10 + 40 * (mat['tamanho_log'] - tmin) / (tmax - tmin)

        import plotly.graph_objects as go
        fig = go.Figure()
        hover_template = (
            "<b>%{customdata[0]}</b><br>"+
            "<b>Produto:</b> %{y}<br>"+
            "<b>Faturamento Cliente:</b> R$ %{customdata[1]:,.0f}<br>"+
            "<b>Score Oportunidade:</b> %{customdata[2]:.1f}<br>"+
            "<b>Penetração Mercado:</b> %{customdata[3]:.1f}%<br>"+
            "<b>Participação Cliente:</b> %{customdata[4]:.1f}%<br>"+
            "<b>Demanda Global:</b> R$ %{customdata[5]:,.0f}<br><extra></extra>"
        )
        custom_data = np.array([
            mat['cliente'], mat['vlr_rol'], mat['score_oportunidade'], mat['penetracao_mercado'], mat['participacao_cliente'], mat['faturamento_total']
        ]).T
        fig.add_trace(go.Scatter(
            x=mat['cliente'], y=mat[product_column], mode='markers',
            marker=dict(size=mat['tamanho_norm'], color=mat['cor_score'], colorscale='RdYlBu_r',
                        colorbar=dict(title="Score de<br>Oportunidade", thickness=15, len=0.5, x=1.02, y=1, xanchor="left", yanchor="top"),
                        sizemode='diameter', sizemin=8, line=dict(width=1, color='rgba(0,51,102,0.3)'), opacity=0.8),
            customdata=custom_data, hovertemplate=hover_template, name=""
        ))
        fig.update_layout(
            title=dict(text=f"Matriz de Oportunidades: Clientes × Produtos<br><span style='font-size:14px'>Top {num_top_clientes} Clientes × Top {top_n_produtos} Produtos</span>", x=0.5, xanchor='center', font=dict(size=18, color='#003366')),
            height=650, template='plotly_white', font=dict(family="Arial", size=12),
            xaxis=dict(title="Cliente", tickangle=45), yaxis=dict(title="Produto"),
            margin=dict(l=200, r=140, t=120, b=150), hovermode='closest'
        )
        return fig
    except Exception as e:
        import traceback
        print(f"❌ Erro em update_products_bubble_chart: {e}")
        traceback.print_exc()
        fig = go.Figure().add_annotation(text=f"Erro: {str(e)}", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        fig.update_layout(template='plotly_white', height=400)
        return fig

""" OPORTUNIDADES POR CLIENTE (Onda A+B) """
@app.callback(
    [
        Output('opportunities-table', 'rowData'),
        Output('opportunities-table', 'columnDefs'),
        Output('opportunities-summary', 'children'),
        Output('opportunities-weight-hint', 'children'),
    ],
    [
        Input('url', 'pathname'),
        Input('global-filtro-ano', 'value'),
        Input('global-filtro-mes', 'value'),
        Input('global-filtro-cliente', 'value'),
        Input('global-filtro-hierarquia', 'value'),
        Input('global-filtro-canal', 'value'),
        Input('peso-freq-cotacao', 'value'),
        Input('opportunities-freq-mode', 'value'),
        Input('opportunities-bucket-filter', 'value'),
    ],
    prevent_initial_call=False
)
def update_opportunities_table(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, peso_freq, freq_mode, bucket_filter):
    # Renderiza apenas na página de Produtos
    is_products = bool(pathname and ("/app/products" in pathname or "/produtos" in pathname or "products" in pathname))
    if not is_products:
        from dash.exceptions import PreventUpdate
        raise PreventUpdate

    # Exige exatamente um cliente selecionado
    if not filtro_cliente or not isinstance(filtro_cliente, (list, tuple)) or len(filtro_cliente) != 1:
        return [], [
            {"headerName": "Mensagem", "field": "mensagem"}
        ], html.Span("Selecione exatamente um cliente no filtro global para ver as oportunidades.")

    cliente_id = str(filtro_cliente[0])

    try:
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_cotados_df = load_produtos_cotados_data()
    except Exception:
        return [], [], html.Span("Falha ao carregar dados.")

    # Aplicar filtros globais nas Vendas (fonte de verdade)
    try:
        from utils import apply_filters as _apply_filters
    except Exception:
        _apply_filters = None

    vendas_filtrado = vendas_df
    if _apply_filters is not None:
        # Importante: não filtrar pelo cliente aqui, para que v_mercado considere demais clientes
        vendas_filtrado = _apply_filters(
            vendas_df, filtro_ano, filtro_mes, None,  # cliente=None
            filtro_hierarquia, filtro_canal, None, None, metrica_type='faturamento'
        )

    # Preparar ranges de ano/mês para filtrar cotações na mesma janela temporal
    ano_range = tuple(filtro_ano) if isinstance(filtro_ano, (list, tuple)) and len(filtro_ano) == 2 else None
    mes_range = tuple(filtro_mes) if isinstance(filtro_mes, (list, tuple)) and len(filtro_mes) == 2 else None

    # Calcular oportunidades
    df = compute_client_opportunities(
        vendas_filtrado, cotacoes_df, produtos_cotados_df,
        cliente_id=cliente_id,
        ano_range=ano_range,
        mes_range=mes_range,
        peso_freq_cotacao=float(peso_freq or 0.5),
        filtro_hierarquia=filtro_hierarquia,
        filtro_canal=filtro_canal,
        vendas_map_df=vendas_df,
        freq_mode=str(freq_mode or 'occurrences'),
    )

    # Se houver filtro de hierarquia, apresentar a "próxima camada" (ex.: se filtro em Hierarquia 1, exibir Hierarquia 2)
    try:
        import pandas as _pd
        level = None
        values = set([str(v) for v in (filtro_hierarquia or [])]) if isinstance(filtro_hierarquia, (list, tuple, set)) else ({str(filtro_hierarquia)} if filtro_hierarquia else set())
        cols_present = [c for c in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3'] if c in vendas_filtrado.columns]
        if values and cols_present:
            if 'hier_produto_1' in cols_present and vendas_filtrado['hier_produto_1'].astype(str).isin(values).any():
                level = 1
            elif 'hier_produto_2' in cols_present and vendas_filtrado['hier_produto_2'].astype(str).isin(values).any():
                level = 2
            elif 'hier_produto_3' in cols_present and vendas_filtrado['hier_produto_3'].astype(str).isin(values).any():
                level = 3

        if level is not None:
            # Mapear material -> hierarquias
            map_cols = ['material'] + cols_present
            mat_map = vendas_filtrado[map_cols].dropna(subset=['material']).drop_duplicates('material')
            mat_map['material'] = mat_map['material'].astype(str)
            df = df.copy()
            df['material'] = df['material'].astype(str)
            df = df.merge(mat_map, on='material', how='left')

            # Escolher coluna de exibição (próximo nível)
            if level == 1 and 'hier_produto_2' in df.columns:
                disp_col = 'hier_produto_2'
            elif level == 2 and 'hier_produto_3' in df.columns:
                disp_col = 'hier_produto_3'
            else:
                disp_col = 'produto'

            # Agregar por display col e recalcular motivo/oportunidade a nível do grupo
            if disp_col in df.columns:
                agg = df.groupby(disp_col).agg({
                    'v_cliente': 'sum',
                    'v_mercado': 'sum',
                    'q_valor': 'sum',
                    'q_freq': 'sum',
                    'ultima_cotacao': 'max'
                }).reset_index().rename(columns={disp_col: 'produto'})

                # Escolher um material representativo por grupo (maior oportunidade, depois maior q_valor)
                _df_rank = df.copy()
                _df_rank['_rank_key'] = (_df_rank['oportunidade_brl'].fillna(0)) * 1e9 + _df_rank['q_valor'].fillna(0)
                rep = _df_rank.sort_values('_rank_key', ascending=False).groupby(disp_col, as_index=False).first()
                rep = rep.rename(columns={'material': '_rep_material'})[[disp_col, '_rep_material']]
                agg = agg.merge(rep.rename(columns={disp_col: 'produto'}), on='produto', how='left')

                # Recalcular potenciais com mesmo critério
                w = float(peso_freq or 0.5)
                mask_b1 = (agg['q_valor'] > 0) & (agg['v_cliente'] <= 0)
                freq_rank = agg.loc[mask_b1, 'q_freq'].rank(pct=True, method='average') if mask_b1.any() else _pd.Series(dtype=float)
                multiplier = (1 - w) + w * freq_rank
                pot1 = _pd.Series(0.0, index=agg.index)
                pot1.loc[mask_b1] = agg.loc[mask_b1, 'q_valor'] * multiplier.values

                mask_b2 = (agg['v_mercado'] > 0) & (agg['v_cliente'] <= 0)
                pot2 = _pd.Series(0.0, index=agg.index)
                pot2.loc[mask_b2] = agg.loc[mask_b2, 'v_mercado']

                mask_b3 = (agg['v_cliente'] > 0) & (agg['v_mercado'] > agg['v_cliente'])
                pot3 = _pd.Series(0.0, index=agg.index)
                pot3.loc[mask_b3] = (agg.loc[mask_b3, 'v_mercado'] - agg.loc[mask_b3, 'v_cliente'])

                agg['oportunidade_brl'] = _pd.concat([pot1, pot2, pot3], axis=1).max(axis=1)
                def _mot(row):
                    if row['oportunidade_brl'] <= 0:
                        return ''
                    if row['oportunidade_brl'] == pot1.loc[row.name]:
                        return 'Cotou e não compra'
                    if row['oportunidade_brl'] == pot2.loc[row.name]:
                        return 'Mercado forte, cliente fora'
                    return 'Baixa penetração'
                agg['motivo'] = agg.apply(_mot, axis=1)

                # Material representativo neste nível (preenche com '-' se não houver)
                agg['material'] = agg['_rep_material'].fillna('-').astype(str)
                agg = agg.drop(columns=['_rep_material'], errors='ignore')
                df = agg.sort_values('oportunidade_brl', ascending=False)
    except Exception:
        # Em caso de qualquer falha, mantém df original por segurança
        pass

    # Filtrar por bucket se necessário (aplicar após quaisquer agregações)
    if isinstance(bucket_filter, str) and bucket_filter != 'all':
        df = df[df['motivo'] == bucket_filter]

    # Montar colunas e formatos
    cols = [
        'material', 'produto', 'oportunidade_brl', 'motivo', 'v_mercado', 'v_cliente', 'q_valor', 'q_freq', 'ultima_cotacao'
    ]
    numeric_cols = ['oportunidade_brl', 'v_mercado', 'v_cliente', 'q_valor', 'q_freq']
    formats = {
        'oportunidade_brl': 'currency',
        'v_mercado': 'currency',
        'v_cliente': 'currency',
        'q_valor': 'currency',
        'q_freq': 'int'
    }
    display_names = {
        'material': 'Material',
        'produto': 'Produto',
        'oportunidade_brl': 'Oportunidade (R$)',
        'motivo': 'Motivo',
        'v_mercado': 'Demanda Mercado (R$)',
        'v_cliente': 'Compras Cliente (R$)',
        'q_valor': 'Valor Cotado Cliente (R$)',
        'q_freq': ('Freq. Cotações (ocorrências)' if str(freq_mode or 'occurrences') == 'occurrences' else 'Freq. Cotações (ponderada por qtd.)'),
        'ultima_cotacao': 'Última Cotação'
    }

    column_defs = build_column_defs(cols, numeric_cols=numeric_cols, formats=formats, display_names=display_names)

    # Resumo
    n_itens = len(df)
    # Quebra por motivo para explicar efeito do peso de frequência
    try:
        counts_by_motivo = df['motivo'].value_counts(dropna=False).to_dict() if 'motivo' in df.columns else {}
    except Exception:
        counts_by_motivo = {}
    n_b1 = int(counts_by_motivo.get('Cotou e não compra', 0) or 0)
    detalhes_peso = ""
    # O peso da frequência só afeta itens do bucket 'Cotou e não compra' e apenas quando há diferenças de frequência
    if n_b1 <= 1:
        detalhes_peso = " (Nota: o peso de frequência impacta apenas itens em 'Cotou e não compra' e pode não alterar a ordem quando há 0 ou 1 item nesse motivo.)"
    else:
        detalhes_peso = f" (Peso de frequência aplicado a {n_b1} itens em 'Cotou e não compra'.)"
    resumo = f"{n_itens} itens de oportunidade para o cliente {cliente_id}. Ordenado por Oportunidade (R$).{detalhes_peso}"
    # Dica curta abaixo do slider
    if n_b1 <= 1:
        hint = "Dica: o peso de frequência só afeta itens em 'Cotou e não compra'; com 0/1 item, a ordem pode não mudar."
    else:
        hint = f"Peso aplicado a {n_b1} item(ns) em 'Cotou e não compra'."

    return df.to_dict('records'), column_defs, resumo, hint

@app.callback(
    Output('grafico-pareto-produtos', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_overview_pareto_chart(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, pathname):
    """Atualiza APENAS o gráfico de Pareto de Produtos na Visão Geral."""
    import plotly.graph_objects as go
    # Restringe execução à Visão Geral
    is_overview_page = bool(pathname and (pathname in ['/', '/app', '/app/'] or '/app/overview' in pathname))
    if not is_overview_page:
        from dash.exceptions import PreventUpdate
        raise PreventUpdate

    try:
        vendas_df = load_vendas_data()
        if vendas_df is None or vendas_df.empty:
            fig = go.Figure().add_annotation(text="Nenhum dado de vendas disponível", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                    filtro_hierarquia, filtro_canal, None, None)
        if df_filtrado is None or df_filtrado.empty:
            fig = go.Figure().add_annotation(text="Sem dados após filtros", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        _, product_column = determine_hierarchy_level(df_filtrado, filtro_hierarquia)
        top_n = 20
        pareto = (df_filtrado.groupby(product_column)['vlr_rol'].sum()
                  .sort_values(ascending=False).reset_index().head(top_n))
        if pareto.empty:
            fig = go.Figure().add_annotation(text="Nenhum dado disponível para análise de Pareto", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False)
            fig.update_layout(template='plotly_white', height=400)
            return fig

        total = pareto['vlr_rol'].sum()
        if total > 0:
            pareto['faturamento_acumulado'] = pareto['vlr_rol'].cumsum()
            pareto['percentual_acumulado'] = (pareto['faturamento_acumulado'] / total) * 100
        else:
            pareto['faturamento_acumulado'] = 0
            pareto['percentual_acumulado'] = 0

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pareto[product_column], y=pareto['vlr_rol'], name='Faturamento', yaxis='y',
            marker=dict(color='#0066cc', line=dict(color='#003366', width=1)),
            hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.0f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=pareto[product_column], y=pareto['percentual_acumulado'], mode='lines+markers', name='% Acumulado', yaxis='y2',
            line=dict(color='#dc3545', width=3), marker=dict(size=8, color='#dc3545'),
            hovertemplate='<b>%{x}</b><br>% Acumulado: %{y:.1f}%<extra></extra>'
        ))
        fig.update_layout(
            title="Análise de Pareto - Faturamento por Produto", height=550, template='plotly_white', showlegend=False,
            yaxis=dict(title="Faturamento (R$)", tickformat=',.0f'),
            yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 100], tickformat='.0f', ticksuffix='%'),
            xaxis=dict(title="Produto", tickangle=45), margin=dict(l=80, r=80, t=100, b=120)
        )
        try:
            fig.add_hline(y=80, yref='y2', line_dash='dash', line_color='red')
        except Exception:
            pass
        return fig
    except Exception as e:
        import traceback
        print(f"❌ Erro em update_overview_pareto_chart: {e}")
        traceback.print_exc()
        fig = go.Figure().add_annotation(text=f"Erro no gráfico Pareto: {str(e)}", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False)
        fig.update_layout(template='plotly_white', height=400)
        return fig

# CALLBACK DESABILITADO - Tabela agora é gerenciada por produtos_table_callback.py
# @app.callback(
#     Output('tabela-kpis-clientes', 'dashGridOptions'),
#     [Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value'),
#      Input('filter-material-table', 'value'),
#      Input('url', 'pathname')],
#     prevent_initial_call=False
# )
# def update_products_table(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, material_filter, pathname):
#     """Atualiza tabela de análise de produtos"""
#     print(f"🔄 UPDATE_PRODUCTS_TABLE executado - pathname: {pathname}")
#     print(f"   Material filter recebido: {material_filter} (tipo: {type(material_filter)})")
#     
#     try:
        # Só processa se estiver na página de produtos
#         if pathname and "/app/products" not in pathname and "products" not in pathname:
#             print(f"❌ Não é página de produtos: {pathname}")
#             return []
            
#         vendas_df = load_vendas_data()
#         cotacoes_df = load_cotacoes_data()
        
#         if vendas_df.empty:
#             print("❌ Dados de vendas vazios")
#             return []
        
#         # Aplica filtros
#         df_vendas_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
#                                          filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
#         df_cotacoes_filtrado = apply_filters(cotacoes_df, filtro_ano, filtro_mes, filtro_cliente, 
#                                           filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
        
#         if df_vendas_filtrado.empty:
#             print("❌ Dados filtrados vazios")
#             return []
        
#         # Analisa produtos
#         produtos_stats = df_vendas_filtrado.groupby(['material', 'produto']).agg({
#             'vlr_rol': ['sum', 'mean', 'count'],
#             'qtd_rol': 'mean'
#         }).reset_index()
        
#         # Flatten columns
#         produtos_stats.columns = ['material', 'produto', 'faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada']
        
#         # Adicionar hierarquia
#         if 'hier_produto_1' in df_vendas_filtrado.columns:
#             hierarquia_map = df_vendas_filtrado.groupby('produto')['hier_produto_1'].first().to_dict()
#             produtos_stats['hierarquia'] = produtos_stats['produto'].map(hierarquia_map).fillna('N/A')
#         else:
#             produtos_stats['hierarquia'] = 'N/A'
        
#         # Calcular dados de cotação se disponível
#         if not df_cotacoes_filtrado.empty and 'produto' in df_cotacoes_filtrado.columns:
#             cotacoes_stats = df_cotacoes_filtrado.groupby('produto').size().to_dict()
#             produtos_stats['recorrencia_cotacao'] = produtos_stats['produto'].map(cotacoes_stats).fillna(0)
            
#             # Taxa de conversão
#             produtos_stats['taxa_conversao'] = (produtos_stats['recorrencia_compra'] / produtos_stats['recorrencia_cotacao'] * 100).fillna(0)
#         else:
#             produtos_stats['recorrencia_cotacao'] = produtos_stats['recorrencia_compra'] * 1.5  # Simulado
#             produtos_stats['taxa_conversao'] = 65.0  # Simulado
        
#         # Filtrar por material se selecionado - CORREÇÃO: Melhor tratamento de múltipla seleção
#         if material_filter and len(material_filter) > 0:
#             print(f"🔍 Aplicando filtro de material: {len(material_filter)} itens selecionados")
#             print(f"   Materiais: {material_filter}")
            
#             # Criar lista de códigos de material a partir das strings completas
#             material_codes = []
#             for item in material_filter:
#                 if isinstance(item, str) and ' - ' in item:
#                     # Extrair código do material (formato: "código - descrição")
#                     code = item.split(' - ')[0].strip()
#                     material_codes.append(code)
#                 else:
#                     # Se já for só o código
#                     material_codes.append(str(item))
            
#             print(f"   Códigos extraídos: {material_codes}")
            
#             # Filtrar pelos códigos de material
#             produtos_stats = produtos_stats[produtos_stats['material'].astype(str).isin(material_codes)]
#             print(f"   Registros após filtro: {len(produtos_stats)}")
#         else:
#             print("🔍 Nenhum filtro de material aplicado")
        
#         print(f"✅ Tabela de produtos gerada: {len(produtos_stats)} registros")
        
#         # CORREÇÃO: Verificar se os dados são válidos antes de retornar
#         if produtos_stats.empty:
#             print("⚠️ produtos_stats está vazio após processamento")
#             return []
        
#         result_data = produtos_stats.head(100).to_dict('records')
        
#         # Validar e limpar dados antes do retorno
#         cleaned_data = []
#         for i, record in enumerate(result_data):
#             if not isinstance(record, dict):
#                 print(f"❌ Registro {i} não é um dicionário válido: {type(record)}")
#                 continue
            
#             # Criar novo registro limpo
#             clean_record = {}
#             for key, value in record.items():
#                 # Converter NaN, None e valores problemáticos
#                 if value is None or (hasattr(value, '__iter__') and not isinstance(value, str) and len(str(value)) == 0):
#                     clean_record[key] = ""
#                 elif hasattr(value, 'isna') and value.isna():
#                     clean_record[key] = 0 if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else ""
#                 elif isinstance(value, (int, float)):
#                     # Verificar se é um número válido
#                     if str(value).lower() in ['nan', 'inf', '-inf']:
#                         clean_record[key] = 0 if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else ""
#                     else:
#                         clean_record[key] = float(value) if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else value
#                 else:
#                     clean_record[key] = str(value) if value is not None else ""
            
#             # Verificar se o registro tem as colunas obrigatórias
#             required_fields = ['material', 'produto', 'hierarquia', 'faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao']
            
#             # Garantir que todos os campos obrigatórios existem
#             for field in required_fields:
#                 if field not in clean_record:
#                     if field in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao']:
#                         clean_record[field] = 0
#                     else:
#                         clean_record[field] = ""
            
#             cleaned_data.append(clean_record)
        
#         print(f"✅ Dados validados e limpos: {len(cleaned_data)} registros prontos para retorno")
        
#         # VALIDAÇÃO FINAL: Garantir que é sempre uma lista válida
#         if not isinstance(cleaned_data, list):
#             print(f"❌ Resultado não é uma lista: {type(cleaned_data)}")
#             return []
        
#         # Verificar se os itens da lista são dicionários válidos
#         validated_data = []
#         for i, item in enumerate(cleaned_data):
#             if isinstance(item, dict) and all(isinstance(k, str) for k in item.keys()):
#                 validated_data.append(item)
#             else:
#                 print(f"❌ Item {i} inválido: {type(item)}")
        
#         # Log dos primeiros registros para debug
#         if validated_data:
#             print(f"🔍 Exemplo do primeiro registro: {list(validated_data[0].keys()) if validated_data[0] else 'vazio'}")
        
#         # VALIDAÇÃO FINAL ROBUSTA: Garantir que os dados são serializáveis JSON
#         try:
#             import json
#             json.dumps(validated_data[:1])  # Testa serializabilidade do primeiro item
#             print("✅ Dados validados como serializáveis JSON")
#         except (TypeError, ValueError) as json_error:
#             print(f"❌ Dados não são serializáveis JSON: {json_error}")
#             # Retornar lista vazia em caso de erro de serialização
#             return []
        
#         return validated_data
        
#     except Exception as e:
#         print(f"❌ Erro em update_products_table: {e}")
#         return []

# CALLBACK DESABILITADO - ID 'tabela-analise-produtos' não existe no layout
# @app.callback(
#     Output('download-csv-produtos', 'data'),
#     [Input('btn-download-csv-produtos', 'n_clicks')],
#     [State('tabela-analise-produtos', 'data')]
# )
# def download_products_csv(n_clicks, table_data):
#     """Download da tabela de produtos em CSV"""
#     if n_clicks and table_data:
#         import pandas as pd
#         df = pd.DataFrame(table_data)
#         return dcc.send_data_frame(df.to_csv, "produtos_analysis.csv", index=False)
#     return dash.no_update

# CALLBACK DESABILITADO - ID 'tabela-analise-produtos' não existe no layout  
# @app.callback(
#     [Output('tabela-analise-produtos', 'filter_query'),
#      Output('filter-material-table', 'value')],
#     [Input('btn-clear-filters-produtos', 'n_clicks')]
# )
# def clear_products_filters(n_clicks):
#     """Limpa apenas os filtros internos da tabela de produtos e filtro de material (não os filtros globais)"""
#     if n_clicks:
#         print("🧹 Limpando filtros internos da tabela de produtos")
#         # Limpa filter_query da tabela e reseta filtro de material
#         return '', []  # filter_query vazio e material vazio
#     return dash.no_update, dash.no_update

# ==========================================
# CALLBACK PARA POPULAR OPÇÕES DE MATERIAL (MOVIDO PARA produtos_table_callback_new.py)
# ==========================================

# @app.callback(
#     Output('filter-material-table', 'options'),
#     [Input('url', 'pathname'),
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value'),
#      Input('global-filtro-unidade', 'value')],
#     [State('global-filtro-representada', 'value')]
# )
# def update_material_filter_options_central(pathname, ano, mes, cliente, hierarquia, canal, unidade, representada):
#     if pathname not in ['/app/products', '/produtos']:
#         return dash.no_update

#     try:
#         # Lógica para carregar e filtrar os dados de vendas
#         df_vendas = load_vendas_data(ano, mes, representada, cliente, hierarquia, canal, unidade)
        
#         if df_vendas.empty:
#             return []

#         # Obter materiais únicos e formatar para o dropdown
#         materiais = sorted(df_vendas['Material'].unique())
#         options = [{'label': material, 'value': material} for material in materiais]
#         return options

#     except Exception as e:
#         print(f"Erro ao atualizar opções de material: {e}")
#         return []

# =================================================================
# CALLBACK PARA ATUALIZAR TABELA DE ANÁLISE DE PRODUTOS (Exemplo)
# =================================================================
