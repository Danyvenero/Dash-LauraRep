"""
Debug simples do callback B2B
"""

import pandas as pd
from datetime import datetime
import sqlite3
import os

def test_simple_b2b():
    """Teste simples para identificar o problema"""
    try:
        print("🔍 Testando componentes básicos...")
        
        # 1. Teste de conexão com banco
        db_path = "instance/database.sqlite"
        if not os.path.exists(db_path):
            print("❌ Banco de dados não encontrado")
            return
            
        conn = sqlite3.connect(db_path)
        
        # 2. Teste de query básica
        try:
            vendas_query = """
            SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
            FROM vendas 
            WHERE data >= date('now', '-24 months')
            LIMIT 5
            """
            vendas_df = pd.read_sql_query(vendas_query, conn)
            print(f"✅ Query vendas OK: {len(vendas_df)} registros")
            
            if vendas_df.empty:
                print("⚠️ Nenhuma venda encontrada")
                return
                
        except Exception as e:
            print(f"❌ Erro na query vendas: {e}")
            return
            
        # 3. Teste de query cotações
        try:
            cotacoes_query = """
            SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
            FROM produtos_cotados p
            LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
            WHERE c.data >= date('now', '-24 months')
            LIMIT 5
            """
            cotacoes_df = pd.read_sql_query(cotacoes_query, conn)
            print(f"✅ Query cotações OK: {len(cotacoes_df)} registros")
            
        except Exception as e:
            print(f"❌ Erro na query cotações: {e}")
            cotacoes_df = pd.DataFrame()
            
        conn.close()
        
        # 4. Teste de processamento básico
        try:
            # Simulação simples do que a função B2B faz
            cod_cliente = vendas_df.iloc[0]['cod_cliente'] if not vendas_df.empty else "TESTE"
            
            print(f"🎯 Cliente de teste: {cod_cliente}")
            
            # Filtrar dados do cliente
            cliente_vendas = vendas_df[vendas_df['cod_cliente'] == cod_cliente]
            print(f"📊 Vendas do cliente: {len(cliente_vendas)}")
            
            # Simulação de resultado
            resultado_teste = {
                'cliente': cod_cliente,
                'status': 'SUCESSO',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analises': {
                    'gaps_mercado': [],
                    'sazonalidade': {},
                    'kpis_comerciais': {},
                    'benchmark': {},
                    'alertas': {},
                    'insights': {}
                },
                'resumo_executivo': {
                    'classificacao_cliente': 'B',
                    'score_percentil': 75,
                    'total_oportunidades': 5,
                    'valor_potencial': 10000.00,
                    'alertas_criticos': 1,
                    'recomendacao_principal': 'Análise disponível'
                }
            }
            
            print("✅ Estrutura de dados B2B válida")
            print(f"📋 Resumo: {resultado_teste['resumo_executivo']}")
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_b2b()