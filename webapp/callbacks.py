import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output, State, callback_context, exceptions, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from flask import session
from datetime import datetime
from io import StringIO

from webapp import app

from utils import db, kpis, etl

def create_interactive_table(df, table_id="interactive-table"):
    """
    Cria uma tabela interativa usando Dash DataTable com funcionalidades avançadas
    """
    if df.empty:
        return dbc.Alert('Nenhum dado disponível.', color='warning')
    
    # Calcular limites dinâmicos para semáforo do % Não Comprado
    def calcular_limites_semaforo_nao_comprado(dataframe):
        if 'pct_nao_comprado' not in dataframe.columns or dataframe['pct_nao_comprado'].empty:
            return {'verde_max': 25, 'amarelo_max': 75}  # Valores padrão
        
        valores = dataframe['pct_nao_comprado'].dropna()
        if len(valores) == 0:
            return {'verde_max': 25, 'amarelo_max': 75}  # Valores padrão
        
        # Calcular percentis 25º e 75º
        p25 = valores.quantile(0.25)
        p75 = valores.quantile(0.75)
        
        return {
            'verde_max': p25,      # 0% a 25º percentil (melhores 25%)
            'amarelo_max': p75     # 25º a 75º percentil (50% intermediários)
        }
    
    # Calcular limites dinâmicos
    limites = calcular_limites_semaforo_nao_comprado(df)
    verde_max = limites['verde_max']
    amarelo_max = limites['amarelo_max']
    
    # Mapeamento de nomes de colunas para nomes mais amigáveis
    column_names = {
        'cod_cliente': 'Código Cliente',
        'cliente': 'Nome do Cliente',
        'ultima_compra': 'Última Compra',
        'total_comprado_valor': 'Valor Total Comprado (R$)',
        'total_comprado_qtd': 'Quantidade Total',
        'mix_produtos': 'Mix de Produtos',
        'unidades_negocio': 'Unidades de Negócio',
        'dias_sem_compra': 'Dias sem Compra',
        'total_cotado_qtd': 'Quantidade Cotada',
        'pct_mix_produtos': '% Mix Produtos',
        'pct_nao_comprado': '% Não Comprado'
    }
    
    # Configurar colunas para DataTable
    columns = []
    for col in df.columns:
        column_config = {
            "name": column_names.get(col, col.replace('_', ' ').title()),
            "id": col,
            "deletable": False,
            "renamable": False,
        }
        
        # Configurações específicas por tipo de dados
        if col in ['total_comprado_valor']:
            column_config.update({
                "type": "numeric",
                "format": {
                    "locale": {"decimal": ",", "group": "."},
                    "nully": "N/A",
                    "specifier": "$,.2f"
                }
            })
        elif col in ['pct_mix_produtos', 'pct_nao_comprado']:
            column_config.update({
                "type": "numeric",
                "format": {
                    "specifier": ".0f"  # Formato numérico sem casas decimais, pois já são percentuais (0-100)
                }
            })
        elif col in ['total_comprado_qtd', 'mix_produtos', 'unidades_negocio', 'total_cotado_qtd', 'dias_sem_compra']:
            column_config.update({
                "type": "numeric",
                "format": {
                    "specifier": ",.0f"
                }
            })
        elif col in ['ultima_compra']:
            column_config.update({
                "type": "datetime"
            })
        
        columns.append(column_config)
    
    # Preparar dados - converter datas para string se necessário
    data = df.copy()
    if 'ultima_compra' in data.columns:
        data['ultima_compra'] = pd.to_datetime(data['ultima_compra']).dt.strftime('%d/%m/%Y')
    
    # Criar DataTable
    data_table = dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data.to_dict('records'),
        
        # Funcionalidades interativas
        sort_action="native",  # Classificação
        sort_mode="multi",     # Classificação múltipla
        filter_action="native", # Filtros
        page_action="native",  # Paginação
        page_current=0,
        page_size=20,
        
        # Seleção
        row_selectable="multi",
        selected_rows=[],
        
        # Edição de colunas (arrastar e soltar)
        column_selectable="single",
        
        # Estilo
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%',
        },
        style_header={
            'backgroundColor': '#2C3E50',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'border': '1px solid #34495E'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'border': '1px solid #BDC3C7'
        },
        style_data={
            'backgroundColor': '#FFFFFF',
            'color': '#2C3E50',
        },
        style_data_conditional=[
            # Zebra striping
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#F8F9FA'
            },
            # Destaque para valores altos
            {
                'if': {
                    'filter_query': '{total_comprado_valor} > 1000000',
                    'column_id': 'total_comprado_valor'
                },
                'backgroundColor': '#E8F5E8',
                'color': '#27AE60',
                'fontWeight': 'bold'
            },
            # Destaque para clientes em período de atenção (90-365 dias) - linha inteira amarela
            {
                'if': {
                    'filter_query': '{dias_sem_compra} > 90 && {dias_sem_compra} <= 365'
                },
                'backgroundColor': '#FFF3CD',  # Amarelo claro
                'color': '#2C3E50'            # Texto normal
            },
            # Destaque para clientes inativos - linha inteira com fundo vermelho claro
            {
                'if': {
                    'filter_query': '{dias_sem_compra} > 365'
                },
                'backgroundColor': '#FADBD8',
                'color': '#2C3E50'  # Texto normal para todas as colunas
            },
            # Destaque específico para a coluna "dias_sem_compra" em clientes inativos
            {
                'if': {
                    'filter_query': '{dias_sem_compra} > 365',
                    'column_id': 'dias_sem_compra'
                },
                'backgroundColor': '#FADBD8',  # Mesmo fundo da linha
                'color': '#E74C3C',           # Texto vermelho apenas nesta coluna
                'fontWeight': 'bold'          # Negrito apenas nesta coluna
            },
            # Semáforo para % Não Comprado - VERDE (Alta Conversão)
            {
                'if': {
                    'filter_query': f'{{pct_nao_comprado}} <= {verde_max:.1f}',
                    'column_id': 'pct_nao_comprado'
                },
                'color': '#27AE60',           # Verde
                'fontWeight': 'bold'
            },
            # Semáforo para % Não Comprado - AMARELO (Conversão Moderada)
            {
                'if': {
                    'filter_query': f'{{pct_nao_comprado}} > {verde_max:.1f} && {{pct_nao_comprado}} <= {amarelo_max:.1f}',
                    'column_id': 'pct_nao_comprado'
                },
                'color': '#F39C12',           # Amarelo/Laranja
                'fontWeight': 'bold'
            },
            # Semáforo para % Não Comprado - VERMELHO (Baixa Conversão)
            {
                'if': {
                    'filter_query': f'{{pct_nao_comprado}} > {amarelo_max:.1f}',
                    'column_id': 'pct_nao_comprado'
                },
                'color': '#E74C3C',           # Vermelho
                'fontWeight': 'bold'
            }
        ],
        
        # Exportação
        export_format="csv",
        export_headers="display",
        
        # Configurações de largura de coluna
        style_cell_conditional=[
            {
                'if': {'column_id': 'cod_cliente'},
                'width': '120px',
                'textAlign': 'center',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'cliente'},
                'width': '300px',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'total_comprado_valor'},
                'width': '180px',
                'textAlign': 'right'
            }
        ] + [
            {
                'if': {'column_id': c},
                'textAlign': 'right'
            } for c in ['total_comprado_qtd', 'mix_produtos', 'unidades_negocio', 'total_cotado_qtd', 'dias_sem_compra', 'pct_mix_produtos', 'pct_nao_comprado']
        ]
    )
    
    # Adicionar botões de controle
    controls = dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("📊 Exportar CSV", id=f"{table_id}-export", color="primary", size="sm"),
                dbc.Button("� Resetar Filtros", id=f"{table_id}-reset", color="secondary", size="sm"),
                dbc.Button("📋 Selecionar Todos", id=f"{table_id}-select-all", color="info", size="sm"),
            ])
        ], width=8),
        dbc.Col([
            dbc.Input(
                id=f"{table_id}-page-size",
                type="number",
                value=20,
                min=10,
                max=100,
                step=10,
                placeholder="Itens por página",
                size="sm"
            )
        ], width=2),
        dbc.Col([
            dbc.Label("Itens/página", className="text-muted small")
        ], width=2)
    ], className="mb-3")
    
    return html.Div([
        # Informações sobre o semáforo
        dbc.Alert([
            html.H6("📊 Critérios do Semáforo - % Não Comprado:", className="mb-1"),
            html.Small([
                html.Span("🟢 Verde: ", style={'color': '#27AE60', 'fontWeight': 'bold'}),
                f"0% a {verde_max:.1f}% (25% melhores clientes) | ",
                html.Span("🟡 Amarelo: ", style={'color': '#F39C12', 'fontWeight': 'bold'}),
                f"{verde_max:.1f}% a {amarelo_max:.1f}% (50% intermediários) | ",
                html.Span("🔴 Vermelho: ", style={'color': '#E74C3C', 'fontWeight': 'bold'}),
                f"{amarelo_max:.1f}% a 100% (25% que precisam atenção)"
            ])
        ], color="info", className="mb-3"),
        controls,
        data_table,
        html.Div(id=f"{table_id}-selected-info", className="mt-2"),
        html.Small([
            html.I(className="fas fa-info-circle me-1"),
            "💡 Dicas: Clique nos cabeçalhos para ordenar, use os filtros para buscar, "
            "selecione linhas para exportar dados específicos!"
        ], className="text-muted d-block mt-2")
    ])

