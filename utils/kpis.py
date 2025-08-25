import pandas as pd
from datetime import datetime
import numpy as np
from utils import db

def calculate_kpis_gerais(df_vendas, df_cotacoes):
    if df_vendas.empty:
        return {'entrada_pedidos': 'R$ 0,00', 'valor_carteira': 'R$ 0,00', 'faturamento': 'R$ 0,00'}
    entrada_pedidos = df_vendas['valor_entrada'].sum()
    valor_carteira = df_vendas['valor_carteira'].sum()
    df_faturado = df_vendas.dropna(subset=['valor_faturado', 'data_faturamento'])
    faturamento = df_faturado['valor_faturado'].sum()
    kpis = {
        'entrada_pedidos': f"R$ {entrada_pedidos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'valor_carteira': f"R$ {valor_carteira:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'faturamento': f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    }
    return kpis

def _calculate_global_mix(df_vendas):
    if df_vendas.empty: return 1
    return df_vendas['material'].nunique()

def calculate_kpis_por_cliente(df_vendas, df_cotacoes):
    if df_vendas.empty: return pd.DataFrame()
    df_vendas = df_vendas.copy()
    df_vendas.loc[:, 'data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
    hoje = datetime.now()
    total_mix_global = _calculate_global_mix(df_vendas)
    kpis_vendas = df_vendas.groupby('cod_cliente').agg(
        cliente=('cliente', 'first'), ultima_compra=('data_faturamento', 'max'),
        total_comprado_valor=('valor_faturado', 'sum'), total_comprado_qtd=('quantidade_faturada', 'sum'),
        mix_produtos=('material', 'nunique'), unidades_negocio=('unidade_negocio', 'nunique')
    ).reset_index()
    kpis_vendas['dias_sem_compra'] = (hoje - kpis_vendas['ultima_compra']).dt.days
    kpis_cotacoes = df_cotacoes.groupby('cod_cliente').agg(total_cotado_qtd=('quantidade', 'sum')).reset_index()
    df_kpis = pd.merge(kpis_vendas, kpis_cotacoes, on='cod_cliente', how='left')
    df_kpis['total_cotado_qtd'] = df_kpis['total_cotado_qtd'].fillna(0)
    df_kpis['pct_mix_produtos'] = (df_kpis['mix_produtos'] / total_mix_global) * 100
    df_kpis.loc[:, 'pct_nao_comprado'] = 0.0
    non_zero_mask = df_kpis['total_cotado_qtd'] > 0
    df_kpis.loc[non_zero_mask, 'pct_nao_comprado'] = ((df_kpis.loc[non_zero_mask, 'total_cotado_qtd'] - df_kpis.loc[non_zero_mask, 'total_comprado_qtd']) / df_kpis.loc[non_zero_mask, 'total_cotado_qtd']) * 100
    df_kpis['total_comprado_valor'] = df_kpis['total_comprado_valor'].round(2)
    df_kpis['pct_nao_comprado'] = df_kpis['pct_nao_comprado'].round(2)
    df_kpis['pct_mix_produtos'] = df_kpis['pct_mix_produtos'].round(2)
    df_kpis.sort_values(by='total_comprado_valor', ascending=False, inplace=True)
    return df_kpis

# --- FUNÇÕES PARA A PÁGINA DE PROPOSTAS ---

def calculate_material_analysis(df_vendas, df_cotacoes):
    if df_cotacoes.empty: return pd.DataFrame()
    df_cotacoes.loc[:, 'data'] = pd.to_datetime(df_cotacoes['data'])
    agg_cotacoes = df_cotacoes.groupby('material').agg(
        total_cotado_qtd=('quantidade', 'sum'),
        primeira_cotacao=('data', 'min'),
        ultima_cotacao=('data', 'max')
    ).reset_index()
    agg_cotacoes['meses_ativo'] = ((agg_cotacoes['ultima_cotacao'] - agg_cotacoes['primeira_cotacao']).dt.days / 30.44).replace(0, 1).round()
    agg_cotacoes['demanda_mensal'] = (agg_cotacoes['total_cotado_qtd'] / agg_cotacoes['meses_ativo']).round(2)
    agg_vendas = df_vendas.groupby('material')['quantidade_faturada'].sum().reset_index(name='total_comprado_qtd')
    df_analysis = pd.merge(agg_cotacoes, agg_vendas, on='material', how='left').fillna(0)
    df_analysis['razao_cot_compra'] = np.where(
        df_analysis['total_comprado_qtd'] > 0,
        df_analysis['total_cotado_qtd'] / df_analysis['total_comprado_qtd'],
        df_analysis['total_cotado_qtd']
    )
    product_map = df_vendas[['material', 'produto']].drop_duplicates(subset=['material'])
    df_analysis = pd.merge(df_analysis, product_map, on='material', how='left')
    return df_analysis[['material', 'produto', 'demanda_mensal', 'razao_cot_compra', 'total_cotado_qtd', 'total_comprado_qtd']]

def get_top_products_comparison(df_vendas, selected_clients=[], top_n=20):
    if df_vendas.empty: return pd.DataFrame()
    top_todos = df_vendas.groupby('produto')['quantidade_faturada'].sum().nlargest(top_n or 20).reset_index()
    top_todos['grupo'] = 'Todos os Clientes'
    if selected_clients:
        df_vendas_cliente = df_vendas[df_vendas['cod_cliente'].isin(selected_clients)]
        if not df_vendas_cliente.empty:
            top_cliente = df_vendas_cliente.groupby('produto')['quantidade_faturada'].sum().nlargest(top_n or 20).reset_index()
            top_cliente['grupo'] = 'Clientes Selecionados'
            return pd.concat([top_todos, top_cliente])
    return top_todos

# --- FUNÇÃO QUE FALTAVA ---
def get_top_n_products_list(df_vendas, top_n=20):
    """Retorna uma lista dos Top N produtos mais comprados (globais)."""
    if df_vendas.empty:
        return []
    return df_vendas.groupby('produto')['quantidade_faturada'].sum().nlargest(top_n or 20).index.tolist()

def generate_purchase_list(df_vendas, df_cotacoes, selected_clients=None):
    if df_vendas.empty or df_cotacoes.empty: return pd.DataFrame()
    total_cotado = df_cotacoes.groupby('material')['quantidade'].sum()
    total_vendido = df_vendas.groupby('material')['quantidade_faturada'].sum()
    df_score = pd.concat([total_cotado, total_vendido], axis=1).fillna(0)
    df_score.columns = ['qtd_cotada', 'qtd_vendida']
    df_score['score'] = (df_score['qtd_cotada'] * 0.5) + (df_score['qtd_vendida'] * 1.5)
    df_score = df_score[df_score['score'] > 0].sort_values(by='score', ascending=False)
    if selected_clients:
        compras_cliente = df_vendas[df_vendas['cod_cliente'].isin(selected_clients)]['material'].unique()
        df_score = df_score[~df_score.index.isin(compras_cliente)]
    sugestoes = df_score.head(50).reset_index()
    
    df_raw_vendas = db.get_raw_data_as_df('raw_vendas')
    product_map = df_raw_vendas[['Material', 'Produto', 'Hier. Produto 3']].rename(
        columns={'Material': 'material', 'Produto': 'produto'}
    ).drop_duplicates(subset=['material'])
    
    sugestoes = pd.merge(sugestoes, product_map, on='material', how='left')
    df_analysis = calculate_material_analysis(df_vendas, df_cotacoes)
    sugestoes = pd.merge(sugestoes, df_analysis[['material', 'demanda_mensal']], on='material', how='left')
    sugestoes_final = sugestoes[['Hier. Produto 3', 'material', 'produto', 'demanda_mensal']].rename(columns={
        'Hier. Produto 3': 'Categoria',
        'material': 'Código do Material',
        'produto': 'Descrição do Produto',
        'demanda_mensal': 'Sugestão de Giro Mensal'
    })
    return sugestoes_final.sort_values(by=['Categoria', 'Sugestão de Giro Mensal'], ascending=[True, False])