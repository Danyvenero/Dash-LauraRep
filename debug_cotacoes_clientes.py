import sqlite3
import pandas as pd
import json

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')

# Materiais que aparecem como "Cliente a Definir" ou "N/A"
materiais_problematicos = ['11277496', '122458619', '14226802', '11097634']

print("=== INVESTIGANDO COTAÇÕES DOS MATERIAIS SEM VENDA ===")

for material in materiais_problematicos:
    print(f"\n🔍 Material: {material}")
    
    # Busca cotações que contenham este material
    cotacoes_query = """
    SELECT numero_cotacao, cod_cliente, cliente, data, linhas_cotacao
    FROM cotacoes 
    WHERE linhas_cotacao LIKE ?
    ORDER BY data DESC
    LIMIT 3
    """
    cotacoes_result = conn.execute(cotacoes_query, (f'%{material}%',)).fetchall()
    
    if cotacoes_result:
        print(f"  ✅ Encontrado em {len(cotacoes_result)} COTAÇÕES:")
        for r in cotacoes_result:
            print(f"    📋 Cotação: {r[0]}")
            print(f"       Cliente: {r[2]} (Código: {r[1]})")
            print(f"       Data: {r[3]}")
            
            # Analisa o JSON das linhas para ver detalhes
            try:
                linhas = json.loads(r[4]) if r[4] else []
                for linha in linhas:
                    if linha.get('material') == material:
                        print(f"       Produto: {linha.get('produto', 'N/A')}")
                        print(f"       Quantidade: {linha.get('quantidade', 'N/A')}")
                        print(f"       Valor: {linha.get('vlr_unitario', 'N/A')}")
                        break
            except:
                print("       (Erro ao analisar JSON das linhas)")
            print("")
    else:
        print("  ❌ NÃO encontrado em COTAÇÕES")

print("\n=== VERIFICANDO PRODUTOS_COTADOS ===")

# Busca na tabela produtos_cotados
for material in materiais_problematicos:
    print(f"\n🔍 Material: {material}")
    
    produtos_cotados_query = """
    SELECT material, cod_cliente, cliente, cotacao, descricao, quantidade, preco_liquido_unitario
    FROM produtos_cotados 
    WHERE material = ?
    LIMIT 3
    """
    produtos_result = conn.execute(produtos_cotados_query, (material,)).fetchall()
    
    if produtos_result:
        print(f"  ✅ Encontrado em PRODUTOS_COTADOS ({len(produtos_result)} registros):")
        for r in produtos_result:
            print(f"    📋 Cliente: {r[2]} (Código: {r[1]})")
            print(f"       Cotação: {r[3]}")
            print(f"       Descrição: {r[4]}")
            print(f"       Quantidade: {r[5]}")
            print(f"       Preço Unitário: R$ {r[6]:.2f}" if r[6] else "Preço: N/A")
            print("")
    else:
        print("  ❌ NÃO encontrado em PRODUTOS_COTADOS")

print("\n=== ANÁLISE DE PADRÕES ===")

# Busca estatísticas gerais de cotações vs vendas
estatisticas_query = """
SELECT 
    COUNT(DISTINCT c.numero_cotacao) as total_cotacoes,
    COUNT(DISTINCT v.material) as materiais_com_venda,
    (SELECT COUNT(DISTINCT material) FROM vendas) as total_materiais_vendas
FROM cotacoes c
LEFT JOIN vendas v ON c.cod_cliente = v.cod_cliente
"""

stats = conn.execute(estatisticas_query).fetchone()
print(f"📊 Total de cotações: {stats[0]}")
print(f"📊 Materiais com vendas: {stats[1]}")
print(f"📊 Total materiais vendidos: {stats[2]}")

conn.close()
print("\n=== ANÁLISE CONCLUÍDA ===")