# --- CALLBACK DA PÁGINA VISÃO GERAL ---
@app.callback(
    Output('kpi-entrada-pedidos', 'children'),
    Output('kpi-valor-carteira', 'children'),
    Output('kpi-faturamento', 'children'),
    Input('page-overview-content', 'style')
)
def update_visao_geral_kpis(style):
    if style and style.get('display') == 'block':
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        print(f"[Visao Geral] Vendas: {len(df_vendas)}, Cotacoes: {len(df_cotacoes)}")
        kpis_dict = kpis.calculate_kpis_gerais(df_vendas, df_cotacoes)
        return kpis_dict['entrada_pedidos'], kpis_dict['valor_carteira'], kpis_dict['faturamento']
    else:
        return "-", "-", "-"

# --- CALLBACKS DA PÁGINA KPIs DE PROPOSTAS ---
@app.callback(
    Output('tabela-propostas-container', 'children'),
    Output('grafico-propostas', 'figure'),
    Input('filtro-cliente-propostas', 'value'),
    Input('filtro-ano-propostas', 'value'),
    Input('filtro-mes-propostas', 'value'),
    Input('filtro-top-n-clientes-propostas', 'value'),
    Input('filtro-canal-vendas', 'value'),
    Input('filtro-hierarquia-produto', 'value'),
    Input('tipo-grafico-propostas', 'value'),
    Input('page-kpis-propostas-content', 'style')
)
def update_propostas_page_visuals_callback(selected_clients, ano_filtro, mes_filtro, top_n, canais, hierarquias, tipo_grafico, style):
    tabela, fig = update_propostas_page_visuals(selected_clients, ano_filtro, mes_filtro, top_n, canais, hierarquias, tipo_grafico, style)
    return tabela, fig
@app.callback(
    Output('filtro-cliente', 'options'),
    Output('filtro-canal-vendas', 'options'),
    Output('filtro-dias-sem-compra', 'max'),
    Output('filtro-dias-sem-compra', 'value'),
    Output('filtro-hierarquia-produto', 'options'),
    Input('page-kpis-cliente-content', 'style'),
    Input('filtro-ano-kpis-cliente', 'value'),
    Input('filtro-mes-kpis-cliente', 'value')
)
def update_kpi_page_filter_options(style, ano_filtro, mes_filtro):
    if style and style.get('display') == 'block':
        df_vendas = db.get_clean_vendas_as_df()
        print(f"[KPIs Cliente] Vendas antes filtro: {len(df_vendas)}")
        # Filtrar vendas por intervalo de ano e mês
        # Aceita tanto valor único quanto intervalo
        if ano_filtro:
            if isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_filtro[0]) & (df_vendas['data_faturamento'].dt.year <= ano_filtro[1])]
            else:
                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
        if mes_filtro:
            if isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_filtro[0]) & (df_vendas['data_faturamento'].dt.month <= mes_filtro[1])]
            else:
                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
        print(f"[KPIs Cliente] Vendas apos filtro: {len(df_vendas)} | Ano: {ano_filtro} | Mes: {mes_filtro}")
        df_raw_vendas = db.get_raw_data_as_df('raw_vendas')
        cliente_map = df_vendas[['cod_cliente', 'cliente']].drop_duplicates(subset=['cod_cliente'])
        cliente_options = [{'label': f"{row['cod_cliente']} - {row['cliente']}", 'value': row['cod_cliente']} for index, row in cliente_map.sort_values('cliente').iterrows()]
        # Opções de canal de vendas devem vir dos dados limpos
        if 'canal_distribuicao' in df_vendas.columns:
            canal_options = [{'label': canal, 'value': canal} for canal in df_vendas['canal_distribuicao'].dropna().unique()]
        else:
            canal_options = []
        materiais_vendas = set(df_vendas['material'].unique())
        df_hierarquia = df_raw_vendas[df_raw_vendas['Material'].isin(materiais_vendas)]
        hierarquia1 = df_hierarquia['Hier. Produto 1'].dropna().unique().tolist() if 'Hier. Produto 1' in df_hierarquia.columns else []
        hierarquia2 = df_hierarquia['Hier. Produto 2'].dropna().unique().tolist() if 'Hier. Produto 2' in df_hierarquia.columns else []
        hierarquia3 = df_hierarquia['Hier. Produto 3'].dropna().unique().tolist() if 'Hier. Produto 3' in df_hierarquia.columns else []
        hierarquia_options = sorted(set(hierarquia1 + hierarquia2 + hierarquia3))
        hierarquia_options = [{'label': h, 'value': h} for h in hierarquia_options]
        try:
            max_dias = 1000
            return cliente_options, canal_options, max_dias, [0, max_dias], hierarquia_options
        except Exception:
            return cliente_options, canal_options, 1000, [0, 1000], hierarquia_options
    raise exceptions.PreventUpdate
