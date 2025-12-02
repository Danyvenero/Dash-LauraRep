"""
Database connection and session management
"""

import sqlite3
from contextlib import contextmanager
from flask import Flask, g
import os

# Caminho do banco de dados
DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../../instance/database.sqlite'
)


@contextmanager
def get_db_connection():
    """Context manager para conexão com o banco"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db():
    """Retorna uma conexão com o banco de dados (deprecated - use get_db_connection)"""
    return get_db_connection()


def init_database():
    """Inicializa o banco de dados se necessário"""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # O schema já é criado pelo setup_database.py
    # Esta função apenas verifica se o banco existe
