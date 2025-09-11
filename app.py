"""
Aplicação Dash - Sistema de Gestão Comercial WEG
Data: 08/09/2025
Desenvolvido do zero seguindo especificação técnica
"""

from webapp import app, server
from webapp.layouts import get_layout
from dash import Input, Output, html

# Database migration on startup
def ensure_database_schema():
    """Ensure database has correct schema before starting app"""
    try:
        from migrate_db import migrate_database
        print("🔧 Checking database schema...")
        migrate_database()
        print("✅ Database schema verified")
    except Exception as e:
        print(f"⚠️  Database migration warning: {e}")

# Run migration before imports to ensure schema is correct
ensure_database_schema()

# Importa callbacks
import webapp.callbacks
import webapp.auth

# Callback principal de roteamento
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=False  # MUDANÇA: Permitir execução inicial
)
def display_page(pathname):
    """Controla roteamento e exibição de páginas"""
    print(f"🔄 display_page executado para pathname: {pathname}")
    
    # Obtém layout da página
    layout = get_layout(pathname)
    
    return layout

# Callback para conteúdo principal baseado na página
@app.callback(
    Output('page-main-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=False  # MUDANÇA: Permitir execução inicial
)
def display_main_content(pathname):
    """Exibe conteúdo principal baseado na página atual"""
    print(f"🔄 display_main_content executado para pathname: {pathname}")
    from webapp.layouts import (
        create_overview_layout, 
        create_clients_layout, 
        create_products_layout,
        create_analytics_layout,
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
    elif pathname == '/app/analytics':
        return create_analytics_layout()
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
    
    app.run(debug=True, host='127.0.0.1', port=8050)