def update_propostas_page_visuals(selected_clients, ano_filtro, mes_filtro, top_n, canais, hierarquias, tipo_grafico, style):
    if not style or style.get('display') != 'block':
        raise exceptions.PreventUpdate
        
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    
    # Aplicar filtros de ano e mês se especificados
    if ano_filtro and isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
        df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_filtro[0]) & 
                              (df_vendas['data_faturamento'].dt.year <= ano_filtro[1])]
    elif ano_filtro:
        df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
        
    if mes_filtro and isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
        df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_filtro[0]) & 
                              (df_vendas['data_faturamento'].dt.month <= mes_filtro[1])]
    elif mes_filtro:
        df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
    
    # Filtrar por clientes se especificado
    if selected_clients:
        df_vendas = df_vendas[df_vendas['cod_cliente'].isin(selected_clients)]
        df_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'].isin(selected_clients)]
    
    # Filtrar por canais se especificado
    if canais:
        canal_col = None
        for col in df_vendas.columns:
            if col.lower().replace(' ', '_') == 'canal_distribuicao':
                canal_col = col
                break
        if canal_col:
            df_vendas = df_vendas[df_vendas[canal_col].isin(canais)]
    
    # Filtrar por hierarquia se especificado
    if hierarquias:
        hier_cols = [col for col in df_vendas.columns if col.lower().startswith('hier_produto')]
        if hier_cols:
            mask = pd.Series(False, index=df_vendas.index)
            for col in hier_cols:
                mask |= df_vendas[col].isin(hierarquias)
            df_vendas = df_vendas[mask]
    
    if df_vendas.empty:
        tabela = dbc.Alert("Nenhum dado disponível para os filtros selecionados.", color="warning")
        fig = {}
        return tabela, fig
    
    # Calcular análise de materiais usando função dos KPIs
    try:
        from utils import kpis as kpis_module
        df_analysis = kpis_module.calculate_material_analysis(df_vendas, df_cotacoes)
        
        # Aplicar Top N se especificado
        if top_n and len(df_analysis) > top_n:
            df_analysis = df_analysis.head(top_n)
        
        if df_analysis.empty:
            tabela = dbc.Alert("Nenhum dado disponível após análise.", color="warning") 
            fig = {}
        else:
            tabela = dbc.Table.from_dataframe(df_analysis, striped=True, bordered=True, hover=True, responsive=True)
            
            # Criar gráfico baseado no tipo selecionado
            if tipo_grafico == 'heatmap':
                # Criar heatmap usando pivot table
                try:
                    pivot_data = df_analysis.pivot_table(
                        index='material', 
                        values=['total_comprado_qtd', 'total_cotado_qtd'], 
                        fill_value=0
                    )
                    fig = px.imshow(pivot_data.values, 
                                  x=pivot_data.columns, 
                                  y=pivot_data.index,
                                  aspect="auto",
                                  color_continuous_scale="Blues",
                                  title='Heatmap: Comprado vs Cotado por Material')
                except:
                    # Fallback para scatter se pivot falhar
                    fig = px.scatter(df_analysis, x='total_comprado_qtd', y='total_cotado_qtd', 
                                   hover_data=['material'], title='Comprado vs Cotado por Material')
            else:  # tipo_grafico == 'barra'
                fig = px.bar(df_analysis, x='material', y='total_comprado_qtd', 
                           title='Total Comprado por Material')
                           
    except Exception as e:
        print(f"Erro na análise de propostas: {e}")
        tabela = dbc.Alert(f"Erro na análise: {e}", color="danger")
        fig = {}
    
    return tabela, fig

# Callback para popular opções de filtros da página de propostas
@app.callback(
    Output('filtro-cliente-propostas', 'options'),
    Input('page-kpis-propostas-content', 'style'),
    Input('filtro-ano-propostas', 'value'),
    Input('filtro-mes-propostas', 'value')
)
def update_propostas_filter_options(style, ano_filtro, mes_filtro):
    if not style or style.get('display') != 'block':
        raise exceptions.PreventUpdate
        
    df_vendas = db.get_clean_vendas_as_df()
    
    # Aplicar filtros de ano e mês se especificados
    if ano_filtro and isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
        df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_filtro[0]) & 
                              (df_vendas['data_faturamento'].dt.year <= ano_filtro[1])]
    elif ano_filtro:
        df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
        
    if mes_filtro and isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
        df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_filtro[0]) & 
                              (df_vendas['data_faturamento'].dt.month <= mes_filtro[1])]
    elif mes_filtro:
        df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
    
    if df_vendas.empty:
        return []
        
    cliente_map = df_vendas[['cod_cliente', 'cliente']].drop_duplicates(subset=['cod_cliente'])
    cliente_options = [{'label': f"{row['cod_cliente']} - {row['cliente']}", 'value': row['cod_cliente']} 
                      for index, row in cliente_map.sort_values('cliente').iterrows()]
    
    return cliente_options

# --- CALLBACKS DA PÁGINA DE CONFIGURAÇÕES ---
@app.callback(
    Output('user-management-table-container', 'children'),
    Input('page-config-content', 'style')
)
def load_management_tables(style):
    if style and style.get('display') == 'block':
        users = db.get_all_users()
        user_table_header = [html.Thead(html.Tr([html.Th("ID"), html.Th("Username"), html.Th("Criado em"), html.Th("Ação")]))]
        user_table_body = [html.Tbody([html.Tr([html.Td(user['id']), html.Td(user['username']), html.Td(user['created_at']), html.Td(dbc.Button("Excluir", id={'type': 'delete-user-btn', 'index': user['id']}, color="danger", size="sm") if user['id'] != 1 else "")]) for user in users])]
        return dbc.Table(user_table_header + user_table_body, bordered=True, striped=True)
    raise exceptions.PreventUpdate

@app.callback(
    Output('confirm-delete-user', 'displayed'),
    Output('store-user-to-delete', 'data'),
    Input({'type': 'delete-user-btn', 'index': 'all'}, 'n_clicks'),
    prevent_initial_call=True
)
def display_confirm_delete_user(n_clicks):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id:
        user_id = eval(triggered_id)['index']
        return True, user_id
    return False, None

@app.callback(
    Output('confirm-wipe-db', 'displayed'),
    Input('wipe-db-button', 'n_clicks'),
    prevent_initial_call=True
)
def display_confirm_wipe_db(n_clicks):
    return True

