"""
Callbacks para página de Sugestões Inteligentes de Compra
Dashboard Laura Representações - WEG
"""

import dash
from dash import callback, Input, Output, State, ctx, no_update, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

# Import do app principal - IMPORTANTE para registro de callbacks
from webapp import app

# Imports locais
from utils import load_all_data
from utils.ml_recommendations import purchase_recommender
from webapp.purchase_suggestions_layout import (
    create_suggestions_table, 
    create_abc_xyz_chart, 
    create_probability_chart
)

# Configuração de logging
logger = logging.getLogger(__name__)

def _create_progress_view(message, progress_value, color, current_step=None, total_steps=None):
    """Cria uma visualização de progresso com barra e status"""
    step_info = ""
    if current_step and total_steps:
        step_info = f" (Etapa {current_step}/{total_steps})"
    
    return dbc.Alert([
        html.H5([
            html.I(className="fas fa-spinner fa-spin me-2"),
            f"Treinamento em Andamento{step_info}"
        ]),
        html.P(message),
        html.Hr(),
        
        # Barra de progresso
        dbc.Progress(
            value=progress_value,
            striped=True,
            animated=True,
            color=color,
            style={"height": "20px", "margin-bottom": "15px"}
        ),
        
        html.Div([
            html.Strong(f"Progresso: {progress_value}%"),
            html.Br(),
            html.Small("⏳ Aguarde enquanto o modelo está sendo treinado...")
        ])
    ], color=color)

def _create_success_view(metricas, message, timestamp):
    """Cria visualização de sucesso com métricas detalhadas"""
    return [
        dbc.Alert([
            html.H5([
                html.I(className="fas fa-check-circle me-2"),
                "Treinamento Concluído com Sucesso!"
            ]),
            html.P(message)
        ], color="success"),
        
        # Barra de progresso completa
        dbc.Progress(
            value=100,
            striped=False,
            color="success",
            style={"height": "20px", "margin-bottom": "20px"}
        ),
        
        # Card com métricas
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-line me-2"),
                "📊 Métricas do Modelo Treinado"
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-database text-primary me-2"),
                            html.Strong("Amostras de Treino:"),
                            html.Br(),
                            html.H4(f"{metricas.get('num_samples', 'N/A')}", className="text-primary")
                        ], className="text-center")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-brain text-info me-2"),
                            html.Strong("Features Utilizadas:"),
                            html.Br(),
                            html.H4(f"{metricas.get('num_features', 'N/A')}", className="text-info")
                        ], className="text-center")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-chart-bar text-success me-2"),
                            html.Strong("Qualidade (AUC):"),
                            html.Br(),
                            html.H4(f"{metricas.get('cv_auc_mean', 0):.3f}", className="text-success") if 'cv_auc_mean' in metricas else html.H4("Heurístico", className="text-warning")
                        ], className="text-center")
                    ], width=4)
                ]),
                
                html.Hr(),
                
                # Detalhes técnicos
                html.Div([
                    html.H6("🔧 Detalhes Técnicos:"),
                    dbc.Row([
                        dbc.Col([
                            html.Small([
                                html.Strong("Validação Cruzada: "),
                                f"{metricas.get('cv_auc_mean', 0):.3f} ± {metricas.get('cv_auc_std', 0):.3f}"
                            ]) if 'cv_auc_mean' in metricas else html.Small("Modelo heurístico baseado em regras de negócio")
                        ], width=6),
                        dbc.Col([
                            html.Small([
                                html.Strong("Timestamp: "),
                                timestamp
                            ])
                        ], width=6)
                    ])
                ])
            ])
        ]),
        
        html.Hr(),
        dbc.Alert([
            html.I(className="fas fa-lightbulb me-2"),
            "O modelo está pronto! Agora você pode gerar sugestões mais precisas usando os filtros acima."
        ], color="info")
    ]

def _create_error_view(message, timestamp):
    """Cria visualização de erro"""
    return dbc.Alert([
        html.H5([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Erro no Treinamento"
        ]),
        html.P(message),
        html.Hr(),
        html.Small(f"Timestamp: {timestamp}"),
        html.Br(),
        html.Small("💡 Verifique se há dados suficientes no banco de dados e tente novamente.")
    ], color="danger")

@callback(
    [Output('dropdown-cliente-suggestions', 'options'),
     Output('dropdown-cliente-suggestions', 'value')],
    [Input('url', 'pathname')]
)
def populate_cliente_dropdown(pathname):
    """Popula dropdown de clientes com busca aprimorada por código e nome"""
    if pathname != '/app/purchase-suggestions':
        return no_update, no_update
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        if vendas_df.empty:
            return [], []
        
        # Combina código e nome do cliente para busca
        clientes_unique = vendas_df[['cod_cliente', 'cliente']].dropna().drop_duplicates()
        
        # Cria opções com formato "código - nome" para facilitar busca
        options = []
        for _, row in clientes_unique.iterrows():
            cod_cliente = str(row['cod_cliente'])
            nome_cliente = str(row['cliente'])
            
            # Formato: "123456 - CLIENTE EXEMPLO LTDA"
            label = f"{cod_cliente} - {nome_cliente}"
            
            options.append({
                "label": label,
                "value": cod_cliente
            })
        
        # Ordena por código do cliente
        options = sorted(options, key=lambda x: x['value'])
        
        logger.info(f"✅ {len(options)} clientes carregados para dropdown")
        return options, []  # Valor vazio para multi-seleção
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar clientes: {e}")
        return [], []

