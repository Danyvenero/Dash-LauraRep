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
    
    # Manter registros que têm data válida OU que têm valor_faturado válido (mesmo sem data)
    if 'valor_faturado' in df_vendas.columns:
        mask_validos = (~df_vendas['data_faturamento'].isnull()) | (~df_vendas['valor_faturado'].isnull() & (df_vendas['valor_faturado'] != 0))
        df_vendas = df_vendas[mask_validos]
    else:
        df_vendas = df_vendas.dropna(subset=['data_faturamento'])
    
    if df_vendas.empty:
        return pd.DataFrame()
    
    hoje = datetime.now()
    total_mix_global = _calculate_global_mix(df_vendas)
    
    # Verificar qual coluna usar para valor - PRIORIZAR valor_faturado
    valor_col = None
    # Ordem de prioridade: valor_faturado, valor_liquido, valor, ROL
    for col in ['valor_faturado', 'valor_liquido', 'valor', 'ROL', 'rol', 'total_valor']:
        if col in df_vendas.columns:
            valor_col = col
            break
    
    if valor_col is None:
        return pd.DataFrame()
    
    # Verificar qual coluna usar para quantidade  
    qtd_col = None
    for col in ['quantidade_faturada', 'quantidade', 'qtd']:
        if col in df_vendas.columns:
            qtd_col = col
            break
    
    if qtd_col is None:
        return pd.DataFrame()
    
    kpis_vendas = df_vendas.groupby('cod_cliente').agg(
        cliente=('cliente', 'first'), 
        ultima_compra=('data_faturamento', 'max'),
        total_comprado_valor=(valor_col, 'sum'), 
        total_comprado_qtd=(qtd_col, 'sum'),
        mix_produtos=('material', 'nunique'), 
        unidades_negocio=('unidade_negocio', 'nunique')
    ).reset_index()
    
    kpis_vendas['dias_sem_compra'] = (hoje - kpis_vendas['ultima_compra']).dt.days
    kpis_cotacoes = df_cotacoes.groupby('cod_cliente').agg(total_cotado_qtd=('quantidade', 'sum')).reset_index()
    df_kpis = pd.merge(kpis_vendas, kpis_cotacoes, on='cod_cliente', how='left')
    df_kpis['total_cotado_qtd'] = df_kpis['total_cotado_qtd'].fillna(0)
    
    # CORREÇÃO 1: % Mix Produtos - limitando a 100% máximo
    df_kpis['pct_mix_produtos'] = (df_kpis['mix_produtos'] / total_mix_global) * 100
    df_kpis['pct_mix_produtos'] = df_kpis['pct_mix_produtos'].clip(upper=100)  # Limitar a 100%
    
    # CORREÇÃO 2: % Não Comprado - limitando entre 0% e 100%
    df_kpis.loc[:, 'pct_nao_comprado'] = 0.0
    non_zero_mask = df_kpis['total_cotado_qtd'] > 0
    df_kpis.loc[non_zero_mask, 'pct_nao_comprado'] = ((df_kpis.loc[non_zero_mask, 'total_cotado_qtd'] - df_kpis.loc[non_zero_mask, 'total_comprado_qtd']) / df_kpis.loc[non_zero_mask, 'total_cotado_qtd']) * 100
    
    # Limitar % Não Comprado entre 0% e 100% (evitar valores negativos e >100%)
    df_kpis['pct_nao_comprado'] = df_kpis['pct_nao_comprado'].clip(lower=0, upper=100)
    
    # CORREÇÃO 3: Arredondamento para 0 casas decimais conforme solicitado
    df_kpis['total_comprado_valor'] = df_kpis['total_comprado_valor'].round(2)
    df_kpis['pct_nao_comprado'] = df_kpis['pct_nao_comprado'].round(0)  # 0 casas decimais
    df_kpis['pct_mix_produtos'] = df_kpis['pct_mix_produtos'].round(0)  # 0 casas decimais
    
    df_kpis.sort_values(by='total_comprado_valor', ascending=False, inplace=True)
    return df_kpis

# --- FUNÇÕES PARA A PÁGINA DE PROPOSTAS ---