@app.callback(
    Output('config-feedback-msg', 'children'),
    Output('config-url', 'pathname'),
    Input('confirm-delete-user', 'submit_n_clicks'),
    Input('confirm-wipe-db', 'submit_n_clicks'),
    State('store-user-to-delete', 'data'),
    prevent_initial_call=True
)
def handle_deletions(user_clicks, wipe_clicks, user_id):
    triggered_id = callback_context.triggered_id
    if triggered_id == 'confirm-delete-user' and user_id:
        db.delete_user(user_id)
        return dbc.Alert(f"Usuário ID {user_id} excluído.", color="success"), '/app/config'
    if triggered_id == 'confirm-wipe-db':
        db.wipe_all_transaction_data()
        return dbc.Alert("Todos os dados foram apagados.", color="warning"), '/app/config'
    return dash.no_update, dash.no_update

@app.callback(
    Output('config-feedback-msg', 'children', allow_duplicate=True),
    Input('run-etl-button', 'n_clicks'),
    prevent_initial_call=True
)
def run_etl_callback(n_clicks):
    try:
        result_message = etl.run_full_etl()
        return dbc.Alert(result_message, color="success")
    except Exception as e:
        return dbc.Alert(str(e), color="danger")

@app.callback(
    Output('grafico-scatter-kpis-cliente', 'figure'),
    Output('tabela-kpis-cliente-container', 'children'),
    Output('grafico-historico-kpis', 'figure'),
    Input('filtro-ano-kpis-cliente', 'value'),
    Input('filtro-mes-kpis-cliente', 'value'),
    Input('filtro-cliente', 'value'),
    Input('filtro-canal-vendas', 'value'),
    Input('filtro-dias-sem-compra', 'value'),
    Input('filtro-hierarquia-produto', 'value'),
    Input('filtro-top-n-clientes', 'value'),
    Input('dropdown-historico-kpis', 'value'),
    Input('page-kpis-cliente-content', 'style')
)
def update_kpis_cliente_visuals(ano_filtro, mes_filtro, clientes, canais, dias_sem_compra, hierarquias, top_n, historico_kpis, style):
    # Carregar dados limpos
    df_vendas_original = db.get_clean_vendas_as_df()
    df_cotacoes_original = db.get_clean_cotacoes_as_df()
    
    print(f'DEBUG - Registros originais: vendas={len(df_vendas_original)}, cotacoes={len(df_cotacoes_original)}')
    print(f'DEBUG - Filtros recebidos: ano={ano_filtro}, mes={mes_filtro}, hierarquias={hierarquias}, top_n={top_n}')
    
    # Trabalhar com cópias para manter dados originais
    df_vendas = df_vendas_original.copy()
    df_cotacoes = df_cotacoes_original.copy()
    
    # Converter datas uma vez só no início
    if 'data_faturamento' in df_vendas.columns:
        df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
        df_vendas = df_vendas.dropna(subset=['data_faturamento'])  # Remover datas inválidas
        print(f'DEBUG - Após limpeza de datas: {len(df_vendas)} registros em vendas')
    
    if 'data' in df_cotacoes.columns:
        df_cotacoes['data'] = pd.to_datetime(df_cotacoes['data'], errors='coerce')
        df_cotacoes = df_cotacoes.dropna(subset=['data'])
        print(f'DEBUG - Após limpeza de datas: {len(df_cotacoes)} registros em cotações')
    
    # === APLICAR FILTROS DE FORMA INDEPENDENTE ===
    
    # 1. Filtro de ANO
    if ano_filtro:
        if isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
            # Range de anos
            df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_filtro[0]) & 
                                 (df_vendas['data_faturamento'].dt.year <= ano_filtro[1])]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[(df_cotacoes['data'].dt.year >= ano_filtro[0]) & 
                                         (df_cotacoes['data'].dt.year <= ano_filtro[1])]
        else:
            # Ano específico
            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[df_cotacoes['data'].dt.year == ano_filtro]
        
        print(f'DEBUG - Após filtro de ano {ano_filtro}: vendas={len(df_vendas)}, cotacoes={len(df_cotacoes)}')
    
    # 2. Filtro de MÊS
    if mes_filtro:
        if isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
            # Range de meses
            df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_filtro[0]) & 
                                 (df_vendas['data_faturamento'].dt.month <= mes_filtro[1])]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[(df_cotacoes['data'].dt.month >= mes_filtro[0]) & 
                                         (df_cotacoes['data'].dt.month <= mes_filtro[1])]
        else:
            # Mês específico
            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[df_cotacoes['data'].dt.month == mes_filtro]
        
        print(f'DEBUG - Após filtro de mês {mes_filtro}: vendas={len(df_vendas)}, cotacoes={len(df_cotacoes)}')
    
    # 3. Filtro de CLIENTES
    if clientes:
        df_vendas = df_vendas[df_vendas['cod_cliente'].isin(clientes)]
        df_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'].isin(clientes)]
        print(f'DEBUG - Após filtro de clientes: vendas={len(df_vendas)}, cotacoes={len(df_cotacoes)}')
    # 4. Filtro de HIERARQUIA/PRODUTO - USAR df_raw_vendas e mapear para vendas
    if hierarquias:
        print(f'DEBUG - Aplicando filtro de hierarquia: {hierarquias}')
        print(f'DEBUG - Registros antes do filtro de hierarquia: {len(df_vendas)}')
        
        # Carregar dados raw para obter informações de hierarquia
        try:
            df_raw_vendas = db.get_raw_data_as_df('raw_vendas')
            
            if not df_raw_vendas.empty:
                print(f'DEBUG - Usando df_raw_vendas para filtro de hierarquia')
                
                # Criar máscara para hierarquias nos dados raw
                mask_hierarquia = pd.Series(False, index=df_raw_vendas.index)
                
                # Verificar colunas de hierarquia disponíveis
                colunas_hier = [col for col in df_raw_vendas.columns if 'Hier. Produto' in col]
                print(f'DEBUG - Colunas de hierarquia encontradas no raw: {colunas_hier}')
                
                for hierarquia in hierarquias:
                    for col_hier in colunas_hier:
                        mask_temp = df_raw_vendas[col_hier].str.contains(str(hierarquia), case=False, na=False)
                        registros_encontrados = mask_temp.sum()
                        print(f'DEBUG - Hierarquia "{hierarquia}" em coluna "{col_hier}": {registros_encontrados} registros')
                        mask_hierarquia |= mask_temp
                
                # Obter materiais que atendem ao filtro de hierarquia
                materiais_filtrados = df_raw_vendas[mask_hierarquia]['Material'].unique()
                print(f'DEBUG - Materiais filtrados por hierarquia: {len(materiais_filtrados)}')
                
                # Aplicar filtro de materiais no df_vendas
                if len(materiais_filtrados) > 0:
                    df_vendas_antes = len(df_vendas)
                    df_vendas = df_vendas[df_vendas['material'].isin(materiais_filtrados)]
                    print(f'DEBUG - Filtro de hierarquia aplicado via materiais: {df_vendas_antes} -> {len(df_vendas)} registros')
                    
                    # Debug adicional: mostrar clientes únicos encontrados
                    clientes_encontrados = df_vendas['cliente'].unique()
                    print(f'DEBUG - Clientes únicos com hierarquia "{hierarquias}": {len(clientes_encontrados)}')
                    print(f'DEBUG - Primeiros 5 clientes: {clientes_encontrados[:5]}')
                else:
                    print(f'DEBUG - ERRO: Nenhum material encontrado para hierarquias: {hierarquias}')
                    df_vendas = df_vendas.iloc[:0]  # DataFrame vazio
            else:
                print(f'DEBUG - df_raw_vendas vazio, tentando filtro direto')
                raise Exception("df_raw_vendas vazio")
        except Exception as e:
            print(f'DEBUG - Erro ao carregar df_raw_vendas: {e}, tentando filtro direto')
            # Fallback: tentar filtro direto nas colunas disponíveis
            colunas_possiveis = [
                'Hier. Produto 1', 'hier_produto_1', 'hierarquia_produto_1',
                'Hier. Produto 2', 'hier_produto_2', 'hierarquia_produto_2', 
                'Hier. Produto 3', 'hier_produto_3', 'hierarquia_produto_3',
                'produto', 'material', 'descricao_produto', 'descricao'
            ]
            coluna_encontrada = None
            
            for col_name in colunas_possiveis:
                if col_name in df_vendas.columns:
                    coluna_encontrada = col_name
                    print(f'DEBUG - Coluna encontrada para hierarquia: {col_name}')
                    break
            
            if coluna_encontrada:
                # Aplicar filtro
                mask = pd.Series(False, index=df_vendas.index)
                for hierarquia in hierarquias:
                    mask_temp = df_vendas[coluna_encontrada].str.contains(str(hierarquia), case=False, na=False)
                    registros_encontrados = mask_temp.sum()
                    print(f'DEBUG - Aplicando filtro "{hierarquia}": {registros_encontrados} registros encontrados')
                    mask |= mask_temp
                
                df_vendas_antes = len(df_vendas)
                df_vendas = df_vendas[mask]
                print(f'DEBUG - Filtro de hierarquia aplicado: {df_vendas_antes} -> {len(df_vendas)} registros')
            else:
                print('ERRO - Nenhuma coluna apropriada encontrada para filtro de hierarquia')
                print(f'DEBUG - Colunas existentes: {df_vendas.columns.tolist()}')
    
    # 5. Filtro de CANAL DE VENDAS
    if canais:
        canal_col = None
        for col in df_vendas.columns:
            if col.lower().replace(' ', '_') == 'canal_distribuicao':
                canal_col = col
                break
        if canal_col:
            df_vendas = df_vendas[df_vendas[canal_col].isin(canais)]
            print(f'DEBUG - Após filtro de canal: {len(df_vendas)} registros')
        else:
            print('DEBUG - Coluna de canal de vendas não encontrada')
    df_kpis = kpis.calculate_kpis_por_cliente(df_vendas, df_cotacoes)
    print(f'DEBUG - KPIs calculados para {len(df_kpis)} clientes')
    if not df_kpis.empty:
        print(f'DEBUG - Primeiros KPIs calculados:')
        print(df_kpis[['cod_cliente', 'cliente', 'total_comprado_valor', 'mix_produtos']].head())
    
    # Aplicar filtro Top N aos KPIs calculados (verificar se é um número válido)
    if top_n:
        try:
            top_n_int = int(top_n)
            if top_n_int > 0 and len(df_kpis) > top_n_int:
                print(f'DEBUG - Aplicando filtro Top {top_n_int}: {len(df_kpis)} -> {top_n_int} clientes')
                df_kpis = df_kpis.head(top_n_int)
            else:
                print(f'DEBUG - Top N não aplicado: top_n={top_n_int}, registros={len(df_kpis)}')
        except (ValueError, TypeError):
            print(f'DEBUG - Top N inválido: {top_n}')
            pass  # Manter todos os clientes se top_n for inválido
    
    # Filtrar df_vendas e df_cotacoes para incluir apenas os clientes que aparecem nos KPIs finais
    if not df_kpis.empty:
        clientes_filtrados = df_kpis['cod_cliente'].unique()
        df_vendas = df_vendas[df_vendas['cod_cliente'].isin(clientes_filtrados)]
        df_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'].isin(clientes_filtrados)]
    
    if not df_kpis.empty:
        # Criar gráfico scatter modernizado
        fig_scatter = px.scatter(
            df_kpis, 
            x='total_comprado_valor', 
            y='dias_sem_compra', 
            color='pct_mix_produtos',
            size='mix_produtos',
            hover_data={
                'cliente': True,
                'cod_cliente': True,
                'total_comprado_valor': ':,.2f',
                'dias_sem_compra': True,
                'pct_mix_produtos': ':.1%',
                'mix_produtos': True
            },
            title='<b>Análise de Clientes: Valor Faturado vs Tempo sem Compra</b>',
            labels={
                'total_comprado_valor': 'Valor Total Faturado (R$)',
                'dias_sem_compra': 'Dias sem Compra',
                'pct_mix_produtos': 'Diversidade (%)',
                'mix_produtos': 'Qtd Produtos'
            },
            color_continuous_scale='RdYlBu_r'  # Escala de cores moderna
        )
        
        # Melhorar layout do gráfico scatter
        fig_scatter.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=600,
            font=dict(family="Arial, sans-serif", size=12),
            title=dict(
                font=dict(size=16, color='#2C3E50'),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E5E5',
                tickformat=',.0f',
                title=dict(font=dict(size=14, color='#2C3E50'))
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E5E5',
                title=dict(font=dict(size=14, color='#2C3E50'))
            ),
            coloraxis_colorbar=dict(
                title="Diversidade de Produtos (%)",
                tickformat='.0%',
                thickness=15,
                len=0.7
            ),
            margin=dict(l=80, r=80, t=80, b=80)
        )
        
        # Adicionar linhas de referência
        fig_scatter.add_hline(
            y=365, 
            line_dash="dash", 
            line_color="red", 
            annotation_text="1 ano sem compra",
            annotation_position="top right"
        )
        fig_scatter.add_hline(
            y=90, 
            line_dash="dash", 
            line_color="orange", 
            annotation_text="90 dias sem compra",
            annotation_position="bottom right"
        )
        
        # DEBUG - Verificar valores finais
        print(f'DEBUG FINAL - Dados dos KPIs calculados:')
        print(f'DEBUG FINAL - Total de clientes: {len(df_kpis)}')
        valores_negativos = df_kpis[df_kpis['total_comprado_valor'] < 0]
        if len(valores_negativos) > 0:
            print(f'DEBUG FINAL - ATENÇÃO: {len(valores_negativos)} clientes com valores negativos!')
            print(valores_negativos[['cod_cliente', 'cliente', 'total_comprado_valor']])
        
        total_geral = df_kpis['total_comprado_valor'].sum()
        print(f'DEBUG FINAL - Valor total geral: {total_geral}')
    else:
        fig_scatter = {}
    
    # Usar tabela interativa AG Grid em vez da tabela simples
    tabela = create_interactive_table(df_kpis, "kpis-cliente-table") if not df_kpis.empty else dbc.Alert('Nenhum dado disponível.', color='warning')
    
    # Histórico
    # Validação para DataFrame vazio e colunas de data
    if df_vendas.empty or 'data_faturamento' not in df_vendas.columns or not pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
        fig_scatter = {}
        tabela = dbc.Alert('Nenhum dado disponível.', color='warning')
        fig_hist = {}
        return fig_scatter, tabela, fig_hist
    # Bloco do gráfico histórico corretamente indentado
    if not df_vendas.empty and historico_kpis:
        # Preparar dados históricos - calcular KPIs por ano e cliente
        try:
            from utils import kpis as kpis_module
            df_vendas_hist = df_vendas.copy()
            df_vendas_hist['ano'] = df_vendas_hist['data_faturamento'].dt.year
            
            # Lista para armazenar dados históricos
            dados_historicos = []
            
            for ano in df_vendas_hist['ano'].unique():
                df_ano = df_vendas_hist[df_vendas_hist['ano'] == ano]
                # Filtrar cotações para o mesmo período se necessário
                df_cotacoes_ano = df_cotacoes.copy()  # Usar as cotações já carregadas
                df_kpis_ano = kpis_module.calculate_kpis_por_cliente(df_ano, df_cotacoes_ano)
                df_kpis_ano['ano'] = ano
                dados_historicos.append(df_kpis_ano)
            
            if dados_historicos:
                df_hist_kpis = pd.concat(dados_historicos, ignore_index=True)
                
                # Criar identificador único combinando código + nome para distinguir clientes com mesmo nome
                df_hist_kpis['cliente_id'] = df_hist_kpis['cod_cliente'].astype(str) + ' - ' + df_hist_kpis['cliente']
                
                # Para a legenda, verificar se há nomes duplicados
                nomes_duplicados = df_hist_kpis['cliente'].duplicated(keep=False)
                if nomes_duplicados.any():
                    # Se há nomes duplicados, usar código + nome
                    df_hist_kpis['cliente_display'] = df_hist_kpis['cliente_id']
                else:
                    # Se não há nomes duplicados, usar apenas o nome
                    df_hist_kpis['cliente_display'] = df_hist_kpis['cliente']
                
                # Mapear KPIs selecionados para colunas disponíveis
                colunas_existentes = [kpi for kpi in historico_kpis if kpi in df_hist_kpis.columns]
                
                if colunas_existentes and 'cliente_id' in df_hist_kpis.columns:
                    # Filtrar apenas para os clientes que estão nos KPIs filtrados
                    if not df_kpis.empty:
                        # Criar o mesmo identificador único para os KPIs filtrados
                        df_kpis['cliente_id'] = df_kpis['cod_cliente'].astype(str) + ' - ' + df_kpis['cliente']
                        clientes_kpis_ids = df_kpis['cliente_id'].unique()
                        df_hist_kpis = df_hist_kpis[df_hist_kpis['cliente_id'].isin(clientes_kpis_ids)]
                    
                    # Garantir todos os anos/clientes no grid
                    anos = sorted(df_hist_kpis['ano'].unique())
                    clientes_unicos_ids = df_hist_kpis['cliente_id'].unique()
                    
                    # Verificar se há mais de um cliente único
                    if len(clientes_unicos_ids) > 1:
                        df_grid = pd.MultiIndex.from_product([anos, clientes_unicos_ids], names=['ano', 'cliente_id']).to_frame(index=False)
                        df_hist = df_grid.merge(df_hist_kpis[['ano', 'cliente_id', 'cliente_display'] + colunas_existentes], on=['ano', 'cliente_id'], how='left')
                        
                        # Preencher valores faltantes com 0
                        for col in colunas_existentes:
                            df_hist[col] = df_hist[col].fillna(0)
                        
                        # Preencher cliente_display para linhas vazias
                        df_hist['cliente_display'] = df_hist.groupby('cliente_id')['cliente_display'].transform('first')
                        
                        df_hist = df_hist.sort_values(['ano', 'cliente_id'])
                        df_hist_melt = df_hist.melt(id_vars=['ano', 'cliente_id', 'cliente_display'], value_vars=colunas_existentes, var_name='variable', value_name='value')
                        
                        # Criar gráfico com linha separada para cada cliente (usando cliente_display na legenda)
                        fig_hist = px.line(
                            df_hist_melt, 
                            x='ano', 
                            y='value', 
                            color='cliente_display', 
                            line_dash='variable', 
                            markers=True,
                            title='<b>Evolução Histórica dos Indicadores por Cliente</b>',
                            labels={
                                'ano': 'Ano',
                                'value': 'Valor',
                                'cliente_display': 'Cliente',
                                'variable': 'Indicador'
                            }
                        )
                    else:
                        # Se há apenas um cliente, criar gráfico mais simples
                        df_hist_melt = df_hist_kpis.melt(id_vars=['ano', 'cliente_id', 'cliente_display'], value_vars=colunas_existentes, var_name='variable', value_name='value')
                        fig_hist = px.line(
                            df_hist_melt, 
                            x='ano', 
                            y='value', 
                            color='variable', 
                            markers=True,
                            title=f'<b>Evolução Histórica - {df_hist_kpis.iloc[0]["cliente_display"]}</b>',
                            labels={
                                'ano': 'Ano',
                                'value': 'Valor',
                                'variable': 'Indicador'
                            }
                        )
                    # Configurações comuns para ambos os tipos de gráfico histórico
                    fig_hist.update_xaxes(
                        type='category', 
                        tickmode='array', 
                        tickvals=anos, 
                        tickformat='d', 
                        categoryorder='category ascending',
                        title=dict(font=dict(size=14, color='#2C3E50')),
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='#E5E5E5'
                    )
                    
                    fig_hist.update_yaxes(
                        title=dict(font=dict(size=14, color='#2C3E50')),
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='#E5E5E5'
                    )
                    
                    fig_hist.update_traces(
                        text=None, 
                        textposition=None, 
                        mode='lines+markers',
                        line=dict(width=3),
                        marker=dict(size=8)
                    )
                    
                    fig_hist.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=600,
                        font=dict(family="Arial, sans-serif", size=12),
                        title=dict(
                            font=dict(size=16, color='#2C3E50'),
                            x=0.5,
                            xanchor='center'
                        ),
                        legend=dict(
                            orientation='v',
                            yanchor='top',
                            y=1,
                            xanchor='left',
                            x=1.02,
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='#CCCCCC',
                            borderwidth=1,
                            font=dict(size=11)
                        ),
                        margin=dict(l=80, r=150, t=80, b=80),
                        hovermode='x unified'
                    )
                else:
                    fig_hist = {}
            else:
                fig_hist = {}
        except Exception as e:
            print(f"Erro ao calcular histórico: {e}")
            fig_hist = {}
    else:
        fig_hist = {}
    return fig_scatter, tabela, fig_hist

