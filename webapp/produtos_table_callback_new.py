"""
Callback específico para tabela de produtos com dash_table funcional
Implementa filtro por material e interação completa
"""

from dash import Input, Output, State, callback, html, dcc, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import traceback
import sys
import os

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
from webapp import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔥 PRODUTOS TABLE CALLBACK NOVO SENDO CARREGADO!")

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [
        Input("filter-material-table", "value"),
        Input("filter-top-produtos", "value"),
        Input("table-page-size-produtos", "value"),
        Input("url", "pathname")
    ],
    prevent_initial_call=False
)
def update_produtos_table_with_filters(filter_materials, top_produtos, page_size, pathname):
    """
    Carrega a tabela de produtos com filtros aplicados usando dash_table
    """
    try:
        print(f"🔥 CALLBACK DE PRODUTOS EXECUTADO! Pathname: {pathname}")
        print(f"   Filtros: materials={filter_materials}, top={top_produtos}, page_size={page_size}")
        logger.info("Callback executado com filtros: materials=%s, top=%s, page_size=%s", 
                   filter_materials, top_produtos, page_size)
        
        # Se não está na página de produtos, retorna placeholder
        if pathname not in ["/produtos", "/app/products"]:
            print(f"⚠️ Não está na página de produtos: {pathname}")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Navegue para a página de produtos para visualizar os dados."
                ], color="info")
            ])
        
        print("✅ Na página de produtos - carregando dados...")
        logger.info("Carregando tabela de produtos com filtros")
        
        # Valores padrão para os filtros
        if top_produtos is None or top_produtos <= 0:
            top_produtos = 20
        if page_size is None or page_size <= 0:
            page_size = 25
            
        # Carregar dados
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_cotados_df = load_produtos_cotados_data()
        
        if vendas_df is None or vendas_df.empty:
            logger.warning("Dados de vendas vazios")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Nenhum dado de vendas encontrado. Verifique a configuração do banco de dados."
                ], color="warning")
            ])
        
        # Processar dados de produtos
        produtos_data = process_produtos_analytics(vendas_df, cotacoes_df, produtos_cotados_df, top_produtos)
        
        if produtos_data is None or produtos_data.empty:
            logger.warning("Dados de produtos processados vazios")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Nenhum produto encontrado."
                ], color="info")
            ])
        
        # Aplicar filtro por material se especificado
        filtered_data = produtos_data.copy()
        if filter_materials and len(filter_materials) > 0:
            print(f"   🔍 Aplicando filtro por materiais: {filter_materials}")
            filtered_data = filtered_data[filtered_data['material'].isin(filter_materials)]
            logger.info(f"Filtro aplicado: {len(filtered_data)} produtos restantes após filtrar por material")
            
            if filtered_data.empty:
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-filter me-2"),
                        f"Nenhum produto encontrado para os materiais selecionados: {', '.join(filter_materials)}"
                    ], color="info")
                ])
        
        # Preparar dados para dash_table
        logger.info(f"Criando dash_table para {len(filtered_data)} produtos")
        
        # Garantir que temos as colunas necessárias
        required_columns = ['material', 'produto', 'faturamento_total', 'valor_medio', 'quantidade_total', 'recorrencia_compra']
        
        # Adicionar hierarquia se disponível
        hierarquia_col = None
        if 'hier_produto_1' in filtered_data.columns:
            hierarquia_col = 'hier_produto_1'
        elif 'hierarquia' in filtered_data.columns:
            hierarquia_col = 'hierarquia'
        
        # Preparar DataFrame para exibição
        display_data = filtered_data.copy()
        
        # Renomear colunas para exibição
        column_mapping = {
            'material': 'Material',
            'produto': 'Produto',
            'faturamento_total': 'Faturamento Total',
            'valor_medio': 'Valor Médio',
            'quantidade_total': 'Quantidade',
            'recorrencia_compra': 'Recorrência'
        }
        
        if hierarquia_col:
            column_mapping[hierarquia_col] = 'Hierarquia'
        
        # Selecionar e renomear colunas
        columns_to_show = [col for col in column_mapping.keys() if col in display_data.columns]
        display_data = display_data[columns_to_show].rename(columns=column_mapping)
        
        # Criar colunas para dash_table
        table_columns = []
        for col in display_data.columns:
            if col in ['Faturamento Total', 'Valor Médio']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                })
            elif col in ['Quantidade', 'Recorrência']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.0f"}
                })
            else:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "text"
                })
        
        # Criar título dinâmico baseado nos filtros
        total_produtos = len(display_data)
        title_parts = [f"Top {min(top_produtos, total_produtos)} Produtos por Faturamento"]
        if filter_materials and len(filter_materials) > 0:
            if len(filter_materials) == 1:
                title_parts.append(f"(Material: {filter_materials[0]})")
            else:
                title_parts.append(f"({len(filter_materials)} materiais selecionados)")
        
        # Criar mensagem de sucesso
        success_message = html.Div([
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Dados carregados com sucesso! Tabela gerada diretamente do banco de dados. ({total_produtos:,} registros processados)"
            ], color="success", className="mb-3")
        ])
        
        # Criar dash_table
        data_table = dash_table.DataTable(
            id='produtos-table',
            columns=table_columns,
            data=display_data.to_dict('records'),
            page_size=page_size,
            sort_action='native',
            filter_action='native',
            row_selectable='multi',  # Permite seleção múltipla
            selected_rows=[],  # Inicialmente nenhuma linha selecionada
            style_table={
                'overflowX': 'auto',
                'minWidth': '100%'
            },
            style_header={
                'backgroundColor': '#0d6efd',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': ['Faturamento Total', 'Valor Médio']},
                    'textAlign': 'right',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': ['Quantidade', 'Recorrência']},
                    'textAlign': 'right'
                }
            ],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Produto'},
                    'width': '30%',
                    'maxWidth': '300px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                {
                    'if': {'column_id': 'Material'},
                    'width': '120px',
                    'fontFamily': 'monospace'
                }
            ]
        )
        
        return html.Div([
            success_message,
            html.H6([
                html.I(className="fas fa-table me-2"),
                " ".join(title_parts)
            ], className="mb-3"),
            data_table
        ])
        
    except Exception as e:
        logger.error(f"Erro geral ao carregar tabela de produtos: {e}")
        traceback.print_exc()
        
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                html.Strong("Erro de Sistema: "),
                f"Falha ao carregar a tabela. {str(e)}"
            ], color="danger")
        ])

