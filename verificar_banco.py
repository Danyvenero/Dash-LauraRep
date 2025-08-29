import sqlite3
import pandas as pd

# Conectar ao banco de dados
db_path = r"c:\Users\danyv\OneDrive - LAURA REPRESENTACOES LTDA\WORKSPACE\dash_laurarep\instance\database.sqlite"

try:
    conn = sqlite3.connect(db_path)
    
    # Verificar estrutura da tabela clean_vendas
    print("=== ESTRUTURA DA TABELA clean_vendas ===")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(clean_vendas)")
    colunas = cursor.fetchall()
    
    print("Colunas na tabela clean_vendas:")
    for i, (cid, name, type_, notnull, default, pk) in enumerate(colunas):
        print(f"{i+1:2d}. {name} ({type_})")
    
    # Carregar uma amostra para verificar dados
    df = pd.read_sql_query("SELECT * FROM clean_vendas LIMIT 5", conn)
    print(f"\n=== AMOSTRA DE DADOS ===")
    print(f"Total de colunas: {len(df.columns)}")
    print(f"Primeiras 5 linhas:")
    print(df.head())
    
    # Verificar colunas de hierarquia
    print(f"\n=== COLUNAS DE HIERARQUIA/PRODUTO ===")
    hier_cols = [col for col in df.columns if any(term in col.lower() for term in ['hier', 'produto', 'categoria', 'familia'])]
    print(f"Colunas encontradas: {hier_cols}")
    
    if hier_cols:
        for col in hier_cols:
            valores = pd.read_sql_query(f"SELECT DISTINCT {col} FROM clean_vendas WHERE {col} IS NOT NULL LIMIT 10", conn)[col].tolist()
            print(f"{col}: {valores}")
    
    # Verificar dados específicos para o teste
    print(f"\n=== TESTE COM FILTROS DA IMAGEM ===")
    
    # Filtro por ano 2023
    query_2023 = """
    SELECT COUNT(*) as total_2023
    FROM clean_vendas 
    WHERE strftime('%Y', data_faturamento) = '2023'
    """
    result = pd.read_sql_query(query_2023, conn)
    print(f"Registros em 2023: {result['total_2023'].iloc[0]}")
    
    # Filtro por janeiro 2023
    query_jan_2023 = """
    SELECT COUNT(*) as total_jan_2023
    FROM clean_vendas 
    WHERE strftime('%Y', data_faturamento) = '2023'
    AND strftime('%m', data_faturamento) = '01'
    """
    result = pd.read_sql_query(query_jan_2023, conn)
    print(f"Registros em Janeiro 2023: {result['total_jan_2023'].iloc[0]}")
    
    # Verificar se existe hierarquia CONTROLS
    if hier_cols:
        for col in hier_cols:
            query_controls = f"""
            SELECT COUNT(*) as total_controls
            FROM clean_vendas 
            WHERE {col} LIKE '%CONTROLS%'
            """
            try:
                result = pd.read_sql_query(query_controls, conn)
                print(f"Registros com CONTROLS em {col}: {result['total_controls'].iloc[0]}")
            except Exception as e:
                print(f"Erro ao consultar {col}: {e}")
    
    conn.close()
    
except Exception as e:
    print(f"Erro ao conectar ao banco: {e}")