# Exemplo de callback para upload de vendas
@app.callback(
    Output('upload-feedback-msg', 'children'),
    Input('upload-vendas', 'contents'),
    State('upload-vendas', 'filename'),
    State('session-user-id', 'data'),
    prevent_initial_call=True
)
def upload_vendas_callback(contents, filename, user_id):
    if not contents:
        return dbc.Alert('Nenhum arquivo enviado.', color='warning')
    try:
        from utils.data_loader import parse_upload_content, read_raw_vendas, generate_fingerprint
        file_bytes_io = parse_upload_content(contents)
        df = read_raw_vendas(file_bytes_io)
        fingerprint = generate_fingerprint(file_bytes_io)
        linhas_inseridas = db.insert_raw_df(df, 'raw_vendas', filename, fingerprint, user_id)
        print(f"Linhas inseridas em raw_vendas: {linhas_inseridas}")
        if linhas_inseridas == 0:
            return dbc.Alert("Erro ao inserir dados no banco. Verifique o arquivo e tente novamente.", color="danger")
        else:
            return dbc.Alert(f"Upload realizado com sucesso! {linhas_inseridas} linhas inseridas.", color="success")
    except Exception as e:
        print(f"Erro no upload: {e}")
        return dbc.Alert(f"Erro no upload: {e}", color="danger")

