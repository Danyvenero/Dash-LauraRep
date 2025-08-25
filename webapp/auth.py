# webapp/auth.py
import dash
from dash import Output, Input, State, html, dcc
from flask import session
import dash_bootstrap_components as dbc # <-- Importação Essencial

from webapp import app
from utils.db import add_user, get_user_by_username
from utils.security import check_password
# Importa apenas os layouts compartilhados/de alto nível
from webapp.layouts import login_layout, cadastro_layout, app_layout

# --- CALLBACKS DE AUTENTICAÇÃO E CADASTRO ---
@app.callback(
    Output('url', 'pathname'),
    Output('login-error', 'children'),
    Input('login-button', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    prevent_initial_call=True
)
def login_callback(n_clicks, username, password):
    if not all([username, password]):
        return dash.no_update, dbc.Alert("Por favor, preencha o usuário e a senha.", color="warning")
    user = get_user_by_username(username)
    if user and check_password(user['password_hash'], password):
        session['user_id'] = user['id']
        return '/app/overview', None
    return dash.no_update, dbc.Alert("Usuário ou senha inválidos.", color="danger")

@app.callback(
    Output('cadastro-msg', 'children'),
    Input('cadastro-button', 'n_clicks'),
    State('cadastro-username', 'value'),
    State('cadastro-password', 'value'),
    State('cadastro-password-confirm', 'value'),
    prevent_initial_call=True
)
def cadastro_callback(n_clicks, username, pwd1, pwd2):
    if not all([username, pwd1, pwd2]):
        return dbc.Alert("Todos os campos são obrigatórios.", color="warning")
    if pwd1 != pwd2:
        return dbc.Alert("As senhas não coincidem.", color="danger")
    success = add_user(username, pwd1)
    if success:
        return dbc.Alert(["Usuário criado com sucesso! ", dcc.Link("Clique aqui para fazer o login.", href="/", className="alert-link")], color="success")
    else:
        return dbc.Alert(f"O nome de usuário '{username}' já está em uso.", color="danger")


# --- ROTEADOR DA APLICAÇÃO ---

# Callback 1: O "Guarda". Decide se mostra a tela de login ou a aplicação principal.
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def guard_layout(pathname):
    if pathname == '/logout':
        session.clear()
        return login_layout
    if 'user_id' not in session:
        if pathname == '/cadastro':
            return cadastro_layout
        return login_layout
    
    if pathname.startswith('/app'):
        return app_layout
        
    return dcc.Location(id='redirect-to-home', pathname='/app/overview')

# Callback 2: Alterna a visibilidade das páginas dentro da aplicação.
@app.callback(
    Output('page-overview-content', 'style'),
    Output('page-kpis-cliente-content', 'style'),
    Output('page-kpis-propostas-content', 'style'),
    Output('page-produtos-content', 'style'),
    Output('page-funil-content', 'style'),
    Output('page-config-content', 'style'),
    Input('url', 'pathname')
)
def render_page_content(pathname):
    hide = {'display': 'none'}
    show = {'display': 'block'}

    if pathname == '/app/kpis-cliente':
        return hide, show, hide, hide, hide, hide
    elif pathname == '/app/kpis-propostas':
        return hide, hide, show, hide, hide, hide
    elif pathname == '/app/produtos':
        return hide, hide, hide, show, hide, hide
    elif pathname == '/app/funil':
        return hide, hide, hide, hide, show, hide
    elif pathname == '/app/config':
        return hide, hide, hide, hide, hide, show
    
    # A página Visão Geral ('/app/overview') é a padrão
    return show, hide, hide, hide, hide, hide