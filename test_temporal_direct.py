#!/usr/bin/env python3
"""
Teste direto da função create_temporal_evolution_chart para debug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import sqlite3
from utils.advanced_analytics import AdvancedAnalytics

# Criar dados de teste simplificados
def create_test_data():
    """Cria dados de teste com vlr_entrada e vlr_rol"""
    print("🔧 Criando dados de teste...")
    
    # Criar dados simulados
    dates_entrada = pd.date_range('2023-01-01', '2024-12-01', freq='D')
    dates_rol = pd.date_range('2023-01-01', '2024-12-01', freq='D')
    
    test_data = []
    
    # Adicionar registros com vlr_entrada (usar coluna 'data')
    for i, date in enumerate(dates_entrada[:100]):  # 100 registros
        test_data.append({
            'data': date.strftime('%Y-%m-%d'),
            'data_faturamento': '',  # Vazio para vlr_entrada
            'vlr_entrada': 10000 + (i % 50) * 1000,  # Valores variados
            'vlr_rol': 0,
            'cod_cliente': f'CLI_{i % 10}',
            'cliente': f'Cliente {i % 10}'
        })
    
    # Adicionar registros com vlr_rol (usar coluna 'data_faturamento')
    for i, date in enumerate(dates_rol[:100]):  # 100 registros
        test_data.append({
            'data': date.strftime('%Y-%m-%d'),
            'data_faturamento': date.strftime('%Y-%m-%d'),
            'vlr_entrada': 0,
            'vlr_rol': 15000 + (i % 30) * 2000,  # Valores variados
            'cod_cliente': f'CLI_{i % 10}',
            'cliente': f'Cliente {i % 10}'
        })
    
    df = pd.DataFrame(test_data)
    print(f"✅ Dados de teste criados: {len(df)} registros")
    print(f"📊 Registros com vlr_entrada > 0: {len(df[df['vlr_entrada'] > 0])}")
    print(f"📊 Registros com vlr_rol > 0: {len(df[df['vlr_rol'] > 0])}")
    
    return df

def test_temporal_evolution():
    """Testa a função create_temporal_evolution_chart diretamente"""
    print("🧪 TESTE DIRETO DA FUNÇÃO create_temporal_evolution_chart")
    print("=" * 60)
    
    # Criar dados de teste
    test_df = create_test_data()
    
    # Inicializar analytics com dados de teste
    analytics = AdvancedAnalytics(test_df, None)
    
    # Importar a função
    sys.path.append('webapp')
    from webapp.callbacks import create_temporal_evolution_chart
    
    # Testar a função
    print("\n🔧 Testando create_temporal_evolution_chart...")
    
    try:
        fig = create_temporal_evolution_chart(
            analytics=analytics, 
            vendas_filtrado=None,
            filtros={
                'ano': [2023, 2024],
                'top_clientes': 5
            }
        )
        
        print(f"✅ Função executada com sucesso!")
        print(f"📊 Número de traces no gráfico: {len(fig.data)}")
        
        # Mostrar informações dos traces
        for i, trace in enumerate(fig.data):
            print(f"📈 Trace {i+1}: {trace.name} - {len(trace.x)} pontos")
            if len(trace.x) > 0:
                print(f"   Período: {min(trace.x)} até {max(trace.x)}")
                print(f"   Valores: {min(trace.y):.2f} até {max(trace.y):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na função: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_temporal_evolution()
    if success:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ TESTE FALHOU!")
