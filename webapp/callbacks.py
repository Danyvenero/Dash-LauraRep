"""
Callbacks principais da aplicação
"""

from dash import Input, Output, State, callback_context, dash_table
import dash
import pandas as pd
from webapp import app
from webapp.auth import authenticated_callback
from utils import (
    load_vendas_data, 
    load_cotacoes_data, 
    load_produtos_cotados_data,
    KPICalculator, 
    VisualizationGenerator,
    SENTINEL_ALL
)

# Importa outros módulos de callbacks
try:
    import webapp.callbacks_uploads
    print("✅ Callbacks de upload carregados")
except ImportError as e:
    print(f"⚠️ Erro ao carregar callbacks de upload: {e}")

try:
    import webapp.callbacks_downloads
    print("✅ Callbacks de download carregados")  
except ImportError as e:
    print(f"⚠️ Callbacks de download não disponíveis: {e}")

# Instâncias dos calculadores
kpi_calc = KPICalculator()
viz_gen = VisualizationGenerator()

# Stores para dados
from dash import dcc
import dash_bootstrap_components as dbc

# Callback para carregar opções dos filtros globais
@app.callback(
    [Output('global-filtro-cliente', 'options'),
     Output('global-filtro-hierarquia', 'options'),
     Output('global-filtro-canal', 'options')],
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
@authenticated_callback
def update_filter_options(pathname):
    """Atualiza opções dos filtros globais"""
    try:
        # Carrega dados
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            return [], [], []
        
        # Opções de clientes
        cliente_options = []
        if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
            clientes_unique = vendas_df[['cod_cliente', 'cliente']].drop_duplicates()
            cliente_options = [
                {'label': f"{row['cod_cliente']} -- {row['cliente']}", 'value': row['cod_cliente']}
                for _, row in clientes_unique.iterrows()
                if not pd.isna(row['cod_cliente']) and not pd.isna(row['cliente'])
            ]
        
        # Opções de hierarquia de produto
        hierarquia_options = []
        for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
            if col in vendas_df.columns:
                unique_vals = vendas_df[col].dropna().unique()
                for val in unique_vals:
                    if val not in [opt['value'] for opt in hierarquia_options]:
                        hierarquia_options.append({'label': str(val), 'value': str(val)})
        
        # Opções de canal
        canal_options = []
        if 'canal_distribuicao' in vendas_df.columns:
            unique_canais = vendas_df['canal_distribuicao'].dropna().unique()
            canal_options = [{'label': str(canal), 'value': str(canal)} for canal in unique_canais]
        
        return cliente_options, hierarquia_options, canal_options
        
    except Exception as e:
        print(f"Erro ao atualizar filtros: {e}")
        return [], [], []

# Callback para KPIs da visão geral
@app.callback(
    [Output('kpi-entrada-pedidos', 'children'),
     Output('kpi-valor-carteira', 'children'), 
     Output('kpi-faturamento', 'children'),
     Output('kpi-entrada-variacao', 'children'),
     Output('kpi-carteira-variacao', 'children'),
     Output('kpi-faturamento-variacao', 'children'),
     Output('kpis-unidades-negocio', 'children')],
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value')],
    prevent_initial_call=True
)
@authenticated_callback
def update_overview_kpis(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal):
    """Atualiza KPIs da visão geral"""
    try:
        # Carrega dados
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_df = load_produtos_cotados_data()
        
        # Prepara filtros
        filters = {
            'ano': filtro_ano,
            'mes': filtro_mes,
            'cliente': filtro_cliente,
            'hierarquia_produto': filtro_hierarquia,
            'canal': filtro_canal
        }
        
        # Calcula KPIs gerais
        kpis_gerais = kpi_calc.calculate_general_kpis(vendas_df, cotacoes_df, produtos_df, filters)
        
        # Formata valores principais
        entrada_valor = f"R$ {kpis_gerais['entrada_pedidos']['valor']:,.0f}"
        carteira_valor = f"R$ {kpis_gerais['valor_carteira']['valor']:,.0f}"
        faturamento_valor = f"R$ {kpis_gerais['faturamento']['valor']:,.0f}"
        
        # Formata variações
        def format_variation(var):
            if var > 0:
                return f"↗️ +{var:.1f}%"
            elif var < 0:
                return f"↘️ {var:.1f}%"
            else:
                return "➡️ 0%"
        
        entrada_var = format_variation(kpis_gerais['entrada_pedidos']['variacao'])
        carteira_var = format_variation(kpis_gerais['valor_carteira']['variacao'])
        faturamento_var = format_variation(kpis_gerais['faturamento']['variacao'])
        
        # KPIs por unidade de negócio
        kpis_un = kpi_calc.calculate_business_unit_kpis(vendas_df, filters)
        
        un_cards = []
        for un, dados in kpis_un.items():
            color = "success" if dados['variacao'] > 0 else "danger" if dados['variacao'] < 0 else "secondary"
            
            card = dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dash.html.H6(f"R$ {dados['faturamento']:,.0f}", className=f"text-{color}"),
                        dash.html.P(str(un), className="small text-muted mb-1"),
                        dash.html.P(format_variation(dados['variacao']), className="small")
                    ])
                ], className="kpi-card")
            ], width=12, md=6, lg=2)
            un_cards.append(card)
        
        return (entrada_valor, carteira_valor, faturamento_valor,
                entrada_var, carteira_var, faturamento_var, un_cards)
        
    except Exception as e:
        print(f"Erro ao calcular KPIs: {e}")
        return "R$ 0", "R$ 0", "R$ 0", "0%", "0%", "0%", []

