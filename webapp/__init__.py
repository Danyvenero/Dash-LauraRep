# webapp/__init__.py

import dash
import dash_bootstrap_components as dbc
from flask import Flask
from utils.db import init_app as init_db_app

server = Flask(__name__, instance_relative_config=True)

server.config.update(
    SECRET_KEY='uma-chave-secreta-muito-forte-deve-ser-usada-aqui',
    DATABASE='instance/database.sqlite'
)

init_db_app(server)

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    url_base_pathname='/'
)

from .layouts import main_layout
app.layout = main_layout

from . import auth
from . import callbacks_uploads
from . import callbacks
from . import callbacks_downloads
