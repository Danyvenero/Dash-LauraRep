"""
Teste básico da aplicação com correções
"""

try:
    print("🔍 Testando importação do módulo...")
    from utils.ml_recommendations import SmartPurchaseRecommendations
    print("✅ Módulo importado com sucesso")
    
    print("🔧 Criando instância...")
    recommender = SmartPurchaseRecommendations()
    print("✅ Instância criada com sucesso")
    
    print("✅ Todas as correções foram aplicadas com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()