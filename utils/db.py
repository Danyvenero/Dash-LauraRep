# utils/db.py

import sqlite3
import click
import pandas as pd
from flask import current_app, g
from utils.security import hash_password

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE']
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def init_database():
    """Função standalone para inicialização do banco"""
    import os
    from flask import Flask
    
    # Criar app temporário para contexto
    app = Flask(__name__, instance_relative_config=True)
    app.config['DATABASE'] = 'instance/database.sqlite'
    
    # Criar diretório instance se não existir
    os.makedirs('instance', exist_ok=True)
    
    with app.app_context():
        # Ler e executar schema
        schema_path = 'schema.sql'
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                
            conn = sqlite3.connect(app.config['DATABASE'])
            conn.executescript(sql_script)
            conn.close()
        else:
            # Schema básico se arquivo não existir
            conn = sqlite3.connect(app.config['DATABASE'])
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    uploaded_by INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vendas_fingerprint TEXT,
                    cot_fingerprint TEXT,
                    FOREIGN KEY (uploaded_by) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER,
                    cod_cliente INTEGER,
                    cliente TEXT,
                    material INTEGER,
                    produto TEXT,
                    unidade_negocio TEXT,
                    data_faturamento DATE,
                    quantidade_faturada REAL,
                    valor_faturado REAL,
                    valor_entrada REAL,
                    valor_carteira REAL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id)
                );
                
                CREATE TABLE IF NOT EXISTS cotacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER,
                    cod_cliente INTEGER,
                    cliente TEXT,
                    material INTEGER,
                    data DATE,
                    quantidade REAL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id)
                );
                
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT
                );
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cod_cliente, data_faturamento);
                CREATE INDEX IF NOT EXISTS idx_vendas_material ON vendas(material);
                CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente ON cotacoes(cod_cliente, data);
                CREATE INDEX IF NOT EXISTS idx_cotacoes_material ON cotacoes(material);
            ''')
            conn.close()

@click.command('init-db')
def init_db_command():
    """Limpa os dados existentes e cria novas tabelas."""
    init_db()
    click.echo('Banco de dados inicializado.')

def add_user(username, password):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        db.commit()
        return True
    except db.IntegrityError:
        return False

def get_user_by_username(username):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    return user

def check_raw_fingerprint_exists(fingerprint, table_name):
    db = get_db()
    query = f"SELECT id FROM {table_name} WHERE fingerprint = ?"
    result = db.execute(query, (fingerprint,)).fetchone()
    return result is not None

def insert_raw_df(df, table_name, filename, fingerprint, user_id):
    db = get_db()
    df['source_filename'] = filename
    df['fingerprint'] = fingerprint
    df['uploaded_by'] = user_id
    try:
        df.to_sql(table_name, db, if_exists='append', index=False)
        db.commit()
        return len(df)
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados brutos: {e}")
        return 0

def get_all_users():
    db = get_db()
    users = db.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
    return users

def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

def wipe_all_transaction_data():
    db = get_db()
    try:
        db.execute("BEGIN TRANSACTION")
        db.execute("DELETE FROM vendas")
        db.execute("DELETE FROM cotacoes")
        db.execute("DELETE FROM raw_vendas")
        db.execute("DELETE FROM raw_materiais_cotados")
        db.execute("DELETE FROM raw_propostas_anuais")
        db.commit()
        return True
    except db.Error as e:
        db.rollback()
        print(f"Erro ao limpar o banco: {e}")
        return False

def get_raw_data_as_df(table_name):
    db = get_db()
    query = f'SELECT * FROM "{table_name}"'
    df = pd.read_sql_query(query, db)
    return df

def truncate_table(table_name):
    db = get_db()
    db.execute(f"DELETE FROM {table_name}")
    db.execute("DELETE FROM sqlite_sequence WHERE name=?", (table_name,))
    db.commit()
    print(f"Tabela {table_name} limpa com sucesso.")

def save_clean_df(df, table_name):
    db = get_db()
    try:
        df.to_sql(table_name, db, if_exists='append', index=False)
        db.commit()
        return len(df)
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar dados limpos: {e}")
        return 0

def get_clean_vendas_as_df():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM vendas")
    data = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    if not data:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(data, columns=columns)
    date_cols = ['data_entrada', 'data_faturamento']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def get_clean_cotacoes_as_df():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM cotacoes")
    data = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    if not data:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(data, columns=columns)
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    return df

@click.command('create-user')
@click.argument('username')
@click.argument('password')
def create_user_command(username, password):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        db.commit()
        click.echo(f'Usuário "{username}" criado com sucesso.')
    except db.IntegrityError:
        click.echo(f'Erro: Usuário "{username}" já existe.', err=True)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_user_command)