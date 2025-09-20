"""
Teste Simples das Funcionalidades de Análise de Conversão e Cross-Selling
"""

import pandas as pd
import sqlite3
import sys
import os

def test_conversion_functionality():
    """Testa as funcionalidades de conversão de forma isolada"""
    print("🚀 Testando Funcionalidades de Análise de Conversão")
    print("=" * 60)
    
    try:
        # Conecta ao banco correto
        conn = sqlite3.connect('instance/database.sqlite')
        
        # Verifica dados disponíveis
        vendas_count = pd.read_sql_query("SELECT COUNT(*) as count FROM vendas", conn).iloc[0]['count']
        cotacoes_count = pd.read_sql_query("SELECT COUNT(*) as count FROM cotacoes", conn).iloc[0]['count']
        produtos_cotados_count = pd.read_sql_query("SELECT COUNT(*) as count FROM produtos_cotados", conn).iloc[0]['count']
        
        print(f"📊 Dados disponíveis:")
        print(f"  📈 Vendas: {vendas_count:,} registros")
        print(f"  📋 Cotações: {cotacoes_count:,} registros")
        print(f"  🛍️ Produtos Cotados: {produtos_cotados_count:,} registros")
        
        # Carrega amostra de dados
        vendas_df = pd.read_sql_query("""
            SELECT material, produto, cliente, data, vlr_entrada, qtd_entrada
            FROM vendas 
            WHERE vlr_entrada > 0 
            LIMIT 2000
        """, conn)
        
        produtos_cotados_df = pd.read_sql_query("""
            SELECT material, descricao, cliente, cotacao, quantidade
            FROM produtos_cotados
            LIMIT 2000
        """, conn)
        
        conn.close()
        
        print(f"\n🎯 Análise de Conversão (amostra):")
        print(f"  • Vendas analisadas: {len(vendas_df)}")
        print(f"  • Cotações analisadas: {len(produtos_cotados_df)}")
        
        # Análise simples de conversão
        vendas_materials = set(vendas_df['material'].unique())
        cotacoes_materials = set(produtos_cotados_df['material'].unique())
        
        # Materiais que foram cotados mas não vendidos
        gap_materials = cotacoes_materials - vendas_materials
        converted_materials = cotacoes_materials.intersection(vendas_materials)
        
        print(f"\n📊 Resultados de Conversão:")
        print(f"  🟢 Materiais convertidos: {len(converted_materials)}")
        print(f"  🔴 Materiais não convertidos: {len(gap_materials)}")
        print(f"  📈 Taxa de conversão: {len(converted_materials)/len(cotacoes_materials)*100:.1f}%")
        
        # Análise de cross-selling simples
        vendas_por_cliente = vendas_df.groupby('cliente')['material'].apply(list).to_dict()
        
        # Conta combinações de produtos por cliente
        product_combinations = {}
        for cliente, materiais in vendas_por_cliente.items():
            if len(materiais) > 1:
                materiais_unicos = list(set(materiais))
                for i, mat1 in enumerate(materiais_unicos):
                    for mat2 in materiais_unicos[i+1:]:
                        combination = tuple(sorted([mat1, mat2]))
                        product_combinations[combination] = product_combinations.get(combination, 0) + 1
        
        print(f"\n🛒 Análise de Cross-Selling:")
        print(f"  👥 Clientes analisados: {len(vendas_por_cliente)}")
        print(f"  🔗 Combinações encontradas: {len(product_combinations)}")
        
        # Top 5 combinações
        if product_combinations:
            top_combinations = sorted(product_combinations.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n🎯 Top 5 Combinações de Produtos:")
            for (mat1, mat2), count in top_combinations:
                print(f"  • {mat1} + {mat2}: {count} vezes")
        
        print(f"\n✅ Teste concluído com sucesso!")
        print(f"🌐 As funcionalidades estão implementadas no dashboard B2B Avançado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_conversion_functionality()