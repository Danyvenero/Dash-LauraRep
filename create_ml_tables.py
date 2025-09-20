#!/usr/bin/env python3
"""
Script para criar tabelas ML no banco de dados
"""

import sqlite3
from utils.db import get_connection

def create_ml_tables():
    """Cria as tabelas necessárias para o sistema ML"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Tabela de feedback de recomendações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_recomendacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL,
                cod_cliente TEXT NOT NULL,
                feedback_type TEXT NOT NULL CHECK (feedback_type IN ('positivo', 'negativo')),
                motivo TEXT,
                quantidade_sugerida REAL,
                usuario TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de ações de prospecção
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acoes_prospecao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL,
                cod_cliente TEXT NOT NULL,
                acao_tipo TEXT NOT NULL,
                acao_descricao TEXT,
                data_acao DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pendente',
                usuario TEXT
            )
        """)
        
        # Tabela de snapshot de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cliente_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cod_cliente TEXT NOT NULL,
                ultima_compra DATE,
                valor_total_12m REAL,
                frequencia_compras INTEGER,
                status_cliente TEXT,
                data_snapshot DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_material ON feedback_recomendacoes(material)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_cliente ON feedback_recomendacoes(cod_cliente)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_acoes_cliente ON acoes_prospecao(cod_cliente)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_cliente ON cliente_snapshot(cod_cliente)")
        
        conn.commit()
        print("✅ Tabelas ML criadas com sucesso!")
        
        # Verifica se as tabelas foram criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%feedback%' OR name LIKE '%acoes%' OR name LIKE '%snapshot%'")
        tables = cursor.fetchall()
        print(f"📋 Tabelas ML disponíveis: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_ml_tables()