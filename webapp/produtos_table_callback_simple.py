"""
Callback simplificado para teste de produtos - forçar execução
"""

from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔥 CALLBACK SIMPLIFICADO SENDO CARREGADO!")

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [Input("url", "pathname")],
    prevent_initial_call=False
)
def update_produtos_table_simple(pathname):
    """
    Callback simplificado para forçar exibição da tabela
    """
    print(f"🔥 CALLBACK SIMPLES EXECUTADO! Pathname: {pathname}")
    logger.info(f"Callback executado com pathname: {pathname}")
    
    # SEMPRE retorna algo para testar se o callback executa
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-table me-2"),
                    f"Teste de Callback - Página: {pathname or 'Não definida'}"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    html.Strong("✅ Callback funcionando! "),
                    f"Página detectada: {pathname or 'inicial'}"
                ], color="success"),
                
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Material", className="bg-primary text-white"),
                            html.Th("Produto", className="bg-primary text-white"),
                            html.Th("Status", className="bg-primary text-white")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("TEST001", className="font-monospace fw-bold"),
                            html.Td("Produto de Teste 1"),
                            html.Td([
                                dbc.Badge("Callback OK", color="success")
                            ])
                        ]),
                        html.Tr([
                            html.Td("TEST002", className="font-monospace fw-bold"),
                            html.Td("Produto de Teste 2"),
                            html.Td([
                                dbc.Badge("Funcionando", color="info")
                            ])
                        ])
                    ])
                ], className="table table-striped"),
                
                html.Hr(),
                html.P([
                    html.I(className="fas fa-clock me-1"),
                    "Callback executado com sucesso. Se você vê esta mensagem, o sistema está funcionando."
                ], className="text-muted small")
            ])
        ])
    ])

print("✅ Callback simplificado carregado!")