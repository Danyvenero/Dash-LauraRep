import sys
sys.path.append('.')
from webapp.b2b_advanced_callbacks import analyze_purchase_gaps
import pandas as pd
import sqlite3

print("🧪 Testando melhorias na análise de gaps...")

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')

# Carrega dados de teste
print("📊 Carregando dados...")
vendas_df = pd.read_sql('SELECT * FROM vendas LIMIT 500', conn)
produtos_cotados_df = pd.read_sql('SELECT * FROM produtos_cotados LIMIT 200', conn)

print(f"✅ Vendas carregadas: {len(vendas_df)}")
print(f"✅ Produtos cotados carregados: {len(produtos_cotados_df)}")

# Testa análise de gaps
print("\n🔍 Executando análise de gaps...")
result = analyze_purchase_gaps(vendas_df, pd.DataFrame(), produtos_cotados_df)

print(f"\n📈 Resultado:")
print(f"   Gaps encontrados: {len(result)}")

if len(result) > 0:
    print(f"   Colunas: {result.columns.tolist()}")
    print(f"\n📋 Primeiro gap:")
    primeiro_gap = result.iloc[0]
    for col in result.columns:
        print(f"   {col}: {primeiro_gap[col]}")
    
    # Verifica se tem a nova coluna
    if 'clientes_detalhes' in result.columns:
        print(f"\n✅ Nova coluna 'clientes_detalhes' funciona!")
        print(f"   Exemplo: {primeiro_gap['clientes_detalhes']}")
    else:
        print(f"\n❌ Coluna 'clientes_detalhes' não encontrada")

conn.close()
print("\n🎯 Teste concluído!")