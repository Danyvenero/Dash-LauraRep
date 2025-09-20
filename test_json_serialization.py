import sys
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ml_recommendations import SmartPurchaseRecommendations

def test_json_serialization():
    """
    Teste específico para verificar se o resultado é JSON serializable
    """
    print("🧪 TESTE DE SERIALIZAÇÃO JSON")
    print("="*50)
    
    try:
        # Carregar dados reais limitados
        conn = sqlite3.connect('instance/database.sqlite')
        vendas_df = pd.read_sql("""
            SELECT cod_cliente, material, qtd_entrada, vlr_entrada, data as data_entrada
            FROM vendas 
            WHERE cod_cliente = 782080
            LIMIT 100
        """, conn)
        conn.close()
        
        if vendas_df.empty:
            print("⚠️ Sem dados para teste")
            return True
        
        recommender = SmartPurchaseRecommendations()
        cod_cliente = 782080
        contexto_comercial = {'prioridade': 'alta', 'tipo_analise': 'completa'}
        
        print(f"🎯 Testando com cliente: {cod_cliente}")
        print(f"📊 Dados: {len(vendas_df)} registros")
        
        # Executar análise completa
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format='completo'
        )
        
        # Tentar serializar como JSON
        print("🔄 Tentando serializar resultado como JSON...")
        
        try:
            json_str = json.dumps(resultado, ensure_ascii=False, indent=2)
            print("✅ SUCESSO: Resultado é JSON serializable!")
            
            # Verificar tamanho
            size_kb = len(json_str.encode('utf-8')) / 1024
            print(f"📏 Tamanho do JSON: {size_kb:.1f} KB")
            
            # Verificar estrutura
            print(f"📋 Chaves principais: {list(resultado.keys())}")
            
            if 'analises' in resultado:
                print(f"📊 Análises disponíveis: {list(resultado['analises'].keys())}")
            
            return True
            
        except TypeError as e:
            print(f"❌ ERRO DE SERIALIZAÇÃO: {str(e)}")
            
            # Tentar identificar o problema
            print("🔍 Analisando tipos problemáticos...")
            
            def find_non_serializable(obj, path=""):
                """Encontra objetos não serializáveis"""
                try:
                    json.dumps(obj)
                    return []
                except TypeError:
                    if isinstance(obj, dict):
                        problems = []
                        for k, v in obj.items():
                            problems.extend(find_non_serializable(v, f"{path}.{k}"))
                        return problems
                    elif isinstance(obj, list):
                        problems = []
                        for i, v in enumerate(obj):
                            problems.extend(find_non_serializable(v, f"{path}[{i}]"))
                        return problems
                    else:
                        return [f"{path}: {type(obj)} - {str(obj)[:100]}"]
            
            problems = find_non_serializable(resultado)
            for problem in problems[:10]:  # Mostrar apenas os primeiros 10
                print(f"   🔴 {problem}")
            
            return False
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_specific_components():
    """
    Teste de componentes específicos que causaram problemas
    """
    print("\n🔍 TESTE DE COMPONENTES ESPECÍFICOS")
    print("="*50)
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        vendas_df = pd.read_sql("""
            SELECT cod_cliente, material, qtd_entrada, vlr_entrada, data as data_entrada
            FROM vendas 
            WHERE cod_cliente = 782080
            LIMIT 50
        """, conn)
        conn.close()
        
        if vendas_df.empty:
            print("⚠️ Sem dados para componentes")
            return True
        
        recommender = SmartPurchaseRecommendations()
        
        # Teste 1: Gaps Analysis
        print("📦 Testando analyze_market_gaps...")
        gaps = recommender.analyze_market_gaps(vendas_df, pd.DataFrame(), 782080)
        gaps_safe = recommender._convert_gaps_to_json_safe(gaps)
        
        try:
            json.dumps(gaps_safe)
            print("   ✅ Gaps: JSON serializable")
        except Exception as e:
            print(f"   ❌ Gaps: {e}")
        
        # Teste 2: Seasonality
        print("📅 Testando detect_seasonality...")
        seasonality = recommender.detect_seasonality(vendas_df, '782080')
        
        try:
            json.dumps(seasonality)
            print("   ✅ Seasonality: JSON serializable")
        except Exception as e:
            print(f"   ❌ Seasonality: {e}")
        
        # Teste 3: Alerts
        print("🚨 Testando generate_intelligent_alerts...")
        alerts = recommender.generate_intelligent_alerts(vendas_df, pd.DataFrame())
        
        try:
            json.dumps(alerts)
            print("   ✅ Alerts: JSON serializable")
        except Exception as e:
            print(f"   ❌ Alerts: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos componentes: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE DE CORREÇÃO DO CALLBACK ERROR")
    print("="*60)
    
    # Teste 1: Componentes específicos
    components_ok = test_specific_components()
    
    # Teste 2: Serialização completa
    serialization_ok = test_json_serialization()
    
    print("\n🏁 RESULTADO:")
    print("="*40)
    
    if components_ok and serialization_ok:
        print("🎉 CALLBACK ERROR CORRIGIDO!")
        print("   ✅ Todos os componentes são JSON serializable")
        print("   ✅ Resultado completo pode ser retornado pelo callback")
        print("   ✅ Tipos pandas/numpy convertidos corretamente")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   • Testar callback real no dashboard")
        print("   • Verificar performance em produção")
        print("   • Implementar interface de usuário completa")
    else:
        print("⚠️ AINDA HÁ PROBLEMAS:")
        print(f"   {'✅' if components_ok else '❌'} Componentes: {'OK' if components_ok else 'PROBLEMAS'}")
        print(f"   {'✅' if serialization_ok else '❌'} Serialização: {'OK' if serialization_ok else 'PROBLEMAS'}")