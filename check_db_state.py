#!/usr/bin/env python3
"""
Script para testar as funções de limpeza corrigidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_data_statistics, get_connection

def check_datasets_after_clear():
    """Verifica quantos datasets existem no banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🔍 Verificando estado atual do banco...")
    
    # Verifica datasets
    cursor.execute("SELECT id, name, vendas_fingerprint, cotacoes_fingerprint, produtos_cotados_fingerprint FROM datasets")
    datasets = cursor.fetchall()
    
    print(f"\n📊 Datasets no banco: {len(datasets)}")
    for dataset in datasets:
        print(f"  ID: {dataset[0]} | Nome: {dataset[1]}")
        print(f"    Vendas FP: {'✅' if dataset[2] else '❌'}")
        print(f"    Cotações FP: {'✅' if dataset[3] else '❌'}")
        print(f"    Materiais FP: {'✅' if dataset[4] else '❌'}")
        print()
    
    # Estatísticas dos dados
    stats = get_data_statistics()
    print(f"📈 Estatísticas atuais:")
    print(f"  Vendas: {stats['vendas']:,}")
    print(f"  Cotações: {stats['cotacoes']:,}")
    print(f"  Materiais: {stats['materiais']:,}")
    print(f"  Datasets: {stats['datasets']:,}")
    
    conn.close()

if __name__ == "__main__":
    check_datasets_after_clear()
