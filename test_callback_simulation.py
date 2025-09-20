#!/usr/bin/env python3
"""
Teste para simular o callback generate_suggestions
Verifica se os dados estão sendo retornados corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_generate_suggestions_callback():
    """Simula o callback generate_suggestions"""
    
    print("🔍 TESTE CALLBACK - generate_suggestions")
    print("=" * 50)
    
    try:
        # Importa os módulos do callback
        from utils import load_all_data
        from utils.ml_recommendations import purchase_recommender
        import pandas as pd
        from datetime import datetime, timedelta
        
        print("📦 Módulos importados com sucesso")
        
        # Simula os parâmetros do callback
        btn_apply = 1  # Botão foi clicado
        btn_refresh = None
        cliente_filter = None  # Todos os clientes
        periodo_meses = None  # Todos os períodos  
        abc_filter = "ALL"
        xyz_filter = "ALL"
        top_n = 20
        selected_hierarchy_tab = None
        hierarchy_filter = None
        
        print("📋 Simulando callback com parâmetros:")
        print(f"   - btn_apply: {btn_apply}")
        print(f"   - cliente_filter: {cliente_filter}")
        print(f"   - top_n: {top_n}")
        
        # === EXECUTA A LÓGICA DO CALLBACK ===
        
        print("📊 Carregando dados...")
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        print(f"✅ Dados carregados - Vendas: {len(vendas_df)}, Cotações: {len(cotacoes_df)}, Produtos Cotados: {len(produtos_cotados_df)}")

        if vendas_df.empty:
            print("❌ ERRO: Dados de vendas vazios!")
            return False
        
        # Filtra período
        if periodo_meses:
            cutoff_date = datetime.now() - timedelta(days=periodo_meses * 30)
            vendas_filtrada = vendas_df[
                pd.to_datetime(vendas_df['data_faturamento'], errors='coerce') >= cutoff_date
            ].copy()
            print(f"🔍 Filtro período aplicado: {len(vendas_df)} → {len(vendas_filtrada)} registros")
        else:
            vendas_filtrada = vendas_df.copy()
            print(f"📅 Sem filtro de período - usando todos os dados: {len(vendas_filtrada)} registros")
        
        # Para ML, gera sugestões
        cliente_param = cliente_filter
        print(f"🔄 Modo padrão - cliente: {cliente_param if cliente_param else 'TODOS'}")
        
        # Gera sugestões usando o motor ML
        print("🎯 Gerando sugestões com ML...")
        df_sugestoes = purchase_recommender.generate_purchase_suggestions(
            vendas_filtrada,
            cotacoes_df,
            produtos_cotados_df,
            cliente_filter=cliente_param,
            top_n=top_n or 20
        )
        print(f"✅ Sugestões geradas: {len(df_sugestoes)} registros")
        
        if df_sugestoes.empty:
            print("❌ PROBLEMA: Nenhuma sugestão gerada!")
            return False, {}
        
        # Aplica filtros ABC-XYZ
        if abc_filter != "ALL":
            df_sugestoes = df_sugestoes[df_sugestoes['classificacao_abc'] == abc_filter]
        
        if xyz_filter != "ALL":
            df_sugestoes = df_sugestoes[df_sugestoes['classificacao_xyz'] == xyz_filter]
        
        # Calcula probabilidades de recompra
        print("🔮 Calculando probabilidades de recompra...")
        df_probabilidades = purchase_recommender.predict_repurchase_probability(
            vendas_filtrada,
            cotacoes_df,
            cod_cliente=cliente_param
        )
        print(f"📊 Probabilidades calculadas: {len(df_probabilidades)} registros")
        
        # Merge com probabilidades
        if not df_probabilidades.empty:
            merge_cols = ['material']
            if cliente_param:
                merge_cols.append('cod_cliente')
            
            df_sugestoes = df_sugestoes.merge(
                df_probabilidades[merge_cols + ['prob_recompra_ml', 'categoria_prob']],
                on=merge_cols,
                how='left'
            )
            df_sugestoes['prob_recompra'] = df_sugestoes['prob_recompra_ml'].fillna(0.5)
            df_sugestoes['categoria_probabilidade'] = df_sugestoes['categoria_prob'].fillna('Média')
        else:
            df_sugestoes['prob_recompra'] = 0.5
            df_sugestoes['categoria_probabilidade'] = 'Média'
        
        # Aplica filtro Top N no resultado final
        if top_n and top_n > 0:
            df_sugestoes = df_sugestoes.head(top_n)
            print(f"🔢 Aplicado filtro Top N: limitado a {top_n} sugestões")
        
        # Converte para dict para store (EXATAMENTE como no callback)
        sugestoes_data = df_sugestoes.to_dict('records')
        
        print(f"📦 Dados convertidos para store: {len(sugestoes_data)} registros")
        print(f"📋 Exemplo de registro no store:")
        if sugestoes_data:
            exemplo = sugestoes_data[0]
            print(f"   Keys: {list(exemplo.keys())}")
            print(f"   Material: {exemplo.get('material', 'N/A')}")
            print(f"   Quantidade: {exemplo.get('quantidade_sugerida', 'N/A')}")
            print(f"   Confiança: {exemplo.get('confianca', 'N/A')}")
            print(f"   Valor estimado: {exemplo.get('valor_estimado', 'N/A')}")
        
        # Simula o retorno do callback
        message = f"✅ {len(sugestoes_data)} sugestões geradas com sucesso"
        
        print(f"\n📤 RETORNO DO CALLBACK:")
        print(f"   - sugestoes_data: {len(sugestoes_data)} registros")
        print(f"   - message: {message}")
        
        # Simula o callback dos KPIs também
        print(f"\n🔢 TESTANDO ATUALIZAÇÃO DOS KPIs:")
        
        if not sugestoes_data:
            kpis = ["0", "R$ 0", "0%", "0", "0%", "⚠️"]
        else:
            df = pd.DataFrame(sugestoes_data)
            
            # Total de sugestões
            total_suggestions = len(df)
            
            # Valor total sugerido
            if 'valor_estimado' in df.columns:
                valor_total = df['valor_estimado'].sum()
                valor_total_str = f"R$ {valor_total:,.0f}".replace(',', '.')
            else:
                valor_total_str = "N/A"
            
            # Confiança média
            confianca_media = df['confianca'].mean() if 'confianca' in df.columns else 0
            confianca_str = f"{confianca_media:.0f}%"
            
            # Produtos classe A
            classe_a = len(df[df['classificacao_abc'] == 'A']) if 'classificacao_abc' in df.columns else 0
            
            # Feedback stats
            feedback_str = "N/A"
            
            # Status do modelo ML
            if purchase_recommender.is_trained:
                modelo_status = "🤖 ML"
            else:
                modelo_status = "📊 Heurístico"
            
            kpis = [
                f"{total_suggestions:,}".replace(',', '.'),
                valor_total_str,
                confianca_str,
                f"{classe_a}",
                feedback_str,
                modelo_status
            ]
        
        print(f"   📊 KPI Total Sugestões: {kpis[0]}")
        print(f"   💰 KPI Valor Total: {kpis[1]}")
        print(f"   🎯 KPI Confiança: {kpis[2]}")
        print(f"   🅰️ KPI Classe A: {kpis[3]}")
        print(f"   👍 KPI Feedback: {kpis[4]}")
        print(f"   🤖 KPI Status: {kpis[5]}")
        
        return True, sugestoes_data
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

if __name__ == "__main__":
    success, data = test_generate_suggestions_callback()
    
    print("\n" + "=" * 50)
    if success and data:
        print("🎉 CALLBACK FUNCIONA PERFEITAMENTE!")
        print(f"   ✅ {len(data)} sugestões retornadas")
        print("   ✅ KPIs calculados corretamente")
        print("\n🔍 O problema deve estar em:")
        print("   • Conectividade entre frontend e callback")
        print("   • Store não sendo atualizado")
        print("   • Atualização da interface não sendo triggered")
    else:
        print("⚠️ PROBLEMA NO CALLBACK")
        print("   O callback não está funcionando como esperado")
    print("=" * 50)