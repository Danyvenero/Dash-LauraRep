#!/usr/bin/env python3
"""
Teste rápido de importações
"""

def test_imports():
    try:
        print("🔧 Testando importações...")
        
        # Teste 1: load_all_data
        from utils import load_all_data
        print("✅ load_all_data importado com sucesso")
        
        # Teste 2: purchase_recommender
        from utils.ml_recommendations import purchase_recommender
        print("✅ purchase_recommender importado com sucesso")
        
        # Teste 3: Execução básica
        vendas, cotacoes, produtos = load_all_data()
        print(f"✅ Dados carregados: vendas={len(vendas)}, cotacoes={len(cotacoes)}, produtos={len(produtos)}")
        
        print("🎉 Todas as importações funcionando!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ TESTE PASSOU - Sistema pronto para uso!")
    else:
        print("\n❌ TESTE FALHOU - Verifique as dependências")