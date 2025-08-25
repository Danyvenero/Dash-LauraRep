-- webapp/schema.sql

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS vendas;
DROP TABLE IF EXISTS cotacoes;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS raw_vendas;
DROP TABLE IF EXISTS raw_materiais_cotados;
DROP TABLE IF EXISTS raw_propostas_anuais;

CREATE TABLE users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP );
CREATE TABLE settings ( key TEXT PRIMARY KEY, value_json TEXT NOT NULL );

CREATE TABLE raw_vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_filename TEXT NOT NULL, fingerprint TEXT NOT NULL, uploaded_by INTEGER NOT NULL, uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "Unidade de Negócio" TEXT, "Canal Distribuição" TEXT, "ID_Cli" TEXT, "Cliente" TEXT, "Hier. Produto 1" TEXT, "Hier. Produto 2" TEXT, "Hier. Produto 3" TEXT,
    "Doc. Vendas" TEXT, "Material" TEXT, "Produto" TEXT, "Data Faturamento" TEXT, "Data" TEXT, "Cidade do Cliente" TEXT,
    "Qtd. Entrada" REAL, "Vlr. Entrada" REAL, "Qtd. Carteira" REAL, "Vlr. Carteira" REAL, "Qtd. ROL" REAL, "Vlr. ROL" REAL,
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

CREATE TABLE raw_materiais_cotados (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_filename TEXT NOT NULL, fingerprint TEXT NOT NULL, uploaded_by INTEGER NOT NULL, uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "Cotação" TEXT, "Cod. Cliente" TEXT, "Cliente" TEXT, "Material" TEXT, "Descrição" TEXT, "Quantidade" REAL, "Preço Líquido Total" REAL,
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

CREATE TABLE raw_propostas_anuais (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_filename TEXT NOT NULL, fingerprint TEXT NOT NULL, uploaded_by INTEGER NOT NULL, uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "Número da Cotação" TEXT, "Número da Revisão" TEXT, "Código do Cliente" TEXT, "Nome do Cliente" TEXT, "Data de Criação" TEXT, "Status da Cotação" TEXT, "Valor Total" REAL,
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

CREATE TABLE vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cod_cliente TEXT NOT NULL, cliente TEXT, material TEXT, produto TEXT, unidade_negocio TEXT, canal_distribuicao TEXT,
    data_entrada DATE, data_faturamento DATE, quantidade_entrada REAL, quantidade_carteira REAL, quantidade_faturada REAL,
    valor_entrada REAL, valor_carteira REAL, valor_faturado REAL
);

CREATE TABLE cotacoes ( id INTEGER PRIMARY KEY AUTOINCREMENT, cod_cliente TEXT NOT NULL, cliente TEXT, material TEXT, data DATE, quantidade REAL NOT NULL );

CREATE INDEX idx_vendas_cliente_data ON vendas (cod_cliente, data_faturamento);
CREATE INDEX idx_cotacoes_cliente_data ON cotacoes (cod_cliente, data);