# --- CALLBACKS PARA PÁGINA DE PRODUTOS (BOLHAS) ---
@app.callback(
    Output('grafico-bolhas-produtos', 'figure'),
    Input('filtro-ano-produtos', 'value'),
    Input('filtro-un-produtos', 'value'),
    Input('filtro-top-produtos', 'value'),
    Input('filtro-top-clientes-produtos', 'value'),
    Input('filtro-paleta-cores', 'value'),
    Input('page-produtos-content', 'style')
)
def update_produtos_bubble_chart(ano, unidades, top_produtos, top_clientes, paleta, style):
    if not style or style.get('display') != 'block':
        raise exceptions.PreventUpdate
    
    try:
        from utils.visualizations import create_bubble_chart
        from utils.kpis import calculate_produtos_matrix
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Filtrar por ano se especificado
        if ano and ano != "__ALL__":
            if 'data_faturamento' in df_vendas.columns:
                df_vendas = df_vendas[pd.to_datetime(df_vendas['data_faturamento']).dt.year == int(ano)]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[pd.to_datetime(df_cotacoes['data']).dt.year == int(ano)]
        
        # Filtrar por unidade de negócio
        if unidades:
            if 'unidade_negocio' in df_vendas.columns:
                df_vendas = df_vendas[df_vendas['unidade_negocio'].isin(unidades)]
            if 'unidade_negocio' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[df_cotacoes['unidade_negocio'].isin(unidades)]
        
        # Calcular matriz de produtos
        df_matrix = calculate_produtos_matrix(
            df_vendas, df_cotacoes, 
            top_produtos=top_produtos or 20, 
            top_clientes=top_clientes or 15
        )
        
        # Criar gráfico
        fig = create_bubble_chart(df_matrix, color_scale=paleta or 'Viridis')
        return fig
        
    except Exception as e:
        print(f"Erro ao gerar gráfico de bolhas: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao carregar dados: {str(e)}", x=0.5, y=0.5)
        return fig

