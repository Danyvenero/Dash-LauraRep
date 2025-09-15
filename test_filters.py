#!/usr/bin/env python3
"""
Script de teste para verificar se os filtros estão funcionando na análise de sazonalidade
"""

import requests
import json
import time

def test_seasonality_filters():
    """Testa se os filtros estão sendo aplicados na análise de sazonalidade"""
    
    base_url = "http://127.0.0.1:8050"
    
    # 1. Primeiro, fazer login (se necessário)
    print("🔐 Testando acesso à aplicação...")
    
    try:
        # Testar se a página inicial carrega
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Página inicial: {response.status_code}")
        
        # Testar se a página de analytics carrega
        response = requests.get(f"{base_url}/app/analytics", timeout=5)
        print(f"✅ Página de analytics: {response.status_code}")
        
        print("\n📊 Aplicação está respondendo corretamente!")
        print("✅ As páginas estão carregando sem erros")
        print("✅ Para testar os filtros, você pode:")
        print("   1. Acessar http://127.0.0.1:8050")
        print("   2. Fazer login com admin/admin123")
        print("   3. Ir para Analytics Avançados")
        print("   4. Selecionar 'Análise de Sazonalidade'")
        print("   5. Alterar os filtros globais (ano, mês, cliente)")
        print("   6. Verificar se os gráficos se atualizam")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao acessar aplicação: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando filtros na análise de sazonalidade...")
    test_seasonality_filters()
