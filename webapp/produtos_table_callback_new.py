"""
Callback específico para tabela de produtos com dash_table funcional
Implementa filtro por material e interação completa
"""

from dash import Input, Output, State, callback, html, dcc, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import traceback
import sys
import os
import re

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
from webapp import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Callback de produtos (novo) sendo carregado")

# Toggle de ajuda do filtro de materiais
@callback(
    Output("material-search-help", "is_open"),
    [Input("material-search-help-toggle", "n_clicks")],
    [State("material-search-help", "is_open")],
    prevent_initial_call=False
)
def toggle_material_search_help(n, is_open):
    if n:
        return not is_open
    return is_open

# Exibir pesos normalizados RFM abaixo dos sliders
@callback(
    Output("rfm-weights-display", "children"),
    [
        Input("rfm-weight-r", "value"),
        Input("rfm-weight-f", "value"),
        Input("rfm-weight-m", "value"),
    ],
    prevent_initial_call=False
)
def display_normalized_rfm_weights(wR_in, wF_in, wM_in):
    try:
        wR = float(wR_in or 0)
        wF = float(wF_in or 0)
        wM = float(wM_in or 0)
        total = wR + wF + wM
        if total <= 0:
            return "Pesos normalizados: R=0%, F=0%, M=0%"
        wR_n = wR / total
        wF_n = wF / total
        wM_n = wM / total
        return f"Pesos normalizados: R={wR_n*100:.0f}%, F={wF_n*100:.0f}%, M={wM_n*100:.0f}%"
    except Exception:
        return "Pesos normalizados: R=40%, F=30%, M=30%"

