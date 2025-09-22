"""
Callback de teste simples para a tabela de produtos
"""

from dash import Input, Output, State, callback, html, dcc
import dash_bootstrap_components as dbc
from webapp import app

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [Input("btn-refresh-produtos", "n_clicks")],
    prevent_initial_call=False
)
def test_produtos_callback(n_clicks):
    """Callback de teste simples"""
    print("🔥 CALLBACK DE TESTE EXECUTADO!")
    return dbc.Alert([
        html.I(className="fas fa-check-circle me-2"),
        "Callback de produtos funcionando! Dados de teste."
    ], color="success")

print("✅ Callback de teste carregado!")