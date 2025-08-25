import plotly.express as px
import dash
from dash import html, dcc, Input, Output, State, callback_context, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from flask import session
from datetime import datetime
from io import StringIO

from webapp import app

from utils import db, kpis, etl

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

@app.callback(
    Output("download-csv-kpis-cliente", "data"),
    Input("btn-csv-kpis-cliente", "n_clicks"),
    State("store-kpis-cliente-filtered", "data"),
    prevent_initial_call=True,
)
def download_kpis_cliente_csv(n_clicks, json_data):
    if not n_clicks or not json_data: raise exceptions.PreventUpdate
    df = pd.read_json(StringIO(json_data), orient='split')
    return dcc.send_data_frame(df.to_csv, f"kpis_por_cliente_{datetime.now().date()}.csv", index=False)


# --- CALLBACKS DA PÁGINA KPIs DE PROPOSTAS ---
@app.callback(
    Output('tabela-propostas-container', 'children'),
    Output('grafico-propostas', 'figure'),
    Input('filtro-cliente', 'value'),
    Input('filtro-ano-propostas', 'value'),
    Input('filtro-mes-propostas', 'value'),
    Input('filtro-top-n-clientes', 'value'),
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
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    # Filtro por canal de vendas
    if canais:
        canal_col = None
        for col in df_vendas.columns:
            if col.lower().replace(' ', '_') == 'canal_distribuicao':
                canal_col = col
                @app.callback(
                    Output('filtro-cliente', 'options'),
                    Output('filtro-canal-vendas', 'options'),
                    Output('filtro-dias-sem-compra', 'max'),
                    Output('filtro-dias-sem-compra', 'value'),
                    Output('filtro-hierarquia-produto', 'options'),
                    Input('page-kpis-cliente-content', 'style'),
                    Input('filtro-ano-kpis-cliente', 'value'),
                    Input('filtro-mes-kpis-cliente', 'value'),
                    Input('page-kpis-propostas-content', 'style'),
                    Input('filtro-ano-propostas', 'value'),
                    Input('filtro-mes-propostas', 'value')
                )
                def update_kpi_and_propostas_filter_options(style_cliente, ano_cliente, mes_cliente, style_propostas, ano_propostas, mes_propostas):
                    ctx = dash.callback_context
                    # Se a página de KPIs Cliente está ativa
                    if style_cliente and style_cliente.get('display') == 'block':
                        df_vendas = db.get_clean_vendas_as_df()
                        # Filtrar vendas por intervalo de ano e mês
                        if ano_cliente:
                            if isinstance(ano_cliente, (list, tuple)) and len(ano_cliente) == 2:
                                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_cliente[0]) & (df_vendas['data_faturamento'].dt.year <= ano_cliente[1])]
                            else:
                                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_cliente]
                        if mes_cliente:
                            if isinstance(mes_cliente, (list, tuple)) and len(mes_cliente) == 2:
                                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_cliente[0]) & (df_vendas['data_faturamento'].dt.month <= mes_cliente[1])]
                            else:
                                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_cliente]
                        cliente_map = df_vendas[['cod_cliente', 'cliente']].drop_duplicates(subset=['cod_cliente'])
                        cliente_options = [{'label': f"{row['cod_cliente']} - {row['cliente']}", 'value': row['cod_cliente']} for index, row in cliente_map.sort_values('cliente').iterrows()]
                        canal_options = [{'label': canal, 'value': canal} for canal in sorted(df_vendas['canal_distribuicao'].dropna().unique())]
                        dias_max = int(df_vendas['dias_sem_compra'].max()) if 'dias_sem_compra' in df_vendas.columns else 90
                        dias_value = min(30, dias_max)
                        hierarquia_options = [{'label': h, 'value': h} for h in sorted(df_vendas['hierarquia_produto'].dropna().unique())]
                        return cliente_options, canal_options, dias_max, dias_value, hierarquia_options
                    # Se a página de Propostas está ativa
                    elif style_propostas and style_propostas.get('display') == 'block':
                        df_vendas = db.get_clean_vendas_as_df()
                        if ano_propostas and isinstance(ano_propostas, (list, tuple)) and len(ano_propostas) == 2:
                            df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_propostas[0]) & (df_vendas['data_faturamento'].dt.year <= ano_propostas[1])]
                        elif ano_propostas:
                            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_propostas]
                        if mes_propostas and isinstance(mes_propostas, (list, tuple)) and len(mes_propostas) == 2:
                            df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_propostas[0]) & (df_vendas['data_faturamento'].dt.month <= mes_propostas[1])]
                        elif mes_propostas:
                            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_propostas]
                        cliente_map = df_vendas[['cod_cliente', 'cliente']].drop_duplicates(subset=['cod_cliente'])
                        cliente_options = [{'label': f"{row['cod_cliente']} - {row['cliente']}", 'value': row['cod_cliente']} for index, row in cliente_map.sort_values('cliente').iterrows()]
                        # Os outros outputs não são usados na página de propostas, então retorna valores padrão
                        return cliente_options, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                    # Nenhuma página ativa
                    else:
                        raise exceptions.PreventUpdate
    # Definir df_base_top_n antes do uso
    # Exemplo: selecionar os Top N produtos por quantidade faturada
    if ano_filtro and isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
        anos_selecionados = list(range(ano_filtro[0], ano_filtro[1]+1))
    else:
        anos_selecionados = [ano_filtro] if ano_filtro else []
    df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
    df_vendas = df_vendas.dropna(subset=['data_faturamento'])
    df_vendas['ano'] = df_vendas['data_faturamento'].dt.year.astype(int)
    df_vendas_periodo = df_vendas[df_vendas['ano'].isin(anos_selecionados)]
    top_n_produtos_periodo = df_vendas_periodo.groupby('produto')['quantidade_faturada'].sum().nlargest(top_n or 20).index.tolist()
    df_base_top_n = pd.DataFrame({'produto': top_n_produtos_periodo})
    df_analysis = kpis.calculate_material_analysis(df_vendas, df_cotacoes)
    print(f"[Propostas] df_analysis: {len(df_analysis)}")
    # 4. Faz um LEFT JOIN para garantir que todos os Top N apareçam
    df_analysis_filtrada = pd.merge(df_base_top_n, df_analysis, on='produto', how='left').fillna(0)
    print(f"[Propostas] df_analysis_filtrada: {len(df_analysis_filtrada)}")
    if selected_clients:
        df_cotacoes_cliente = df_cotacoes[df_cotacoes['cod_cliente'].isin(selected_clients)]
        df_vendas_cliente = df_vendas[df_vendas['cod_cliente'].isin(selected_clients)]
        print(f"[Propostas] Cotacoes cliente: {len(df_cotacoes_cliente)}, Vendas cliente: {len(df_vendas_cliente)}")
        cli_cot_qtd = df_cotacoes_cliente.groupby('material')['quantidade'].sum().reset_index(name='cliente_cotou_qtd')
        cli_comp_qtd = df_vendas_cliente.groupby('material')['quantidade_faturada'].sum().reset_index(name='cliente_comprou_qtd')
        df_analysis_filtrada = pd.merge(df_analysis_filtrada, cli_cot_qtd, on='material', how='left')
        df_analysis_filtrada = pd.merge(df_analysis_filtrada, cli_comp_qtd, on='material', how='left')
        df_analysis_filtrada.fillna(0, inplace=True)
        print(f"[Propostas] df_analysis_filtrada pos cliente: {len(df_analysis_filtrada)}")
    if df_analysis_filtrada.empty:
        print("[Propostas] Nenhum dado disponível para os filtros selecionados.")
        tabela = dbc.Alert("Nenhum dado disponível para os filtros selecionados.", color="warning")
        fig = {}
    else:
        tabela = dbc.Table.from_dataframe(df_analysis_filtrada, striped=True, bordered=True, hover=True, responsive=True)
        anos_selecionados = list(range(ano_filtro[0], ano_filtro[1]+1)) if isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2 else [ano_filtro]
        df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
        df_vendas = df_vendas.dropna(subset=['data_faturamento'])
        df_vendas['ano'] = df_vendas['data_faturamento'].dt.year.astype(int)
        df_vendas_periodo = df_vendas[df_vendas['ano'].isin(anos_selecionados)]
        top_n_produtos_periodo = df_vendas_periodo.groupby('produto')['quantidade_faturada'].sum().nlargest(top_n or 20).index.tolist()
        produtos_grid = top_n_produtos_periodo
        grid = pd.MultiIndex.from_product([anos_selecionados, produtos_grid, ['Todos os Clientes', 'Clientes Selecionados']], names=['ano', 'produto', 'grupo']).to_frame(index=False)
        df_todos = df_vendas_periodo[df_vendas_periodo['produto'].isin(produtos_grid)]
        df_todos_agg = df_todos.groupby(['ano', 'produto']).agg(quantidade_faturada=('quantidade_faturada', 'sum')).reset_index()
        df_todos_agg['grupo'] = 'Todos os Clientes'
        if selected_clients:
            df_sel = df_todos[df_todos['cod_cliente'].isin(selected_clients)]
            df_sel_agg = df_sel.groupby(['ano', 'produto']).agg(quantidade_faturada=('quantidade_faturada', 'sum')).reset_index()
            df_sel_agg['grupo'] = 'Clientes Selecionados'
            df_comparison = pd.concat([df_todos_agg, df_sel_agg], ignore_index=True)
        else:
            df_comparison = df_todos_agg.copy()
        df_comparison = grid.merge(df_comparison, on=['ano', 'produto', 'grupo'], how='left').fillna(0)
        print(f"[Propostas] df_comparison: {len(df_comparison)}")
        if tipo_grafico == 'heatmap':
            fig = px.imshow(
                df_comparison.pivot_table(index='produto', columns='ano', values='quantidade_faturada', fill_value=0),
                labels=dict(x="Ano", y="Produto", color="Qtd Vendida"),
                aspect="auto",
                color_continuous_scale="Blues",
                title=f"Heatmap Top {top_n} Produtos por Ano (Todos os Clientes e Selecionados)"
            )
        else:
            fig = px.bar(
                df_comparison,
                x='produto',
                y='quantidade_faturada',
                color='ano',
                barmode='group',
                facet_col='grupo',
                title=f"Top {top_n} Produtos Comprados (Qtd) por Ano e Grupo",
                text_auto='.2s',
                category_orders={'produto': produtos_grid, 'ano': anos_selecionados}
            )
            fig.update_layout(template="plotly_white")
    return tabela, fig

