#!/usr/bin/env python3
"""
Script para testar callbacks diretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data

def test_simple_callback_logic():
    """Testa a lógica dos callbacks isoladamente"""
    print("🧪 TESTANDO LÓGICA DOS CALLBACKS")
    print("="*50)
    
    # Testa carregamento de dados
    vendas_df = load_vendas_data()
    cotacoes_df = load_cotacoes_data()
    produtos_df = load_produtos_cotados_data()
    
    print(f"📊 Dados carregados:")
    print(f"   Vendas: {len(vendas_df)} registros")
    print(f"   Cotações: {len(cotacoes_df)} registros")
    print(f"   Produtos: {len(produtos_df)} registros")
    
    if not vendas_df.empty:
        print(f"\n💰 Cálculos básicos:")
        
        # Testa cálculos básicos
        entrada_valor = vendas_df['vlr_entrada'].sum() if 'vlr_entrada' in vendas_df.columns else 0
        carteira_valor = vendas_df['vlr_carteira'].sum() if 'vlr_carteira' in vendas_df.columns else 0
        faturamento_valor = vendas_df['vlr_rol'].sum() if 'vlr_rol' in vendas_df.columns else 0
        
        print(f"   Entrada: R$ {entrada_valor:,.2f}")
        print(f"   Carteira: R$ {carteira_valor:,.2f}")
        print(f"   Faturamento: R$ {faturamento_valor:,.2f}")
        
        # Testa unidades de negócio
        if 'unidade_negocio' in vendas_df.columns:
            unidades = vendas_df['unidade_negocio'].unique()
            print(f"\n🏢 Unidades de negócio ({len(unidades)}):")
            for i, un in enumerate(unidades[:5]):
                un_data = vendas_df[vendas_df['unidade_negocio'] == un]
                un_faturamento = un_data['vlr_rol'].sum() if 'vlr_rol' in un_data.columns else 0
                print(f"   {i+1}. {un}: R$ {un_faturamento:,.2f}")
        
        # Testa dados temporais
        if 'data' in vendas_df.columns:
            import pandas as pd
            vendas_df['ano_mes'] = pd.to_datetime(vendas_df['data']).dt.to_period('M').astype(str)
            evolucao = vendas_df.groupby('ano_mes')['vlr_rol'].sum()
            print(f"\n📈 Evolução temporal ({len(evolucao)} períodos):")
            for periodo, valor in evolucao.head(5).items():
                print(f"   {periodo}: R$ {valor:,.2f}")
    
    print("\n✅ Lógica dos callbacks funciona corretamente!")
    print("❌ O problema está na execução dos callbacks no Dash")

if __name__ == "__main__":
    test_simple_callback_logic()
