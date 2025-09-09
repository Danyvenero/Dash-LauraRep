#!/usr/bin/env python3
"""
Script para testar a validação de duplicatas no sistema
"""

import pandas as pd
from utils.db import get_dataset_statistics, save_dataset
from utils.data_loader_fixed import DataLoaderFixed

def test_duplicate_validation():
    """Testa o sistema de validação de duplicatas"""
    
    print("🧪 TESTE DE VALIDAÇÃO DE DUPLICATAS")
    print("=" * 50)
    
    # 1. Estatísticas iniciais
    stats = get_dataset_statistics()
    print(f"📊 ESTATÍSTICAS INICIAIS:")
    print(f"   Datasets: {stats['total_datasets']}")
    print(f"   Vendas: {stats['total_vendas']}")
    print(f"   Cotações: {stats['total_cotacoes']}")
    print(f"   Produtos: {stats['total_produtos_cotados']}")
    print()
    
    # 2. Criar dados de teste
    print("🔧 CRIANDO DADOS DE TESTE...")
    
    # Dados de vendas de teste
    vendas_test = pd.DataFrame({
        'cod_cliente': ['CLI001', 'CLI002', 'CLI003'],
        'cliente': ['Cliente A', 'Cliente B', 'Cliente C'],
        'material': ['MAT001', 'MAT002', 'MAT003'],
        'produto': ['Produto A', 'Produto B', 'Produto C'],
        'data': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'qtd_entrada': [100, 200, 300],
        'vlr_entrada': [1000.0, 2000.0, 3000.0]
    })
    
    # Dados de cotações de teste
    cotacoes_test = pd.DataFrame({
        'numero_cotacao': ['COT001', 'COT002'],
        'numero_revisao': [1, 1],
        'cod_cliente': ['CLI001', 'CLI002'],
        'cliente': ['Cliente A', 'Cliente B'],
        'data': ['2025-01-01', '2025-01-02'],
        'status_cotacao': ['Aberta', 'Fechada']
    })
    
    print(f"   ✅ Vendas: {len(vendas_test)} registros")
    print(f"   ✅ Cotações: {len(cotacoes_test)} registros")
    print()
    
    # 3. Primeiro upload (deve inserir todos)
    print("📤 PRIMEIRO UPLOAD (deve inserir todos)...")
    dataset_id1 = save_dataset(
        "Teste_Primeiro_Upload",
        1,  # user_id admin
        vendas_test,
        cotacoes_test,
        None
    )
    print(f"   Dataset ID: {dataset_id1}")
    print()
    
    # 4. Segundo upload (MESMOS dados - deve detectar duplicata)
    print("📤 SEGUNDO UPLOAD (mesmos dados - deve detectar duplicata)...")
    dataset_id2 = save_dataset(
        "Teste_Segundo_Upload_Duplicado",
        1,  # user_id admin
        vendas_test,
        cotacoes_test,
        None
    )
    print(f"   Dataset ID: {dataset_id2}")
    print(f"   Duplicata detectada: {dataset_id1 == dataset_id2}")
    print()
    
    # 5. Terceiro upload (dados MODIFICADOS - deve inserir)
    print("📤 TERCEIRO UPLOAD (dados modificados - deve inserir)...")
    vendas_modificadas = vendas_test.copy()
    vendas_modificadas.loc[0, 'qtd_entrada'] = 999  # Mudança pequena
    
    dataset_id3 = save_dataset(
        "Teste_Terceiro_Upload_Modificado",
        1,  # user_id admin
        vendas_modificadas,
        cotacoes_test,
        None
    )
    print(f"   Dataset ID: {dataset_id3}")
    print(f"   Dados novos inseridos: {dataset_id3 != dataset_id1}")
    print()
    
    # 6. Estatísticas finais
    stats_final = get_dataset_statistics()
    print(f"📊 ESTATÍSTICAS FINAIS:")
    print(f"   Datasets: {stats_final['total_datasets']} (diff: +{stats_final['total_datasets'] - stats['total_datasets']})")
    print(f"   Vendas: {stats_final['total_vendas']} (diff: +{stats_final['total_vendas'] - stats['total_vendas']})")
    print(f"   Cotações: {stats_final['total_cotacoes']} (diff: +{stats_final['total_cotacoes'] - stats['total_cotacoes']})")
    print()
    
    print("✅ TESTE CONCLUÍDO!")
    print("   - Duplicatas devem ser detectadas e bloqueadas")
    print("   - Apenas dados novos/modificados devem ser inseridos")

if __name__ == "__main__":
    test_duplicate_validation()
