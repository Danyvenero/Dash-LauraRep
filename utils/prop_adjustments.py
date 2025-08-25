from pathlib import Path
import pandas as pd

def carrega_materiais():
    pasta_dataset = Path('data/arquivos_compilados')
    caminho_materiais = pasta_dataset / 'materiais_cotados.xlsx'

    df = pd.read_excel(caminho_materiais, decimal=',')
    df.fillna({'Centro Fornecedor':0}, inplace=True)
    df['Material'] = df['Material'].astype('string')
    df['Unidade'] = df.apply(centro_fornecedor, axis=1)
    return df


def carrega_hierarquia_2(df_prop, df_ovs):
    df_prop = df_prop.merge(
    df_ovs[['Material', 'Hier. Produto 2']],
    on='Material',
    how='left'
    ).rename(columns={'Hier. Produto 2': 'Hierarquia'})
    return df_prop


def carrega_propostas():
    caminho = Path('data/propostas')
    lista_dfs = []
    colunas = ['Número da Cotação', 'Número da Revisão', 'Linhas de Cotação',
        'Código do Cliente', 'Nome do Cliente', 'Data de Criação',
        'Data de Emissão', 'Status da Cotação', 'Valor total',
        'Emissor', 'Representante de Vendas', 'Criado Por (login)',
        'Incoterm 1', 'Condição de Pagamento', 'Organização de Vendas',
        'Canal de Distribuição', 'Divisão', 'Escritório de Vendas',
        'Equipe de Vendas']

    # Percorre todos os arquivos com extensão .xls na pasta
    for arquivo in caminho.glob('*.xls'):
        # Lê todas as planilhas do arquivo, retornando um dicionário
        planilhas = pd.read_excel(arquivo, sheet_name=None, usecols=colunas)
        # Itera sobre as planilhas e adiciona cada DataFrame à lista
        for nome, df in planilhas.items():
            lista_dfs.append(df)

    # Concatena todos os DataFrames em um único DataFrame consolidado
    df = pd.concat(lista_dfs, ignore_index=True)
    materiais = carrega_materiais()
    df = prop_general_adjusments(df)
    df = prop_merge_products(df, materiais)
    df = prop_columns_adjustments(df)
    return df


def busca_hierarquia(df, df_ovs):
    df = df.merge(
    df_ovs[['Material', 'Hier. Produto 2']],
    on='Material',
    how='left'
    ).rename(columns={'Hier. Produto 2': 'Hierarquia'})
    return df


def prop_general_adjusments(df):
    df.rename(columns={'Número da Cotação': 'Cotação'}, inplace=True)
    df.rename(columns={'Nome do Cliente': 'Cliente'}, inplace=True)
    #df.rename(columns={'Descrição': 'Produto'}, inplace=True)
    df['Cliente'] = df['Cliente'].astype('string').str.lower()
    df['Código do Cliente'] = df['Código do Cliente'].astype('string')
    df['Data de Criação'] = pd.to_datetime(df['Data de Criação'], format='%d/%m/%Y', errors='coerce')
    return df


def prop_merge_products(df_prop, df_materiais):
    df = df_prop.merge(df_materiais, how='left', on='Cotação')
    df = df.drop(columns=['Data de Emissão', 'IPI %', 'Preço base', 'Representante', 'Cliente_y', 'Prazo de entrega (Dias)', 'Representante de Vendas',
                          'Criado Por (login)', 'Incoterm 1', 'Condição de Pagamento', 'Emissor', 'Escritório de Vendas', 'Equipe de Vendas',
                          'Taxa Financeira %', 'Cod Cliente'], errors='ignore')
    df['Unidade'] = df.apply(centro_fornecedor, axis=1)
    return df


def prop_columns_adjustments(df):
    #print(df.columns)
    df = df[df['Material'].notnull()].copy()
    df.rename(columns={'Descrição': 'Produto', 'Cliente_x': 'Cliente', 'Código do Cliente': 'ID_Cli', 'Data de Criação_x': 'Data de Criação'}, inplace=True)
    df['Ano'] = df['Data de Criação'].dt.year
    df['Mês'] = df['Data de Criação'].dt.month
    df['Dia'] = df['Data de Criação'].dt.day
    return df


def centro_fornecedor(row):
    if row['Centro Fornecedor'] == 1100.0:
        return 'WMO-I'
    elif row['Centro Fornecedor'] == 1106.0:
        return 'WMO-C'
    elif row['Centro Fornecedor'] == 1108.0:
        return 'WCES'
    elif row['Centro Fornecedor'] == 1109.0:
        return 'WCES'
    elif row['Centro Fornecedor'] == 1200.0:
        return 'WEN'
    elif row['Centro Fornecedor'] == 1201.0:
        return 'WEN'
    elif row['Centro Fornecedor'] == 1202.0:
        return 'WTD'
    elif row['Centro Fornecedor'] == 1203.0:
        return 'WTD'
    elif row['Centro Fornecedor'] == 1304.0:
        return 'WDS'
    elif row['Centro Fornecedor'] == 1305.0:
        return 'WDC'
    elif row['Centro Fornecedor'] == 1306.0:
        return 'WDC'
    elif row['Centro Fornecedor'] == 1312.0:
        return 'WDC'
    elif row['Centro Fornecedor'] == 1320.0:
        return 'WDC'
    elif row['Centro Fornecedor'] == 1321.0:
        return 'WDC'
    elif row['Centro Fornecedor'] == 1323.0:
        return 'WDS'
    elif row['Centro Fornecedor'] == 1340.0:
        return 'SOLAR'
    elif row['Centro Fornecedor'] == 1341.0:
        return 'SOLAR'
    elif row['Centro Fornecedor'] == 1505.0:
        return 'WTD'
    else:
        return 'OUTRO'