#!/usr/bin/env python3
"""
Testa a lógica de detecção de duplicatas corrigida
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_connection

def test_duplicate_detection():
    """Testa como a detecção de duplicatas funciona agora"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🧪 Testando detecção de duplicatas...")
    
    # Simula fingerprints como se fosse um upload de cotações
    test_vendas_fp = None
    test_cotacoes_fp = "e75fe59234abcd"  # Exemplo de fingerprint
    test_produtos_fp = None
    
    print(f"🔍 Simulando upload com:")
    print(f"  - Vendas FP: {test_vendas_fp}")
    print(f"  - Cotações FP: {test_cotacoes_fp}")
    print(f"  - Produtos FP: {test_produtos_fp}")
    
    # Aplica a nova lógica
    duplicate_conditions = []
    params = []
    
    if test_vendas_fp:
        duplicate_conditions.append("vendas_fingerprint = ?")
        params.append(test_vendas_fp)
    
    if test_cotacoes_fp:
        duplicate_conditions.append("cotacoes_fingerprint = ?")
        params.append(test_cotacoes_fp)
    
    if test_produtos_fp:
        duplicate_conditions.append("produtos_cotados_fingerprint = ?")
        params.append(test_produtos_fp)
    
    print(f"\n🔍 Condições de busca: {duplicate_conditions}")
    print(f"🔍 Parâmetros: {params}")
    
    # Executa a busca
    duplicate_check = None
    if duplicate_conditions:
        query = f"""
            SELECT id, name, uploaded_at 
            FROM datasets 
            WHERE {' OR '.join(duplicate_conditions)}
            ORDER BY uploaded_at DESC 
            LIMIT 1
        """
        print(f"\n📝 Query: {query}")
        duplicate_check = cursor.execute(query, params).fetchone()
    
    if duplicate_check:
        print(f"⚠️  DUPLICATA ENCONTRADA:")
        print(f"   Dataset: {duplicate_check[1]} (ID: {duplicate_check[0]})")
        print(f"   Data: {duplicate_check[2]}")
    else:
        print(f"✅ NENHUMA DUPLICATA - Upload seria aceito!")
    
    conn.close()

if __name__ == "__main__":
    test_duplicate_detection()