# Callback para gráfico de evolução
@app.callback(
    Output('grafico-evolucao-vendas', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value')],
    prevent_initial_call=True
)
@authenticated_callback
def update_evolution_chart(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal):
    """Atualiza gráfico de evolução de vendas"""
    try:
        vendas_df = load_vendas_data()
        
        filters = {
            'ano': filtro_ano,
            'mes': filtro_mes,
            'cliente': filtro_cliente,
            'hierarquia_produto': filtro_hierarquia,
            'canal': filtro_canal
        }
        
        fig = viz_gen.create_evolution_chart(vendas_df, filters)
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de evolução: {e}")
        return viz_gen._create_empty_chart("Erro ao carregar dados")

# Callback para tabela de KPIs por cliente
@app.callback(
    [Output('tabela-kpis-clientes', 'data'),
     Output('tabela-kpis-clientes', 'page_size')],
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('table-page-size-clientes', 'value')],
    prevent_initial_call=True
)
@authenticated_callback
def update_clients_table(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, page_size):
    """Atualiza tabela de KPIs por cliente"""
    try:
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_df = load_produtos_cotados_data()
        
        filters = {
            'ano': filtro_ano,
            'mes': filtro_mes,
            'cliente': filtro_cliente,
            'hierarquia_produto': filtro_hierarquia,
            'canal': filtro_canal
        }
        
        client_kpis_df = kpi_calc.calculate_client_kpis(vendas_df, cotacoes_df, produtos_df, filters)
        
        if client_kpis_df.empty:
            return [], page_size or 25
        
        return client_kpis_df.to_dict('records'), page_size or 25
        
    except Exception as e:
        print(f"Erro ao calcular KPIs de clientes: {e}")
        return [], 25

# Callback para gráfico de status dos clientes
@app.callback(
    Output('grafico-status-clientes', 'figure'),
    [Input('tabela-kpis-clientes', 'data')],
    prevent_initial_call=True
)
@authenticated_callback
def update_client_status_chart(table_data):
    """Atualiza gráfico de status dos clientes"""
    try:
        if not table_data:
            return viz_gen._create_empty_chart("Sem dados de clientes")
        
        client_kpis_df = pd.DataFrame(table_data)
        fig = viz_gen.create_client_status_chart(client_kpis_df)
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de status: {e}")
        return viz_gen._create_empty_chart("Erro ao processar dados")

# Callback para gráfico de bolhas de produtos
@app.callback(
    Output('grafico-bolhas-produtos', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('filter-top-produtos', 'value'),
     Input('filter-top-clientes-bolhas', 'value'),
     Input('filter-color-scale', 'value')],
    prevent_initial_call=True
)
@authenticated_callback
def update_bubble_chart(filtro_ano, filtro_mes, filtro_cliente, top_produtos, top_clientes, color_scale):
    """Atualiza gráfico de bolhas de produtos"""
    try:
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_df = load_produtos_cotados_data()
        
        filters = {
            'ano': filtro_ano,
            'mes': filtro_mes,
            'cliente': filtro_cliente
        }
        
        fig = viz_gen.create_bubble_chart(
            vendas_df, cotacoes_df, produtos_df,
            top_produtos or 20, top_clientes or 20, 
            color_scale or 'weg_blue', filters
        )
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de bolhas: {e}")
        return viz_gen._create_empty_chart("Erro ao carregar dados de produtos")

# Callback para gráfico de Pareto
@app.callback(
    Output('grafico-pareto-produtos', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value')],
    prevent_initial_call=True
)
@authenticated_callback
def update_pareto_chart(filtro_ano, filtro_mes, filtro_cliente):
    """Atualiza gráfico de Pareto de produtos"""
    try:
        vendas_df = load_vendas_data()
        
        filters = {
            'ano': filtro_ano,
            'mes': filtro_mes,
            'cliente': filtro_cliente
        }
        
        fig = viz_gen.create_pareto_chart(vendas_df, filters)
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de Pareto: {e}")
        return viz_gen._create_empty_chart("Erro ao processar dados de produtos")


# Callback para atualizar título da página
@app.callback(
    Output('page-title', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def update_page_title(pathname):
    """Atualiza o título da página baseado na URL"""
    
    titles = {
        '/app/overview': 'Visão Geral',
        '/app/clients': 'KPIs por Cliente', 
        '/app/products': 'Mix de Produtos',
        '/app/funnel': 'Funil & Ações',
        '/app/insights': 'Insights IA',
        '/app/config': 'Configurações',
        '/app': 'Visão Geral',
        '/': 'Visão Geral'
    }
    
    return titles.get(pathname, 'Dashboard WEG')


print("✅ Callbacks principais registrados com sucesso")