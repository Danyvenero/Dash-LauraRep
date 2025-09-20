from utils import load_all_data

# Carrega dados
vendas_df, _, _ = load_all_data()

print("📊 ANÁLISE DO CÁLCULO DO VALOR TOTAL SUGERIDO")
print("=" * 60)

print("\n1. 📋 ORIGEM DOS DADOS:")
print(f"   • Registros de vendas: {len(vendas_df):,}")
print(f"   • Colunas principais: {vendas_df.columns.tolist()[:8]}")

print("\n2. 💰 VALORES DE VENDA (vlr_rol):")
print(f"   • Valor mínimo: R$ {vendas_df['vlr_rol'].min():,.2f}")
print(f"   • Valor médio: R$ {vendas_df['vlr_rol'].mean():,.2f}")
print(f"   • Valor máximo: R$ {vendas_df['vlr_rol'].max():,.2f}")

print("\n3. 🔍 AMOSTRA DE DADOS:")
sample = vendas_df[['material', 'produto', 'qtd_rol', 'vlr_rol', 'data_faturamento']].head(3)
for _, row in sample.iterrows():
    print(f"   • Material: {row['material']} | Qtd: {row['qtd_rol']} | Valor: R$ {row['vlr_rol']:,.2f}")

print("\n4. 🧮 COMO É CALCULADO O PREÇO UNITÁRIO:")
print("   Fórmula: valor_medio_mensal / demanda_media_mensal")
print("   • valor_medio_mensal = Média dos vlr_rol mensais do produto")
print("   • demanda_media_mensal = Média das qtd_rol mensais do produto")

# Exemplo prático
produto_exemplo = vendas_df[vendas_df['material'] == vendas_df['material'].iloc[0]]
if len(produto_exemplo) > 1:
    material = produto_exemplo['material'].iloc[0]
    valor_total = produto_exemplo['vlr_rol'].sum()
    qtd_total = produto_exemplo['qtd_rol'].sum()
    preco_medio = valor_total / qtd_total if qtd_total > 0 else 0
    
    print(f"\n5. 📈 EXEMPLO PRÁTICO - Material {material}:")
    print(f"   • Total vendido: {qtd_total:,.0f} unidades")
    print(f"   • Valor total: R$ {valor_total:,.2f}")
    print(f"   • Preço médio unitário: R$ {preco_medio:,.2f}")

print("\n6. ⚠️ IMPORTANTES OBSERVAÇÕES:")
print("   • Os valores são baseados em VENDAS HISTÓRICAS (vlr_rol)")
print("   • Não são preços de COMPRA, mas sim de VENDA")
print("   • Podem incluir margem de lucro da empresa")
print("   • Variações de preço ao longo do tempo são consideradas")