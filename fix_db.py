#!/usr/bin/env python3
"""
Script to recreate database with correct schema
"""

import sqlite3
from pathlib import Path
import os

def recreate_database():
    """Recreate database with correct schema"""
    
    DB_PATH = Path('instance/database.sqlite')
    
    # Remove old database
    if DB_PATH.exists():
        print("🗑️  Removing old database...")
        os.remove(DB_PATH)
    
    # Create directory if not exists
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Create new database
    print("🔧 Creating new database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create datasets table
    cursor.execute("""
        CREATE TABLE datasets (
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
    
    # Create vendas table
    cursor.execute("""
        CREATE TABLE vendas (
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
    
    # Create cotacoes table WITH numero_revisao column
    cursor.execute("""
        CREATE TABLE cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            numero_cotacao TEXT,
            numero_revisao TEXT,
            linhas_cotacao TEXT,
            status_cotacao TEXT,
            cod_cliente TEXT,
            cliente TEXT,
            data DATE,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    """)
    
    # Create produtos_cotados table
    cursor.execute("""
        CREATE TABLE produtos_cotados (
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
    
    # Create settings table
    cursor.execute("""
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value_json TEXT
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_vendas_cliente_data ON vendas(cod_cliente, data)")
    cursor.execute("CREATE INDEX idx_vendas_material ON vendas(material)")
    cursor.execute("CREATE INDEX idx_vendas_data_faturamento ON vendas(data_faturamento)")
    cursor.execute("CREATE INDEX idx_vendas_unidade_negocio ON vendas(unidade_negocio)")
    
    cursor.execute("CREATE INDEX idx_cotacoes_cliente_data ON cotacoes(cod_cliente, data, numero_cotacao)")
    cursor.execute("CREATE INDEX idx_cotacoes_numero ON cotacoes(numero_cotacao)")
    
    cursor.execute("CREATE INDEX idx_produtos_cotados_cotacao ON produtos_cotados(cotacao)")
    cursor.execute("CREATE INDEX idx_produtos_cotados_material ON produtos_cotados(material)")
    cursor.execute("CREATE INDEX idx_produtos_cotados_cliente ON produtos_cotados(cod_cliente)")
    
    # Insert default user (admin/admin123)
    cursor.execute("""
        INSERT INTO users (username, password_hash, is_active)
        VALUES ('admin', 'pbkdf2:sha256:260000$rZxQD8UJ$e9e8a5d7a8a1c7f3d5c9a8b1f2e4d6c8a0b2d4f6e8a1c3d5f7b9e1c3d5f7b9e1', 1)
    """)
    
    conn.commit()
    
    # Verify table structure
    cursor.execute('PRAGMA table_info(cotacoes)')
    columns = cursor.fetchall()
    
    print("✅ Database created successfully!")
    print("\n📋 Cotacoes table columns:")
    for row in columns:
        print(f"  - {row[1]} ({row[2]})")
    
    conn.close()

if __name__ == "__main__":
    recreate_database()
