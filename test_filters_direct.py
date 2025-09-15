#!/usr/bin/env python3
"""
Teste simples da função apply_filters
"""

import sys
import os
import pandas as pd
import sqlite3

def test_apply_filters_direct():
    """Teste direto da função apply_filters"""
    print("🧪 Testando função apply_filters diretamente...")
    
    # Conectar ao banco
    db_path = "instance/database.sqlite"
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Carregar dados diretamente
    print("📊 Carregando dados do banco...")
    try:
        df_vendas = pd.read_sql_query("SELECT * FROM vendas LIMIT 1000", conn)
        print(f"✅ Vendas carregadas: {len(df_vendas)} registros")
        print(f"📋 Colunas: {list(df_vendas.columns)}")
        
        # Verificar se tem dados
        if df_vendas.empty:
            print("❌ Sem dados de vendas para testar")
            return
        
        # Importar a função apply_filters diretamente
        sys.path.append(os.path.join(os.getcwd(), 'webapp'))
        from callbacks import apply_filters
        
        # Teste 1: Sem filtros
        print("\n🔍 Teste 1: Sem filtros")
        dados_sem_filtro = apply_filters(df_vendas, None, None, None, None, None, None)
        print(f"Registros sem filtro: {len(dados_sem_filtro)}")
        
        # Verificar colunas de data
        colunas_data = ['data_faturamento', 'data', 'data_venda']
        coluna_data_encontrada = None
        for col in colunas_data:
            if col in df_vendas.columns:
                coluna_data_encontrada = col
                break
        
        if coluna_data_encontrada:
            print(f"📅 Coluna de data encontrada: {coluna_data_encontrada}")
            
            # Converter para datetime
            df_vendas[coluna_data_encontrada] = pd.to_datetime(df_vendas[coluna_data_encontrada], errors='coerce')
            anos_unicos = df_vendas[coluna_data_encontrada].dt.year.dropna().unique()
            print(f"📅 Anos disponíveis: {sorted(anos_unicos)}")
            
            # Teste 2: Filtro por ano
            if len(anos_unicos) > 0:
                ano_teste = int(anos_unicos[0])
                print(f"\n🔍 Teste 2: Filtro por ano {ano_teste}")
                dados_filtro_ano = apply_filters(df_vendas, ano_teste, None, None, None, None, None)
                print(f"Registros com filtro ano {ano_teste}: {len(dados_filtro_ano)}")
        
        # Teste 3: Filtro por canal
        if 'canal_distribuicao' in df_vendas.columns:
            canais = df_vendas['canal_distribuicao'].dropna().unique()
            if len(canais) > 0:
                canal_teste = canais[0]
                print(f"\n🔍 Teste 3: Filtro por canal '{canal_teste}'")
                dados_filtro_canal = apply_filters(df_vendas, None, None, None, None, canal_teste, None)
                print(f"Registros com filtro canal: {len(dados_filtro_canal)}")
        
        print("\n✅ Testes de filtros concluídos com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_apply_filters_direct()
