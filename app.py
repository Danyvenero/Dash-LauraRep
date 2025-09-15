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

# Callback removido - já está implementado em webapp/callbacks.py

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard WEG - Laura Representações...")
    print("✅ App Dash inicializado com configurações funcionais")
    print("✅ Layout principal definido")
    print("✅ Roteamento configurado")
    print("✅ Sistema de login configurado")
    print("📊 Acesse: http://127.0.0.1:8050")
    print("👤 Login padrão: admin / admin123")
    
    app.run(debug=True, host='127.0.0.1', port=8050)