@app.callback(
    Output('filtro-un-produtos', 'options'),
    Input('page-produtos-content', 'style')
)
def update_un_options_produtos(style):
    if style and style.get('display') == 'block':
        try:
            df_vendas = db.get_clean_vendas_as_df()
            df_cotacoes = db.get_clean_cotacoes_as_df()
            
            unidades = set()
            if 'unidade_negocio' in df_vendas.columns:
                unidades.update(df_vendas['unidade_negocio'].dropna().unique())
            if 'unidade_negocio' in df_cotacoes.columns:
                unidades.update(df_cotacoes['unidade_negocio'].dropna().unique())
            
            return [{'label': un, 'value': un} for un in sorted(unidades)]
        except:
            return []
    return []

@app.callback(
    Output("download-csv-produtos", "data"),
    Input("btn-csv-produtos", "n_clicks"),
    State('filtro-ano-produtos', 'value'),
    State('filtro-un-produtos', 'value'),
    State('filtro-top-produtos', 'value'),
    State('filtro-top-clientes-produtos', 'value'),
    prevent_initial_call=True
)
def download_produtos_csv(n_clicks, ano, unidades, top_produtos, top_clientes):
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    try:
        from utils.kpis import calculate_produtos_matrix
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Aplicar filtros (mesmo código do gráfico)
        if ano and ano != "__ALL__":
            if 'data_faturamento' in df_vendas.columns:
                df_vendas = df_vendas[pd.to_datetime(df_vendas['data_faturamento']).dt.year == int(ano)]
            if 'data' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[pd.to_datetime(df_cotacoes['data']).dt.year == int(ano)]
        
        if unidades:
            if 'unidade_negocio' in df_vendas.columns:
                df_vendas = df_vendas[df_vendas['unidade_negocio'].isin(unidades)]
            if 'unidade_negocio' in df_cotacoes.columns:
                df_cotacoes = df_cotacoes[df_cotacoes['unidade_negocio'].isin(unidades)]
        
        df_matrix = calculate_produtos_matrix(
            df_vendas, df_cotacoes,
            top_produtos=top_produtos or 20,
            top_clientes=top_clientes or 15
        )
        
        return dcc.send_data_frame(
            df_matrix.to_csv, 
            f"analise_produtos_{datetime.now().date()}.csv",
            index=False
        )
    except Exception as e:
        print(f"Erro no download CSV produtos: {e}")
        raise exceptions.PreventUpdate