def process_produtos_analytics(vendas_df, cotacoes_df, produtos_cotados_df, top_n=20):
    """
    Processa dados para análise de produtos
    """
    try:
        print(f"🔄 Processando analytics de produtos (top {top_n})...")
        
        if vendas_df is None or vendas_df.empty:
            logger.warning("DataFrame de vendas vazio")
            return pd.DataFrame()
        
        print(f"   📊 Dados de vendas: {len(vendas_df)} registros")
        
        # Verificar colunas obrigatórias
        required_cols = ['material', 'produto', 'vlr_rol']
        missing_cols = [col for col in required_cols if col not in vendas_df.columns]
        
        if missing_cols:
            logger.error(f"Colunas obrigatórias faltando: {missing_cols}")
            return pd.DataFrame()
        
        # Agrupar por material e produto para calcular métricas
        produtos_stats = vendas_df.groupby(['material', 'produto']).agg({
            'vlr_rol': ['sum', 'mean', 'count'],
            'qtd_vendida': 'sum' if 'qtd_vendida' in vendas_df.columns else 'count'
        }).round(2)
        
        # Flatten column names
        produtos_stats.columns = ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'quantidade_total']
        produtos_stats = produtos_stats.reset_index()
        
        # Adicionar hierarquia se disponível
        if 'hier_produto_1' in vendas_df.columns:
            hierarquia_map = vendas_df[['material', 'hier_produto_1']].drop_duplicates()
            produtos_stats = produtos_stats.merge(hierarquia_map, on='material', how='left')
        
        # Ordenar por faturamento total e pegar top N
        produtos_stats = produtos_stats.sort_values('faturamento_total', ascending=False).head(top_n)
        
        print(f"   ✅ Analytics processado: {len(produtos_stats)} produtos")
        
        return produtos_stats
        
    except Exception as e:
        logger.error(f"Erro ao processar analytics de produtos: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# Callback para popular opções do filtro de material
@callback(
    Output("filter-material-table", "options"),
    [Input("url", "pathname")],
    prevent_initial_call=False
)
def update_material_filter_options(pathname):
    """
    Popula as opções do filtro de material baseado nos dados disponíveis
    """
    try:
        # Só atualizar se estiver na página de produtos
        if pathname not in ["/produtos", "/app/products"]:
            return []
        
        print("🔄 Atualizando opções do filtro de materiais...")
        
        # Carregar dados de vendas para extrair materiais únicos
        vendas_df = load_vendas_data()
        
        if vendas_df is None or vendas_df.empty:
            logger.warning("Sem dados para popular filtro de materiais")
            return []
        
        # Verificar se existe coluna material
        if 'material' not in vendas_df.columns:
            logger.warning("Coluna 'material' não encontrada nos dados")
            return []
        
        # Extrair materiais únicos com informações do produto
        materials_info = vendas_df[['material', 'produto']].drop_duplicates()
        
        # Criar opções para o dropdown (limitado a 200 para performance)
        options = []
        for _, row in materials_info.head(200).iterrows():
            material = str(row['material'])
            produto = str(row['produto'])
            
            # Truncar nome do produto se muito longo
            produto_display = produto[:50] + "..." if len(produto) > 50 else produto
            
            options.append({
                "label": f"{material} - {produto_display}",
                "value": material
            })
        
        # Ordenar por material
        options = sorted(options, key=lambda x: x['value'])
        
        logger.info(f"Filtro de materiais populado com {len(options)} opções")
        print(f"   ✅ {len(options)} materiais carregados no filtro")
        
        return options
        
    except Exception as e:
        logger.error(f"Erro ao popular filtro de materiais: {e}")
        print(f"   ❌ Erro: {e}")
        return []

# Callback para limpar filtros da tabela
@callback(
    [Output("filter-material-table", "value"),
     Output("filter-top-produtos", "value"),
     Output("table-page-size-produtos", "value")],
    [Input("btn-clear-filters-produtos", "n_clicks")],
    prevent_initial_call=True
)
def clear_table_filters(n_clicks):
    """
    Limpa todos os filtros da tabela de produtos
    """
    if n_clicks:
        print("🗑️ Limpando filtros da tabela de produtos...")
        return [], 20, 25  # Valores padrão
    return no_update, no_update, no_update

# Callback para selecionar/desmarcar todas as linhas
@callback(
    Output("produtos-table", "selected_rows"),
    [Input("btn-select-all-produtos", "n_clicks"),
     Input("btn-deselect-all-produtos", "n_clicks")],
    [State("produtos-table", "data")],
    prevent_initial_call=True
)
def select_deselect_all_rows(select_clicks, deselect_clicks, table_data):
    """
    Seleciona ou desmarca todas as linhas da tabela
    """
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-select-all-produtos" and select_clicks:
        print("✅ Selecionando todas as linhas da tabela")
        return list(range(len(table_data))) if table_data else []
    elif button_id == "btn-deselect-all-produtos" and deselect_clicks:
        print("❌ Desmarcando todas as linhas da tabela")
        return []
    
    return no_update

if __name__ == "__main__":
    print("✅ Callback NOVO de produtos com filtros carregado!")