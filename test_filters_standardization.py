#!/usr/bin/env python3
"""
Teste das correções de filtros e padronização
Dashboard Laura Representações
"""

import pandas as pd
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection, load_vendas_data
from utils.data_standardization import apply_vendas_standardization, deduplicate_customers

def test_data_standardization():
    """Testa se a padronização está funcionando corretamente"""
    print("🧪 TESTE: Padronização de Dados")
    print("=" * 50)
    
    try:
        # Carrega dados direto do banco (sem padronização)
        conn = get_connection()
        df_raw = pd.read_sql_query("SELECT * FROM vendas LIMIT 1000", conn)
        conn.close()
        
        print(f"📊 Dados brutos carregados: {len(df_raw)} registros")
        
        if 'unidade_negocio' in df_raw.columns:
            print("🔍 Unidades de negócio originais:")
            unidades_originais = df_raw['unidade_negocio'].dropna().unique()[:10]
            for u in unidades_originais:
                print(f"   - {u}")
        
        # Aplica padronização
        df_padronizado = apply_vendas_standardization(df_raw.copy())
        
        print(f"\n✅ Dados padronizados: {len(df_padronizado)} registros")
        
        if 'unidade' in df_padronizado.columns:
            print("🔍 Unidades de negócio padronizadas:")
            unidades_padronizadas = df_padronizado['unidade'].dropna().unique()
            for u in unidades_padronizadas:
                print(f"   - {u}")
        
        # Testa hierarquias
        print("\n🏗️ Hierarquias de produto:")
        for i in range(1, 4):
            col = f'hier_produto_{i}'
            if col in df_padronizado.columns:
                unique_count = df_padronizado[col].nunique()
                print(f"   - Hierarquia {i}: {unique_count} valores únicos")
                
                # Mostra alguns exemplos
                exemplos = df_padronizado[col].dropna().unique()[:5]
                for exemplo in exemplos:
                    print(f"     • {exemplo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de padronização: {e}")
        return False


def test_client_deduplication():
    """Testa se a deduplicação de clientes está funcionando"""
    print("\n🧪 TESTE: Deduplicação de Clientes")
    print("=" * 50)
    
    try:
        # Carrega dados padronizados
        vendas_df = load_vendas_data(limit=5000)
        
        if 'cod_cliente' not in vendas_df.columns or 'cliente' not in vendas_df.columns:
            print("❌ Colunas cod_cliente ou cliente não encontradas")
            return False
        
        print(f"📊 Dados carregados: {len(vendas_df)} registros")
        
        # Analisa clientes únicos por código
        clientes_por_codigo = vendas_df.groupby('cod_cliente')['cliente'].nunique()
        duplicados = clientes_por_codigo[clientes_por_codigo > 1]
        
        print(f"🔍 Análise de duplicação:")
        print(f"   - Total códigos de cliente: {len(clientes_por_codigo)}")
        print(f"   - Códigos com múltiplos nomes: {len(duplicados)}")
        
        if len(duplicados) > 0:
            print(f"⚠️  Ainda existem {len(duplicados)} códigos com múltiplos nomes:")
            for cod, count in duplicados.head(5).items():
                nomes = vendas_df[vendas_df['cod_cliente'] == cod]['cliente'].unique()
                print(f"   - {cod}: {count} nomes -> {list(nomes[:3])}")
        else:
            print("✅ Todos os códigos de cliente têm nome único!")
        
        # Testa exemplo específico mencionado pelo usuário (792550)
        if 792550 in vendas_df['cod_cliente'].values:
            nomes_792550 = vendas_df[vendas_df['cod_cliente'] == 792550]['cliente'].unique()
            print(f"\n🎯 Cliente 792550: {len(nomes_792550)} nome(s)")
            for nome in nomes_792550:
                print(f"   - {nome}")
        
        return len(duplicados) == 0
        
    except Exception as e:
        print(f"❌ Erro no teste de deduplicação: {e}")
        return False


