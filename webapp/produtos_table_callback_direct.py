"""
Callback direto e simples para forçar carregamento da tabela de produtos
"""

from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import sys
import os

# Adicionar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_vendas_data
from webapp import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 CALLBACK DIRETO DE PRODUTOS SENDO CARREGADO!")

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [Input("url", "pathname")],
    prevent_initial_call=False
)
def force_load_produtos_table(pathname):
    """
    Força carregamento direto da tabela de produtos
    """
    print(f"🚀 CALLBACK DIRETO EXECUTADO! Pathname: {pathname}")
    
    try:
        # Sempre carrega dados independente da URL
        print("📊 Carregando dados diretos...")
        
        # Carregar dados de vendas
        vendas_df = load_vendas_data()
        
        if vendas_df is None or vendas_df.empty:
            print("❌ Dados de vendas vazios")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Erro: Nenhum dado de vendas encontrado."
                ], color="danger")
            ])
        
        print(f"✅ Dados carregados: {len(vendas_df)} registros")
        
        # Processar top produtos direto
        if 'vlr_rol' not in vendas_df.columns:
            print("❌ Coluna vlr_rol não encontrada")
            return html.Div([
                dbc.Alert("Erro: Coluna de valor não encontrada", color="danger")
            ])
        
        # Agrupar por produto e calcular faturamento
        produtos_summary = vendas_df.groupby(['material', 'produto']).agg({
            'vlr_rol': ['sum', 'count', 'mean']
        }).round(2)
        
        # Renomear colunas
        produtos_summary.columns = ['faturamento_total', 'recorrencia', 'valor_medio']
        produtos_summary = produtos_summary.reset_index()
        
        # Ordenar por faturamento e pegar top 20
        produtos_top = produtos_summary.sort_values('faturamento_total', ascending=False).head(20)
        
        print(f"✅ Processados {len(produtos_top)} produtos")
        
        # Criar tabela HTML direto
        rows = []
        for idx, row in produtos_top.iterrows():
            rows.append(html.Tr([
                html.Td(str(row['material']), className="font-monospace fw-bold"),
                html.Td(
                    html.Div(str(row['produto']), 
                    style={'maxWidth': '400px', 'wordWrap': 'break-word'}
                    )
                ),
                html.Td(f"R$ {row['faturamento_total']:,.2f}", 
                        className="text-end fw-bold text-success"),
                html.Td(f"R$ {row['valor_medio']:,.2f}", 
                        className="text-end"),
                html.Td(f"{row['recorrencia']:,.0f}", 
                        className="text-end text-info fw-bold")
            ]))
        
        table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th("Material", className="bg-primary text-white"),
                    html.Th("Produto", className="bg-primary text-white"),
                    html.Th("Faturamento Total", className="bg-primary text-white text-end"),
                    html.Th("Valor Médio", className="bg-primary text-white text-end"),
                    html.Th("Recorrência", className="bg-primary text-white text-end")
                ])
            ]),
            html.Tbody(rows)
        ], className="table table-striped table-hover")
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-table me-2"),
                        f"Top 20 Produtos por Faturamento ({len(vendas_df):,} registros processados)"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        html.Strong("✅ Dados carregados com sucesso! "),
                        f"Tabela gerada diretamente do banco de dados."
                    ], color="success", className="mb-3"),
                    
                    html.Div([
                        table
                    ], className="table-responsive"),
                    
                    html.Hr(),
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        f"Página: {pathname or 'inicial'} • Dados: {len(produtos_top)} produtos • ",
                        f"Base: {len(vendas_df):,} transações"
                    ], className="text-muted")
                ])
            ])
        ])
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        logger.error(f"Erro no callback direto: {e}")
        import traceback
        traceback.print_exc()
        
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                html.Strong("Erro: "),
                f"Falha ao carregar dados: {str(e)}"
            ], color="danger"),
            dbc.Card([
                dbc.CardBody([
                    html.H6("Debug Info:", className="mb-2"),
                    html.P(f"Pathname: {pathname}"),
                    html.P("Verifique os logs do terminal para mais detalhes.")
                ])
            ])
        ])

print("✅ Callback direto de produtos carregado!")