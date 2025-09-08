"""
Aplicação Dash - Sistema de Gestão Comercial WEG
Data: 08/09/2025
Desenvolvido do zero seguindo especificação técnica
"""

from webapp import app, server
from webapp.layouts import get_layout
from dash import Input, Output, html

# Importa callbacks
import webapp.callbacks
import webapp.auth

# Callback principal de roteamento
@app.callback(
    [Output('page-content', 'children'),
     Output('page-title', 'children', allow_duplicate=True)],
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def display_page(pathname):
    """Controla roteamento e exibição de páginas"""
    
    # Define títulos das páginas
    titles = {
        '/app/overview': 'Visão Geral',
        '/app/clients': 'KPIs por Cliente', 
        '/app/products': 'Mix de Produtos',
        '/app/funnel': 'Funil & Ações',
        '/app/insights': 'Insights IA',
        '/app/config': 'Configurações',
        '/login': 'Login'
    }
    
    # Obtém layout da página
    layout = get_layout(pathname)
    
    # Obtém título da página
    title = titles.get(pathname, 'Dashboard WEG')
    
    return layout, title

# Callback para conteúdo principal baseado na página
@app.callback(
    Output('page-main-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def display_main_content(pathname):
    """Exibe conteúdo principal baseado na página atual"""
    from webapp.layouts import (
        create_overview_layout, 
        create_clients_layout, 
        create_products_layout,
        create_config_layout
    )
    from utils import is_authenticated
    
    if not is_authenticated():
        return html.Div()
    
    if pathname == '/app/overview' or pathname == '/app' or pathname == '/':
        return create_overview_layout()
    elif pathname == '/app/clients':
        return create_clients_layout() 
    elif pathname == '/app/products':
        return create_products_layout()
    elif pathname == '/app/config':
        return create_config_layout()
    elif pathname == '/app/funnel':
        return html.Div([
            html.H4("Funil & Ações"),
            html.P("Em desenvolvimento...")
        ])
    elif pathname == '/app/insights':
        return html.Div([
            html.H4("Insights IA"), 
            html.P("Em desenvolvimento...")
        ])
    else:
        return html.Div([
            html.H4("Página não encontrada"),
            html.P("A página solicitada não existe.")
        ])

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard WEG - Laura Representações...")
    print("✅ App Dash inicializado com configurações funcionais")
    print("✅ Layout principal definido")
    print("✅ Roteamento configurado")
    print("✅ Sistema de login configurado")
    print("📊 Acesse: http://127.0.0.1:8050")
    print("👤 Login padrão: admin / admin123")
    
    app.run_server(debug=True, host='127.0.0.1', port=8050)
