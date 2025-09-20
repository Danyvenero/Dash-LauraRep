from utils import load_all_data
from utils.ml_recommendations import ml_recommender
import pandas as pd

print("🧮 DEMONSTRAÇÃO PRÁTICA: COMO É CALCULADO O VALOR TOTAL SUGERIDO")
print("=" * 80)

# Carrega dados
vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()

# Gera algumas sugestões para demonstração
print("\n1. 🚀 GERANDO SUGESTÕES DE EXEMPLO...")
sugestoes = ml_recommender.generate_purchase_suggestions(
    vendas_df, cotacoes_df, produtos_cotados_df, 
    cliente_filter=None, top_n=3  # Apenas 3 para demonstração
)

if not sugestoes.empty:
    print(f"   ✅ {len(sugestoes)} sugestões geradas para demonstração")
    
    print("\n2. 📊 BREAKDOWN DO CÁLCULO PARA CADA PRODUTO:")
    print("-" * 80)
    
    valor_total_calculado = 0
    
    for idx, produto in sugestoes.iterrows():
        material = produto['material']
        qtd_sugerida = produto.get('quantidade_sugerida', 0)
        valor_medio_mensal = produto.get('valor_medio_mensal', 0)
        demanda_media_mensal = produto.get('demanda_media_mensal', 1)
        
        # Calcula preço unitário estimado
        preco_unitario = valor_medio_mensal / demanda_media_mensal if demanda_media_mensal > 0 else 0
        
        # Calcula valor estimado para este produto
        valor_estimado = qtd_sugerida * preco_unitario
        valor_total_calculado += valor_estimado
        
        print(f"\n📦 PRODUTO {idx + 1}: {material}")
        print(f"   • Quantidade Sugerida: {qtd_sugerida:,.0f} unidades")
        print(f"   • Valor Médio Mensal (histórico): R$ {valor_medio_mensal:,.2f}")
        print(f"   • Demanda Média Mensal (histórico): {demanda_media_mensal:,.1f} unidades")
        print(f"   • Preço Unitário Estimado: R$ {preco_unitario:,.2f}")
        print(f"   • Valor Estimado Total: R$ {valor_estimado:,.2f}")
        print(f"     └─ Cálculo: {qtd_sugerida:,.0f} × R$ {preco_unitario:,.2f} = R$ {valor_estimado:,.2f}")
    
    print("\n" + "=" * 80)
    print(f"💰 VALOR TOTAL SUGERIDO: R$ {valor_total_calculado:,.2f}")
    print("=" * 80)
    
    print("\n3. 🔍 DETALHAMENTO DA METODOLOGIA:")
    print("""
    🧮 FÓRMULA COMPLETA:
    
    Para cada produto recomendado:
    ├── 1. Calcula Preço Unitário Estimado:
    │   └── preço_unitário = valor_medio_mensal ÷ demanda_media_mensal
    │
    ├── 2. Calcula Valor Estimado do Produto:
    │   └── valor_produto = quantidade_sugerida × preço_unitário
    │
    └── 3. Soma Todos os Produtos:
        └── VALOR TOTAL = Σ(valor_produto₁ + valor_produto₂ + ... + valor_produto_n)
    """)
    
    print("\n4. 📋 ORIGEM DOS VALORES BASE:")
    print("   🎯 QUANTIDADE SUGERIDA:")
    print("   • Baseada em demanda histórica + safety stock")
    print("   • Considera lead time de fornecimento")
    print("   • Inclui margem de segurança")
    
    print("\n   💰 PREÇO UNITÁRIO (valor_medio_mensal / demanda_media_mensal):")
    print("   • valor_medio_mensal: Média dos valores de VENDA (vlr_rol) por mês")
    print("   • demanda_media_mensal: Média das quantidades vendidas por mês")
    print("   • Resultado: Preço médio unitário baseado no histórico de vendas")
    
    print("\n5. ⚠️ IMPORTANTE - LIMITAÇÕES:")
    print("   ❌ Usa preços de VENDA, não de COMPRA")
    print("   ❌ Pode incluir margem de lucro da empresa")
    print("   ❌ Não considera descontos por volume")
    print("   ❌ Não considera variações atuais de fornecedores")
    print("   ❌ Baseado em dados históricos, não preços atuais")
    
    print("\n6. 🎯 INTERPRETAÇÃO:")
    print("   📊 O Valor Total Sugerido representa uma ESTIMATIVA de investimento")
    print("   📊 baseada em padrões históricos de vendas da empresa")
    print("   📊 Para decisões de compra, recomenda-se validar preços atuais")
    
else:
    print("   ❌ Não foi possível gerar sugestões para demonstração")