@callback(
    Output("tabela-analise-produtos-container", "children"),
    [
        Input("filter-material-search", "value"),         # texto digitado (busca server-side)
    Input("filter-top-produtos", "value"),
    Input("table-page-size-produtos", "value"),
        # Filtros globais
        Input("global-filtro-ano", "value"),
        Input("global-filtro-mes", "value"),
        Input("global-filtro-cliente", "value"),
        Input("global-filtro-hierarquia", "value"),
        Input("global-filtro-canal", "value"),
        Input("global-filtro-top-clientes", "value"),
        Input("global-filtro-dias-sem-compra", "value"),
        # Pesos RFM (sliders)
        Input("rfm-weight-r", "value"),
        Input("rfm-weight-f", "value"),
        Input("rfm-weight-m", "value"),
        Input("url", "pathname")
    ],
    prevent_initial_call=False
)
def update_produtos_table_with_filters(search_value, top_produtos, page_size,
                                       filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia,
                                       filtro_canal, filtro_top_clientes, filtro_dias_sem_compra,
                                       wR_in, wF_in, wM_in,
                                       pathname):
    """
    Carrega a tabela de produtos com filtros aplicados usando dash_table
    """
    try:
        logger.debug(f"Produtos callback pathname={pathname}")
        logger.debug(f"Filtros: search='{search_value}', top={top_produtos}, page_size={page_size}")
        logger.info("Callback executado com filtros: top=%s, page_size=%s", top_produtos, page_size)
        
        # Se não está na página de produtos, retorna placeholder (aceita variações de rota)
        allowed_paths = {"/produtos", "/produtos/", "/app/products", "/app/products/", "/app/produtos", "/app/produtos/", "/products", "/products/"}
        if pathname not in allowed_paths:
            logger.debug(f"Ignorando callback fora da página de produtos: {pathname}")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Navegue para a página de produtos para visualizar os dados."
                ], color="info")
            ])
        
        logger.info("Carregando tabela de produtos com filtros")
        
        # Valores padrão para os filtros
        if top_produtos is None or top_produtos <= 0:
            # Carregar TODOS os itens por padrão (sem corte Top N)
            top_produtos = None
        # Validar tamanho de página (fallback 25)
        if page_size is None or page_size <= 0:
            page_size = 25
            
        # Carregar dados
        vendas_df = load_vendas_data()
        cotacoes_df = load_cotacoes_data()
        produtos_cotados_df = load_produtos_cotados_data()
        
        if vendas_df is None or vendas_df.empty:
            logger.warning("Dados de vendas vazios")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Nenhum dado de vendas encontrado. Verifique a configuração do banco de dados."
                ], color="warning")
            ])
        
        # Aplicar filtros globais como nos gráficos (se possível)
        try:
            from webapp import callbacks as _callbacks
            _apply_filters = getattr(_callbacks, 'apply_filters', None)
        except Exception as _e:
            _apply_filters = None
            logger.warning(f"Não foi possível importar apply_filters: {_e}")

        vendas_filtrado = vendas_df
        if _apply_filters is not None:
            # usar métrica faturamento para alinhar com gráficos
            vendas_filtrado = _apply_filters(
                vendas_df, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia,
                filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='faturamento'
            )
        
        # Normalizar pesos (fallback para 40/30/30)
        try:
            wR = float(wR_in or 40.0)
            wF = float(wF_in or 30.0)
            wM = float(wM_in or 30.0)
            total = max(wR + wF + wM, 1e-6)
            wR, wF, wM = wR/total, wF/total, wM/total
        except Exception:
            wR, wF, wM = 0.4, 0.3, 0.3

        # Processar dados de produtos (com base no DataFrame filtrado)
        produtos_data = process_produtos_analytics(
            vendas_filtrado, cotacoes_df, produtos_cotados_df, top_n=None,
            r_weight=wR, f_weight=wF, m_weight=wM
        ).reset_index(drop=True)
        
        fallback_alert = None
        if produtos_data is None or produtos_data.empty:
            logger.warning("Produtos vazios com filtros globais — aplicando fallback sem filtros globais")
            # Fallback: tentar sem filtros globais para não sumir a tabela
            produtos_data = process_produtos_analytics(
                vendas_df, cotacoes_df, produtos_cotados_df, top_n=None,
                r_weight=wR, f_weight=wF, m_weight=wM
            ).reset_index(drop=True)
            if produtos_data is None or produtos_data.empty:
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "Nenhum produto encontrado."
                    ], color="info")
                ])
            else:
                fallback_alert = dbc.Alert([
                    html.I(className="fas fa-filter-circle-xmark me-2"),
                    "Sem resultados para os filtros atuais. Exibindo todos os produtos."
                ], color="warning", className="mb-3")
        
        # Aplicar filtros: por seleção de material (códigos) e/ou por filtro avançado digitado
        filtered_data = produtos_data.copy().reset_index(drop=True)
        # Coerção de tipos para evitar mismatch (int vs str)
        if 'material' in filtered_data.columns:
            filtered_data['material'] = filtered_data['material'].astype(str).str.strip()
        if 'produto' in filtered_data.columns:
            filtered_data['produto'] = filtered_data['produto'].astype(str)

        # Sem filtro por seleção — apenas busca digitada e filtros globais
        filtered_data = filtered_data.reset_index(drop=True)

        # Filtro avançado no texto digitado (mesma sintaxe do dropdown)
        if search_value and isinstance(search_value, str) and len(search_value.strip()) >= 1:
            q_raw = search_value.strip()
            q_norm = re.sub(r'(?<!\S)-\s+', '-', q_raw)  # transforma '- termo' em '-termo'
            sv = q_norm.lower()
            logger.debug(f"Filtro avançado: '{sv}' em material/produto")

            def parse_query(q: str):
                if not q:
                    return {
                        'pos': [], 'neg': [], 'pos_code': [], 'pos_desc': [],
                        'anch_start': [], 'anch_end': [], 'ors': [], 'exact': []
                    }
                # frases exatas
                exact = re.findall(r'"([^"]+)"', q)
                q_wo_exact = re.sub(r'"([^"]+)"', ' ', q)
                q_wo_exact = re.sub(r'(?<!\S)-\s+', '-', q_wo_exact)
                parts = [p for p in re.split(r"\s+", q_wo_exact) if p]

                pos, neg, pos_code, pos_desc, anch_start, anch_end, ors = [], [], [], [], [], [], []
                i = 0
                while i < len(parts):
                    p = parts[i]
                    if p == '-' and i + 1 < len(parts):
                        i += 1
                        term = parts[i]
                        target = neg
                    else:
                        target = neg if p.startswith('-') else None
                        term = p[1:] if p.startswith('-') else p

                    # OR por pipe
                    if '|' in term:
                        group = [s for s in term.split('|') if s]
                        if target is not None:
                            for g in group:
                                neg.append(g)
                        else:
                            ors.append(group)
                        i += 1
                        continue

                    # campo específico
                    if term.startswith('code:'):
                        (target if target is not None else pos_code).append(term[5:])
                    elif term.startswith('desc:'):
                        (target if target is not None else pos_desc).append(term[5:])
                    # âncoras
                    elif term.startswith('^'):
                        (target if target is not None else anch_start).append(term[1:])
                    elif term.endswith('$'):
                        (target if target is not None else anch_end).append(term[:-1])
                    else:
                        (target if target is not None else pos).append(term)
                    i += 1

                return {
                    'pos': pos, 'neg': neg, 'pos_code': pos_code, 'pos_desc': pos_desc,
                    'anch_start': anch_start, 'anch_end': anch_end, 'ors': ors, 'exact': exact
                }

            q = parse_query(sv)

            mat_low = filtered_data['material'].astype(str).str.lower()
            prod_low = filtered_data['produto'].astype(str).str.lower()

            mask = pd.Series([True] * len(filtered_data), index=filtered_data.index)
            # AND positivos genéricos
            for tok in q['pos']:
                mask &= (mat_low.str.contains(tok, na=False) | prod_low.str.contains(tok, na=False))
            # code: e desc:
            for tok in q['pos_code']:
                mask &= mat_low.str.contains(tok, na=False)
            for tok in q['pos_desc']:
                mask &= prod_low.str.contains(tok, na=False)
            # âncoras
            for tok in q['anch_start']:
                mask &= (mat_low.str.startswith(tok) | prod_low.str.startswith(tok))
            for tok in q['anch_end']:
                mask &= (mat_low.str.endswith(tok) | prod_low.str.endswith(tok))
            # frases exatas
            for phrase in q['exact']:
                pl = phrase.lower()
                mask &= (mat_low.str.contains(pl, na=False) | prod_low.str.contains(pl, na=False))
            # OR grupos (todos os grupos devem ser satisfeitos por pelo menos um termo)
            for group in q['ors']:
                group_mask = pd.Series([False] * len(filtered_data), index=filtered_data.index)
                for tok in group:
                    tl = tok.lower()
                    group_mask |= mat_low.str.contains(tl, na=False) | prod_low.str.contains(tl, na=False)
                mask &= group_mask
            # negativos
            for tok in q['neg']:
                tl = tok.lower()
                mask &= ~(mat_low.str.contains(tl, na=False) | prod_low.str.contains(tl, na=False))

            before_count = len(filtered_data)
            filtered_data = filtered_data[mask]
            after_count = len(filtered_data)
            # Fallback: se nada mudou, aplicar contains simples do texto inteiro
            if after_count == before_count:
                simple = sv.strip()
                if simple:
                    mat_low = filtered_data['material'].astype(str).str.lower()
                    prod_low = filtered_data['produto'].astype(str).str.lower()
                    simple_mask = mat_low.str.contains(simple, na=False) | prod_low.str.contains(simple, na=False)
                    # Otimização para busca numérica: prefixo no código
                    if simple.isdigit():
                        simple_mask = simple_mask | filtered_data['material'].astype(str).str.startswith(simple)
                    filtered_data = filtered_data[simple_mask]
            logger.info(f"Filtro avançado aplicado: {len(filtered_data)} produtos restantes")

        if filtered_data.empty:
            hint = f"busca: '{search_value}'" if search_value else "filtros atuais"
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-filter me-2"),
                    f"Nenhum produto encontrado para os {hint}."
                ], color="info")
            ])
        
        # Preparar dados para dash_table
        logger.info(f"Criando dash_table para {len(filtered_data)} produtos")
        
        # Adicionar hierarquia se disponível
        hierarquia_col = None
        if 'hier_produto_1' in filtered_data.columns:
            hierarquia_col = 'hier_produto_1'
        elif 'hierarquia' in filtered_data.columns:
            hierarquia_col = 'hierarquia'
        
        # Aplicar corte Top N APÓS os filtros de seleção/busca (evita esconder matches fora do Top N original)
        if top_produtos and top_produtos > 0:
            filtered_data = filtered_data.head(top_produtos)

        # Preparar DataFrame para exibição
        display_data = filtered_data.copy()

        # Criar colunas de exibição derivadas (percentuais)
        if 'freq_gap' in display_data.columns:
            display_data['freq_gap_pct'] = (display_data['freq_gap'] * 100).round(2)
        if 'recency_gap' in display_data.columns:
            display_data['recency_gap_pct'] = (display_data['recency_gap'] * 100).round(2)
        if 'valor_gap' in display_data.columns:
            display_data['valor_gap_pct'] = (display_data['valor_gap'] * 100).round(2)

        # Renomear colunas para exibição
        column_mapping = {
            'material': 'Material',
            'produto': 'Produto',
            # Vendas
            'faturamento_total': 'Faturamento Total',
            'valor_medio': 'Valor Médio',
            'quantidade_total': 'Quantidade',
            'recorrencia_mensal': 'Recorrência/Mês',
            'recency_days': 'Recência (Venda) Dias',
            'prioridade_score': 'Prioridade (Venda)',
            # Cotações
            'valor_cotado_total': 'Valor Cotado Total',
            'qtd_cotada_total': 'Qtd Cotada Total',
            'q_recorrencia_mensal': 'Recorrência Cotação/Mês',
            'q_recency_days': 'Recência (Cotação) Dias',
            'q_prioridade_score': 'Prioridade (Cotação)',
            # Frequências médias em dias
            'freq_media_cotacao_dias': 'Freq. Cotação (Dias)',
            'freq_media_compra_dias': 'Freq. Compra (Dias)',
            'obs_freq_compra': 'Obs. Freq. Compra',
            # Conversões e Gaps
            'conversao_valor_percent': 'Conversão Valor (%)',
            'freq_gap_pct': 'Gap Freq (%)',
            'recency_gap_pct': 'Gap Recência (%)',
            'valor_gap_pct': 'Gap Valor (%)',
            'meses_cotados_sem_compra': 'Meses Cotados Sem Compra',
            'pct_qtd_cotada_vs_comprada': 'Qtd Cotada vs Comprada (%)',
            # Oportunidade
            'oportunidade_score': 'Oportunidade',
            'status_oportunidade': 'Status'
        }
        
        if hierarquia_col:
            column_mapping[hierarquia_col] = 'Hierarquia'
        
        # Selecionar e renomear colunas
        # Ordenar um conjunto enxuto, mas completo, priorizando oportunidade e info-chave
        preferred_order = [
            'material', 'produto',
            'oportunidade_score', 'status_oportunidade',
            'prioridade_score', 'q_prioridade_score',
            'recorrencia_mensal', 'q_recorrencia_mensal',
            'recency_days', 'q_recency_days',
            'freq_media_compra_dias', 'freq_media_cotacao_dias',
            'obs_freq_compra',
            'faturamento_total', 'valor_cotado_total',
            'quantidade_total', 'qtd_cotada_total',
            'conversao_valor_percent',
            'freq_gap_pct', 'recency_gap_pct', 'valor_gap_pct',
            'meses_cotados_sem_compra', 'pct_qtd_cotada_vs_comprada'
        ]
        columns_to_show = [col for col in preferred_order if col in display_data.columns]
        # Fallback: se algo faltar, inclui demais disponíveis que tenham mapping
        columns_to_show += [col for col in column_mapping.keys() if col in display_data.columns and col not in columns_to_show]
        display_data = display_data[columns_to_show].rename(columns=column_mapping)
        
        # Criar colunas para dash_table
        table_columns = []
        for col in display_data.columns:
            if col in ['Faturamento Total', 'Valor Médio']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                })
            elif col in ['Quantidade', 'Qtd Cotada Total', 'Meses Cotados Sem Compra', 'Recência (Venda) Dias', 'Recência (Cotação) Dias', 'Freq. Compra (Dias)', 'Freq. Cotação (Dias)']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.0f"}
                })
            elif col in ['Recorrência', 'Recorrência/Mês', 'Recorrência Cotação/Mês']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                })
            elif col in ['Prioridade (Venda)', 'Prioridade (Cotação)', 'Oportunidade']:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                })
            elif col.endswith('(%)'):
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.2f"}
                })
            else:
                table_columns.append({
                    "name": col,
                    "id": col,
                    "type": "text"
                })
        
        # Criar título dinâmico baseado nos filtros
        total_produtos = len(display_data)
        # Sempre evitar mencionar 'Top N' no título
        title_text = f"Produtos (ordenados por RFV Cotação, RFV Vendas, Freq. Cotação) — {total_produtos:,} itens"
        # Sem seleção de materiais — apenas busca
        
        # Criar mensagem de sucesso
        success_message = html.Div([
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Dados carregados com sucesso! Tabela gerada diretamente do banco de dados. ({total_produtos:,} registros processados)"
            ], color="success", className="mb-3")
        ])
        
        # Criar dash_table
        data_table = dash_table.DataTable(
            id='produtos-table',
            columns=table_columns,
            data=display_data.to_dict('records'),
            page_size=page_size,
            sort_action='native',
            filter_action='native',
            filter_options={"case": "insensitive"},
            row_selectable='multi',  # Permite seleção múltipla
            selected_rows=[],  # Inicialmente nenhuma linha selecionada
            style_table={
                'overflowX': 'auto',
                'minWidth': '100%'
            },
            style_header={
                'backgroundColor': '#0d6efd',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': ['Faturamento Total', 'Valor Médio']},
                    'textAlign': 'right',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': ['Quantidade', 'Recorrência', 'Recorrência/Mês', 'Prioridade']},
                    'textAlign': 'right'
                }
            ],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Produto'},
                    'width': '30%',
                    'maxWidth': '300px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                {
                    'if': {'column_id': 'Material'},
                    'width': '120px',
                    'fontFamily': 'monospace'
                }
            ]
        )
        
        return html.Div([
            success_message,
            (fallback_alert if fallback_alert else html.Span()),
            html.H6([
                html.I(className="fas fa-table me-2"),
                title_text
            ], className="mb-3"),
            data_table
        ])
        
    except Exception as e:
        logger.error(f"Erro geral ao carregar tabela de produtos: {e}")
        traceback.print_exc()
        
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                html.Strong("Erro de Sistema: "),
                f"Falha ao carregar a tabela. {str(e)}"
            ], color="danger")
        ])

