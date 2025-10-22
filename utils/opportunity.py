from __future__ import annotations

from typing import Optional, Tuple, Dict
import pandas as pd
import numpy as np


def _pick_value_col(vendas: pd.DataFrame) -> Optional[str]:
    candidates = [
        'vlr_rol', 'valor_faturado', 'valor', 'vlr_total', 'valor_liquido',
        'total_valor', 'vlr_entrada', 'valor_entrada'
    ]
    for c in candidates:
        if c in vendas.columns:
            return c
    return None


def compute_client_opportunities(
    vendas_df: pd.DataFrame,
    cotacoes_df: pd.DataFrame,
    produtos_cotados_df: pd.DataFrame,
    cliente_id: str,
    ano_range: Optional[Tuple[int, int]] = None,
    mes_range: Optional[Tuple[int, int]] = None,
    peso_freq_cotacao: float = 0.5,
    filtro_hierarquia: Optional[Tuple] = None,
    filtro_canal: Optional[Tuple] = None,
    vendas_map_df: Optional[pd.DataFrame] = None,
    freq_mode: str = 'occurrences',
) -> pd.DataFrame:
    """
    Calcula oportunidades por produto para um cliente específico, respeitando filtros de ano/mês.

    Buckets (motivos):
      - "Cotou e não compra": Q_value>0 e V_cliente==0; Pot1 = Q_value * ((1 - w) + w * rank_pct(Q_freq))
      - "Mercado forte, cliente fora": V_mercado>0 e V_cliente==0; Pot2 = V_mercado
      - "Baixa penetração": V_mercado > V_cliente > 0; Pot3 = V_mercado - V_cliente

    Retorna um DataFrame com colunas principais:
      material, produto, oportunidade_brl, motivo, v_cliente, v_mercado, q_valor, q_freq, ultima_cotacao
    """
    if vendas_df is None:
        vendas_df = pd.DataFrame()
    if cotacoes_df is None:
        cotacoes_df = pd.DataFrame()
    if produtos_cotados_df is None:
        produtos_cotados_df = pd.DataFrame()

    # Normalizações básicas
    cliente_id = str(cliente_id) if cliente_id is not None else None
    if cliente_id is None or cliente_id == '' or cliente_id == 'None':
        return pd.DataFrame()

    for df in (vendas_df, cotacoes_df, produtos_cotados_df):
        if 'material' in df.columns:
            df['material'] = df['material'].astype(str).str.strip()
        if 'cod_cliente' in df.columns:
            df['cod_cliente'] = df['cod_cliente'].astype(str).str.strip()

    # Filtro temporal simples para cotações (ano/mês)
    quotes = produtos_cotados_df.copy()
    if not quotes.empty:
        # Tentar enriquecer com data a partir de cotacoes_df
        if 'cotacao' in quotes.columns and 'numero_cotacao' in cotacoes_df.columns:
            co = cotacoes_df[['numero_cotacao', 'data']].drop_duplicates('numero_cotacao') if 'data' in cotacoes_df.columns else cotacoes_df[['numero_cotacao']].copy()
            co['numero_cotacao'] = co['numero_cotacao'].astype(str).str.strip()
            quotes['cotacao'] = quotes['cotacao'].astype(str).str.strip()
            quotes = quotes.merge(co, left_on='cotacao', right_on='numero_cotacao', how='left')
        # Garantir coluna de data, se possível
        if 'data' in quotes.columns:
            quotes['data'] = pd.to_datetime(quotes['data'], errors='coerce')
            if ano_range and isinstance(ano_range, (list, tuple)) and len(ano_range) == 2:
                quotes = quotes[quotes['data'].dt.year.between(int(ano_range[0]), int(ano_range[1]), inclusive='both')]
            if mes_range and isinstance(mes_range, (list, tuple)) and len(mes_range) == 2:
                quotes = quotes[quotes['data'].dt.month.between(int(mes_range[0]), int(mes_range[1]), inclusive='both')]

        # Enriquecer cotações com hierarquia/canal a partir das vendas (para coerência de filtros)
        # Usar um DataFrame amplo para mapear hierarquia/canal (não filtrado por cliente),
        # para não perder materiais apenas cotados (sem vendas no filtro atual)
        source_map_df = vendas_map_df if vendas_map_df is not None else vendas_df
        hier_cols = [c for c in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3', 'canal_distribuicao'] if c in (source_map_df.columns if source_map_df is not None else [])]
        if source_map_df is not None and 'material' in source_map_df.columns and hier_cols:
            mat_map = source_map_df[['material'] + hier_cols].dropna(subset=['material']).drop_duplicates('material')
            mat_map['material'] = mat_map['material'].astype(str).str.strip()
            quotes['material'] = quotes.get('material', pd.Series(dtype=str)).astype(str).str.strip()
            quotes = quotes.merge(mat_map, on='material', how='left')

        # Aplicar filtro de canal/hierarquia se possível
        try:
            from .filters import apply_filters as _apply_filters
        except Exception:
            _apply_filters = None
        if _apply_filters is not None:
            # Cliente de cotações pode não estar em coluna 'cliente' — filtraremos por cod_cliente abaixo
            quotes = _apply_filters(quotes, filtro_ano=None, filtro_mes=None, filtro_cliente=None,
                                    filtro_hierarquia=filtro_hierarquia, filtro_canal=filtro_canal,
                                    filtro_top_clientes=None, filtro_dias_sem_compra=None, metrica_type=None)

    # Selecionar cliente
    quotes_client = quotes[quotes.get('cod_cliente', pd.Series(dtype=str)) == cliente_id] if not quotes.empty else pd.DataFrame()

    # Q_value: usar preco_liquido_total quando disponível; fallback por quantidade * unit, senão zero
    if not quotes_client.empty:
        q_val_col = None
        for c in ['preco_liquido_total', 'preco_total', 'valor_total']:
            if c in quotes_client.columns:
                q_val_col = c
                break
        if q_val_col is None and 'preco_liquido_unitario' in quotes_client.columns and 'quantidade' in quotes_client.columns:
            quotes_client['_q_value_proxy'] = pd.to_numeric(quotes_client['preco_liquido_unitario'], errors='coerce').fillna(0) * pd.to_numeric(quotes_client['quantidade'], errors='coerce').fillna(0)
            q_val_col = '_q_value_proxy'
        if q_val_col is None:
            quotes_client['_q_value_proxy'] = pd.to_numeric(quotes_client.get('quantidade', pd.Series(dtype=float)), errors='coerce').fillna(0)
            q_val_col = '_q_value_proxy'
        quotes_client[q_val_col] = pd.to_numeric(quotes_client[q_val_col], errors='coerce').fillna(0)
        # Frequência: nº de cotações distintas (ou linhas, se não houver ID)
        # Frequência: ocorrência de cotações ou frequência ponderada por quantidade
        mode = str(freq_mode or 'occurrences').lower()
        if mode == 'quantity' and 'quantidade' in quotes_client.columns:
            q_freq_series = pd.to_numeric(quotes_client['quantidade'], errors='coerce').fillna(0)
            q_freq_series = quotes_client.assign(_q=q_freq_series).groupby('material')['_q'].sum()
        else:
            if 'cotacao' in quotes_client.columns:
                q_freq_series = quotes_client.groupby('material')['cotacao'].nunique()
            else:
                q_freq_series = quotes_client.groupby('material').size()
        q_val_series = quotes_client.groupby('material')[q_val_col].sum()
        last_quote = None
        if 'data' in quotes_client.columns:
            last_quote = quotes_client.groupby('material')['data'].max()
    else:
        q_val_series = pd.Series(dtype=float)
        q_freq_series = pd.Series(dtype=float)
        last_quote = None

    # Vendas: identificar coluna de valor
    v = vendas_df.copy()
    val_col = _pick_value_col(v)
    if val_col is None:
        # fallback: tenta 'vlr_rol' calculado a partir de quantidade*preço se houver; caso contrário, zero
        v['__valor__'] = 0.0
        val_col = '__valor__'
    v[val_col] = pd.to_numeric(v[val_col], errors='coerce').fillna(0)
    v['cod_cliente'] = v.get('cod_cliente', pd.Series(dtype=str)).astype(str)
    v['material'] = v.get('material', pd.Series(dtype=str)).astype(str)

    # Vendas do cliente e do mercado
    v_cliente = v[v['cod_cliente'] == cliente_id].groupby('material')[val_col].sum()
    v_mercado = v[v['cod_cliente'] != cliente_id].groupby('material')[val_col].sum()

    # Monta base por material
    keys = set(v_cliente.index).union(set(v_mercado.index)).union(set(q_val_series.index)).union(set(q_freq_series.index))

    df = pd.DataFrame({'material': list(keys)}).set_index('material')
    df['v_cliente'] = df.index.map(v_cliente.to_dict()).fillna(0.0)
    df['v_mercado'] = df.index.map(v_mercado.to_dict()).fillna(0.0)
    df['q_valor'] = df.index.map(q_val_series.to_dict()).fillna(0.0)
    df['q_freq'] = df.index.map(q_freq_series.to_dict()).fillna(0.0)

    # Produto/descrição (puxa da primeira fonte disponível; aceita sinônimos)
    def _build_prod_map(source: pd.DataFrame) -> Dict[str, str]:
        if source is None or source.empty:
            return {}
        if 'material' not in source.columns:
            return {}
        prod_cols = [c for c in ['produto', 'descricao', 'descricao_produto', 'nome_produto', 'ds_produto', 'produto_desc', 'material_desc'] if c in source.columns]
        if not prod_cols:
            return {}
        col = prod_cols[0]
        s = source.dropna(subset=['material']).drop_duplicates('material')[['material', col]].rename(columns={col: 'produto'})
        return dict(zip(s['material'].astype(str), s['produto'].astype(str)))

    prod_map = {}
    # Preferir vendas (melhor padronização), depois produtos cotados, depois cotações
    for src in (vendas_df, produtos_cotados_df, cotacoes_df):
        prod_map.update(_build_prod_map(src))
    df['produto'] = df.index.map(prod_map).fillna('')

    # Última cotação
    if isinstance(last_quote, pd.Series):
        df['ultima_cotacao'] = df.index.map(last_quote.to_dict())
    else:
        df['ultima_cotacao'] = pd.NaT

    # Potenciais por bucket
    # Bucket 1: cotou e não compra
    mask_b1 = (df['q_valor'] > 0) & (df['v_cliente'] <= 0)
    # rank de frequência apenas entre itens cotados
    freq_rank = df.loc[mask_b1, 'q_freq'].rank(pct=True, method='average') if mask_b1.any() else pd.Series(dtype=float)
    w = float(np.clip(peso_freq_cotacao, 0.0, 1.0))
    multiplier = (1 - w) + w * freq_rank
    pot1 = pd.Series(0.0, index=df.index)
    pot1.loc[mask_b1] = df.loc[mask_b1, 'q_valor'] * multiplier

    # Bucket 2: mercado forte, cliente fora
    mask_b2 = (df['v_mercado'] > 0) & (df['v_cliente'] <= 0)
    pot2 = pd.Series(0.0, index=df.index)
    pot2.loc[mask_b2] = df.loc[mask_b2, 'v_mercado']

    # Bucket 3: baixa penetração
    mask_b3 = (df['v_cliente'] > 0) & (df['v_mercado'] > df['v_cliente'])
    pot3 = pd.Series(0.0, index=df.index)
    pot3.loc[mask_b3] = (df.loc[mask_b3, 'v_mercado'] - df.loc[mask_b3, 'v_cliente'])

    # Escolher motivo principal
    df['pot1'] = pot1
    df['pot2'] = pot2
    df['pot3'] = pot3
    df['oportunidade_brl'] = df[['pot1', 'pot2', 'pot3']].max(axis=1)

    def _motivo(row: pd.Series) -> str:
        if row['oportunidade_brl'] <= 0:
            return ''
        if row['oportunidade_brl'] == row['pot1']:
            return 'Cotou e não compra'
        if row['oportunidade_brl'] == row['pot2']:
            return 'Mercado forte, cliente fora'
        return 'Baixa penetração'

    df['motivo'] = df.apply(_motivo, axis=1)

    # Ordenação por oportunidade desc
    df = df.reset_index()
    df = df[df['oportunidade_brl'] > 0].sort_values(by='oportunidade_brl', ascending=False)

    # Formatar última cotação como string para exibição, mantendo original em outra coluna se quiser
    if 'ultima_cotacao' in df.columns:
        try:
            df['ultima_cotacao'] = pd.to_datetime(df['ultima_cotacao'], errors='coerce').dt.date.astype(str)
        except Exception:
            df['ultima_cotacao'] = df['ultima_cotacao'].astype(str)

    return df[['material', 'produto', 'oportunidade_brl', 'motivo', 'v_cliente', 'v_mercado', 'q_valor', 'q_freq', 'ultima_cotacao']]
