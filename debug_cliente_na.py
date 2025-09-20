import sqlite3
import pandas as pd

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')

# Materiais que aparecem com N/A
materiais_na = ['10000008', '11277496', '122458619', '14226802', '11097634']

print("=== INVESTIGANDO MATERIAIS COM N/A ===")

for material in materiais_na:
    print(f"\n🔍 Material: {material}")
    
    # Busca na tabela de vendas
    vendas_query = """
    SELECT material, cod_cliente, cliente, data, vlr_entrada 
    FROM vendas 
    WHERE material = ? 
    LIMIT 3
    """
    vendas_result = conn.execute(vendas_query, (material,)).fetchall()
    
    if vendas_result:
        print(f"  ✅ Encontrado em VENDAS ({len(vendas_result)} registros):")
        for r in vendas_result:
            print(f"    Cliente: {r[2]} (Código: {r[1]}), Data: {r[3]}, Valor: {r[4]}")
    else:
        print("  ❌ NÃO encontrado em VENDAS")
    
    # Busca na tabela de cotações
    cotacoes_query = """
    SELECT numero_cotacao, cod_cliente, cliente, linhas_cotacao
    FROM cotacoes 
    WHERE linhas_cotacao LIKE ?
    LIMIT 2
    """
    cotacoes_result = conn.execute(cotacoes_query, (f'%{material}%',)).fetchall()
    
    if cotacoes_result:
        print(f"  ✅ Encontrado em COTAÇÕES ({len(cotacoes_result)} registros):")
        for r in cotacoes_result:
            print(f"    Cliente: {r[2]} (Código: {r[1]}), Cotação: {r[0]}")
    else:
        print("  ❌ NÃO encontrado em COTAÇÕES")

conn.close()
print("\n=== ANÁLISE CONCLUÍDA ===")