"""
Callback para tabela de produtos com dados reais e filtros funcionais
"""

from dash import Input, Output, callback, html, dcc
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

print("🔥 PRODUTOS TABLE CALLBACK FINAL SENDO CARREGADO!")

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [
        Input("filter-material-table", "value"),
        Input("filter-top-produtos", "value"), 
        Input("btn-refresh-produtos", "n_clicks"),
        Input("url", "pathname")
    ],
    prevent_initial_call=False
)
def update_produtos_table_with_filters(filter_materials, top_produtos, refresh_clicks, pathname):
    """
    Carrega a tabela de produtos com filtros aplicados e dados reais
    """
    try:
        print(f"🔥 CALLBACK DE PRODUTOS EXECUTADO! Pathname: {pathname}")
        print(f"   Filtros: materials={filter_materials}, top={top_produtos}")
        logger.info("Callback executado com filtros aplicados")
        
        # Se não está na página de produtos, retorna placeholder
        if pathname != "/produtos":
            print(f"⚠️ Não está na página de produtos: {pathname}")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    f"Página atual: {pathname}. Navegue para /produtos para ver a tabela."
                ], color="info")
            ])
        
        print("✅ Na página de produtos - carregando dados reais...")
        
        # Valores padrão para os filtros
        if top_produtos is None or top_produtos <= 0:
            top_produtos = 20
        page_size = 25
            
        # Carregar dados reais
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
        if filter_materials and len(filter_materials) > 0:
            print(f"   🔍 Aplicando filtro por materiais: {filter_materials}")
            produtos_data = produtos_data[produtos_data['material'].isin(filter_materials)]
            logger.info(f"Filtro aplicado: {len(produtos_data)} produtos restantes após filtrar por material")
            
            if produtos_data.empty:
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-filter me-2"),
                        f"Nenhum produto encontrado para os materiais selecionados."
                    ], color="info"),
                    dbc.Button([
                        html.I(className="fas fa-times me-1"),
                        "Limpar Filtros"
                    ], id="btn-clear-filters", color="outline-secondary", size="sm")
                ])
        
        # Criar tabela HTML simples e funcional  
        logger.info(f"Criando tabela para {len(produtos_data)} produtos")
        
        # Preparar dados para exibição (limitado à página)
        produtos_display = produtos_data.head(page_size).copy()
        
        # Formatar valores monetários
        for col in ['faturamento_total', 'valor_medio']:
            if col in produtos_display.columns:
                produtos_display[col + '_formatted'] = produtos_display[col].apply(
                    lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                )
        
        # Formatar quantidades  
        for col in ['quantidade_total', 'recorrencia_compra']:
            if col in produtos_display.columns:
                produtos_display[col + '_formatted'] = produtos_display[col].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else "0"
                )
        
        # Criar header da tabela
        header = html.Thead([
            html.Tr([
                html.Th("Material", className="bg-primary text-white", style={'width': '120px'}),
                html.Th("Produto", className="bg-primary text-white"),
                html.Th("Hierarquia", className="bg-primary text-white", style={'width': '120px'}),
                html.Th("Faturamento Total", className="bg-primary text-white text-end", style={'width': '140px'}),
                html.Th("Valor Médio", className="bg-primary text-white text-end", style={'width': '120px'}),
                html.Th("Quantidade", className="bg-primary text-white text-end", style={'width': '100px'}),
                html.Th("Recorrência", className="bg-primary text-white text-end", style={'width': '100px'})
            ])
        ])
        
        # Criar linhas da tabela
        rows = []
        for idx, row in produtos_display.iterrows():
            # Determinar nome da coluna de hierarquia
            hierarquia_val = row.get('hier_produto_1', row.get('hierarquia', 'N/A'))
            
            rows.append(html.Tr([
                html.Td(row.get('material', ''), className="font-monospace fw-bold"),
                html.Td(
                    html.Div(row.get('produto', ''), 
                    style={'maxWidth': '300px', 'wordWrap': 'break-word', 'lineHeight': '1.2'}
                    )
                ),
                html.Td(hierarquia_val, className="text-muted small"),
                html.Td(
                    row.get('faturamento_total_formatted', 
                    f"R$ {row.get('faturamento_total', 0):,.2f}"), 
                    className="text-end fw-bold text-success"
                ),
                html.Td(
                    row.get('valor_medio_formatted', 
                    f"R$ {row.get('valor_medio', 0):,.2f}"), 
                    className="text-end"
                ),
                html.Td(
                    row.get('quantidade_total_formatted', 
                    f"{row.get('quantidade_total', 0):,.0f}"), 
                    className="text-end"
                ),
                html.Td(
                    row.get('recorrencia_compra_formatted', 
                    f"{row.get('recorrencia_compra', 0):,.0f}"), 
                    className="text-end text-info fw-bold"
                )
            ], className="table-row-hover"))
        
        tbody = html.Tbody(rows)
        
        # Criar tabela completa
        table = html.Table([
            header,
            tbody
        ], 
        className="table table-striped table-hover table-sm mb-0"
        )
        
        # Informações de paginação
        total_produtos = len(produtos_data)
        showing_count = min(page_size, total_produtos)
        
        pagination_info = html.Div([
            dbc.Row([
                dbc.Col([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        f"Mostrando {showing_count} de {total_produtos} produtos"
                    ], className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.Badge([
                        html.I(className="fas fa-chart-line me-1"),
                        "Analytics Ativo"
                    ], color="success", className="float-end")
                ], width=4)
            ])
        ], className="mt-2 px-3 pb-2")
        
        # Criar título dinâmico baseado nos filtros
        title_parts = [f"Top {total_produtos} Produtos por Faturamento"]
        if filter_materials and len(filter_materials) > 0:
            if len(filter_materials) == 1:
                title_parts.append(f"(Material: {filter_materials[0]})")
            else:
                title_parts.append(f"({len(filter_materials)} materiais selecionados)")
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H6([
                            html.I(className="fas fa-table me-2"),
                            " ".join(title_parts)
                        ], className="mb-0 d-inline"),
                        dbc.Badge([
                            f"Página: {page_size} itens"
                        ], color="primary", className="float-end")
                    ])
                ]),
                dbc.CardBody([
                    html.Div([
                        table
                    ], className="table-responsive", style={'maxHeight': '600px', 'overflowY': 'auto'}),
                    pagination_info
                ], className="p-0")
            ])
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
    Processa dados para análise de produtos com tratamento de erro
    """
    try:
        if vendas_df is None or vendas_df.empty:
            logger.warning("DataFrame de vendas vazio ou None")
            return pd.DataFrame()
        
        logger.info(f"Processando dados de vendas: {len(vendas_df)} registros")
        
        # Verificar se as colunas necessárias existem
        required_cols = ['material', 'produto']
        existing_cols = [col for col in required_cols if col in vendas_df.columns]
        
        if len(existing_cols) < 2:
            logger.error(f"Colunas obrigatórias não encontradas. Esperado: {required_cols}, Encontrado: {existing_cols}")
            return pd.DataFrame()
        
        # Determinar coluna de hierarquia
        hier_col = None
        for col in ['hier_produto_1', 'hierarquia', 'hierarquia_produto']:
            if col in vendas_df.columns:
                hier_col = col
                break
        
        # Determinar coluna de valor
        valor_col = None
        for col in ['vlr_rol', 'valor_liquido', 'valor_faturamento', 'valor_total']:
            if col in vendas_df.columns:
                valor_col = col
                break
        
        # Determinar coluna de quantidade
        qty_col = None
        for col in ['qtd_rol', 'quantidade', 'qtde', 'qty']:
            if col in vendas_df.columns:
                qty_col = col
                break
        
        if not valor_col:
            logger.error("Nenhuma coluna de valor encontrada")
            return pd.DataFrame()
        
        # Preparar colunas para agrupamento
        group_cols = ['material', 'produto']
        if hier_col:
            group_cols.append(hier_col)
        
        # Análise de produtos por vendas
        agg_dict = {valor_col: ['count', 'mean', 'sum']}
        if qty_col:
            agg_dict[qty_col] = 'sum'
        
        produtos_vendas = vendas_df.groupby(group_cols).agg(agg_dict).round(2)
        
        # Renomear colunas
        new_cols = ['recorrencia_compra', 'valor_medio', 'faturamento_total']
        if qty_col:
            new_cols.append('quantidade_total')
        
        produtos_vendas.columns = new_cols
        produtos_vendas = produtos_vendas.reset_index()
        
        # Se não tem hierarquia, adicionar coluna vazia
        if 'hierarquia' not in produtos_vendas.columns and hier_col:
            produtos_vendas['hierarquia'] = produtos_vendas[hier_col]
        elif 'hierarquia' not in produtos_vendas.columns:
            produtos_vendas['hierarquia'] = 'N/A'
        
        # Ordenar por faturamento total e pegar top N
        produtos_analytics = produtos_vendas.sort_values('faturamento_total', ascending=False).head(top_n)
        
        logger.info(f"Processados {len(produtos_analytics)} produtos para análise")
        
        return produtos_analytics
        
    except Exception as e:
        logger.error(f"Erro ao processar analytics de produtos: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

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
        if pathname != "/produtos":
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

print("✅ Callback de produtos com dados reais e filtros carregado!")