@app.callback(
    Output("download-lista-sugestao", "data"),
    Input("btn-gerar-lista", "n_clicks"),
    State('filtro-cliente', 'value'),
    prevent_initial_call=True
)
def generate_and_download_list(n_clicks, selected_clients):
    if not n_clicks: raise exceptions.PreventUpdate
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    df_sugestao = kpis.generate_purchase_list(df_vendas, df_cotacoes, selected_clients)
    if df_sugestao.empty: raise exceptions.PreventUpdate
    filename = f"sugestao_compra_{'_'.join(selected_clients)}.xlsx" if selected_clients else "sugestao_compra_mercado.xlsx"
    return dcc.send_data_frame(df_sugestao.to_excel, filename, index=False)


# --- CALLBACKS DA PÁGINA DE CONFIGURAÇÕES ---
# ... (manter os callbacks da página de configurações como estão) ...

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
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    # Validação para coluna de data antes de usar .dt
    if ano_filtro:
        if 'data_faturamento' in df_vendas.columns and pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
            if isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.year >= ano_filtro[0]) & (df_vendas['data_faturamento'].dt.year <= ano_filtro[1])]
            else:
                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
        else:
            print('Coluna data_faturamento ausente ou não é datetime:', df_vendas.get('data_faturamento'))
    # Validação para coluna de data antes de usar .dt no filtro de mês
    if mes_filtro:
        if 'data_faturamento' in df_vendas.columns and pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
            if isinstance(mes_filtro, (list, tuple)) and len(mes_filtro) == 2:
                df_vendas = df_vendas[(df_vendas['data_faturamento'].dt.month >= mes_filtro[0]) & (df_vendas['data_faturamento'].dt.month <= mes_filtro[1])]
            else:
                df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
        else:
            print('Coluna data_faturamento ausente ou não é datetime:', df_vendas.get('data_faturamento'))
    if clientes:
        df_vendas = df_vendas[df_vendas['cod_cliente'].isin(clientes)]
    # Ajuste do nome da coluna de canal de vendas
    if canais:
        canal_col = None
        for col in df_vendas.columns:
            if col.lower().replace(' ', '_') == 'canal_distribuicao':
                canal_col = col
                break
        if canal_col:
            df_vendas = df_vendas[df_vendas[canal_col].isin(canais)]
        else:
            print('Coluna de canal de vendas não encontrada:', df_vendas.columns)
    # Ajuste do nome da coluna de hierarquia de produto
    if hierarquias:
        hier_cols = [col for col in df_vendas.columns if col.lower().startswith('hier_produto')]
        if hier_cols:
            mask = pd.Series(False, index=df_vendas.index)
            for col in hier_cols:
                mask |= df_vendas[col].isin(hierarquias)
            df_vendas = df_vendas[mask]
        else:
            print('Colunas de hierarquia de produto não encontradas:', df_vendas.columns)
    df_kpis = kpis.calculate_kpis_por_cliente(df_vendas, df_cotacoes)
    if top_n:
        df_kpis = df_kpis.head(top_n)
    if not df_kpis.empty:
        fig_scatter = px.scatter(df_kpis, x='total_comprado_valor', y='dias_sem_compra', color='pct_mix_produtos', hover_data=['cliente'], title='Valor x Dias Sem Compra')
    else:
        fig_scatter = {}
    tabela = dbc.Table.from_dataframe(df_kpis, striped=True, bordered=True, hover=True, responsive=True) if not df_kpis.empty else dbc.Alert('Nenhum dado disponível.', color='warning')
    # Histórico
    historico_map = {
        'total_comprado_valor': 'valor_faturado',
        'total_comprado_qtd': 'quantidade_faturada',
        'mix_produtos': 'mix_produtos',
        'pct_mix_produtos': 'pct_mix_produtos'
    }
    # Validação para DataFrame vazio e colunas de data
    if df_vendas.empty or 'data_faturamento' not in df_vendas.columns or not pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
        fig_scatter = {}
        tabela = dbc.Alert('Nenhum dado disponível.', color='warning')
        fig_hist = {}
        return fig_scatter, tabela, fig_hist
    # Bloco do gráfico histórico corretamente indentado
    if not df_vendas.empty and historico_kpis:
        # Mapear colunas de vendas para os KPIs selecionados
        colunas_existentes = [historico_map.get(kpi, kpi) for kpi in historico_kpis if historico_map.get(kpi, kpi) in df_vendas.columns]
        if colunas_existentes:
            # Adicionar coluna de ano
            df_vendas['ano'] = df_vendas['data_faturamento'].dt.year.astype(int)
            clientes_unicos = df_vendas['cliente'].unique()
            if isinstance(ano_filtro, (list, tuple)) and len(ano_filtro) == 2:
                anos = list(range(ano_filtro[0], ano_filtro[1] + 1))
            else:
                anos = sorted(df_vendas['ano'].unique())
            # Agrupar por ano e cliente
            df_hist = df_vendas.groupby(['ano', 'cliente'])[colunas_existentes].sum().reset_index()
            # Garantir todos os anos/clientes no grid
            df_grid = pd.MultiIndex.from_product([anos, clientes_unicos], names=['ano', 'cliente']).to_frame(index=False)
            df_hist = df_grid.merge(df_hist, on=['ano', 'cliente'], how='left')
            for col in colunas_existentes:
                df_hist[col] = df_hist[col].fillna(0)
            df_hist = df_hist.sort_values(['ano', 'cliente'])
            df_hist_melt = df_hist.melt(id_vars=['ano', 'cliente'], value_vars=colunas_existentes, var_name='variable', value_name='value')
            fig_hist = px.line(df_hist_melt, x='ano', y='value', color='cliente', line_dash='variable', markers=True,
                               title='Histórico Anual dos Indicadores por Cliente')
            fig_hist.update_xaxes(type='category', tickmode='array', tickvals=anos, tickformat='d', categoryorder='category ascending')
            fig_hist.update_traces(text=None, textposition=None, mode='lines+markers')
            fig_hist.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1), height=600, margin=dict(t=100))
        else:
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