@callback(
    Output('store-hierarchy-data', 'data'),
    [Input('url', 'pathname')]
)
def load_hierarchy_data(pathname):
    """Carrega dados de hierarquia de produtos"""
    if pathname != '/app/purchase-suggestions':
        return no_update
    
    try:
        # Carrega dados
        vendas_df, _, _ = load_all_data()
        
        if vendas_df.empty:
            return {}
        
        # Extrai hierarquias únicas
        hierarchy_data = {}
        
        for level in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
            if level in vendas_df.columns:
                unique_values = vendas_df[level].dropna().unique().tolist()
                unique_values.sort()
                
                hierarchy_data[level] = [
                    {"label": val, "value": val} for val in unique_values
                ]
            else:
                hierarchy_data[level] = []
        
        logger.info(f"✅ Dados de hierarquia carregados: {len(hierarchy_data)} níveis")
        return hierarchy_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar hierarquia: {e}")
        return {}

@callback(
    Output('dropdown-hierarchy-container', 'children'),
    [Input('tabs-hierarchy', 'value'),
     Input('store-hierarchy-data', 'data')]
)
def update_hierarchy_dropdown(selected_tab, hierarchy_data):
    """Atualiza o dropdown de hierarquia baseado na aba selecionada"""
    if not hierarchy_data:
        return html.Div("Carregando dados de hierarquia...", className="text-muted")
    
    # Mapeia aba para coluna
    tab_mapping = {
        'tab-hier1': 'hier_produto_1',
        'tab-hier2': 'hier_produto_2', 
        'tab-hier3': 'hier_produto_3'
    }
    
    column = tab_mapping.get(selected_tab, 'hier_produto_1')
    options = hierarchy_data.get(column, [])
    
    if not options:
        return html.Div(f"Nenhum dado disponível para {column}", className="text-muted")
    
    return dcc.Dropdown(
        id="dropdown-hierarchy-filter",
        options=options,
        multi=True,
        placeholder=f"Selecione categorias de {column.replace('_', ' ').title()}...",
        searchable=True,
        clearable=True,
        style={"fontSize": "14px"}
    )

