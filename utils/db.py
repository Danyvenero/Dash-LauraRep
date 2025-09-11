"""
Módulo de configuração e operações do banco de dados SQLite
"""

import sqlite3
import hashlib
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import json
from typing import Optional, Dict, Any, List
from .data_standardization import apply_vendas_standardization, apply_cotacoes_standardization

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
            numero_revisao TEXT,
            linhas_cotacao TEXT,
            status_cotacao TEXT,
            cod_cliente TEXT,
            cliente TEXT,
            data DATE,
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
    """Salva dataset no banco com validação inteligente de duplicatas"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calcula fingerprints
    vendas_fp = calculate_fingerprint(vendas_df) if vendas_df is not None else None
    cotacoes_fp = calculate_fingerprint(cotacoes_df) if cotacoes_df is not None else None
    produtos_fp = calculate_fingerprint(produtos_cotados_df) if produtos_cotados_df is not None else None
    
    # 🔍 VALIDAÇÃO DE DUPLICATAS POR FINGERPRINT
    print(f"🔍 Verificando duplicatas...")
    print(f"  - Vendas FP: {vendas_fp[:10] if vendas_fp else 'None'}...")
    print(f"  - Cotações FP: {cotacoes_fp[:10] if cotacoes_fp else 'None'}...")
    print(f"  - Produtos FP: {produtos_fp[:10] if produtos_fp else 'None'}...")
    
    # LÓGICA CORRIGIDA: Só verifica duplicatas se pelo menos um fingerprint não for NULL
    duplicate_conditions = []
    params = []
    
    if vendas_fp:
        duplicate_conditions.append("vendas_fingerprint = ?")
        params.append(vendas_fp)
    
    if cotacoes_fp:
        duplicate_conditions.append("cotacoes_fingerprint = ?")
        params.append(cotacoes_fp)
    
    if produtos_fp:
        duplicate_conditions.append("produtos_cotados_fingerprint = ?")
        params.append(produtos_fp)
    
    # Só verifica duplicatas se houver pelo menos um fingerprint para comparar
    duplicate_check = None
    if duplicate_conditions:
        query = f"""
            SELECT id, name, uploaded_at 
            FROM datasets 
            WHERE {' OR '.join(duplicate_conditions)}
            ORDER BY uploaded_at DESC 
            LIMIT 1
        """
        duplicate_check = cursor.execute(query, params).fetchone()
    
    if duplicate_check:
        existing_id, existing_name, existing_date = duplicate_check
        print(f"⚠️  DADOS IDÊNTICOS DETECTADOS!")
        print(f"   Dataset existente: '{existing_name}' (ID: {existing_id})")
        print(f"   Uploaded em: {existing_date}")
        print(f"   ❌ Upload cancelado para evitar duplicação")
        
        conn.close()
        return existing_id  # Retorna ID do dataset existente
    
    
    # 🆕 DADOS NOVOS - Prosseguir com inserção
    print(f"✅ Dados novos detectados - prosseguindo com inserção")
    
    # Insere o dataset
    cursor.execute("""
        INSERT INTO datasets (name, uploaded_by, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint)
        VALUES (?, ?, ?, ?, ?)
    """, (name, uploaded_by, vendas_fp, cotacoes_fp, produtos_fp))
    
    dataset_id = cursor.lastrowid
    print(f"🆔 Novo dataset criado com ID: {dataset_id}")
    
    # 📊 ESTRATÉGIA INTELIGENTE DE INSERÇÃO
    records_summary = {
        'vendas_novos': 0,
        'cotacoes_novas': 0, 
        'produtos_novos': 0,
        'vendas_atualizados': 0,
        'cotacoes_atualizadas': 0,
        'produtos_atualizados': 0
    }
    
    # Salva os dados das vendas com validação inteligente
    if vendas_df is not None and not vendas_df.empty:
        vendas_df_copy = vendas_df.copy()
        vendas_df_copy['dataset_id'] = dataset_id
        
        # Filtra apenas colunas válidas para a tabela vendas
        valid_vendas_columns = [
            'dataset_id', 'cod_cliente', 'cliente', 'material', 'produto', 
            'unidade_negocio', 'canal_distribuicao', 'hier_produto_1', 
            'hier_produto_2', 'hier_produto_3', 'data', 'data_faturamento',
            'qtd_entrada', 'vlr_entrada', 'qtd_carteira', 'vlr_carteira',
            'qtd_rol', 'vlr_rol'
        ]
        columns_to_keep = [col for col in valid_vendas_columns if col in vendas_df_copy.columns]
        vendas_df_copy = vendas_df_copy[columns_to_keep]
        
        # 🔍 INSERÇÃO INTELIGENTE - Evita duplicatas por chave de negócio
        records_summary['vendas_novos'] = _smart_insert_vendas(conn, vendas_df_copy)
        print(f"📊 VENDAS: {records_summary['vendas_novos']} registros inseridos")
    
    # Salva os dados das cotações com validação inteligente
    if cotacoes_df is not None and not cotacoes_df.empty:
        cotacoes_df_copy = cotacoes_df.copy()
        cotacoes_df_copy['dataset_id'] = dataset_id
        
        # Filtra apenas colunas válidas para a tabela cotacoes
        valid_cotacoes_columns = [
            'dataset_id', 'numero_cotacao', 'numero_revisao', 
            'linhas_cotacao', 'status_cotacao', 'cod_cliente', 'cliente', 'data'
        ]
        columns_to_keep = [col for col in valid_cotacoes_columns if col in cotacoes_df_copy.columns]
        cotacoes_df_copy = cotacoes_df_copy[columns_to_keep]
        
        # 🔍 INSERÇÃO INTELIGENTE - Evita duplicatas por chave de negócio
        records_summary['cotacoes_novas'] = _smart_insert_cotacoes(conn, cotacoes_df_copy)
        print(f"📊 COTAÇÕES: {records_summary['cotacoes_novas']} registros inseridos")
    
    # Salva os dados dos produtos cotados com validação inteligente
    if produtos_cotados_df is not None and not produtos_cotados_df.empty:
        produtos_df_copy = produtos_cotados_df.copy()
        produtos_df_copy['dataset_id'] = dataset_id
        
        # Filtra apenas colunas válidas para a tabela produtos_cotados
        valid_produtos_columns = [
            'dataset_id', 'cotacao', 'cod_cliente', 'cliente', 
            'centro_fornecedor', 'material', 'descricao', 'quantidade',
            'preco_liquido_unitario', 'preco_liquido_total'
        ]
        columns_to_keep = [col for col in valid_produtos_columns if col in produtos_df_copy.columns]
        produtos_df_copy = produtos_df_copy[columns_to_keep]
        
        # 🔍 INSERÇÃO INTELIGENTE - Evita duplicatas por chave de negócio
        records_summary['produtos_novos'] = _smart_insert_produtos_cotados(conn, produtos_df_copy)
        print(f"📊 PRODUTOS COTADOS: {records_summary['produtos_novos']} registros inseridos")
    
    # 📈 RESUMO FINAL
    total_novos = records_summary['vendas_novos'] + records_summary['cotacoes_novas'] + records_summary['produtos_novos']
    print(f"✅ UPLOAD CONCLUÍDO!")
    print(f"   📊 Total de registros novos: {total_novos}")
    print(f"   💾 Dataset ID: {dataset_id}")
    
    conn.commit()
    conn.close()
    
    return dataset_id

def _smart_insert_vendas(conn, vendas_df: pd.DataFrame) -> int:
    """Inserção inteligente de vendas evitando duplicatas"""
    cursor = conn.cursor()
    inserted_count = 0
    
    for _, row in vendas_df.iterrows():
        # Chave de negócio para vendas: cod_cliente + material + data
        business_key = (row.get('cod_cliente'), row.get('material'), row.get('data'))
        
        # Verifica se já existe este registro
        existing = cursor.execute("""
            SELECT id FROM vendas 
            WHERE cod_cliente = ? AND material = ? AND data = ?
        """, business_key).fetchone()
        
        if not existing:
            # Insere novo registro
            columns = list(row.index)
            values = tuple(row.values)
            placeholders = ', '.join(['?' for _ in columns])
            
            cursor.execute(f"""
                INSERT INTO vendas ({', '.join(columns)})
                VALUES ({placeholders})
            """, values)
            inserted_count += 1
    
    return inserted_count

def _smart_insert_cotacoes(conn, cotacoes_df: pd.DataFrame) -> int:
    """Inserção inteligente de cotações evitando duplicatas"""
    cursor = conn.cursor()
    inserted_count = 0
    
    for _, row in cotacoes_df.iterrows():
        # Chave de negócio para cotações: numero_cotacao + numero_revisao
        business_key = (row.get('numero_cotacao'), row.get('numero_revisao'))
        
        # Verifica se já existe este registro
        existing = cursor.execute("""
            SELECT id FROM cotacoes 
            WHERE numero_cotacao = ? AND numero_revisao = ?
        """, business_key).fetchone()
        
        if not existing:
            # Insere novo registro
            columns = list(row.index)
            values = tuple(row.values)
            placeholders = ', '.join(['?' for _ in columns])
            
            cursor.execute(f"""
                INSERT INTO cotacoes ({', '.join(columns)})
                VALUES ({placeholders})
            """, values)
            inserted_count += 1
    
    return inserted_count

def _smart_insert_produtos_cotados(conn, produtos_df: pd.DataFrame) -> int:
    """Inserção inteligente de produtos cotados evitando duplicatas"""
    cursor = conn.cursor()
    inserted_count = 0
    
    for _, row in produtos_df.iterrows():
        # Chave de negócio para produtos cotados: cotacao + material
        business_key = (row.get('cotacao'), row.get('material'))
        
        # Verifica se já existe este registro
        existing = cursor.execute("""
            SELECT id FROM produtos_cotados 
            WHERE cotacao = ? AND material = ?
        """, business_key).fetchone()
        
        if not existing:
            # Insere novo registro
            columns = list(row.index)
            values = tuple(row.values)
            placeholders = ', '.join(['?' for _ in columns])
            
            cursor.execute(f"""
                INSERT INTO produtos_cotados ({', '.join(columns)})
                VALUES ({placeholders})
            """, values)
            inserted_count += 1
    
    return inserted_count

def get_dataset_statistics() -> Dict:
    """Retorna estatísticas de datasets e duplicatas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Estatísticas gerais
    stats = {}
    
    # Total de datasets
    stats['total_datasets'] = cursor.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    
    # Total de registros por tabela
    stats['total_vendas'] = cursor.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
    stats['total_cotacoes'] = cursor.execute("SELECT COUNT(*) FROM cotacoes").fetchone()[0]
    stats['total_produtos_cotados'] = cursor.execute("SELECT COUNT(*) FROM produtos_cotados").fetchone()[0]
    
    # Datasets únicos por fingerprint
    stats['unique_vendas_fps'] = cursor.execute("""
        SELECT COUNT(DISTINCT vendas_fingerprint) FROM datasets 
        WHERE vendas_fingerprint IS NOT NULL
    """).fetchone()[0]
    
    stats['unique_cotacoes_fps'] = cursor.execute("""
        SELECT COUNT(DISTINCT cotacoes_fingerprint) FROM datasets 
        WHERE cotacoes_fingerprint IS NOT NULL
    """).fetchone()[0]
    
    stats['unique_produtos_fps'] = cursor.execute("""
        SELECT COUNT(DISTINCT produtos_cotados_fingerprint) FROM datasets 
        WHERE produtos_cotados_fingerprint IS NOT NULL
    """).fetchone()[0]
    
    # Datasets mais recentes
    recent_datasets = cursor.execute("""
        SELECT name, uploaded_at, 
               CASE WHEN vendas_fingerprint IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_vendas,
               CASE WHEN cotacoes_fingerprint IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_cotacoes,
               CASE WHEN produtos_cotados_fingerprint IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_produtos
        FROM datasets 
        ORDER BY uploaded_at DESC 
        LIMIT 5
    """).fetchall()
    
    stats['recent_datasets'] = [
        {
            'name': row[0],
            'uploaded_at': row[1], 
            'tem_vendas': row[2],
            'tem_cotacoes': row[3],
            'tem_produtos': row[4]
        } for row in recent_datasets
    ]
    
    conn.close()
    return stats

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

