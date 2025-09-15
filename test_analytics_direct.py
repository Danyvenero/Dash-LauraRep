import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Teste direto dos dados para vlr_entrada
from utils.advanced_analytics import AdvancedAnalytics
import pandas as pd

print("🔍 TESTANDO ACESSO DIRETO AOS DADOS")
print("=" * 50)

try:
    # Inicializa analytics
    analytics = AdvancedAnalytics()
    
    print(f"📊 Analytics carregado: {type(analytics)}")
    print(f"📊 Vendas DF: {type(analytics.vendas_df)}")
    
    if analytics.vendas_df is not None:
        print(f"📊 Shape dos dados: {analytics.vendas_df.shape}")
        print(f"📊 Colunas: {list(analytics.vendas_df.columns)}")
        
        # Estatísticas vlr_entrada
        vlr_entrada_stats = analytics.vendas_df['vlr_entrada'].describe()
        print(f"📊 Estatísticas vlr_entrada:")
        print(vlr_entrada_stats)
        
        # Registros com vlr_entrada > 0
        registros_entrada = len(analytics.vendas_df[analytics.vendas_df['vlr_entrada'] > 0])
        print(f"📊 Registros com vlr_entrada > 0: {registros_entrada}")
        
        # Exemplos
        if registros_entrada > 0:
            print(f"📊 Exemplos de registros com vlr_entrada:")
            exemplos = analytics.vendas_df[analytics.vendas_df['vlr_entrada'] > 0][['data', 'vlr_entrada', 'vlr_rol']].head()
            print(exemplos.to_string(index=False))
        
    else:
        print("⚠️ analytics.vendas_df é None!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
