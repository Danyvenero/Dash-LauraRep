#!/usr/bin/env python3
"""
Script para testar o carregamento de dados atual
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data, get_latest_dataset

def test_data_loading():
    """Testa o carregamento atual de dados"""
    print("🔍 TESTANDO CARREGAMENTO DE DADOS...")
    print("="*50)
    
    # Verifica dataset mais recente
    latest = get_latest_dataset()
    print(f"📊 Dataset mais recente: {latest}")
    print()
    
    # Testa carregamento com método atual
    print("📈 CARREGAMENTO ATUAL (último dataset):")
    
    vendas_df = load_vendas_data()
    print(f"   Vendas: {len(vendas_df)} registros")
    
    cotacoes_df = load_cotacoes_data()
    print(f"   Cotações: {len(cotacoes_df)} registros")
    
    produtos_df = load_produtos_cotados_data()
    print(f"   Produtos: {len(produtos_df)} registros")
    
    print()
    print("🔍 PROBLEMA IDENTIFICADO:")
    print("   As funções só carregam do dataset mais recente!")
    print("   Mas os dados estão em datasets diferentes:")
    print("   - Vendas: Dataset 1")
    print("   - Cotações: Dataset 6") 
    print("   - Produtos: Dataset 11")

if __name__ == "__main__":
    test_data_loading()
