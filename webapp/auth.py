"""
Módulo de autenticação da aplicação
"""

from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from webapp import app
from utils import verify_user, is_authenticated, login_user, logout_user, rate_limiter
from flask import session
import dash

def create_login_layout():
    """Cria layout da página de login"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("Dashboard WEG", className="text-center mb-0"),
                        html.P("Laura Representações", className="text-center text-muted mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="login-alerts"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("Usuário", html_for="login-username"),
                                dbc.Input(
                                    id="login-username",
                                    type="text",
                                    placeholder="Digite seu usuário",
                                    required=True
                                )
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Label("Senha", html_for="login-password"),
                                dbc.Input(
                                    id="login-password",
                                    type="password",
                                    placeholder="Digite sua senha",
                                    required=True
                                )
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Button(
                                    "Entrar",
                                    id="login-button",
                                    color="primary",
                                    className="w-100",
                                    size="lg"
                                )
                            ])
                        ])
                    ])
                ], className="shadow")
            ], width=12, md=6, lg=4)
        ], justify="center", className="min-vh-100 align-items-center")
    ], fluid=True, className="login-container")

# Callback para processar login
@app.callback(
    [Output('login-alerts', 'children'),
     Output('url', 'pathname')],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def process_login(n_clicks, username, password):
    """Processa tentativa de login"""
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    # Verifica se campos foram preenchidos
    if not username or not password:
        alert = dbc.Alert(
            "Por favor, preencha todos os campos.",
            color="warning",
            dismissable=True
        )
        return alert, dash.no_update
    
    # Verifica rate limiting
    client_id = f"login_{username}"
    if rate_limiter.is_rate_limited(client_id):
        remaining_time = 5  # minutos
        alert = dbc.Alert(
            f"Muitas tentativas de login. Tente novamente em {remaining_time} minutos.",
            color="danger",
            dismissable=True
        )
        return alert, dash.no_update
    
    # Verifica credenciais
    user_data = verify_user(username, password)
    
    if user_data:
        # Login bem-sucedido
        login_user(user_data)
        return dash.no_update, '/app/overview'
    else:
        # Registra tentativa falhada
        rate_limiter.record_attempt(client_id)
        remaining_attempts = rate_limiter.get_remaining_attempts(client_id)
        
        alert = dbc.Alert(
            f"Credenciais inválidas. Tentativas restantes: {remaining_attempts}",
            color="danger",
            dismissable=True
        )
        return alert, dash.no_update

# Callback para logout
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def process_logout(n_clicks):
    """Processa logout"""
    if n_clicks:
        logout_user()
        return '/login'
    return dash.no_update

def create_user_info_component():
    """Cria componente com informações do usuário logado"""
    if not is_authenticated():
        return html.Div()
    
    from utils.security import get_current_username
    username = get_current_username()
    
    return dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem("Perfil", disabled=True),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                "Sair",
                id="logout-button",
                className="text-danger"
            )
        ],
        label=f"👤 {username}",
        color="link",
        className="text-white"
    )

def require_login(layout_function):
    """Decorator para exigir login em layouts"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return create_login_layout()
        return layout_function(*args, **kwargs)
    return wrapper

# Guards para callbacks
def authenticated_callback(func):
    """Decorator para callbacks que requerem autenticação"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return dash.no_update
        return func(*args, **kwargs)
    return wrapper
