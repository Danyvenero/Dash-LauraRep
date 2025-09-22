"""
Teste direto do callback de produtos para verificar funcionamento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
from webapp.produtos_table_callback import process_produtos_analytics

def test_produtos_callback():
    print("🧪 Testando callback de produtos...")
    
    # Carregar dados
    print("📊 Carregando dados...")
    vendas_df = load_vendas_data()
    cotacoes_df = load_cotacoes_data()
    produtos_cotados_df = load_produtos_cotados_data()
    
    if vendas_df is None or vendas_df.empty:
        print("❌ Dados de vendas vazios")
        return False
    
    print(f"✅ Vendas: {len(vendas_df)} registros")
    print(f"   Colunas: {list(vendas_df.columns)}")
    
    # Processar dados
    print("🔄 Processando analytics...")
    produtos_data = process_produtos_analytics(vendas_df, cotacoes_df, produtos_cotados_df, 20)
    
    if produtos_data is None or produtos_data.empty:
        print("❌ Processamento resultou em dados vazios")
        return False
    
    print(f"✅ Processados: {len(produtos_data)} produtos")
    print(f"   Colunas: {list(produtos_data.columns)}")
    
    # Mostrar primeiros produtos
    print("\n📋 Primeiros 5 produtos:")
    for idx, row in produtos_data.head(5).iterrows():
        material = row.get('material', 'N/A')
        produto = row.get('produto', 'N/A')[:50]
        faturamento = row.get('faturamento_total', 0)
        print(f"   {material}: {produto}... - R$ {faturamento:,.2f}")
    
    # Testar filtro por material
    print("\n🔍 Testando filtro por material...")
    materiais_disponiveis = produtos_data['material'].unique()[:3]
    print(f"   Materiais disponíveis (3 primeiros): {list(materiais_disponiveis)}")
    
    # Aplicar filtro
    produtos_filtrados = produtos_data[produtos_data['material'].isin(materiais_disponiveis[:2])]
    print(f"   Após filtro: {len(produtos_filtrados)} produtos")
    
    return True

if __name__ == "__main__":
    test_produtos_callback()