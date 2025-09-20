"""
Análise de Colinearidade nas Features do Modelo ML
"""

# Features atuais do modelo ML:
features_atuais = [
    'recencia_dias',                  # Dias desde última compra
    'frequencia_12m',                 # Número de compras em 12 meses
    'valor_medio',                    # Valor médio das compras
    'valor_total_12m',                # Valor total em 12 meses
    'concentracao_sazonal',           # Concentração em trimestres
    'regularidade_cv',                # CV dos intervalos entre compras (POTENCIAL CONFLITO)
    'tendencia',                      # Tendência de crescimento
    'intensidade',                    # Compras/mês ativo
    'cotacoes_ratio',                 # Cotações/compras
    'num_compras_total',              # Total histórico de compras
    'dias_desde_primeira',            # Dias desde primeira compra
    'intervalo_medio_dias',           # Intervalo médio entre compras
    'coef_var_intervalo',             # CV do intervalo (POTENCIAL CONFLITO)
    'ratio_tempo_ciclo',              # Tempo atual/ciclo esperado
    'compras_por_ano',                # Frequência anualizada
    'probabilidade_recorrencia'       # Feature derivada contínua
]

print("🔍 ANÁLISE DE COLINEARIDADE")
print("=" * 50)

print("\n📊 FEATURES RELACIONADAS A VARIABILIDADE:")
variability_features = [
    'regularidade_cv',        # CV dos intervalos entre compras
    'coef_var_intervalo',     # CV do intervalo (parece duplicado!)
    'concentracao_sazonal',   # Também mede variabilidade temporal
]

print(f"  • {variability_features}")

print("\n📊 FEATURES RELACIONADAS A FREQUÊNCIA:")
frequency_features = [
    'frequencia_12m',         # Compras últimos 12m  
    'num_compras_total',      # Total histórico
    'compras_por_ano',        # Frequência anualizada (derivada de frequencia_12m!)
    'intensidade',            # Compras/mês ativo (derivada!)
]

print(f"  • {frequency_features}")

print("\n📊 FEATURES RELACIONADAS A TEMPO:")
time_features = [
    'recencia_dias',          # Tempo desde última
    'dias_desde_primeira',    # Tempo desde primeira
    'intervalo_medio_dias',   # Ciclo médio
    'ratio_tempo_ciclo',      # Relação atual/esperado
]

print(f"  • {time_features}")

print("\n⚠️ POTENCIAIS PROBLEMAS DE COLINEARIDADE:")
print("1. 'regularidade_cv' vs 'coef_var_intervalo' - Ambos medem CV de intervalos!")
print("2. 'frequencia_12m' vs 'compras_por_ano' - Altamente correlacionados")
print("3. 'frequencia_12m' vs 'intensidade' - Derivados da mesma base")
print("4. 'valor_medio' vs 'valor_total_12m/frequencia_12m' - Redundantes")

print("\n✅ RECOMENDAÇÕES:")
print("1. Remover 'regularidade_cv' (manter apenas 'coef_var_intervalo')")
print("2. Remover 'compras_por_ano' (derivado de 'frequencia_12m')")
print("3. Escolher entre 'frequencia_12m' ou 'intensidade'")
print("4. Adicionar feature CV do produto (classificação XYZ) pode ser útil SE não causar overfitting")

print("\n🎯 SOBRE COEFICIENTE DE VARIAÇÃO DO PRODUTO:")
print("• CV do produto (demanda) ≠ CV do intervalo (temporal)")
print("• CV do produto pode ser feature valiosa para segmentação")
print("• Não deveria causar colinearidade direta")
print("• Mas pode causar overfitting se correlacionado com target")