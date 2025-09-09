-- Schema do banco de dados SQLite para Dashboard WEG
-- Gerado automaticamente em 08/09/2025

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de datasets
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    uploaded_by INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vendas_fingerprint TEXT,
    cotacoes_fingerprint TEXT,
    produtos_cotados_fingerprint TEXT,
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- Tabela de vendas
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
);

-- Tabela de cotações
CREATE TABLE IF NOT EXISTS cotacoes (
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
);

-- Tabela de produtos cotados
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
);

-- Tabela de configurações
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_vendas_cliente_data ON vendas(cod_cliente, data);
CREATE INDEX IF NOT EXISTS idx_vendas_material ON vendas(material);
CREATE INDEX IF NOT EXISTS idx_vendas_data_faturamento ON vendas(data_faturamento);
CREATE INDEX IF NOT EXISTS idx_vendas_unidade_negocio ON vendas(unidade_negocio);

CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente_data ON cotacoes(cod_cliente, data, numero_cotacao);
CREATE INDEX IF NOT EXISTS idx_cotacoes_numero ON cotacoes(numero_cotacao);

CREATE INDEX IF NOT EXISTS idx_produtos_cotados_cotacao ON produtos_cotados(cotacao);
CREATE INDEX IF NOT EXISTS idx_produtos_cotados_material ON produtos_cotados(material);
CREATE INDEX IF NOT EXISTS idx_produtos_cotados_cliente ON produtos_cotados(cod_cliente);

-- Usuário padrão (senha: admin123)
INSERT OR IGNORE INTO users (username, password_hash, is_active)
VALUES ('admin', 'pbkdf2:sha256:260000$rZxQD8UJ$e9e8a5d7a8a1c7f3d5c9a8b1f2e4d6c8a0b2d4f6e8a1c3d5f7b9e1c3d5f7b9e1', 1);

-- Configurações padrão
INSERT OR REPLACE INTO settings (key, value_json) VALUES 
('business_unit_thresholds', '{"WAU": {"baixo": 50000, "medio": 100000, "alto": 200000}, "WEN": {"baixo": 75000, "medio": 150000, "alto": 300000}, "WMO-C": {"baixo": 60000, "medio": 120000, "alto": 250000}, "WMO-I": {"baixo": 80000, "medio": 160000, "alto": 320000}, "WDS": {"baixo": 40000, "medio": 80000, "alto": 160000}}'),
('app_version', '"1.0.0"'),
('last_update', '"2025-09-08"');
