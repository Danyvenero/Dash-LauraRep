#!/usr/bin/env python3
"""
Teste para diagnóstico do problema de sugestões
Verifica se o purchase_recommender gera sugestões válidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_purchase_suggestions():
    """Testa se o sistema gera sugestões válidas"""
    
    print("🔍 DIAGNÓSTICO - GERAÇÃO DE SUGESTÕES")
    print("=" * 50)
    
    try:
        # Importa módulos necessários
        from utils import load_all_data
        from utils.ml_recommendations import purchase_recommender
        
        print("📦 Módulos carregados com sucesso")
        
        # Carrega dados
        print("📊 Carregando dados...")
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        print(f"✅ Dados carregados:")
        print(f"   📈 Vendas: {len(vendas_df)} registros")
        print(f"   📋 Cotações: {len(cotacoes_df)} registros") 
        print(f"   🛒 Produtos cotados: {len(produtos_cotados_df)} registros")
        
        if vendas_df.empty:
            print("❌ ERRO: Dados de vendas vazios!")
            return False
        
        # Verifica status do modelo
        print(f"\n🤖 Status do modelo ML: {purchase_recommender.is_trained}")
        
        # Testa geração de sugestões
        print("\n🎯 Testando geração de sugestões...")
        df_sugestoes = purchase_recommender.generate_purchase_suggestions(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            cliente_filter=None,  # Todos os clientes
            top_n=10
        )
        
        print(f"📊 Resultado: {len(df_sugestoes)} sugestões geradas")
        
        if df_sugestoes.empty:
            print("❌ PROBLEMA: Nenhuma sugestão foi gerada!")
            print("\n🔍 Verificando dados de entrada...")
            
            # Debug básico
            unique_materials = vendas_df['material'].nunique()
            unique_clients = vendas_df['cod_cliente'].nunique()
            print(f"   📦 Materiais únicos: {unique_materials}")
            print(f"   👥 Clientes únicos: {unique_clients}")
            
            # Verifica dados recentes
            import pandas as pd
            from datetime import datetime, timedelta
            
            vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'])
            cutoff_3months = datetime.now() - timedelta(days=90)
            vendas_recentes = vendas_df[vendas_df['data_faturamento'] >= cutoff_3months]
            print(f"   📅 Vendas últimos 3 meses: {len(vendas_recentes)}")
            
            return False
        else:
            print("✅ SUCESSO: Sugestões geradas!")
            print(f"\n📋 Colunas disponíveis: {list(df_sugestoes.columns)}")
            print(f"\n📈 Primeiras 3 sugestões:")
            for i, row in df_sugestoes.head(3).iterrows():
                print(f"   {i+1}. Material: {row.get('material', 'N/A')} | "
                      f"Cliente: {row.get('cod_cliente', 'N/A')} | "
                      f"Qtd: {row.get('quantidade_sugerida', 'N/A')} | "
                      f"Confiança: {row.get('confianca', 'N/A')}%")
            
            # Testa também probabilidades de recompra
            print("\n🔮 Testando probabilidades de recompra...")
            df_probabilidades = purchase_recommender.predict_repurchase_probability(
                vendas_df=vendas_df,
                cotacoes_df=cotacoes_df,
                cod_cliente=None
            )
            print(f"📊 Probabilidades geradas: {len(df_probabilidades)} registros")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_purchase_suggestions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SISTEMA DE SUGESTÕES FUNCIONAL!")
        print("   O problema pode estar na interface ou callback.")
        print("\n🔍 Próximos passos:")
        print("   • Verificar callback btn-apply-filters-suggestions") 
        print("   • Checar se store-suggestions-data está sendo populado")
        print("   • Validar se os KPIs estão lendo do store correto")
    else:
        print("⚠️ PROBLEMA NO SISTEMA DE SUGESTÕES")
        print("   O motor de recomendações não está funcionando.")
        print("\n🔧 Ações necessárias:")
        print("   • Verificar dados de entrada")
        print("   • Checar configuração do purchase_recommender")
        print("   • Revisar lógica de geração de sugestões")
    print("=" * 50)