@app.callback(
    [Output('store-suggestions-data', 'data'),
     Output('loading-output-suggestions', 'children')],
    [Input('btn-apply-filters-suggestions', 'n_clicks'),
     Input('btn-refresh-suggestions', 'n_clicks')],
    [State('dropdown-cliente-suggestions', 'value'),
     State('dropdown-periodo-suggestions', 'value'),
     State('dropdown-abc-suggestions', 'value'),
     State('dropdown-xyz-suggestions', 'value'),
     State('input-top-n-suggestions', 'value'),
     State('tabs-hierarchy', 'value'),
     State('dropdown-hierarchy-filter', 'value')],
    prevent_initial_call=True
)
def generate_suggestions(btn_apply, btn_refresh, cliente_filter, periodo_meses, 
                        abc_filter, xyz_filter, top_n, selected_hierarchy_tab, hierarchy_filter):
    """
    Gera sugestões inteligentes baseadas nos filtros aplicados incluindo hierarquia de produtos
    """
    print(f"🔄 GENERATE_SUGGESTIONS chamado - btn_apply: {btn_apply}, btn_refresh: {btn_refresh}")
    print(f"📊 Filtros recebidos - Hierarquia: {selected_hierarchy_tab}, Valores: {hierarchy_filter}")
    
    if not any([btn_apply, btn_refresh]):
        print("❌ Nenhum botão foi clicado - retornando no_update")
        return no_update, no_update
    
    try:
        print(f"� CALLBACK EXECUTADO! Iniciando geração de sugestões...")
        print(f"�📋 Filtros recebidos:")
        print(f"   - Cliente: {cliente_filter} (tipo: {type(cliente_filter)})")
        print(f"   - Período: {periodo_meses} meses")
        print(f"   - ABC: {abc_filter}")
        print(f"   - XYZ: {xyz_filter}")
        print(f"   - Top N: {top_n}")
        
        logger.info("🔄 Gerando novas sugestões...")
        
        # Carrega dados
        print("📊 Carregando dados...")
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        print(f"✅ Dados carregados - Vendas: {len(vendas_df)}, Cotações: {len(cotacoes_df)}, Produtos Cotados: {len(produtos_cotados_df)}")

        if vendas_df.empty:
            print("❌ ERRO: Dados de vendas vazios!")
            return {}, "❌ Sem dados de vendas disponíveis"
        
        # Filtra período
        if periodo_meses:
            cutoff_date = datetime.now() - timedelta(days=periodo_meses * 30)
            vendas_filtrada = vendas_df[
                pd.to_datetime(vendas_df['data_faturamento'], errors='coerce') >= cutoff_date
            ].copy()
            print(f"🔍 Filtro período aplicado: {len(vendas_df)} → {len(vendas_filtrada)} registros")
        else:
            vendas_filtrada = vendas_df.copy()
            print(f"📅 Sem filtro de período - usando todos os dados: {len(vendas_filtrada)} registros")
        
        # Filtra clientes (agora suporta multi-seleção)
        if cliente_filter and len(cliente_filter) > 0:
            # Se é lista, filtra por múltiplos clientes
            if isinstance(cliente_filter, list):
                vendas_filtrada = vendas_filtrada[vendas_filtrada['cod_cliente'].isin(cliente_filter)]
                print(f"👥 Filtro múltiplos clientes aplicado: {cliente_filter} → {len(vendas_filtrada)} registros")
            else:
                # Compatibilidade com seleção única
                vendas_filtrada = vendas_filtrada[vendas_filtrada['cod_cliente'] == cliente_filter]
                print(f"👤 Filtro cliente único aplicado: {cliente_filter} → {len(vendas_filtrada)} registros")
        else:
            print(f"👥 Sem filtro de cliente - usando todos: {len(vendas_filtrada)} registros")
        
        # Para ML, gera sugestões agregadas se múltiplos clientes
        if isinstance(cliente_filter, list) and len(cliente_filter) > 1:
            # Multi-cliente: gera sugestões agregadas
            cliente_param = None  # Análise agregada
            print(f"🔄 Modo agregado para {len(cliente_filter)} clientes")
        elif isinstance(cliente_filter, list) and len(cliente_filter) == 1:
            # Um cliente selecionado: análise específica
            cliente_param = cliente_filter[0]
            print(f"👤 Modo específico para cliente: {cliente_param}")
        else:
            # Sem seleção ou valor único: usa como está
            cliente_param = cliente_filter if cliente_filter and len(cliente_filter) > 0 else None
            print(f"🔄 Modo padrão - cliente: {cliente_param if cliente_param else 'TODOS'}")        # Gera sugestões usando o motor ML
        print("🎯 Gerando sugestões com ML...")
        df_sugestoes = purchase_recommender.generate_purchase_suggestions(
            vendas_filtrada,
            cotacoes_df,
            produtos_cotados_df,
            cliente_filter=cliente_param,
            top_n=top_n or 20
        )
        print(f"✅ Sugestões geradas: {len(df_sugestoes)} registros")
        
        if df_sugestoes.empty:
            return {}, "⚠️ Nenhuma sugestão pôde ser gerada com os filtros aplicados"
        
        # Aplica filtros ABC-XYZ
        if abc_filter != "ALL":
            df_sugestoes = df_sugestoes[df_sugestoes['classificacao_abc'] == abc_filter]
        
        if xyz_filter != "ALL":
            df_sugestoes = df_sugestoes[df_sugestoes['classificacao_xyz'] == xyz_filter]
        
        # Aplica filtro de hierarquia de produtos
        if hierarchy_filter and len(hierarchy_filter) > 0:
            # Mapeia a aba selecionada para a coluna correspondente
            tab_mapping = {
                'tab-hier1': 'hier_produto_1',
                'tab-hier2': 'hier_produto_2', 
                'tab-hier3': 'hier_produto_3'
            }
            
            hierarchy_column = tab_mapping.get(selected_hierarchy_tab, 'hier_produto_1')
            
            # Verifica se a coluna existe no dataframe de sugestões
            if hierarchy_column in df_sugestoes.columns:
                df_sugestoes = df_sugestoes[df_sugestoes[hierarchy_column].isin(hierarchy_filter)]
                print(f"🏷️ Filtro hierarquia aplicado ({hierarchy_column}): {hierarchy_filter} → {len(df_sugestoes)} registros")
            else:
                # Se não existe na sugestão, filtra nos dados originais
                print(f"⚠️ Coluna {hierarchy_column} não encontrada em sugestões. Filtrando dados originais...")
                vendas_filtrada = vendas_filtrada[vendas_filtrada[hierarchy_column].isin(hierarchy_filter)]
                
                # Regenera sugestões com dados filtrados
                df_sugestoes = purchase_recommender.generate_purchase_suggestions(
                    vendas_filtrada,
                    cotacoes_df,
                    produtos_cotados_df,
                    cliente_filter=cliente_param,
                    top_n=top_n or 20
                )
                print(f"🔄 Sugestões regeneradas com filtro hierarquia: {len(df_sugestoes)} registros")
        
        # Calcula probabilidades de recompra
        df_probabilidades = purchase_recommender.predict_repurchase_probability(
            vendas_filtrada,
            cotacoes_df,
            cod_cliente=cliente_param
        )
        
        # Merge com probabilidades
        if not df_probabilidades.empty:
            merge_cols = ['material']
            if cliente_param:
                merge_cols.append('cod_cliente')
            
            df_sugestoes = df_sugestoes.merge(
                df_probabilidades[merge_cols + ['prob_recompra_ml', 'categoria_prob']],
                on=merge_cols,
                how='left'
            )
            df_sugestoes['prob_recompra'] = df_sugestoes['prob_recompra_ml'].fillna(0.5)
            df_sugestoes['categoria_probabilidade'] = df_sugestoes['categoria_prob'].fillna('Média')
        else:
            df_sugestoes['prob_recompra'] = 0.5
            df_sugestoes['categoria_probabilidade'] = 'Média'
        
        # Aplica filtro Top N no resultado final
        if top_n and top_n > 0:
            df_sugestoes = df_sugestoes.head(top_n)
            print(f"🔢 Aplicado filtro Top N: limitado a {top_n} sugestões")
        
        # Converte para dict para store
        sugestoes_data = df_sugestoes.to_dict('records')
        
        print(f"📦 RETORNO DO CALLBACK:")
        print(f"   - sugestoes_data: {len(sugestoes_data)} registros")
        print(f"   - message: ✅ {len(sugestoes_data)} sugestões geradas com sucesso")
        if sugestoes_data:
            print(f"   - Exemplo: Material {sugestoes_data[0].get('material', 'N/A')}, Qtd: {sugestoes_data[0].get('quantidade_sugerida', 'N/A')}")
        
        logger.info(f"✅ {len(sugestoes_data)} sugestões geradas")
        return sugestoes_data, f"✅ {len(sugestoes_data)} sugestões geradas com sucesso"
        
    except Exception as e:
        print(f"❌ ERRO NO CALLBACK: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Erro ao gerar sugestões: {e}")
        return {}, f"❌ Erro: {str(e)}"

