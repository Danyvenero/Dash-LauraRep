"""
Módulo de configuração e operações do banco de dados SQLite
"""

import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
from typing import Optional, Dict, Any, List

# Configuração do banco
DB_PATH = Path(__file__).parent.parent / "instance" / "database.sqlite"

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    # Cria o diretório instance se não existir
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de datasets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vendas_fingerprint TEXT,
            cotacoes_fingerprint TEXT,
            produtos_cotados_fingerprint TEXT,
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    """)
    
    # Tabela de vendas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            cod_cliente TEXT,
            cliente TEXT,
            material TEXT,
            produto TEXT,
            unidade_negocio TEXT,
            canal_distribuicao TEXT,
            hier_produto_1 TEXT,
            hier_produto_2 TEXT,
            hier_produto_3 TEXT,
            data DATE,
            data_faturamento DATE,
            qtd_entrada REAL,
            vlr_entrada REAL,
            qtd_carteira REAL,
            vlr_carteira REAL,
            qtd_rol REAL,
            vlr_rol REAL,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    """)
    
    # Tabela de cotações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            numero_cotacao TEXT,
            cod_cliente TEXT,
            cliente TEXT,
            material TEXT,
            data DATE,
            quantidade REAL,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    """)
    
    # Tabela de produtos cotados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos_cotados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            cotacao TEXT,
            cod_cliente TEXT,
            cliente TEXT,
            centro_fornecedor TEXT,
            material TEXT,
            descricao TEXT,
            quantidade REAL,
            preco_liquido_unitario REAL,
            preco_liquido_total REAL,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    """)
    
    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value_json TEXT
        )
    """)
    
    # Criar índices para performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_cliente_data ON vendas(cod_cliente, data)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_material ON vendas(material)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente_data ON cotacoes(cod_cliente, data, numero_cotacao)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cotacoes_material ON cotacoes(material)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_cotados_cotacao ON produtos_cotados(cotacao)")
    
    # Criar usuário admin padrão se não existir
    from werkzeug.security import generate_password_hash
    admin_hash = generate_password_hash('admin123')
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, is_active)
        VALUES (?, ?, 1)
    """, ('admin', admin_hash))
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso")

def get_connection():
    """Retorna uma conexão com o banco de dados"""
    return sqlite3.connect(DB_PATH)

def calculate_fingerprint(df: pd.DataFrame) -> str:
    """Calcula o fingerprint MD5 de um DataFrame"""
    if df is None or df.empty:
        return ""
    
    # Converte o DataFrame para string e calcula MD5
    df_string = df.to_string()
    return hashlib.md5(df_string.encode()).hexdigest()

def save_dataset(name: str, uploaded_by: int, 
                vendas_df: Optional[pd.DataFrame] = None,
                cotacoes_df: Optional[pd.DataFrame] = None,
                produtos_cotados_df: Optional[pd.DataFrame] = None) -> int:
    """Salva um novo dataset no banco"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calcula fingerprints
    vendas_fp = calculate_fingerprint(vendas_df) if vendas_df is not None else None
    cotacoes_fp = calculate_fingerprint(cotacoes_df) if cotacoes_df is not None else None
    produtos_fp = calculate_fingerprint(produtos_cotados_df) if produtos_cotados_df is not None else None
    
    # Insere o dataset
    cursor.execute("""
        INSERT INTO datasets (name, uploaded_by, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint)
        VALUES (?, ?, ?, ?, ?)
    """, (name, uploaded_by, vendas_fp, cotacoes_fp, produtos_fp))
    
    dataset_id = cursor.lastrowid
    
    # Salva os dados das vendas
    if vendas_df is not None and not vendas_df.empty:
        vendas_df_copy = vendas_df.copy()
        vendas_df_copy['dataset_id'] = dataset_id
        vendas_df_copy.to_sql('vendas', conn, if_exists='append', index=False)
    
    # Salva os dados das cotações
    if cotacoes_df is not None and not cotacoes_df.empty:
        cotacoes_df_copy = cotacoes_df.copy()
        cotacoes_df_copy['dataset_id'] = dataset_id
        cotacoes_df_copy.to_sql('cotacoes', conn, if_exists='append', index=False)
    
    # Salva os dados dos produtos cotados
    if produtos_cotados_df is not None and not produtos_cotados_df.empty:
        produtos_df_copy = produtos_cotados_df.copy()
        produtos_df_copy['dataset_id'] = dataset_id
        produtos_df_copy.to_sql('produtos_cotados', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    
    return dataset_id

def get_latest_dataset() -> Optional[Dict]:
    """Retorna informações do dataset mais recente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, uploaded_at, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint
        FROM datasets 
        ORDER BY uploaded_at DESC 
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'uploaded_at': row[2],
            'vendas_fingerprint': row[3],
            'cotacoes_fingerprint': row[4],
            'produtos_cotados_fingerprint': row[5]
        }
    return None

def load_vendas_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de vendas do banco"""
    conn = get_connection()
    
    if dataset_id:
        query = "SELECT * FROM vendas WHERE dataset_id = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_id,))
    else:
        # Carrega dados do dataset mais recente
        latest = get_latest_dataset()
        if latest:
            query = "SELECT * FROM vendas WHERE dataset_id = ?"
            df = pd.read_sql_query(query, conn, params=(latest['id'],))
        else:
            df = pd.DataFrame()
    
    conn.close()
    
    # Converte colunas de data
    if not df.empty:
        for col in ['data', 'data_faturamento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

def load_cotacoes_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de cotações do banco"""
    conn = get_connection()
    
    if dataset_id:
        query = "SELECT * FROM cotacoes WHERE dataset_id = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_id,))
    else:
        # Carrega dados do dataset mais recente
        latest = get_latest_dataset()
        if latest:
            query = "SELECT * FROM cotacoes WHERE dataset_id = ?"
            df = pd.read_sql_query(query, conn, params=(latest['id'],))
        else:
            df = pd.DataFrame()
    
    conn.close()
    
    # Converte coluna de data
    if not df.empty and 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    return df

def load_produtos_cotados_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de produtos cotados do banco"""
    conn = get_connection()
    
    if dataset_id:
        query = "SELECT * FROM produtos_cotados WHERE dataset_id = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_id,))
    else:
        # Carrega dados do dataset mais recente
        latest = get_latest_dataset()
        if latest:
            query = "SELECT * FROM produtos_cotados WHERE dataset_id = ?"
            df = pd.read_sql_query(query, conn, params=(latest['id'],))
        else:
            df = pd.DataFrame()
    
    conn.close()
    return df

def get_setting(key: str, default=None):
    """Recupera uma configuração do banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value_json FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return default

def save_setting(key: str, value: Any):
    """Salva uma configuração no banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    value_json = json.dumps(value)
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value_json)
        VALUES (?, ?)
    """, (key, value_json))
    
    conn.commit()
    conn.close()

def verify_user(username: str, password: str) -> Optional[Dict]:
    """Verifica credenciais de usuário"""
    from werkzeug.security import check_password_hash
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, password_hash, is_active 
        FROM users 
        WHERE username = ? AND is_active = 1
    """, (username,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and check_password_hash(row[2], password):
        return {
            'id': row[0],
            'username': row[1],
            'is_active': bool(row[3])
        }
    
    return None

# Constantes e helpers
SENTINEL_ALL = "__ALL__"

def _norm_year(v):
    """Normaliza valores de ano"""
    if v in (None, SENTINEL_ALL, "", "Todos"):
        return None
    try:
        return int(v)
    except:
        return None