def calculate_funil_metrics(df_vendas, df_cotacoes, periodo_meses=12, threshold_conversao=20, threshold_dias_risco=90):
    """
    Calcula métricas do funil de vendas
    
    Args:
        df_vendas: DataFrame de vendas
        df_cotacoes: DataFrame de cotações
        periodo_meses: Período em meses para análise
        threshold_conversao: % limite para baixa conversão
        threshold_dias_risco: Dias limite para risco de inatividade
    
    Returns:
        dict: Métricas do funil
    """
    hoje = datetime.now()
    data_limite = hoje - pd.DateOffset(months=periodo_meses)
    
    # Filtrar por período
    if 'data_faturamento' in df_vendas.columns:
        df_vendas_periodo = df_vendas[pd.to_datetime(df_vendas['data_faturamento']) >= data_limite]
    else:
        df_vendas_periodo = df_vendas
        
    if 'data' in df_cotacoes.columns:
        df_cotacoes_periodo = df_cotacoes[pd.to_datetime(df_cotacoes['data']) >= data_limite]
    else:
        df_cotacoes_periodo = df_cotacoes
    
    # Calcular conversões por cliente
    cotacoes_por_cliente = df_cotacoes_periodo.groupby('cod_cliente').agg({
        'quantidade': 'sum',
        'cliente': 'first'
    }).reset_index()
    
    vendas_por_cliente = df_vendas_periodo.groupby('cod_cliente').agg({
        'quantidade_faturada': 'sum',
        'data_faturamento': 'max'
    }).reset_index()
    
    # Merge para calcular conversão
    funil_data = pd.merge(cotacoes_por_cliente, vendas_por_cliente, on='cod_cliente', how='left')
    funil_data['quantidade_faturada'] = funil_data['quantidade_faturada'].fillna(0)
    funil_data['conversao_pct'] = np.where(
        funil_data['quantidade'] > 0,
        (funil_data['quantidade_faturada'] / funil_data['quantidade']) * 100,
        0
    )
    
    # Calcular dias sem compra
    funil_data['dias_sem_compra'] = np.where(
        funil_data['data_faturamento'].notna(),
        (hoje - pd.to_datetime(funil_data['data_faturamento'])).dt.days,
        999
    )
    
    # Lista A: Baixa conversão, alto volume
    lista_a = funil_data[
        (funil_data['conversao_pct'] < threshold_conversao) & 
        (funil_data['quantidade'] > funil_data['quantidade'].quantile(0.75))
    ].sort_values('quantidade', ascending=False)
    
    # Lista B: Risco de inatividade
    lista_b = funil_data[
        funil_data['dias_sem_compra'] > threshold_dias_risco
    ].sort_values('dias_sem_compra', ascending=False)
    
    # Métricas gerais
    total_clientes_cotaram = len(cotacoes_por_cliente)
    total_clientes_compraram = len(vendas_por_cliente)
    taxa_conversao_geral = (total_clientes_compraram / total_clientes_cotaram * 100) if total_clientes_cotaram > 0 else 0
    
    return {
        'total_clientes_cotaram': total_clientes_cotaram,
        'total_clientes_compraram': total_clientes_compraram,
        'taxa_conversao_geral': round(taxa_conversao_geral, 2),
        'lista_a': lista_a,
        'lista_b': lista_b,
        'funil_completo': funil_data
    }

def calculate_produtos_matrix(df_vendas, df_cotacoes, top_produtos=20, top_clientes=15):
    """
    Calcula matriz de produtos vs clientes para gráfico de bolhas
    """
    if df_cotacoes.empty:
        return pd.DataFrame()
    
    # Agrupar cotações por cliente e material
    cotacoes_matrix = df_cotacoes.groupby(['cod_cliente', 'cliente', 'material']).agg({
        'quantidade': 'sum'
    }).reset_index()
    
    # Agrupar vendas por cliente e material
    if not df_vendas.empty:
        vendas_matrix = df_vendas.groupby(['cod_cliente', 'material']).agg({
            'quantidade_faturada': 'sum'
        }).reset_index()
        
        # Merge para calcular % não comprado
        matrix = pd.merge(cotacoes_matrix, vendas_matrix, on=['cod_cliente', 'material'], how='left')
        matrix['quantidade_faturada'] = matrix['quantidade_faturada'].fillna(0)
        matrix['pct_nao_comprado'] = np.where(
            matrix['quantidade'] > 0,
            ((matrix['quantidade'] - matrix['quantidade_faturada']) / matrix['quantidade']) * 100,
            0
        )
    else:
        matrix = cotacoes_matrix.copy()
        matrix['quantidade_faturada'] = 0
        matrix['pct_nao_comprado'] = 100
    
    # Filtrar top produtos e clientes
    top_materiais = matrix.groupby('material')['quantidade'].sum().nlargest(top_produtos).index
    top_clientes_list = matrix.groupby(['cod_cliente', 'cliente'])['quantidade'].sum().nlargest(top_clientes).index
    
    matrix_filtered = matrix[
        matrix['material'].isin(top_materiais) & 
        matrix[['cod_cliente', 'cliente']].apply(tuple, axis=1).isin(top_clientes_list)
    ]
    
    return matrix_filtered

def get_client_recommendations(client_code, df_vendas, df_cotacoes):
    """
    Gera recomendações específicas para um cliente
    """
    client_vendas = df_vendas[df_vendas['cod_cliente'] == client_code]
    client_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'] == client_code]
    
    recommendations = []
    
    if client_cotacoes.empty:
        recommendations.append("Cliente não possui histórico de cotações recentes.")
        return recommendations
    
    # Produtos cotados mas não comprados
    materiais_cotados = set(client_cotacoes['material'].unique())
    materiais_comprados = set(client_vendas['material'].unique()) if not client_vendas.empty else set()
    materiais_nao_comprados = materiais_cotados - materiais_comprados
    
    if materiais_nao_comprados:
        recommendations.append(f"Cliente cotou {len(materiais_nao_comprados)} produtos que não comprou. Foco em follow-up.")
    
    # Análise de frequência
    if not client_vendas.empty and 'data_faturamento' in client_vendas.columns:
        ultima_compra = pd.to_datetime(client_vendas['data_faturamento']).max()
        dias_sem_compra = (datetime.now() - ultima_compra).days
        
        if dias_sem_compra > 90:
            recommendations.append(f"Cliente sem comprar há {dias_sem_compra} dias. Agendar visita comercial.")
        elif dias_sem_compra > 30:
            recommendations.append("Cliente em período normal. Manter contato regular.")
    
    # Volume de cotações vs compras
    vol_cotado = client_cotacoes['quantidade'].sum()
    vol_comprado = client_vendas['quantidade_faturada'].sum() if not client_vendas.empty else 0
    
    if vol_cotado > 0:
        conversao = (vol_comprado / vol_cotado) * 100
        if conversao < 30:
            recommendations.append(f"Taxa de conversão baixa ({conversao:.1f}%). Revisar proposta comercial.")
    
    return recommendations

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