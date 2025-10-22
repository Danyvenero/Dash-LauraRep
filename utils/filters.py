"""
Funções utilitárias de filtros e hierarquia reutilizadas em múltiplos módulos.

- apply_filters: aplica filtros globais a um DataFrame (vendas/cotações), tolerante a parâmetros extras
- determine_hierarchy_level: decide a coluna de produto/hierarquia a utilizar

Ponto único de verdade para a aplicação.
"""

from typing import Iterable, Optional, Tuple
import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    filtro_ano: Optional[Iterable] = None,
    filtro_mes: Optional[Iterable] = None,
    filtro_cliente: Optional[Iterable] = None,
    filtro_hierarquia: Optional[Iterable] = None,
    filtro_canal: Optional[Iterable] = None,
    filtro_top_clientes: Optional[int] = None,
    filtro_dias_sem_compra: Optional[Iterable] = None,
    metrica_type: Optional[str] = None,
) -> pd.DataFrame:
    """Aplica filtros globais de forma resiliente sobre o DataFrame informado.

    Suporta:
    - Filtro de ano/mes via colunas 'ano'/'mes' ou derivadas de 'data'
    - Filtro de cliente via coluna 'cliente' (aceita lista)
    - Filtro de canal via colunas 'canal' ou 'canal_distribuicao'
    - Filtro de hierarquia comparando valores em hier_produto_1..3 quando disponíveis
    - Top N clientes por 'vlr_rol' agregado

    Parâmetros extras (metrica_type, filtro_dias_sem_compra) são aceitos para compatibilidade
    ainda que não aplicados aqui (sem coluna base universal).
    """
    if df is None or df.empty:
        return df

    out = df.copy()

    # Ano
    try:
        if filtro_ano and isinstance(filtro_ano, (list, tuple)) and len(filtro_ano) == 2:
            a_min, a_max = filtro_ano
            if 'ano' in out.columns:
                out = out[(out['ano'] >= a_min) & (out['ano'] <= a_max)]
            elif 'data' in out.columns:
                anos = pd.to_datetime(out['data'], errors='coerce').dt.year
                out = out[(anos >= a_min) & (anos <= a_max)]
    except Exception:
        pass

    # Mês
    try:
        if filtro_mes and isinstance(filtro_mes, (list, tuple)) and len(filtro_mes) == 2:
            m_min, m_max = filtro_mes
            if 'mes' in out.columns:
                out = out[(out['mes'] >= m_min) & (out['mes'] <= m_max)]
            elif 'data' in out.columns:
                meses = pd.to_datetime(out['data'], errors='coerce').dt.month
                out = out[(meses >= m_min) & (meses <= m_max)]
    except Exception:
        pass

    # Cliente (aceita lista de códigos/strings). Preferir 'cod_cliente' quando disponível.
    try:
        if filtro_cliente is not None:
            valores = filtro_cliente if isinstance(filtro_cliente, (list, tuple, set)) else [filtro_cliente]
            valores_str = {str(v) for v in valores}
            if 'cod_cliente' in out.columns:
                out['cod_cliente'] = out['cod_cliente'].astype(str)
                out = out[out['cod_cliente'].isin(valores_str)]
            elif 'cliente' in out.columns:
                out = out[out['cliente'].isin(valores)]
    except Exception:
        pass

    # Canal (tenta duas colunas possíveis)
    try:
        if filtro_canal is not None:
            valores = filtro_canal if isinstance(filtro_canal, (list, tuple, set)) else [filtro_canal]
            if 'canal' in out.columns:
                out = out[out['canal'].isin(valores)]
            elif 'canal_distribuicao' in out.columns:
                out = out[out['canal_distribuicao'].isin(valores)]
    except Exception:
        pass

    # Hierarquia (compara valores nas colunas hierárquicas, se existirem)
    try:
        if filtro_hierarquia is not None:
            valores = set(
                filtro_hierarquia if isinstance(filtro_hierarquia, (list, tuple, set)) else [filtro_hierarquia]
            )
            cols_hier = [c for c in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3'] if c in out.columns]
            if cols_hier and len(valores) > 0:
                mask = False
                for c in cols_hier:
                    mask = mask | out[c].astype(str).isin({str(v) for v in valores})
                out = out[mask]
    except Exception:
        pass

    # Top clientes por faturamento (preservando cliente(s) selecionado(s) explicitamente)
    try:
        if filtro_top_clientes and isinstance(filtro_top_clientes, (int, float)) and filtro_top_clientes > 0:
            chave = 'cod_cliente' if 'cod_cliente' in out.columns else ('cliente' if 'cliente' in out.columns else None)
            if chave and 'vlr_rol' in out.columns:
                grp = out.groupby(chave)['vlr_rol'].sum().nlargest(int(filtro_top_clientes)).index
                manter = set(grp)
                # Se houve filtro_cliente, garantir inclusão explícita
                if filtro_cliente is not None:
                    valores = filtro_cliente if isinstance(filtro_cliente, (list, tuple, set)) else [filtro_cliente]
                    if chave == 'cod_cliente':
                        manter |= {str(v) for v in valores}
                    else:
                        manter |= set(valores)
                out = out[out[chave].astype(str).isin({str(v) for v in manter})]
    except Exception:
        pass

    return out


def determine_hierarchy_level(
    df: pd.DataFrame,
    filtro_hierarquia: Optional[Iterable] = None
) -> Tuple[str, str]:
    """Determina o nível/coluna para agregação de produto.

    Regras:
    - Se houver filtro_hierarquia, tenta detectar em qual coluna hierárquica (1/2/3) esses valores aparecem
      e retorna essa coluna como dimensão.
    - Caso contrário, se houver 'hier_produto_1', usa como padrão (atende requisito do usuário).
    - Fallbacks: 'produto', depois 'material', depois a primeira coluna não numérica.

    Retorna: (nome_nivel, coluna)
    """
    if df is None or df.empty:
        # Preferência pelo padrão requisitado
        return ('Hierarquia 1', 'hier_produto_1') if 'hier_produto_1' in (df.columns if df is not None else []) else ('Produto', 'produto')

    # Se filtro explícito de hierarquia veio, escolher a coluna correspondente
    try:
        if filtro_hierarquia is not None:
            valores = set(
                filtro_hierarquia if isinstance(filtro_hierarquia, (list, tuple, set)) else [filtro_hierarquia]
            )
            if len(valores) > 0:
                valores_str = {str(v) for v in valores}
                for col, label in [
                    ('hier_produto_1', 'Hierarquia 1'),
                    ('hier_produto_2', 'Hierarquia 2'),
                    ('hier_produto_3', 'Hierarquia 3'),
                ]:
                    if col in df.columns:
                        col_vals = df[col].astype(str)
                        if col_vals.isin(valores_str).any():
                            return label, col
                # Se não encontrou, ainda assim preferir hier_produto_1 se existir
                if 'hier_produto_1' in df.columns:
                    return 'Hierarquia 1', 'hier_produto_1'
    except Exception:
        pass

    # Padrão: hier_produto_1 quando existir (requisito)
    if 'hier_produto_1' in df.columns:
        # Opcional: garantir que tenha pelo menos algum valor não nulo
        try:
            if df['hier_produto_1'].notna().any():
                return 'Hierarquia 1', 'hier_produto_1'
        except Exception:
            return 'Hierarquia 1', 'hier_produto_1'

    # Fallbacks anteriores
    if 'produto' in df.columns:
        return 'Produto', 'produto'
    if 'material' in df.columns:
        return 'Material', 'material'
    for c in ['descricao_produto', 'descricao', 'produto_nome', 'nome_produto']:
        if c in df.columns:
            return 'Produto', c

    # Fallback final: primeira coluna não numérica
    for c in df.columns:
        try:
            if not pd.api.types.is_numeric_dtype(df[c]):
                return 'Produto', c
        except Exception:
            return 'Produto', c
    return 'Produto', df.columns[0]