def process_produtos_analytics(vendas_df, cotacoes_df, produtos_cotados_df, top_n=20,
                               r_weight=0.4, f_weight=0.3, m_weight=0.3):
    """
    Processa dados para análise de produtos
    """
    try:
        print(f"🔄 Processando analytics de produtos (top {top_n})...")
        
        if vendas_df is None or vendas_df.empty:
            logger.warning("DataFrame de vendas vazio")
            return pd.DataFrame()
        
        print(f"   📊 Dados de vendas: {len(vendas_df)} registros")
        
        # Verificar colunas obrigatórias
        required_cols = ['material', 'produto', 'vlr_rol']
        missing_cols = [col for col in required_cols if col not in vendas_df.columns]
        
        if missing_cols:
            logger.error(f"Colunas obrigatórias faltando: {missing_cols}")
            return pd.DataFrame()
        
        # Determinar coluna de quantidade de forma robusta (vendas)
        qty_candidates = [
            'qtd_vendida', 'qtd_rol', 'quantidade', 'qtde', 'qty',
            'qtd', 'qtd_venda', 'quantidade_vendida', 'qtd_itens', 'qtd_item'
        ]
        qty_col = next((c for c in qty_candidates if c in vendas_df.columns), None)

        # Garantir tipos numéricos para agregação
        vendas_df['vlr_rol'] = pd.to_numeric(vendas_df['vlr_rol'], errors='coerce').fillna(0)
        if qty_col:
            vendas_df[qty_col] = pd.to_numeric(vendas_df[qty_col], errors='coerce').fillna(0)

        # Calcular número de meses distintos no período filtrado (com base em data_faturamento se existir)
        month_col = None
        for c in ['data_faturamento', 'data']:
            if c in vendas_df.columns:
                month_col = c
                break

        distinct_months = 1.0
        if month_col is not None:
            # normalizar para período mensal
            try:
                meses = pd.to_datetime(vendas_df[month_col], errors='coerce').dt.to_period('M').dropna().nunique()
                distinct_months = float(meses) if meses and meses > 0 else 1.0
            except Exception:
                distinct_months = 1.0

        # Agrupar por material e produto para calcular métricas (named aggregation)
        if qty_col:
            produtos_stats = (
                vendas_df.groupby(['material', 'produto'], as_index=False)
                .agg(
                    faturamento_total=('vlr_rol', 'sum'),
                    valor_medio=('vlr_rol', 'mean'),
                    recorrencia_compra=('vlr_rol', 'count'),
                    quantidade_total=(qty_col, 'sum')
                )
            )
        else:
            # Fallback: quando não há coluna de quantidade, usar contagem como quantidade
            produtos_stats = (
                vendas_df.groupby(['material', 'produto'], as_index=False)
                .agg(
                    faturamento_total=('vlr_rol', 'sum'),
                    valor_medio=('vlr_rol', 'mean'),
                    recorrencia_compra=('vlr_rol', 'count'),
                    quantidade_total=('vlr_rol', 'count')
                )
            )
        
        # Base de meses para médias mensais
        v_month_index = None
        if month_col is not None and month_col in vendas_df.columns:
            _dates_v = pd.to_datetime(vendas_df[month_col], errors='coerce')
            if _dates_v.notna().any():
                v_min = _dates_v.min().to_period('M')
                v_max = _dates_v.max().to_period('M')
                try:
                    v_month_index = pd.period_range(v_min, v_max, freq='M')
                except Exception:
                    v_month_index = None

        def monthly_mean_count(df_src, date_col_src, base_months):
            if df_src is None or df_src.empty or date_col_src is None or date_col_src not in df_src.columns:
                return pd.DataFrame({'material': [], 'monthly_mean': []})
            tmp = df_src[['material', date_col_src]].copy()
            tmp[date_col_src] = pd.to_datetime(tmp[date_col_src], errors='coerce')
            tmp = tmp.dropna(subset=[date_col_src])
            if tmp.empty:
                return pd.DataFrame({'material': [], 'monthly_mean': []})
            tmp['month'] = tmp[date_col_src].dt.to_period('M')
            # Se base_months existir, filtra o período e reindexa para incluir zeros
            if base_months is not None and len(base_months) > 0:
                tmp = tmp[(tmp['month'] >= base_months.min()) & (tmp['month'] <= base_months.max())]
            counts = tmp.groupby(['material', 'month']).size().rename('count')
            if counts.empty:
                return pd.DataFrame({'material': [], 'monthly_mean': []})
            wide = counts.unstack(fill_value=0)
            if base_months is not None and len(base_months) > 0:
                # reindexar colunas para cobrir todos os meses do período
                wide = wide.reindex(columns=base_months, fill_value=0)
                denom = float(len(base_months)) if len(base_months) > 0 else 1.0
            else:
                denom = float(wide.shape[1]) if wide.shape[1] > 0 else 1.0
            monthly_mean = wide.sum(axis=1) / denom
            return monthly_mean.reset_index().rename(columns={0: 'monthly_mean'})

        # Recorrência mensal de compras (média de ocorrências por mês por material)
        # Usa a coluna de data de vendas detectada em 'month_col'
        v_month_mean = monthly_mean_count(vendas_df, month_col, v_month_index)
        if not v_month_mean.empty:
            produtos_stats = produtos_stats.drop(columns=['recorrencia_mensal'], errors='ignore')
            produtos_stats = produtos_stats.merge(
                v_month_mean.rename(columns={'monthly_mean': 'recorrencia_mensal'}),
                on='material', how='left'
            )
        else:
            produtos_stats['recorrencia_mensal'] = 0.0

        # RECENCY: dias desde a última venda (menor é melhor)
        recency_days = None
        date_col = None
        for c in ['data_faturamento', 'data']:
            if c in vendas_df.columns:
                date_col = c
                break
        if date_col is not None:
            df_dates = vendas_df[['material', 'produto', date_col]].copy()
            df_dates[date_col] = pd.to_datetime(df_dates[date_col], errors='coerce')
            ref_date = df_dates[date_col].max()
            last_dates = df_dates.groupby(['material', 'produto'], as_index=False)[date_col].max()
            last_dates['recency_days'] = (ref_date - last_dates[date_col]).dt.days
            produtos_stats = produtos_stats.merge(last_dates[['material', 'produto', 'recency_days']],
                                                 on=['material', 'produto'], how='left')
        else:
            produtos_stats['recency_days'] = None

        # Normalização por quantis (robusta a outliers) para [0,1]
        def quantile_norm(series, invert=False):
            s = series.astype(float)
            if not s.notna().any():
                return pd.Series(0.5, index=s.index)
            # usar ranks normalizados (empíricos)
            ranks = s.rank(method='average', pct=True)
            norm = ranks
            return (1 - norm) if invert else norm

        r_norm = quantile_norm(produtos_stats['recency_days'].fillna(produtos_stats['recency_days'].max() or 0), invert=True)
        f_norm = quantile_norm(produtos_stats['recorrencia_mensal'].fillna(0))
        m_norm = quantile_norm(produtos_stats['faturamento_total'].fillna(0))

        # Guardar normalizações de vendas para cálculo de gaps
        produtos_stats['_r_norm_v'] = r_norm
        produtos_stats['_f_norm_v'] = f_norm
        produtos_stats['_m_norm_v'] = m_norm

        # Pesos RFM vindos do layout (já normalizados)
        produtos_stats['prioridade_score'] = ((r_weight * r_norm) + (f_weight * f_norm) + (m_weight * m_norm)) * 100.0

        # ======================
        # Cotações (Q-RFV)
        # ======================
        quotes_df = None
        if produtos_cotados_df is not None and not produtos_cotados_df.empty:
            quotes_df = produtos_cotados_df.copy()
        elif cotacoes_df is not None and not cotacoes_df.empty:
            quotes_df = cotacoes_df.copy()

        q_stats = None
        if quotes_df is not None and not quotes_df.empty:
            # Mapear colunas principais
            if 'material' not in quotes_df.columns:
                for alt in ['codigo', 'cod_material', 'cd_material', 'produto_codigo']:
                    if alt in quotes_df.columns:
                        quotes_df = quotes_df.rename(columns={alt: 'material'})
                        break
            if 'produto' not in quotes_df.columns:
                for alt in ['descricao', 'ds_produto', 'produto_desc', 'nome_produto']:
                    if alt in quotes_df.columns:
                        quotes_df = quotes_df.rename(columns={alt: 'produto'})
                        break
            if 'produto' not in quotes_df.columns:
                quotes_df['produto'] = ''

            # Valor e quantidade em cotações
            val_candidates = ['valor_total', 'vlr_total', 'valor', 'vlr_cotado', 'vlr_rol']
            qval_col = next((c for c in val_candidates if c in quotes_df.columns), None)
            qqty_candidates = ['qtd_cotada', 'quantidade_cotada', 'qtd', 'quantidade', 'qtde', 'qty']
            qqty_col = next((c for c in qqty_candidates if c in quotes_df.columns), None)

            if qval_col is None:
                # se não houver valor em cotações, usar contagem como proxy
                quotes_df['_proxy_val'] = 1.0
                qval_col = '_proxy_val'
            quotes_df[qval_col] = pd.to_numeric(quotes_df[qval_col], errors='coerce').fillna(0)
            if qqty_col:
                quotes_df[qqty_col] = pd.to_numeric(quotes_df[qqty_col], errors='coerce').fillna(0)

            # Coluna de data
            qdate_col = None
            for c in ['data_cotacao', 'data_emissao', 'data']:
                if c in quotes_df.columns:
                    qdate_col = c
                    break

            # Meses distintos de cotações e base mensal alinhada com vendas quando possível
            q_month_index = None
            if qdate_col is not None:
                q_dates_all = pd.to_datetime(quotes_df[qdate_col], errors='coerce')
                if q_dates_all.notna().any():
                    q_min = q_dates_all.min().to_period('M')
                    q_max = q_dates_all.max().to_period('M')
                    try:
                        q_month_index = pd.period_range(q_min, q_max, freq='M')
                    except Exception:
                        q_month_index = None
            # Base para cotações: usar meses de vendas quando disponível para comparação; senão usar meses das cotações
            base_months_quotes = v_month_index if (v_month_index is not None and len(v_month_index) > 0) else q_month_index
            q_months_len = len(base_months_quotes) if (base_months_quotes is not None and len(base_months_quotes) > 0) else 1

            # Agregações por material/produto
            agg_dict = {
                'valor_cotado_total': (qval_col, 'sum'),
                'q_recorrencia_cotacao': (qval_col, 'count')
            }
            if qqty_col:
                agg_dict['qtd_cotada_total'] = (qqty_col, 'sum')
            else:
                agg_dict['qtd_cotada_total'] = (qval_col, 'count')  # proxy se faltar quantidade

            # Importante: agrupar por material (não depender da descrição exata para o merge)
            q_stats = (
                quotes_df.groupby(['material'], as_index=False)
                .agg(**agg_dict)
            )

            # Recorrência mensal de cotações (média por mês por material)
            q_month_mean = monthly_mean_count(quotes_df, qdate_col, base_months_quotes)
            if not q_month_mean.empty:
                q_stats = q_stats.merge(
                    q_month_mean.rename(columns={'monthly_mean': 'q_recorrencia_mensal'}),
                    on='material', how='left'
                )
            else:
                q_stats['q_recorrencia_mensal'] = 0.0

            # Recência de cotações (dias desde última cotação)
            if qdate_col is not None:
                q_dates = quotes_df[['material', qdate_col]].copy()
                q_dates[qdate_col] = pd.to_datetime(q_dates[qdate_col], errors='coerce')
                q_ref = q_dates[qdate_col].max()
                q_last = q_dates.groupby(['material'], as_index=False)[qdate_col].max()
                q_last['q_recency_days'] = (q_ref - q_last[qdate_col]).dt.days
                q_stats = q_stats.merge(q_last[['material', 'q_recency_days']], on=['material'], how='left')
            else:
                q_stats['q_recency_days'] = None

            # Normalização Q-RFV
            q_r_norm = quantile_norm(q_stats['q_recency_days'].fillna(q_stats['q_recency_days'].max() or 0), invert=True)
            q_f_norm = quantile_norm(q_stats['q_recorrencia_mensal'].fillna(0))
            q_m_norm = quantile_norm(q_stats['valor_cotado_total'].fillna(0))
            q_stats['_r_norm_q'] = q_r_norm
            q_stats['_f_norm_q'] = q_f_norm
            q_stats['_m_norm_q'] = q_m_norm
            q_stats['q_prioridade_score'] = ((r_weight * q_r_norm) + (f_weight * q_f_norm) + (m_weight * q_m_norm)) * 100.0

            # Merge com vendas usando somente 'material' (evita mismatch por descrições diferentes)
            produtos_stats = produtos_stats.merge(q_stats, on=['material'], how='left')
        else:
            # Se não há cotações, criar colunas vazias
            for col in ['valor_cotado_total', 'q_recorrencia_cotacao', 'q_recorrencia_mensal', 'q_recency_days', 'qtd_cotada_total', 'q_prioridade_score', '_r_norm_q', '_f_norm_q', '_m_norm_q']:
                produtos_stats[col] = 0.0

        # ======================
        # Gaps, conversões, oportunidade e indicadores solicitados
        # ======================
        # Normalizados de vendas (já presentes como colunas ocultas)
        v_r = produtos_stats.get('_r_norm_v', pd.Series(0, index=produtos_stats.index))
        v_f = produtos_stats.get('_f_norm_v', pd.Series(0, index=produtos_stats.index))
        v_m = produtos_stats.get('_m_norm_v', pd.Series(0, index=produtos_stats.index))
        # Normalizados de cotações
        q_r = produtos_stats.get('_r_norm_q', pd.Series(0, index=produtos_stats.index))
        q_f = produtos_stats.get('_f_norm_q', pd.Series(0, index=produtos_stats.index))
        q_m = produtos_stats.get('_m_norm_q', pd.Series(0, index=produtos_stats.index))

        # Gaps (0..1)
        produtos_stats['freq_gap'] = (q_f - v_f).clip(lower=0)
        produtos_stats['recency_gap'] = (q_r - v_r).clip(lower=0)
        produtos_stats['valor_gap'] = (q_m - v_m).clip(lower=0)

        # Conversão por valor (0..100%)
        denom_val = produtos_stats['valor_cotado_total'].replace(0, pd.NA)
        conv_val = (produtos_stats['faturamento_total'] / denom_val).fillna(0)
        produtos_stats['conversao_valor_percent'] = (conv_val.clip(lower=0, upper=1.0) * 100).round(2)

        # Meses com venda e com cotação (aproximação via recorrência mensal * meses distintos)
        meses_v = (produtos_stats['recorrencia_mensal'] * distinct_months).round().astype('Int64') if 'recorrencia_mensal' in produtos_stats.columns else 0
        meses_q = (produtos_stats.get('q_recorrencia_mensal', 0) * (q_months_len if 'q_months_len' in locals() else 1.0)).round().astype('Int64')
        try:
            produtos_stats['meses_cotados_sem_compra'] = (meses_q - meses_v).clip(lower=0)
        except Exception:
            produtos_stats['meses_cotados_sem_compra'] = 0

        # ======================
        # Frequência média em dias (cotação e compra)
        # ======================
        def avg_interval_days(df, date_col_name):
            if df is None or df.empty or date_col_name is None or date_col_name not in df.columns:
                return pd.DataFrame({'material': [], 'avg_interval_days': []})
            tmp = df[['material', date_col_name]].copy()
            tmp[date_col_name] = pd.to_datetime(tmp[date_col_name], errors='coerce')
            tmp = tmp.dropna(subset=[date_col_name])
            if tmp.empty:
                return pd.DataFrame({'material': [], 'avg_interval_days': []})
            tmp = tmp.sort_values([ 'material', date_col_name ])
            # calcular diffs por material
            def _calc(group):
                dates = group[date_col_name].dropna().sort_values().unique()
                if len(dates) < 2:
                    return pd.Series({'avg_interval_days': None})
                diffs = pd.Series(dates[1:]) - pd.Series(dates[:-1])
                return pd.Series({'avg_interval_days': diffs.dt.days.mean()})
            res = tmp.groupby('material').apply(_calc).reset_index()
            return res

        # Compra: usar date_col detectada acima
        compra_freq = avg_interval_days(vendas_df, date_col)
        if not compra_freq.empty:
            produtos_stats = produtos_stats.merge(
                compra_freq.rename(columns={'avg_interval_days': 'freq_media_compra_dias'}),
                on='material', how='left'
            )
        else:
            produtos_stats['freq_media_compra_dias'] = None

        # Fallback pedido: se o material foi comprado apenas uma vez (ou não temos intervalo),
        # preencher com dias desde a última compra até hoje
        if date_col is not None and date_col in vendas_df.columns:
            _tmp_last = vendas_df[['material', date_col]].copy()
            _tmp_last[date_col] = pd.to_datetime(_tmp_last[date_col], errors='coerce')
            _tmp_last = _tmp_last.dropna(subset=[date_col])
            if not _tmp_last.empty:
                _last = _tmp_last.groupby('material', as_index=False)[date_col].max()
                _today = pd.Timestamp.today().normalize()
                _last['days_since_last_purchase'] = (_today - _last[date_col]).dt.days
                produtos_stats = produtos_stats.merge(_last[['material', 'days_since_last_purchase']], on='material', how='left')
                if 'freq_media_compra_dias' not in produtos_stats.columns:
                    produtos_stats['freq_media_compra_dias'] = None
                # Flag "estimado" quando preenchermos com dias desde última compra
                produtos_stats['freq_compra_estimado'] = produtos_stats['freq_media_compra_dias'].isna() & produtos_stats['days_since_last_purchase'].notna()
                produtos_stats['freq_media_compra_dias'] = produtos_stats['freq_media_compra_dias'].fillna(produtos_stats['days_since_last_purchase'])
                # Coluna textual amigável para indicar
                produtos_stats['obs_freq_compra'] = produtos_stats['freq_compra_estimado'].map(lambda x: 'Estimado' if bool(x) else '')
                produtos_stats = produtos_stats.drop(columns=['days_since_last_purchase'])

        # Cotação: usar qdate_col detectada
        cotacao_freq = avg_interval_days(quotes_df, qdate_col) if quotes_df is not None else pd.DataFrame({'material': [], 'avg_interval_days': []})
        if not cotacao_freq.empty:
            produtos_stats = produtos_stats.merge(
                cotacao_freq.rename(columns={'avg_interval_days': 'freq_media_cotacao_dias'}),
                on='material', how='left'
            )
        else:
            produtos_stats['freq_media_cotacao_dias'] = None

        # Indicador solicitado: relação % entre quantidade cotada e comprada (0..100)
        denom_qty = produtos_stats['quantidade_total'].replace(0, pd.NA)
        qtd_ratio = (produtos_stats.get('qtd_cotada_total', 0) / denom_qty).fillna(0)
        produtos_stats['pct_qtd_cotada_vs_comprada'] = (qtd_ratio.clip(lower=0) * 100).clip(upper=100).round(2)

        # Score de oportunidade (0..100)
        alpha, beta, gamma = f_weight, r_weight, m_weight  # pesos coerentes com semântica dos gaps
        o_base = (alpha * produtos_stats['freq_gap'] + beta * produtos_stats['recency_gap'] + gamma * produtos_stats['valor_gap'])
        # Penalidades e boost leves
        penalty_recent_sales = (v_r * 0.2)  # vendas muito recentes reduzem oportunidade
        penalty_high_conv = ((conv_val.clip(0, 1.5) - 0.6).clip(lower=0) / 0.4).clip(upper=1.0) * 0.4
        boost_quote_priority = (produtos_stats.get('q_prioridade_score', 0) / 100.0) * 0.15
        o_final = (o_base * (1 - penalty_recent_sales) * (1 - penalty_high_conv)) * (1 + boost_quote_priority)
        produtos_stats['oportunidade_score'] = (o_final.clip(lower=0, upper=1.5).clip(upper=1.0) * 100).round(2)
        # Status
        def status_from_o(o):
            if pd.isna(o):
                return 'OK'
            if o >= 70:
                return 'Recomendar'
            if o >= 40:
                return 'Observar'
            return 'OK'
        produtos_stats['status_oportunidade'] = produtos_stats['oportunidade_score'].apply(status_from_o)

        # Arredondar colunas numéricas para 2 casas
        for col in ['faturamento_total', 'valor_medio', 'quantidade_total', 'recorrencia_mensal', 'prioridade_score']:
            if col in produtos_stats.columns:
                produtos_stats[col] = produtos_stats[col].round(2)
        # Converter com segurança para numérico antes de arredondar
        for col in ['freq_media_compra_dias', 'freq_media_cotacao_dias']:
            if col in produtos_stats.columns:
                produtos_stats[col] = pd.to_numeric(produtos_stats[col], errors='coerce')
        # Arredondamentos específicos
        for col in ['q_prioridade_score', 'oportunidade_score', 'conversao_valor_percent', 'pct_qtd_cotada_vs_comprada', 'freq_media_compra_dias', 'freq_media_cotacao_dias']:
            if col in produtos_stats.columns:
                # Frequências em dias arredondadas para inteiro, demais com 2 casas
                if col in ['freq_media_compra_dias', 'freq_media_cotacao_dias']:
                    produtos_stats[col] = produtos_stats[col].round(0)
                else:
                    produtos_stats[col] = produtos_stats[col].round(2)
        
        # Adicionar hierarquia se disponível
        if 'hier_produto_1' in vendas_df.columns:
            hierarquia_map = vendas_df[['material', 'hier_produto_1']].drop_duplicates()
            produtos_stats = produtos_stats.merge(hierarquia_map, on='material', how='left')
        
        # Ordenação solicitada: RFV de cotação (q_prioridade_score), RFV de vendas (prioridade_score),
        # e depois Frequência Média de Cotação por mês (q_recorrencia_mensal). Como desempate adicional,
        # mantemos faturamento_total.
        sort_cols = []
        asc = []
        if 'q_prioridade_score' in produtos_stats.columns:
            sort_cols.append('q_prioridade_score'); asc.append(False)
        if 'prioridade_score' in produtos_stats.columns:
            sort_cols.append('prioridade_score'); asc.append(False)
        if 'q_recorrencia_mensal' in produtos_stats.columns:
            sort_cols.append('q_recorrencia_mensal'); asc.append(False)
        if 'faturamento_total' in produtos_stats.columns:
            sort_cols.append('faturamento_total'); asc.append(False)
        if not sort_cols:
            sort_cols = ['faturamento_total']; asc = [False]
        produtos_stats = produtos_stats.sort_values(sort_cols, ascending=asc)
        # Garantir pelo menos 200 itens por padrão se top_n não especificado
        if isinstance(top_n, int) and top_n > 0:
            produtos_stats = produtos_stats.head(top_n)

        print(f"   ✅ Analytics processado: {len(produtos_stats)} produtos")

        return produtos_stats

    except Exception as e:
        logger.error(f"Erro ao processar analytics de produtos: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# Callback para limpar filtros da tabela (ajustado para limpar o campo de busca)
@callback(
    [Output("filter-material-search", "value"),
     Output("filter-top-produtos", "value"),
     Output("table-page-size-produtos", "value")],
    [Input("btn-clear-filters-produtos", "n_clicks")],
    prevent_initial_call=True
)
def clear_table_filters(n_clicks):
    """
    Limpa todos os filtros da tabela de produtos
    """
    if n_clicks:
        print("🗑️ Limpando filtros da tabela de produtos...")
        # Top vazio = todos; page size volta para 25
        return "", None, 25
    return no_update, no_update, no_update

# Callback para selecionar/desmarcar todas as linhas
@callback(
    Output("produtos-table", "selected_rows"),
    [Input("btn-select-all-produtos", "n_clicks"),
     Input("btn-deselect-all-produtos", "n_clicks")],
    [State("produtos-table", "data")],
    prevent_initial_call=True
)
def select_deselect_all_rows(select_clicks, deselect_clicks, table_data):
    """
    Seleciona ou desmarca todas as linhas da tabela
    """
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-select-all-produtos" and select_clicks:
        print("✅ Selecionando todas as linhas da tabela")
        return list(range(len(table_data))) if table_data else []
    elif button_id == "btn-deselect-all-produtos" and deselect_clicks:
        print("❌ Desmarcando todas as linhas da tabela")
        return []
    
    return no_update

if __name__ == "__main__":
    print("✅ Callback NOVO de produtos com filtros carregado!")