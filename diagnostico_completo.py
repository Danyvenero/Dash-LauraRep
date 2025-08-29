import sqlite3
import pandas as pd

# Conectar diretamente ao banco
db_path = r"c:\Users\danyv\OneDrive - LAURA REPRESENTACOES LTDA\WORKSPACE\dash_laurarep\instance\database.sqlite"

try:
    conn = sqlite3.connect(db_path)
    
    print("=== VERIFICANDO ESTRUTURA DAS TABELAS ===")
    
    # 1. Verificar colunas da tabela vendas
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(vendas)")
    colunas_vendas = cursor.fetchall()
    
    print("\nColunas na tabela VENDAS:")
    for i, (cid, name, type_, notnull, default, pk) in enumerate(colunas_vendas):
        print(f"{i+1:2d}. {name} ({type_})")
    
    # 2. Verificar dados de exemplo
    df = pd.read_sql_query("SELECT * FROM vendas LIMIT 3", conn)
    print(f"\n=== AMOSTRA DE DADOS DA TABELA VENDAS ===")
    print(df.to_string())
    
    # 3. Verificar valores de produtos/materiais
    print(f"\n=== VALORES DE PRODUTOS ===")
    produtos = pd.read_sql_query("SELECT DISTINCT produto FROM vendas WHERE produto IS NOT NULL LIMIT 20", conn)
    print("Produtos disponíveis:")
    print(produtos['produto'].tolist())
    
    # 4. Verificar valores que contêm CONTROLS
    print(f"\n=== PRODUTOS COM 'CONTROLS' ===")
    controls = pd.read_sql_query("SELECT DISTINCT produto FROM vendas WHERE produto LIKE '%CONTROLS%' OR produto LIKE '%controls%'", conn)
    print("Produtos com CONTROLS:")
    print(controls['produto'].tolist())
    
    # 5. Verificar dados de 2024/2025
    print(f"\n=== DADOS POR ANO ===")
    anos = pd.read_sql_query("""
        SELECT 
            strftime('%Y', data_faturamento) as ano,
            COUNT(*) as registros,
            COUNT(DISTINCT cod_cliente) as clientes_unicos
        FROM vendas 
        WHERE data_faturamento IS NOT NULL
        GROUP BY strftime('%Y', data_faturamento)
        ORDER BY ano
    """, conn)
    print(anos.to_string())
    
    # 6. Verificar valores negativos
    print(f"\n=== VERIFICANDO VALORES NEGATIVOS ===")
    negativos = pd.read_sql_query("""
        SELECT 
            cod_cliente, cliente, valor_faturado, quantidade_faturada, valor_entrada, valor_carteira
        FROM vendas 
        WHERE valor_faturado < 0 OR quantidade_faturada < 0 OR valor_entrada < 0 OR valor_carteira < 0
        LIMIT 10
    """, conn)
    print(f"Registros com valores negativos: {len(negativos)}")
    if len(negativos) > 0:
        print(negativos.to_string())
    
    # 7. Verificar dados específicos do cliente AILDO
    print(f"\n=== DADOS DO CLIENTE AILDO ===")
    aildo = pd.read_sql_query("""
        SELECT 
            cod_cliente, cliente, data_faturamento, valor_faturado, quantidade_faturada, produto
        FROM vendas 
        WHERE cliente LIKE '%AILDO%'
        ORDER BY data_faturamento DESC
        LIMIT 10
    """, conn)
    print(aildo.to_string())
    
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}")