from .cache_manager import cached_dataframe

@cached_dataframe(ttl_seconds=1800)  # Cache por 30 minutos (otimizado)
def load_vendas_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de vendas do banco com cache otimizado"""
    start_time = time.time()
    print(f"💾 Cache MISS para load_vendas_data - executando...")
    
    conn = get_connection()
    
    try:
        if dataset_id:
            query = "SELECT * FROM vendas WHERE dataset_id = ?"
            df = pd.read_sql_query(query, conn, params=(dataset_id,))
        else:
            # Carrega TODOS os dados de vendas (de todos os datasets) - OTIMIZADO
            # Usa query mais eficiente com índices
            query = """
            SELECT * FROM vendas 
            ORDER BY dataset_id DESC, id ASC
            """
            df = pd.read_sql_query(query, conn)
        
        # Otimização: processa conversões em lote
        if not df.empty:
            # Converte colunas de data de forma mais eficiente
            date_columns = ['data', 'data_faturamento']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce', cache=True)
            
            # Aplica padronizações antes de retornar os dados
            df = apply_vendas_standardization(df)
        
        end_time = time.time()
        print(f"⏱️ load_vendas_data executado em {end_time - start_time:.2f}s")
        print(f"📊 Dados carregados: {len(df)} registros de vendas")
        
        return df
        
    finally:
        conn.close()

@cached_dataframe(ttl_seconds=300)  # Cache por 5 minutos
def load_cotacoes_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de cotações do banco com cache"""
    conn = get_connection()
    
    if dataset_id:
        query = "SELECT * FROM cotacoes WHERE dataset_id = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_id,))
    else:
        # Carrega TODOS os dados de cotações (de todos os datasets)
        query = "SELECT * FROM cotacoes ORDER BY dataset_id DESC, id ASC"
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    # Converte coluna de data
    if not df.empty and 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Aplica padronizações antes de retornar os dados
    if not df.empty:
        df = apply_cotacoes_standardization(df)
    
    return df