# --- CALLBACKS PARA PÁGINA DE FUNIL & AÇÕES ---
@app.callback(
    Output('metricas-funil', 'children'),
    Output('lista-a-container', 'children'),
    Output('lista-b-container', 'children'),
    Output('grafico-funil', 'figure'),
    Input('filtro-periodo-funil', 'value'),
    Input('threshold-conversao-baixa', 'value'),
    Input('threshold-dias-risco', 'value'),
    Input('page-funil-content', 'style')
)
def update_funil_analysis(periodo, threshold_conversao, threshold_dias, style):
    if not style or style.get('display') != 'block':
        raise exceptions.PreventUpdate
    
    try:
        from utils.kpis import calculate_funil_metrics
        from utils.visualizations import create_funnel_chart
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Calcular métricas do funil
        funil_metrics = calculate_funil_metrics(
            df_vendas, df_cotacoes,
            periodo_meses=periodo or 12,
            threshold_conversao=threshold_conversao or 20,
            threshold_dias_risco=threshold_dias or 90
        )
        
        # Métricas gerais
        metricas_cards = [
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(funil_metrics['total_clientes_cotaram'], className="card-title"),
                            html.P("Clientes que Cotaram", className="card-text")
                        ])
                    ], color="info", outline=True)
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(funil_metrics['total_clientes_compraram'], className="card-title"),
                            html.P("Clientes que Compraram", className="card-text")
                        ])
                    ], color="success", outline=True)
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{funil_metrics['taxa_conversao_geral']:.1f}%", className="card-title"),
                            html.P("Taxa de Conversão Geral", className="card-text")
                        ])
                    ], color="primary", outline=True)
                ], md=4)
            ])
        ]
        
        # Lista A - Baixa conversão, alto volume
        lista_a = funil_metrics['lista_a'].head(10)
        lista_a_items = []
        for _, row in lista_a.iterrows():
            lista_a_items.append(
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(row['cliente'][:30] + "..." if len(str(row['cliente'])) > 30 else str(row['cliente'])),
                        html.Br(),
                        html.Small(f"Conversão: {row['conversao_pct']:.1f}% | Qtd Cotada: {row['quantidade']:,.0f}"),
                    ])
                ])
            )
        
        lista_a_component = dbc.ListGroup(lista_a_items) if lista_a_items else html.P("Nenhum cliente encontrado")
        
        # Lista B - Risco de inatividade
        lista_b = funil_metrics['lista_b'].head(10)
        lista_b_items = []
        for _, row in lista_b.iterrows():
            lista_b_items.append(
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(row['cliente'][:30] + "..." if len(str(row['cliente'])) > 30 else str(row['cliente'])),
                        html.Br(),
                        html.Small(f"Dias sem compra: {row['dias_sem_compra']} | Última qtd: {row['quantidade_faturada']:,.0f}"),
                    ])
                ])
            )
        
        lista_b_component = dbc.ListGroup(lista_b_items) if lista_b_items else html.P("Nenhum cliente encontrado")
        
        # Gráfico do funil
        fig_funil = create_funnel_chart(funil_metrics['funil_completo'])
        
        return metricas_cards, lista_a_component, lista_b_component, fig_funil
        
    except Exception as e:
        print(f"Erro na análise do funil: {e}")
        error_msg = html.P(f"Erro ao carregar dados: {str(e)}")
        empty_fig = go.Figure()
        return error_msg, error_msg, error_msg, empty_fig

@app.callback(
    Output("download-lista-a", "data"),
    Input("btn-download-lista-a", "n_clicks"),
    State('filtro-periodo-funil', 'value'),
    State('threshold-conversao-baixa', 'value'),
    State('threshold-dias-risco', 'value'),
    prevent_initial_call=True
)
def download_lista_a(n_clicks, periodo, threshold_conversao, threshold_dias):
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    try:
        from utils.kpis import calculate_funil_metrics
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        funil_metrics = calculate_funil_metrics(
            df_vendas, df_cotacoes,
            periodo_meses=periodo or 12,
            threshold_conversao=threshold_conversao or 20,
            threshold_dias_risco=threshold_dias or 90
        )
        
        lista_a = funil_metrics['lista_a']
        return dcc.send_data_frame(
            lista_a.to_csv,
            f"lista_a_baixa_conversao_{datetime.now().date()}.csv",
            index=False
        )
    except Exception as e:
        print(f"Erro no download Lista A: {e}")
        raise exceptions.PreventUpdate

@app.callback(
    Output("download-lista-b", "data"),
    Input("btn-download-lista-b", "n_clicks"),
    State('filtro-periodo-funil', 'value'),
    State('threshold-conversao-baixa', 'value'),
    State('threshold-dias-risco', 'value'),
    prevent_initial_call=True
)
def download_lista_b(n_clicks, periodo, threshold_conversao, threshold_dias):
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    try:
        from utils.kpis import calculate_funil_metrics
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        funil_metrics = calculate_funil_metrics(
            df_vendas, df_cotacoes,
            periodo_meses=periodo or 12,
            threshold_conversao=threshold_conversao or 20,
            threshold_dias_risco=threshold_dias or 90
        )
        
        lista_b = funil_metrics['lista_b']
        return dcc.send_data_frame(
            lista_b.to_csv,
            f"lista_b_risco_inatividade_{datetime.now().date()}.csv",
            index=False
        )
    except Exception as e:
        print(f"Erro no download Lista B: {e}")
        raise exceptions.PreventUpdate

# --- CALLBACK PARA GERAÇÃO DE PDF POR CLIENTE ---
@app.callback(
    Output("download-pdf-produtos", "data"),
    Input("btn-pdf-produtos", "n_clicks"),
    State('filtro-ano-produtos', 'value'),
    prevent_initial_call=True
)
def generate_client_pdf_report(n_clicks, ano):
    if not n_clicks:
        raise exceptions.PreventUpdate
    
    try:
        from utils.report import generate_client_pdf, create_chart_for_pdf
        
        df_vendas = db.get_clean_vendas_as_df()
        df_cotacoes = db.get_clean_cotacoes_as_df()
        
        # Filtrar por ano se especificado
        if ano and ano != "__ALL__":
            if 'data_faturamento' in df_vendas.columns:
                df_vendas = df_vendas[pd.to_datetime(df_vendas['data_faturamento']).dt.year == int(ano)]
        
        # Pegar o cliente com maior volume (exemplo)
        if not df_vendas.empty:
            top_client = df_vendas.groupby(['cod_cliente', 'cliente'])['valor_faturado'].sum().idxmax()
            client_code, client_name = top_client
            client_data = df_vendas[df_vendas['cod_cliente'] == client_code]
            
            # Criar gráfico para o PDF
            monthly_data = client_data.groupby(pd.to_datetime(client_data['data_faturamento']).dt.to_period('M'))['valor_faturado'].sum()
            chart_b64 = create_chart_for_pdf(monthly_data, 'bar')
            
            charts_data = {'image_base64': chart_b64} if chart_b64 else None
            
            # Gerar PDF
            pdf_bytes = generate_client_pdf(client_data, client_name, charts_data)
            
            return dcc.send_bytes(
                pdf_bytes,
                f"relatorio_{client_name}_{datetime.now().date()}.pdf"
            )
        else:
            raise exceptions.PreventUpdate
            
    except Exception as e:
        print(f"Erro na geração do PDF: {e}")
        raise exceptions.PreventUpdate

# Callbacks para tabela interativa
@app.callback(
    Output('kpis-cliente-table-selected-info', 'children'),
    Input('kpis-cliente-table', 'selected_rows'),
    Input('kpis-cliente-table', 'data'),
    prevent_initial_call=True
)
def update_table_selection_info(selected_rows, data):
    """Atualiza informações sobre seleção na tabela"""
    if not selected_rows or not data:
        return ""
    
    selected_data = [data[i] for i in selected_rows]
    total_valor = sum(row.get('total_comprado_valor', 0) for row in selected_data)
    
    return dbc.Alert([
        html.I(className="fas fa-check-circle me-2"),
        f"{len(selected_rows)} cliente(s) selecionado(s) - ",
        html.Strong(f"Valor total: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    ], color="info", className="mt-2")

@app.callback(
    Output('kpis-cliente-table', 'page_size'),
    Input('kpis-cliente-table-page-size', 'value'),
    prevent_initial_call=True
)
def update_page_size(page_size):
    """Atualiza o tamanho da página da tabela"""
    return page_size if page_size and page_size > 0 else 20