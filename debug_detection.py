#!/usr/bin/env python3

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.data_loader_fixed import DataLoaderFixed

def test_detection():
    loader = DataLoaderFixed()
    
    # Simula as colunas dos arquivos de cotações
    cotacoes_columns = ['número da cotação', 'número da revisão', 'linhas de cotação', 
                       'referência do cliente', 'código do cliente', 'nome do cliente']
    
    # Simula as colunas dos materiais cotados
    materiais_columns = ['cotação', 'cod. cliente', 'cliente', 'representante', 
                        'centro fornecedor', 'material', 'descrição', 'prazo de entrega (dias)', 
                        'quantidade', 'preço base', 'preço líquido unitário', 'preço líquido total']
    
    # Cria DataFrames de teste
    df_cotacoes = pd.DataFrame(columns=cotacoes_columns)
    df_materiais = pd.DataFrame(columns=materiais_columns)
    
    print("=== TESTE DE DETECÇÃO DE TIPO ===")
    
    # Testa detecção para arquivo de cotações
    print("\n1. Testando arquivo: 2019.xls")
    tipo_2019 = loader.detect_file_type("2019.xls", df_cotacoes)
    print(f"Resultado: {tipo_2019}")
    
    # Testa detecção para arquivo de materiais
    print("\n2. Testando arquivo: materiais_cotados.xlsx")
    tipo_materiais = loader.detect_file_type("materiais_cotados.xlsx", df_materiais)
    print(f"Resultado: {tipo_materiais}")
    
    # Testa com nomes mais explícitos
    print("\n3. Testando arquivo: cotacoes_2019.xls")
    tipo_cotacoes_explicito = loader.detect_file_type("cotacoes_2019.xls", df_cotacoes)
    print(f"Resultado: {tipo_cotacoes_explicito}")

if __name__ == "__main__":
    test_detection()