def load_produtos_cotados_data(dataset_id: Optional[int] = None) -> pd.DataFrame:
    """Carrega dados de produtos cotados do banco"""
    conn = get_connection()
    
    if dataset_id:
        query = "SELECT * FROM produtos_cotados WHERE dataset_id = ?"
        df = pd.read_sql_query(query, conn, params=(dataset_id,))
    else:
        # Carrega TODOS os dados de produtos cotados (de todos os datasets)
        query = "SELECT * FROM produtos_cotados ORDER BY dataset_id DESC, id ASC"
        df = pd.read_sql_query(query, conn)
    
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

# Funções de limpeza de dados
def clear_vendas_data():
    """Limpa todos os dados de vendas do banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM vendas")
        affected_rows = cursor.rowcount
        
        # Remove datasets que só tinham vendas ou atualiza fingerprints
        cursor.execute("""
            DELETE FROM datasets 
            WHERE vendas_fingerprint IS NOT NULL 
            AND cotacoes_fingerprint IS NULL 
            AND produtos_cotados_fingerprint IS NULL
        """)
        
        # Para datasets que têm outros dados, apenas limpa o fingerprint de vendas
        cursor.execute("UPDATE datasets SET vendas_fingerprint = NULL WHERE vendas_fingerprint IS NOT NULL")
        
        conn.commit()
        print(f"✅ {affected_rows} registros de vendas removidos")
        return affected_rows
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao limpar dados de vendas: {e}")
        raise e
    finally:
        conn.close()

def clear_cotacoes_data():
    """Limpa todos os dados de cotações do banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM cotacoes")
        affected_rows = cursor.rowcount
        
        # Remove datasets que só tinham cotações ou atualiza fingerprints
        cursor.execute("""
            DELETE FROM datasets 
            WHERE cotacoes_fingerprint IS NOT NULL 
            AND vendas_fingerprint IS NULL 
            AND produtos_cotados_fingerprint IS NULL
        """)
        
        # Para datasets que têm outros dados, apenas limpa o fingerprint de cotações
        cursor.execute("UPDATE datasets SET cotacoes_fingerprint = NULL WHERE cotacoes_fingerprint IS NOT NULL")
        
        conn.commit()
        print(f"✅ {affected_rows} registros de cotações removidos")
        return affected_rows
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao limpar dados de cotações: {e}")
        raise e
    finally:
        conn.close()