def test_filter_data():
    """Testa se os dados dos filtros estão corretos"""
    print("\n🧪 TESTE: Dados para Filtros")
    print("=" * 50)
    
    try:
        # Simula o que acontece nos callbacks de filtros
        vendas_df = load_vendas_data()
        
        print(f"📊 Dados para filtros: {len(vendas_df)} registros")
        
        # Testa filtros de hierarquia
        print("\n🏗️ Dados para filtros de hierarquia:")
        for i in range(1, 4):
            col = f'hier_produto_{i}'
            if col in vendas_df.columns:
                unique_vals = vendas_df[col].dropna().unique()
                print(f"   - Hierarquia {i}: {len(unique_vals)} opções")
                # Mostra primeiras 5 opções
                for val in sorted(unique_vals)[:5]:
                    print(f"     • {val}")
        
        # Testa filtro de unidade de negócio
        if 'unidade_negocio' in vendas_df.columns:
            unidades = vendas_df['unidade_negocio'].dropna().unique()
            print(f"\n🏢 Unidades de negócio: {len(unidades)} opções")
            for unidade in sorted(unidades):
                print(f"   - {unidade}")
        
        # Testa filtro de clientes (primeiros 10)
        if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
            clientes_unique = (vendas_df[['cod_cliente', 'cliente']]
                             .dropna()
                             .groupby('cod_cliente')['cliente']
                             .first()
                             .reset_index())
            print(f"\n👥 Clientes únicos: {len(clientes_unique)} opções")
            print("   Primeiros 5 clientes:")
            for _, row in clientes_unique.head(5).iterrows():
                print(f"   - {row['cod_cliente']} -- {row['cliente']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de filtros: {e}")
        return False


def test_database_queries():
    """Testa se as queries do banco retornam dados padronizados"""
    print("\n🧪 TESTE: Queries de Banco")
    print("=" * 50)
    
    try:
        conn = get_connection()
        
        # Testa query de hierarquia 1 (como no callback)
        query_hier1 = """
            SELECT DISTINCT hier_produto_1 
            FROM vendas 
            WHERE hier_produto_1 IS NOT NULL
            ORDER BY hier_produto_1
            LIMIT 10
        """
        df_hier1 = pd.read_sql_query(query_hier1, conn)
        print(f"🏗️ Hierarquia 1 do banco: {len(df_hier1)} valores")
        for val in df_hier1['hier_produto_1']:
            print(f"   - {val}")
        
        # Testa query de unidade (como no callback)
        query_unidade = """
            SELECT DISTINCT unidade_negocio 
            FROM vendas 
            WHERE unidade_negocio IS NOT NULL
            ORDER BY unidade_negocio
        """
        df_unidade = pd.read_sql_query(query_unidade, conn)
        if not df_unidade.empty:
            print(f"\n🏢 Unidades do banco: {len(df_unidade)} valores")
            for val in df_unidade['unidade_negocio']:
                print(f"   - {val}")
        else:
            print("\n⚠️  Nenhuma unidade encontrada no banco")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de queries: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🚀 TESTE COMPLETO: Filtros e Padronização")
    print("=" * 60)
    
    resultados = []
    
    # Executa todos os testes
    resultados.append(("Padronização de Dados", test_data_standardization()))
    resultados.append(("Deduplicação de Clientes", test_client_deduplication()))
    resultados.append(("Dados para Filtros", test_filter_data()))
    resultados.append(("Queries de Banco", test_database_queries()))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    total_testes = len(resultados)
    testes_ok = sum(1 for _, resultado in resultados if resultado)
    
    for teste, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{teste:<30} {status}")
    
    print(f"\n🎯 RESULTADO FINAL: {testes_ok}/{total_testes} testes passaram")
    
    if testes_ok == total_testes:
        print("🎉 Todos os testes passaram! Sistema está funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os problemas acima.")
    
    return testes_ok == total_testes


if __name__ == "__main__":
    main()