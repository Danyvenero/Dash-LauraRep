#!/usr/bin/env python3
"""
Teste da correção de vlr_entrada com uso correto da coluna data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import load_vendas_data
from webapp.callbacks import apply_filters

def test_entrada_correction():
    """Testa se a correção da entrada está funcionando"""
    print("🧪 TESTE DA CORREÇÃO VLR_ENTRADA")
    print("=" * 50)
    
    # Carrega dados
    vendas_df = load_vendas_data()
    print(f"📊 Dados carregados: {len(vendas_df)} registros")
    print(f"   Colunas: {list(vendas_df.columns)}")
    
    if vendas_df.empty:
        print("❌ Não há dados para testar!")
        return
    
    # Teste estatísticas originais
    if 'vlr_entrada' in vendas_df.columns:
        total_entrada = vendas_df['vlr_entrada'].sum()
        registros_entrada = (vendas_df['vlr_entrada'] > 0).sum()
        print(f"\n💰 DADOS ORIGINAIS:")
        print(f"   Total vlr_entrada: R$ {total_entrada:,.2f}")
        print(f"   Registros com entrada > 0: {registros_entrada}")
    
    # Teste filtros SEM especificar métrica (comportamento antigo)
    print(f"\n🔍 TESTE 1: Filtro PADRÃO (sem especificar métrica)")
    df_filtrado_padrao = apply_filters(vendas_df, [2018, 2025], None, None, None, None, None)
    entrada_padrao = df_filtrado_padrao['vlr_entrada'].sum() if 'vlr_entrada' in df_filtrado_padrao.columns else 0
    print(f"   Resultado filtro padrão: R$ {entrada_padrao:,.2f}")
    
    # Teste filtros ESPECIFICANDO métrica entrada
    print(f"\n🔍 TESTE 2: Filtro para ENTRADA (com metrica_type='entrada')")
    df_filtrado_entrada = apply_filters(vendas_df, [2018, 2025], None, None, None, None, None, metrica_type='entrada')
    entrada_corrigida = df_filtrado_entrada['vlr_entrada'].sum() if 'vlr_entrada' in df_filtrado_entrada.columns else 0
    print(f"   Resultado filtro entrada: R$ {entrada_corrigida:,.2f}")
    
    # Teste filtros ESPECIFICANDO métrica faturamento
    print(f"\n🔍 TESTE 3: Filtro para FATURAMENTO (com metrica_type='faturamento')")
    df_filtrado_faturamento = apply_filters(vendas_df, [2018, 2025], None, None, None, None, None, metrica_type='faturamento')
    faturamento = df_filtrado_faturamento['vlr_rol'].sum() if 'vlr_rol' in df_filtrado_faturamento.columns else 0
    print(f"   Resultado filtro faturamento: R$ {faturamento:,.2f}")
    
    # Verificar se há diferença
    print(f"\n📈 ANÁLISE DOS RESULTADOS:")
    if entrada_corrigida > entrada_padrao:
        print(f"   ✅ CORREÇÃO FUNCIONOU! Entrada corrigida é maior: R$ {entrada_corrigida - entrada_padrao:,.2f}")
    elif entrada_corrigida == entrada_padrao:
        print(f"   ⚠️ Sem diferença detectada - pode estar OK ou precisar investigar")
    else:
        print(f"   ❌ Entrada corrigida é menor - algo pode estar errado")
    
    # Verificar colunas de data usadas
    print(f"\n📅 VERIFICAÇÃO DAS COLUNAS DE DATA:")
    if 'data' in vendas_df.columns:
        data_count = vendas_df['data'].notna().sum()
        print(f"   Coluna 'data': {data_count} valores não-nulos")
    
    if 'data_faturamento' in vendas_df.columns:
        data_fat_count = vendas_df['data_faturamento'].notna().sum()
        print(f"   Coluna 'data_faturamento': {data_fat_count} valores não-nulos")

if __name__ == "__main__":
    test_entrada_correction()
