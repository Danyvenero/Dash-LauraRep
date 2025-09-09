"""
Módulo webapp - Interface web do Dashboard WEG
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask import Flask
from utils import init_db

# Configuração do servidor Flask
server = Flask(__name__)
server.secret_key = 'weg-dashboard-secret-key-2025-laura-rep'

# Configuração de sessão
server.config.update(
    SESSION_COOKIE_SECURE=False,  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hora
)

# Registra comandos CLI personalizados
from webapp import cli
cli.init_app(server)

# Inicialização da aplicação Dash
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder='../assets',
    title="Dashboard WEG - Laura Representações",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Configurações da aplicação
app.config.suppress_callback_exceptions = True

# Inicializa o banco de dados
init_db()

# Layout principal será definido em layouts.py
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

print("✅ Webapp inicializado com sucesso")