@callback(
    [Output('kpi-total-suggestions', 'children'),
     Output('kpi-valor-total', 'children'),
     Output('kpi-confianca-media', 'children'),
     Output('kpi-classe-a', 'children'),
     Output('kpi-feedback-positivo', 'children'),
     Output('kpi-modelo-status', 'children')],
    [Input('store-suggestions-data', 'data')]
)
def update_kpis(suggestions_data):
    """Atualiza KPIs da página"""
    if not suggestions_data:
        return "0", "R$ 0", "0%", "0", "0%", "⚠️"
    
    try:
        df = pd.DataFrame(suggestions_data)
        
        # Total de sugestões
        total_suggestions = len(df)
        
        # Valor total sugerido (estimativa)
        if 'valor_estimado' in df.columns:
            # Usa a coluna valor_estimado se disponível
            valor_total = df['valor_estimado'].sum()
            valor_total_str = f"R$ {valor_total:,.0f}".replace(',', '.')
        elif 'valor_medio_mensal' in df.columns and 'quantidade_sugerida' in df.columns:
            # Fallback: estima valor baseado na quantidade sugerida e preço médio
            df['valor_estimado'] = df['quantidade_sugerida'] * (df['valor_medio_mensal'] / df['demanda_media_mensal'].replace(0, 1))
            valor_total = df['valor_estimado'].sum()
            valor_total_str = f"R$ {valor_total:,.0f}".replace(',', '.')
        else:
            valor_total_str = "N/A"
        
        # Confiança média
        confianca_media = df['confianca'].mean() if 'confianca' in df.columns else 0
        confianca_str = f"{confianca_media:.0f}%"
        
        # Produtos classe A
        classe_a = len(df[df['classificacao_abc'] == 'A']) if 'classificacao_abc' in df.columns else 0
        
        # Feedback stats (busca do banco)
        try:
            feedback_stats = purchase_recommender.get_feedback_stats()
            taxa_aprovacao = feedback_stats.get('taxa_aceitacao', 0) * 100
            feedback_str = f"{taxa_aprovacao:.0f}%"
        except:
            feedback_str = "N/A"
        
        # Status do modelo ML
        if purchase_recommender.is_trained:
            modelo_status = "🤖 ML"
        else:
            modelo_status = "📊 Heurístico"
        
        return (
            f"{total_suggestions:,}".replace(',', '.'),
            valor_total_str,
            confianca_str,
            f"{classe_a}",
            feedback_str,
            modelo_status
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular KPIs: {e}")
        return "Erro", "Erro", "Erro", "Erro", "Erro", "❌"

@callback(
    Output('div-suggestions-table', 'children'),
    [Input('store-suggestions-data', 'data'),
     Input('switch-show-details', 'value')]
)
def update_suggestions_table(suggestions_data, show_details):
    """Atualiza tabela de sugestões"""
    if not suggestions_data:
        return dbc.Alert("Aplique os filtros para gerar sugestões", color="info")
    
    try:
        df = pd.DataFrame(suggestions_data)
        if df.empty:
            return dbc.Alert("Nenhuma sugestão encontrada", color="warning")
        
        table_component = create_suggestions_table(df, show_details)
        
        # Garante que retorna um componente válido
        if table_component is None:
            return dbc.Alert("Erro ao gerar tabela", color="danger")
            
        return table_component
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabela: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro ao criar tabela: {str(e)}", color="danger")

@callback(
    Output('graph-abc-xyz-distribution', 'figure'),
    [Input('store-suggestions-data', 'data')]
)
def update_abc_xyz_chart(suggestions_data):
    """Atualiza gráfico de distribuição ABC-XYZ"""
    if not suggestions_data:
        return {}
    
    try:
        df = pd.DataFrame(suggestions_data)
        return create_abc_xyz_chart(df)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar gráfico ABC-XYZ: {e}")
        return {}

@callback(
    Output('graph-probability-distribution', 'figure'),
    [Input('store-suggestions-data', 'data')]
)
def update_probability_chart(suggestions_data):
    """Atualiza gráfico de distribuição de probabilidades"""
    if not suggestions_data:
        return {}
    
    try:
        df = pd.DataFrame(suggestions_data)
        return create_probability_chart(df)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar gráfico probabilidades: {e}")
        return {}

@callback(
    [Output('toast-feedback', 'is_open'),
     Output('toast-feedback', 'children'),
     Output('toast-feedback', 'icon')],
    [Input('table-suggestions', 'active_cell')],
    [State('table-suggestions', 'data'),
     State('table-suggestions', 'active_cell')]
)
def handle_table_clicks(active_cell, table_data, cell_state):
    """
    Manipula cliques na tabela para feedback e detalhes
    """
    if not active_cell or not table_data:
        return no_update, no_update, no_update
    
    try:
        row_idx = active_cell['row']
        col_id = active_cell['column_id']
        
        # Só processa cliques na coluna de ações
        if col_id != 'acoes':
            return no_update, no_update, no_update
        
        row_data = table_data[row_idx]
        material = row_data['material']
        cod_cliente = row_data.get('cod_cliente', row_data.get('cliente', 'N/A'))
        
        # Por simplicidade, registra feedback positivo
        # Em implementação real, detectaria qual botão foi clicado
        sucesso = purchase_recommender.save_feedback(
            material=material,
            cod_cliente=cod_cliente,
            feedback_type='positivo',
            motivo='Clique na tabela',
            quantidade_sugerida=row_data.get('quantidade_sugerida', 0),
            usuario='sistema'
        )
        
        if sucesso:
            return True, f"Feedback registrado para {material}", "success"
        else:
            return True, "Erro ao registrar feedback", "danger"
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar clique: {e}")
        return True, f"Erro: {str(e)}", "danger"

@callback(
    Output('btn-close-modal', 'n_clicks'),
    [Input('btn-close-modal', 'n_clicks')]
)
def close_modal(n_clicks):
    """Fecha modal de detalhes"""
    return 0

@callback(
    [Output('modal-training', 'is_open')],
    [Input('btn-train-ml', 'n_clicks'),
     Input('btn-close-training-modal', 'n_clicks')],
    [State('modal-training', 'is_open')]
)
def toggle_training_modal(btn_train, btn_close, is_open):
    """Abre/fecha modal de treinamento"""
    if btn_train:
        return [True]  # Abre modal
    elif btn_close:
        return [False]  # Fecha modal
    return [is_open]

@callback(
    [Output('store-training-status', 'data'),
     Output('interval-training-progress', 'disabled'),
     Output('btn-start-training', 'disabled'),
     Output('btn-start-training', 'children')],
    [Input('btn-start-training', 'n_clicks')],
    [State('store-training-status', 'data')]
)
def start_ml_training(n_clicks, current_status):
    """Inicia o treinamento do modelo ML com progresso em tempo real"""
    if not n_clicks:
        return no_update, True, False, [html.I(className="fas fa-play me-1"), "Iniciar Treinamento"]
    
    try:
        print("🤖 INICIANDO TREINAMENTO ML - n_clicks:", n_clicks)
        logger.info("🤖 Iniciando treinamento do modelo ML...")
        
        # Habilita o interval para mostrar progresso IMEDIATAMENTE
        return {
            'status': 'iniciando',
            'message': 'Iniciando treinamento do modelo...',
            'timestamp': datetime.now().isoformat(),
            'step': 1,
            'total_steps': 5
        }, False, True, [html.I(className="fas fa-spinner fa-spin me-1"), "Treinando..."]
        
    except Exception as e:
        print(f"❌ ERRO GERAL no treinamento: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        logger.error(f"❌ Erro no treinamento: {e}")
        return {
            'status': 'erro',
            'message': f"Erro inesperado: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }, True, False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro"]


# Proteção global contra múltiplas execuções
training_lock = False

@callback(
    Output('store-training-status', 'data', allow_duplicate=True),
    [Input('interval-training-progress', 'n_intervals')],
    [State('store-training-status', 'data')],
    prevent_initial_call=True
)
def execute_training_steps(n_intervals, training_status):
    """Executa as etapas do treinamento uma por vez para mostrar progresso"""
    global training_lock
    
    if not training_status or training_status.get('status') in ['sucesso', 'erro']:
        training_lock = False
        return no_update
    
    # Previne execuções múltiplas simultâneas na etapa crítica
    if training_lock and training_status.get('step', 1) >= 4:
        logger.warning("⚠️ Treinamento já em execução - ignorando callback duplicado")
        return no_update
    
    try:
        current_step = training_status.get('step', 1)
        
        # Etapa 1: Carregamento de dados
        if current_step == 1:
            return {
                'status': 'carregando_dados',
                'message': 'Carregando dados do banco...',
                'timestamp': datetime.now().isoformat(),
                'step': 2,
                'total_steps': 5
            }
        
        # Etapa 2: Validação dos dados
        elif current_step == 2:
            vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
            
            if vendas_df.empty:
                return {
                    'status': 'erro',
                    'message': 'Sem dados de vendas para treinar o modelo',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'status': 'extraindo_features',
                'message': f'Dados carregados: {len(vendas_df)} vendas. Extraindo features...',
                'timestamp': datetime.now().isoformat(),
                'step': 3,
                'total_steps': 5,
                'dados': {
                    'vendas_count': len(vendas_df),
                    'cotacoes_count': len(cotacoes_df),
                    'produtos_count': len(produtos_cotados_df)
                }
            }
        
        # Etapa 3: Treinamento do modelo
        elif current_step == 3:
            vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
            
            return {
                'status': 'treinando',
                'message': 'Executando algoritmos de ML...',
                'timestamp': datetime.now().isoformat(),
                'step': 4,
                'total_steps': 5
            }
        
        # Etapa 4: Execução do treinamento
        elif current_step == 4:
            # Ativa o lock para prevenir múltiplas execuções
            training_lock = True
            
            try:
                vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
                
                # Executa o treinamento real
                resultado = purchase_recommender.train_repurchase_model(
                    vendas_df, cotacoes_df, produtos_cotados_df, retrain=True
                )
                
                training_lock = False  # Libera o lock
                
                if 'erro' in resultado:
                    return {
                        'status': 'erro',
                        'message': f"Erro no treinamento: {resultado['erro']}",
                        'timestamp': datetime.now().isoformat()
                    }
                
                return {
                    'status': 'validando',
                    'message': 'Validando resultados e calculando métricas...',
                    'timestamp': datetime.now().isoformat(),
                    'step': 5,
                    'total_steps': 5,
                    'resultado_temp': resultado
                }
            except Exception as e:
                training_lock = False  # Libera o lock em caso de erro
                raise e
        
        # Etapa 5: Finalização
        elif current_step == 5:
            resultado = training_status.get('resultado_temp', {})
            
            return {
                'status': 'sucesso',
                'message': 'Modelo treinado com sucesso!',
                'metricas': resultado,
                'timestamp': datetime.now().isoformat(),
                'step': 5,
                'total_steps': 5
            }
        
        return no_update
        
    except Exception as e:
        logger.error(f"❌ Erro na execução do treinamento: {e}")
        return {
            'status': 'erro',
            'message': f"Erro durante treinamento: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }
        print(f"❌ ERRO GERAL no treinamento: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        logger.error(f"❌ Erro no treinamento: {e}")
        return {
            'status': 'erro',
            'message': f"Erro inesperado: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }, True, False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro"]

@callback(
    Output('modal-body-training-progress', 'children'),
    [Input('store-training-status', 'data'),
     Input('interval-training-progress', 'n_intervals')]
)
def update_training_progress(training_status, n_intervals):
    """Atualiza o progresso do treinamento com indicadores visuais avançados"""
    if not training_status:
        return dbc.Alert([
            html.H5([
                html.I(className="fas fa-info-circle me-2"),
                "Treinamento do Modelo ML"
            ]),
            html.P("Este processo irá treinar o modelo de Machine Learning com os dados disponíveis no banco de dados."),
            html.Hr(),
            
            # Seção de dados disponíveis
            html.H6("📊 Dados Disponíveis:"),
            html.Ul([
                html.Li("Vendas históricas para análise de padrões"),
                html.Li("Cotações para enriquecer o modelo"),
                html.Li("Features de recência, frequência e sazonalidade")
            ]),
            
            # Seção de benefícios
            html.H6("🎯 Benefícios do Treinamento:"),
            html.Ul([
                html.Li("Sugestões mais precisas e personalizadas"),
                html.Li("Melhor identificação de oportunidades"),
                html.Li("Predições baseadas em dados reais")
            ]),
            
            # Progresso esperado
            html.Hr(),
            html.H6("⏱️ Etapas do Processo:"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.I(className="fas fa-database me-2"),
                    "1. Carregamento e validação dos dados"
                ]),
                dbc.ListGroupItem([
                    html.I(className="fas fa-cog me-2"),
                    "2. Extração de features ML"
                ]),
                dbc.ListGroupItem([
                    html.I(className="fas fa-brain me-2"),
                    "3. Treinamento do modelo"
                ]),
                dbc.ListGroupItem([
                    html.I(className="fas fa-chart-line me-2"),
                    "4. Validação e métricas"
                ])
            ], flush=True)
        ], color="info")
    
    status = training_status.get('status', '')
    message = training_status.get('message', '')
    timestamp = training_status.get('timestamp', '')
    current_step = training_status.get('step', 1)
    total_steps = training_status.get('total_steps', 5)
    
    # Calcula progresso baseado na etapa atual
    progress_percentage = (current_step / total_steps) * 100
    
    # Status de progresso em tempo real
    if status == 'iniciando':
        return _create_progress_view("Iniciando treinamento...", 10, "info", current_step, total_steps)
    elif status == 'carregando_dados':
        return _create_progress_view("Carregando dados do banco...", 25, "info", current_step, total_steps)
    elif status == 'extraindo_features':
        dados_info = training_status.get('dados', {})
        message_with_data = f"Dados carregados: {dados_info.get('vendas_count', 0)} vendas. Extraindo features..."
        return _create_progress_view(message_with_data, 50, "info", current_step, total_steps)
    elif status == 'treinando':
        return _create_progress_view("Executando algoritmos de ML...", 75, "warning", current_step, total_steps)
    elif status == 'validando':
        return _create_progress_view("Validando resultados...", 90, "warning", current_step, total_steps)
    elif status == 'sucesso':
        metricas = training_status.get('metricas', {})
        return _create_success_view(metricas, message, timestamp)
        
    elif status == 'erro':
        return _create_error_view(message, timestamp)
    
    # Estado padrão
    return dbc.Alert([
        html.H5([
            html.I(className="fas fa-clock me-2"),
            "Preparando Treinamento..."
        ]),
        html.P("Aguardando início do processo de treinamento."),
        dbc.Progress(value=0, color="secondary", style={"height": "10px"})
    ], color="secondary")

# Callbacks para exportação
@callback(
    [Output('btn-export-excel', 'disabled'),
     Output('btn-export-excel', 'children'),
     Output('alert-export-excel', 'children'),
     Output('alert-export-excel', 'is_open')],
    [Input('btn-export-excel', 'n_clicks')],
    [State('store-suggestions-data', 'data')]
)
def export_excel(n_clicks, suggestions_data):
    """Exporta sugestões para Excel com feedback de localização"""
    if not n_clicks:
        return False, [html.I(className="fas fa-download me-1"), "Exportar Excel"], "", False
    
    if not suggestions_data:
        return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Sem Dados"], dbc.Alert("❌ Nenhum dado disponível para exportação", color="warning"), True
    
    try:
        logger.info("📊 Iniciando exportação Excel...")
        
        # Cria exportação
        filepath = _create_excel_export(suggestions_data)
        
        if filepath:
            # Extrai apenas o nome do arquivo para exibição
            filename = filepath.split("\\")[-1]
            alert_message = dbc.Alert([
                html.H6("✅ Excel exportado com sucesso!", className="alert-heading"),
                html.P(f"📁 Localização: pasta Downloads"),
                html.P(f"📄 Arquivo: {filename}"),
                html.Hr(),
                html.P("O arquivo foi salvo na pasta Downloads do seu computador.", className="mb-0")
            ], color="success")
            
            return False, [html.I(className="fas fa-check me-1"), "Excel Gerado!"], alert_message, True
        else:
            return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro na Exportação"], dbc.Alert("❌ Erro ao criar arquivo Excel", color="danger"), True
        
    except Exception as e:
        logger.error(f"❌ Erro na exportação Excel: {e}")
        return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro na Exportação"], dbc.Alert(f"❌ Erro: {str(e)}", color="danger"), True

def _create_excel_export(suggestions_data):
    """Cria arquivo Excel completo com sugestões e análises"""
    try:
        import pandas as pd
        from datetime import datetime
        import os
        
        # Cria DataFrame das sugestões
        df = pd.DataFrame(suggestions_data)
        
        # Define nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Sugestoes_Compra_ML_{timestamp}.xlsx"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads_path, filename)
        
        # Cria arquivo Excel com múltiplas abas
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Aba 1: Sugestões Principais
            df_export = df.copy()
            
            # Garante que valor_estimado existe
            if 'valor_estimado' not in df_export.columns:
                if 'valor_medio_mensal' in df_export.columns and 'quantidade_sugerida' in df_export.columns:
                    df_export['valor_estimado'] = df_export['quantidade_sugerida'] * (df_export['valor_medio_mensal'] / df_export['demanda_media_mensal'].replace(0, 1))
                else:
                    df_export['valor_estimado'] = 0
            
            # Formata colunas para Excel
            if 'valor_estimado' in df_export.columns:
                df_export['valor_estimado'] = df_export['valor_estimado'].round(2)
            if 'confianca' in df_export.columns:
                df_export['confianca'] = df_export['confianca'].round(1)
            
            # Ordena por score ou valor
            if 'score_final' in df_export.columns:
                df_export = df_export.sort_values('score_final', ascending=False)
            elif 'valor_estimado' in df_export.columns:
                df_export = df_export.sort_values('valor_estimado', ascending=False)
            
            df_export.to_excel(writer, sheet_name='Sugestões de Compra', index=False)
            
            # Aba 2: Resumo Executivo
            resumo_data = _create_summary_data(df)
            resumo_df = pd.DataFrame([resumo_data])
            resumo_df.to_excel(writer, sheet_name='Resumo Executivo', index=False)
            
            # Aba 3: Análise ABC-XYZ
            if 'classificacao_abc' in df.columns and 'classificacao_xyz' in df.columns:
                abc_xyz_analysis = _create_abc_xyz_analysis(df)
                abc_xyz_analysis.to_excel(writer, sheet_name='Análise ABC-XYZ', index=False)
            
            # Aba 4: Top Produtos por Valor
            if 'valor_estimado' in df.columns:
                top_produtos = df.nlargest(10, 'valor_estimado')[
                    ['material', 'produto', 'valor_estimado', 'quantidade_sugerida', 'confianca']
                ]
                top_produtos.to_excel(writer, sheet_name='Top 10 por Valor', index=False)
        
        logger.info(f"✅ Excel exportado: {filepath}")
        return filepath
        
    except ImportError:
        logger.error("❌ Biblioteca openpyxl não encontrada. Instale com: pip install openpyxl")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao criar Excel: {e}")
        return None

def _create_summary_data(df):
    """Cria dados de resumo executivo com tratamento robusto de erros"""
    try:
        from datetime import datetime
        
        # Validação básica
        if df is None or df.empty:
            return {
                'Data_Exportacao': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'Total_Produtos': 0,
                'Valor_Total_Estimado': 'R$ 0,00',
                'Confianca_Media': '0%',
                'Produtos_Classe_A': 0,
                'Produtos_Classe_B': 0,
                'Produtos_Classe_C': 0,
                'Percentual_Classe_A': '0%'
            }
        
        total_produtos = len(df)
        
        # Valor total com tratamento seguro
        try:
            if 'valor_estimado' in df.columns:
                valor_total = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0).sum()
            else:
                valor_total = 0
        except Exception:
            valor_total = 0
        
        # Confiança média com tratamento seguro
        try:
            if 'confianca' in df.columns:
                confianca_media = pd.to_numeric(df['confianca'], errors='coerce').fillna(0).mean()
            else:
                confianca_media = 0
        except Exception:
            confianca_media = 0
        
        # Análise por classe ABC com tratamento seguro
        try:
            if 'classificacao_abc' in df.columns:
                classe_a = len(df[df['classificacao_abc'].fillna('') == 'A'])
                classe_b = len(df[df['classificacao_abc'].fillna('') == 'B'])
                classe_c = len(df[df['classificacao_abc'].fillna('') == 'C'])
            else:
                classe_a = classe_b = classe_c = 0
        except Exception:
            classe_a = classe_b = classe_c = 0
        
        return {
            'Data_Exportacao': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'Total_Produtos': total_produtos,
            'Valor_Total_Estimado': f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Confianca_Media': f"{confianca_media:.1f}%",
            'Produtos_Classe_A': classe_a,
            'Produtos_Classe_B': classe_b,
            'Produtos_Classe_C': classe_c,
            'Percentual_Classe_A': f"{(classe_a/total_produtos*100):.1f}%" if total_produtos > 0 else "0%"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar resumo: {e}")
        from datetime import datetime
        return {
            'Data_Exportacao': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'Erro': f"Erro na geração do resumo: {str(e)}",
            'Total_Produtos': 'N/A',
            'Valor_Total_Estimado': 'N/A',
            'Confianca_Media': 'N/A',
            'Produtos_Classe_A': 'N/A',
            'Produtos_Classe_B': 'N/A',
            'Produtos_Classe_C': 'N/A',
            'Percentual_Classe_A': 'N/A'
        }

def _create_abc_xyz_analysis(df):
    """Cria análise detalhada ABC-XYZ"""
    try:
        # Combina classificações
        df['combinacao'] = df['classificacao_abc'] + df['classificacao_xyz']
        
        # Agrupa por combinação
        analysis = df.groupby('combinacao').agg({
            'material': 'count',
            'valor_estimado': ['sum', 'mean'],
            'quantidade_sugerida': 'sum',
            'confianca': 'mean'
        }).round(2)
        
        # Flatten column names
        analysis.columns = [
            'Quantidade_Produtos',
            'Valor_Total', 'Valor_Medio',
            'Quantidade_Total',
            'Confianca_Media'
        ]
        
        analysis = analysis.reset_index()
        analysis['Percentual'] = (analysis['Quantidade_Produtos'] / len(df) * 100).round(1)
        
        return analysis
        
    except Exception as e:
        logger.error(f"❌ Erro na análise ABC-XYZ: {e}")
        return pd.DataFrame({'Erro': [str(e)]})

@callback(
    [Output('btn-export-pdf', 'disabled'),
     Output('btn-export-pdf', 'children'),
     Output('alert-export-pdf', 'children'),
     Output('alert-export-pdf', 'is_open')],
    [Input('btn-export-pdf', 'n_clicks')],
    [State('store-suggestions-data', 'data')]
)
def export_pdf(n_clicks, suggestions_data):
    """Exporta relatório em PDF profissional com feedback de localização"""
    if not n_clicks:
        return False, [html.I(className="fas fa-file-pdf me-1"), "Relatório PDF"], "", False
    
    if not suggestions_data:
        return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Sem Dados"], dbc.Alert("❌ Nenhum dado disponível para exportação", color="warning"), True
    
    try:
        logger.info("📄 Iniciando geração PDF...")
        
        # Cria relatório PDF
        filepath = _create_pdf_report(suggestions_data)
        
        if filepath:
            # Extrai apenas o nome do arquivo para exibição
            filename = filepath.split("\\")[-1]
            alert_message = dbc.Alert([
                html.H6("✅ PDF gerado com sucesso!", className="alert-heading"),
                html.P(f"📁 Localização: pasta Downloads"),
                html.P(f"📄 Arquivo: {filename}"),
                html.Hr(),
                html.P("O arquivo foi salvo na pasta Downloads do seu computador.", className="mb-0")
            ], color="success")
            
            return False, [html.I(className="fas fa-check me-1"), "PDF Gerado!"], alert_message, True
        else:
            return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro na Geração"], dbc.Alert("❌ Erro ao criar arquivo PDF", color="danger"), True
        
    except Exception as e:
        logger.error(f"❌ Erro na geração PDF: {e}")
        return False, [html.I(className="fas fa-exclamation-triangle me-1"), "Erro na Geração"], dbc.Alert(f"❌ Erro: {str(e)}", color="danger"), True

def _create_pdf_report(suggestions_data):
    """Cria relatório PDF profissional"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from datetime import datetime
        import pandas as pd
        import os
        
        logger.info("📄 Iniciando criação do PDF...")
        
        # Valida dados de entrada
        if not suggestions_data:
            logger.error("❌ Dados de sugestões vazios")
            return None
            
        # Cria DataFrame das sugestões
        df = pd.DataFrame(suggestions_data)
        logger.info(f"📊 DataFrame criado com {len(df)} registros")
        
        # Define nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Relatorio_Sugestoes_ML_{timestamp}.pdf"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads_path, filename)
        
        logger.info(f"📁 Caminho do arquivo: {filepath}")
        
        # Verifica se o diretório existe
        if not os.path.exists(downloads_path):
            logger.error(f"❌ Diretório não existe: {downloads_path}")
            return None
        
        # Cria documento
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        logger.info("✅ Documento PDF inicializado")
        
        # Estilo customizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Título
        story.append(Paragraph("RELATÓRIO DE SUGESTÕES INTELIGENTES DE COMPRA", title_style))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        logger.info("✅ Título adicionado")
        
        # Resumo Executivo - com tratamento seguro
        try:
            resumo = _create_summary_data(df)
            story.append(Paragraph("RESUMO EXECUTIVO", styles['Heading2']))
            resumo_text = f"""
            • Total de Produtos: {resumo.get('Total_Produtos', 'N/A')}<br/>
            • Valor Total Estimado: {resumo.get('Valor_Total_Estimado', 'N/A')}<br/>
            • Confiança Média: {resumo.get('Confianca_Media', 'N/A')}<br/>
            • Produtos Classe A: {resumo.get('Produtos_Classe_A', 'N/A')}<br/>
            """
            story.append(Paragraph(resumo_text, styles['Normal']))
            story.append(Spacer(1, 20))
            logger.info("✅ Resumo executivo adicionado")
        except Exception as e:
            logger.warning(f"⚠️ Erro no resumo, continuando sem ele: {e}")
            story.append(Paragraph("RESUMO EXECUTIVO", styles['Heading2']))
            story.append(Paragraph("Dados de resumo não disponíveis", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Tabela de Sugestões (Top 15) - com validação
        try:
            story.append(Paragraph("TOP 15 SUGESTÕES DE COMPRA", styles['Heading2']))
            
            # Prepara dados da tabela com validação
            df_top = df.head(15)
            table_data = [['Material', 'Produto', 'Qtd', 'Valor Est.', 'ABC', 'Conf.']]
            
            for _, row in df_top.iterrows():
                # Trata valores com segurança
                material = str(row.get('material', 'N/A'))[:12]
                produto = str(row.get('produto', 'N/A'))[:25]
                
                # Quantidade
                try:
                    qtd = int(float(row.get('quantidade_sugerida', 0)))
                except (ValueError, TypeError):
                    qtd = 0
                
                # Valor estimado
                try:
                    valor = float(row.get('valor_estimado', 0))
                    valor_str = f"R$ {valor:,.0f}"
                except (ValueError, TypeError):
                    valor_str = "R$ 0"
                
                # Classificação ABC
                abc = str(row.get('classificacao_abc', 'N/A'))
                
                # Confiança
                try:
                    conf = float(row.get('confianca', 0))
                    conf_str = f"{conf:.0f}%"
                except (ValueError, TypeError):
                    conf_str = "0%"
                
                table_data.append([
                    material,
                    produto,
                    str(qtd),
                    valor_str,
                    abc,
                    conf_str
                ])
            
            logger.info(f"✅ Dados da tabela preparados: {len(table_data)-1} linhas")
            
            # Cria tabela
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
            logger.info("✅ Tabela adicionada")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na tabela, adicionando texto simples: {e}")
            story.append(Paragraph("TOP SUGESTÕES DE COMPRA", styles['Heading2']))
            story.append(Paragraph("Dados da tabela não disponíveis", styles['Normal']))
        
        # Constrói PDF
        logger.info("🔧 Construindo PDF...")
        doc.build(story)
        
        # Verifica se foi criado
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"✅ PDF gerado com sucesso: {filepath} ({file_size} bytes)")
            return filepath
        else:
            logger.error("❌ Arquivo PDF não foi criado")
            return None
        
    except ImportError as e:
        logger.error(f"❌ Biblioteca reportlab não encontrada: {e}")
        logger.info("💡 Instale com: pip install reportlab")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao criar PDF: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return None