def clear_materiais_data():
    """Limpa todos os dados de materiais cotados do banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM produtos_cotados")
        affected_rows = cursor.rowcount
        
        # Remove datasets que só tinham materiais ou atualiza fingerprints
        cursor.execute("""
            DELETE FROM datasets 
            WHERE produtos_cotados_fingerprint IS NOT NULL 
            AND vendas_fingerprint IS NULL 
            AND cotacoes_fingerprint IS NULL
        """)
        
        # Para datasets que têm outros dados, apenas limpa o fingerprint de materiais
        cursor.execute("UPDATE datasets SET produtos_cotados_fingerprint = NULL WHERE produtos_cotados_fingerprint IS NOT NULL")
        
        conn.commit()
        print(f"✅ {affected_rows} registros de materiais cotados removidos")
        return affected_rows
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao limpar dados de materiais: {e}")
        raise e
    finally:
        conn.close()

def clear_all_data():
    """Limpa TODOS os dados do banco (vendas, cotações, materiais e datasets)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Remove dados das tabelas principais
        cursor.execute("DELETE FROM vendas")
        vendas_count = cursor.rowcount
        
        cursor.execute("DELETE FROM cotacoes")
        cotacoes_count = cursor.rowcount
        
        cursor.execute("DELETE FROM produtos_cotados")
        materiais_count = cursor.rowcount
        
        cursor.execute("DELETE FROM datasets")
        datasets_count = cursor.rowcount
        
        conn.commit()
        
        total_count = vendas_count + cotacoes_count + materiais_count + datasets_count
        print(f"✅ Limpeza total concluída:")
        print(f"  - {vendas_count} registros de vendas")
        print(f"  - {cotacoes_count} registros de cotações")
        print(f"  - {materiais_count} registros de materiais")
        print(f"  - {datasets_count} datasets")
        print(f"  - Total: {total_count} registros removidos")
        
        return {
            'vendas': vendas_count,
            'cotacoes': cotacoes_count,
            'materiais': materiais_count,
            'datasets': datasets_count,
            'total': total_count
        }
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao limpar todos os dados: {e}")
        raise e
    finally:
        conn.close()

def get_data_statistics():
    """Retorna estatísticas dos dados no banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Contar registros de cada tabela
        cursor.execute("SELECT COUNT(*) FROM vendas")
        stats['vendas'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cotacoes")
        stats['cotacoes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM produtos_cotados")
        stats['materiais'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM datasets")
        stats['datasets'] = cursor.fetchone()[0]
        
        return stats
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return {'vendas': 0, 'cotacoes': 0, 'materiais': 0, 'datasets': 0}
    finally:
        conn.close()
