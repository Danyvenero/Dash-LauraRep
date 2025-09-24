import dash
from dash import html, Input, Output, callback

# Este é um callback de teste para diagnosticar o problema da tabela de produtos.
# Ele tem como alvo o mesmo 'Output' do callback problemático.
# Se este texto aparecer na tela, significa que o problema não está no layout
# ou no registro do callback, mas sim na lógica interna do 
# 'produtos_table_callback_new.py'.

@callback(
    Output('produtos-table-container', 'children', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True  # Alterado para True para evitar execução na carga inicial antes do pathname estar pronto
)
def simple_test_callback(pathname):
    if pathname in ["/produtos", "/app/products"]:
        print(">>> EXECUTANDO CALLBACK DE TESTE SIMPLES <<<")
        return html.Div([
            html.H4("--- MENSAGEM DE TESTE ---"),
            html.P("Se você está vendo esta mensagem, o callback de teste está funcionando."),
            html.P(f"A página atual é: {pathname}"),
            html.P("O problema está na lógica do callback 'produtos_table_callback_new.py', não no layout.")
        ])
    return dash.no_update

