"""
App Dash mínimo para teste
"""

from dash import Dash, html, dcc, Input, Output, callback

app = Dash(__name__)

app.layout = html.Div([
    dcc.Input(id="inp", value="oi", type="text"),
    html.Button("Somar clique", id="btn", n_clicks=0),
    html.Div(id="out")
])

@callback(Output("out","children"),
          Input("inp","value"),
          Input("btn","n_clicks"))
def update(v, n):
    print(f"🔄 Callback executado! Valor: {v}, Cliques: {n}")
    return f"Valor: {v} | Cliques: {n}"

if __name__ == "__main__":
    print("🚀 Iniciando app de teste...")
    app.run(debug=True, port=8051)
