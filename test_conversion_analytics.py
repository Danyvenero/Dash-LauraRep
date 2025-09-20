"""
Teste das Funcionalidades de Análise de Conversão e Cross-Selling
"""

import pandas as pd
import sqlite3
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ml_recommendations import conversion_analyzer
from utils.db import get_connection as get_db_connection

def test_conversion_analysis():
    """Testa a análise de conversão"""
    print("🎯 Testando Análise de Conversão...")
    
    try:
        # Carrega dados
        conn = get_db_connection()
        vendas_df = pd.read_sql_query("SELECT * FROM vendas LIMIT 1000", conn)
        produtos_cotados_df = pd.read_sql_query("SELECT * FROM produtos_cotados LIMIT 1000", conn)
        conn.close()
        
        print(f"📊 Dados carregados: {len(vendas_df)} vendas, {len(produtos_cotados_df)} cotações")
        
        # Executa análise
        conversion_results = conversion_analyzer.analyze_conversion_rates(vendas_df, produtos_cotados_df)
        
        if not conversion_results.empty:
            print(f"✅ Análise de conversão concluída: {len(conversion_results)} produtos analisados")
            
            # Estatísticas
            zero_conversion = len(conversion_results[conversion_results['total_vendas'] == 0])
            high_conversion = len(conversion_results[conversion_results['taxa_conversao_cotacao'] >= 50])
            
            print(f"🔴 Produtos com zero conversão: {zero_conversion}")
            print(f"🟢 Produtos com alta conversão (≥50%): {high_conversion}")
            
            # Top 5 problemas
            print("\n🎯 Top 5 Oportunidades de Conversão:")
            top_opportunities = conversion_results.head()
            for _, row in top_opportunities.iterrows():
                print(f"  • {row['material']}: {row['total_cotacoes']} cotações → {row['total_vendas']} vendas ({row['taxa_conversao_cotacao']:.1f}%)")
                
        else:
            print("⚠️ Nenhum resultado de conversão encontrado")
            
    except Exception as e:
        print(f"❌ Erro na análise de conversão: {e}")
        import traceback
        traceback.print_exc()

def test_cross_selling_analysis():
    """Testa a análise de cross-selling"""
    print("\n🛒 Testando Análise de Cross-Selling...")
    
    try:
        # Carrega dados de vendas
        conn = get_db_connection()
        vendas_df = pd.read_sql_query("SELECT * FROM vendas LIMIT 1000", conn)
        conn.close()
        
        print(f"📊 Dados carregados: {len(vendas_df)} vendas")
        
        # Executa análise
        cross_selling_results = conversion_analyzer.analyze_cross_selling_opportunities(vendas_df)
        
        if not cross_selling_results.empty:
            print(f"✅ Análise de cross-selling concluída: {len(cross_selling_results)} associações encontradas")
            
            # Estatísticas
            strong_associations = len(cross_selling_results[cross_selling_results['lift'] >= 2.0])
            very_strong = len(cross_selling_results[cross_selling_results['lift'] >= 3.0])
            
            print(f"🔥 Associações fortes (lift ≥ 2.0): {strong_associations}")
            print(f"⚡ Muito fortes (lift ≥ 3.0): {very_strong}")
            
            # Top 5 associações
            print("\n🎯 Top 5 Oportunidades Cross-Selling:")
            top_cross_selling = cross_selling_results.head()
            for _, row in top_cross_selling.iterrows():
                print(f"  • {row['produto_a']} + {row['produto_b']}: {row['confidence_a_to_b']:.1%} chance, Lift {row['lift']:.2f}x")
                
        else:
            print("⚠️ Nenhuma associação de cross-selling encontrada")
            
    except Exception as e:
        print(f"❌ Erro na análise de cross-selling: {e}")
        import traceback
        traceback.print_exc()

def test_database_connection():
    """Testa a conexão com o banco"""
    print("🔍 Testando Conexão com Banco...")
    
    try:
        conn = get_db_connection()
        
        # Verifica tabelas
        vendas_count = pd.read_sql_query("SELECT COUNT(*) as count FROM vendas", conn).iloc[0]['count']
        cotacoes_count = pd.read_sql_query("SELECT COUNT(*) as count FROM cotacoes", conn).iloc[0]['count']
        produtos_cotados_count = pd.read_sql_query("SELECT COUNT(*) as count FROM produtos_cotados", conn).iloc[0]['count']
        
        conn.close()
        
        print(f"✅ Banco conectado com sucesso:")
        print(f"  📈 Vendas: {vendas_count:,} registros")
        print(f"  📋 Cotações: {cotacoes_count:,} registros")
        print(f"  🛍️ Produtos Cotados: {produtos_cotados_count:,} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando Testes de Análise de Conversão e Cross-Selling")
    print("=" * 60)
    
    # Testa conexão
    if test_database_connection():
        # Testa funcionalidades
        test_conversion_analysis()
        test_cross_selling_analysis()
        
        print("\n" + "=" * 60)
        print("✅ Testes concluídos com sucesso!")
        print("🌐 Acesse http://127.0.0.1:8050 para usar as funcionalidades no dashboard")
    else:
        print("❌ Falha na conexão com banco. Verifique a configuração.")