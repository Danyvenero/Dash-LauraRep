"""
Callback específico para tabela de produtos com dash_table funcional
Implementa filtro por material e interação completa
"""

from dash import Input, Output, State, callback, html, dcc, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
from utils.table_styles import (
    TABLE_STYLE_HEADER_PRIMARY,
    TABLE_STYLE_CELL_DEFAULT,
    TABLE_STYLE_TABLE_FULL_WIDTH,
)
import logging
import traceback
import sys
import os
import re
import plotly.graph_objects as go

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_vendas_data, load_cotacoes_data, load_produtos_cotados_data
from utils import get_setting, save_setting, delete_setting
from utils.security import get_current_username
from webapp import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Callback de produtos (novo) sendo carregado")
# Preset padrão de colunas (campos críticos)
DEFAULT_COL_PRESET = [
    'oportunidade_score', 'status_oportunidade',
    'prioridade_score', 'prioridade_venda_cat', 'q_prioridade_score', 'q_prioridade_cat',
    'recorrencia_mensal', 'q_recorrencia_mensal',
    'recency_days', 'q_recency_days',
    'freq_media_compra_dias', 'freq_media_cotacao_dias',
    'pct_qtd_comprada_vs_cotada', 'meses_cotados_sem_compra',
]

# Inicializa dropdown de colunas a partir do preset salvo (local/SQLite)
@callback(
    Output("produtos-column-select", "value"),
    [Input("url", "pathname")],
    [State("produtos-column-preset", "data")],
    prevent_initial_call=False
)
def init_column_select(pathname, local_store_data):
    allowed_paths = {"/produtos", "/produtos/", "/app/products", "/app/products/", "/app/produtos", "/app/produtos/", "/products", "/products/"}
    if pathname not in allowed_paths:
        return no_update
    # 1) Se houver no localStorage, usa
    if isinstance(local_store_data, list) and local_store_data:
        return local_store_data
    # 2) Tenta buscar no SQLite por usuário
    try:
        username = get_current_username() or 'anon'
        key = f"produtos_col_preset::{username}"
        db_val = get_setting(key, None)
        if isinstance(db_val, list) and db_val:
            return db_val
    except Exception:
        pass
    # 3) Fallback para preset padrão
    return DEFAULT_COL_PRESET

# Botão para salvar o preset atual
@callback(
    Output("produtos-column-preset", "data", allow_duplicate=True),
    [Input("btn-save-col-preset", "n_clicks"), Input("btn-reset-col-preset", "n_clicks")],
    [State("produtos-column-select", "value")],
    prevent_initial_call=True
)
def save_column_preset(save_clicks, selected_cols):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    trig = ctx.triggered[0]['prop_id'].split('.')[0]
    username = get_current_username() or 'anon'
    key = f"produtos_col_preset::{username}"
    if trig == 'btn-reset-col-preset':
        try:
            delete_setting(key)
        except Exception:
            pass
        # Limpa o store local e retorna preset padrão ao dropdown via init callback
        return []
    # salvar
    cols = selected_cols if isinstance(selected_cols, list) else []
    try:
        save_setting(key, cols)
    except Exception:
        pass
    return cols

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
        Input("produtos-meses-janela", "value"),
        # Disparo inicial ao montar a página de produtos
        Input("produtos-initial-trigger", "n_intervals"),
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
        Input("url", "pathname"),
        # Controle de colunas visíveis (opcional)
        Input("produtos-column-select", "value")
    ],
    [
        State("produtos-grid-state", "data")
    ],
    prevent_initial_call=False
)
def update_produtos_table_with_filters(search_value, top_produtos, meses_janela,
                                       _initial_tick,
                                       filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia,
                                       filtro_canal, filtro_top_clientes, filtro_dias_sem_compra,
                                       wR_in, wF_in, wM_in,
                                       pathname,
                                       selected_columns,
                                       grid_state):
    """
    Carrega a tabela de produtos com filtros aplicados usando dash_table
    """
    try:
        logger.debug(f"Produtos callback pathname={pathname}")
        logger.debug(f"Filtros: search='{search_value}', top={top_produtos}")
        logger.info("Callback executado com filtros: top=%s", top_produtos)
        
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
        # Tamanho de página inicial padrão (controle nativo do AG Grid pode sobrescrever no cliente)
        page_size_effective = 25
            
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
        
        # Aplicar filtros globais como nos gráficos (usar fonte única em utils)
        try:
            from utils import apply_filters as _apply_filters  # fonte de verdade
        except Exception as _e:
            logger.warning(f"Falha ao importar utils.apply_filters, tentando fallback: {_e}")
            try:
                from webapp import callbacks as _callbacks
                _apply_filters = getattr(_callbacks, 'apply_filters', None)
            except Exception as _e2:
                _apply_filters = None
                logger.warning(f"Não foi possível obter apply_filters (fallback): {_e2}")

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
        # Janela de meses default 12 se não vier valor válido
        try:
            months_window = int(meses_janela) if meses_janela else 12
        except Exception:
            months_window = 12

        produtos_data = process_produtos_analytics(
            vendas_filtrado, cotacoes_df, produtos_cotados_df, top_n=None,
            r_weight=wR, f_weight=wF, m_weight=wM, months_window=months_window
        ).reset_index(drop=True)
        
        # Se não há dados após filtros, mostre mensagem ao invés de ignorar filtros
        if produtos_data is None or produtos_data.empty:
            logger.warning("Produtos vazios após aplicar filtros globais — sem fallback para 'todos'")
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-filter-circle-xmark me-2"),
                    "Sem resultados para os filtros atuais. Ajuste os filtros para visualizar dados."
                ], color="warning")
            ])
        
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
            'prioridade_venda_cat': 'Prioridade (Venda) Cat.',
            # Cotações
            'valor_cotado_total': 'Valor Cotado Total',
            'qtd_cotada_total': 'Qtd Cotada Total',
            'q_recorrencia_mensal': 'Recorrência Cotação/Mês',
            'q_recency_days': 'Recência (Cotação) Dias',
            'q_prioridade_score': 'Prioridade (Cotação)',
            'q_prioridade_cat': 'Prioridade (Cotação) Cat.',
            # Frequências médias em dias
            'freq_media_cotacao_dias': 'Freq. Cotação (Dias)',
            'freq_media_compra_dias': 'Freq. Compra (Dias)',
            'obs_freq_compra': 'Obs. Freq. Compra',
            'ticket_medio_cotacao_ano': 'Ticket Médio (Cotação Ano)',
            # Conversões e Gaps
            'conversao_valor_percent': 'Conversão Valor (%)',
            'freq_gap_pct': 'Gap Freq (%)',
            'recency_gap_pct': 'Gap Recência (%)',
            'valor_gap_pct': 'Gap Valor (%)',
            'meses_cotados_sem_compra': f'Meses Cotados Sem Compra ({months_window}m)',
            'pct_qtd_comprada_vs_cotada': 'Qtd Comprada vs Cotada (%)',
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
            'prioridade_score', 'prioridade_venda_cat', 'q_prioridade_score', 'q_prioridade_cat',
            'recorrencia_mensal', 'q_recorrencia_mensal',
            'recency_days', 'q_recency_days',
            'freq_media_compra_dias', 'freq_media_cotacao_dias',
            'obs_freq_compra',
            'faturamento_total', 'valor_cotado_total',
            'quantidade_total', 'qtd_cotada_total',
            'ticket_medio_cotacao_ano',
            'conversao_valor_percent',
            'freq_gap_pct', 'recency_gap_pct', 'valor_gap_pct',
            'meses_cotados_sem_compra', 'pct_qtd_comprada_vs_cotada'
        ]
        columns_to_show = [col for col in preferred_order if col in display_data.columns]
        # Fallback: se algo faltar, inclui demais disponíveis que tenham mapping
        columns_to_show += [col for col in column_mapping.keys() if col in display_data.columns and col not in columns_to_show]
        # Aplicar seleção de colunas do usuário (baseia-se nos nomes originais)
        if selected_columns and isinstance(selected_columns, list) and len(selected_columns) > 0:
            # Manter sempre material/produto por usabilidade
            base_keep = ['material', 'produto']
            cols = base_keep + [c for c in selected_columns if c not in base_keep]
            columns_to_show = [c for c in columns_to_show if c in cols]
            if not columns_to_show:
                columns_to_show = base_keep
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
            elif col in ['Ticket Médio (Cotação Ano)']:
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
        
        # Tamanho de página inicial permanece 25; o seletor nativo permite alterar no grid

        # Criar Dash AG Grid
        try:
            import dash_ag_grid as dag
            from utils.aggrid_config import default_col_def, build_coldefs_from_datatable
            # Map DataTable columns spec to AG Grid columnDefs with valueFormatters
            col_defs = build_coldefs_from_datatable(table_columns)
            # Restaurar estado salvo do grid (filtros/ordenação/colunas)
            saved_filter = {}
            saved_sort = []
            saved_colstate = []
            try:
                if isinstance(grid_state, dict):
                    saved_filter = grid_state.get('filterModel') or {}
                    saved_sort = grid_state.get('sortModel') or []
                    saved_colstate = grid_state.get('columnState') or []
            except Exception:
                pass
            data_table = dag.AgGrid(
                id='produtos-table',
                rowData=display_data.to_dict('records'),
                columnDefs=col_defs,
                defaultColDef=default_col_def(),
                # Restaura filtros/ordenação e estado de colunas
                filterModel=saved_filter,
                sortModel=saved_sort,
                columnState=saved_colstate,
                getRowStyle={
                    "function": (
                        "params => {"
                        " const s = params && params.data ? params.data['Status'] : undefined;"
                        " if (s === 'Recomendar') return {backgroundColor:'rgba(40,167,69,0.10)'};"
                        " if (s === 'Observar') return {backgroundColor:'rgba(255,193,7,0.12)'};"
                        " return null;"
                        " }"
                    )
                },
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": page_size_effective,
                    "paginationPageSizeSelector": [10, 25, 50, 100],
                    "rowSelection": "multiple",
                    "animateRows": True,
                    "ensureDomOrder": True,
                    "domLayout": "autoHeight",
                },
                style={"width": "100%"}
            )
        except Exception:
            # Fallback to DataTable if AG Grid not available
            data_table = dash_table.DataTable(
                id='produtos-table',
                columns=table_columns,
                data=display_data.to_dict('records'),
                page_size=page_size_effective,
                sort_action='native',
                filter_action='native',
                row_selectable='multi',
                selected_rows=[],
                style_table=TABLE_STYLE_TABLE_FULL_WIDTH,
                style_header=TABLE_STYLE_HEADER_PRIMARY,
                style_cell=TABLE_STYLE_CELL_DEFAULT,
            )

        try:
            # Distribuição/Histograma interativo para "Qtd Comprada vs Cotada (%)"
            dist_vals = pd.to_numeric(
                filtered_data.get('pct_qtd_comprada_vs_cotada', pd.Series(dtype=float)),
                errors='coerce'
            )
            bins = [(0, 25), (25, 50), (50, 75), (75, 100)]
            x_labels = [f"{lo}-{hi}" for (lo, hi) in bins]
            counts = []
            z_vals = []
            # Normalizar recorrência
            qrec = pd.to_numeric(filtered_data.get('q_recorrencia_mensal', pd.Series(dtype=float)), errors='coerce').fillna(0)
            denom = float(qrec.max()) if pd.notna(qrec.max()) and qrec.max() > 0 else 1.0
            # Baseline
            try:
                baseline_vals = pd.to_numeric(produtos_data.get('pct_qtd_comprada_vs_cotada', pd.Series(dtype=float)), errors='coerce')
                baseline_qrec = pd.to_numeric(produtos_data.get('q_recorrencia_mensal', pd.Series(dtype=float)), errors='coerce').fillna(0)
            except Exception:
                baseline_vals = pd.Series(dtype=float)
                baseline_qrec = pd.Series(dtype=float)
            b_denom = float(baseline_qrec.max()) if pd.notna(baseline_qrec.max()) and baseline_qrec.max() > 0 else 1.0
            baseline_counts = []
            baseline_z = []
            for (lo, hi) in bins:
                if hi == 100:
                    mask = (dist_vals >= lo) & (dist_vals <= hi)
                else:
                    mask = (dist_vals >= lo) & (dist_vals < hi)
                subset = filtered_data[mask]
                counts.append(int(mask.sum()))
                if not subset.empty and 'q_recorrencia_mensal' in subset.columns:
                    z_vals.append((pd.to_numeric(subset['q_recorrencia_mensal'], errors='coerce').fillna(0) / denom).mean())
                else:
                    z_vals.append(0.0)
                # Baseline
                if baseline_vals is not None and len(baseline_vals) > 0:
                    if hi == 100:
                        bmask = (baseline_vals >= lo) & (baseline_vals <= hi)
                    else:
                        bmask = (baseline_vals >= lo) & (baseline_vals < hi)
                    bsubset = produtos_data[bmask]
                    baseline_counts.append(int(bmask.sum()))
                    if not bsubset.empty and 'q_recorrencia_mensal' in bsubset.columns:
                        baseline_z.append((pd.to_numeric(bsubset['q_recorrencia_mensal'], errors='coerce').fillna(0) / b_denom).mean())
                    else:
                        baseline_z.append(0.0)
                else:
                    baseline_counts.append(0)
                    baseline_z.append(0.0)

            # Histograma sobreposto
            hist_fig = go.Figure()
            total_baseline = max(sum(baseline_counts), 1)
            total_current = max(sum(counts), 1)
            atual_pct = [c / total_current for c in counts]
            base_pct = [c / total_baseline for c in baseline_counts]
            atual_text = [f"n={c} • {p:.0%}" if c > 0 else "" for c, p in zip(counts, atual_pct)]
            base_text = [f"n={c} • {p:.0%}" if c > 0 else "" for c, p in zip(baseline_counts, base_pct)]
            inside_threshold = 0.12
            atual_text_pos = ["inside" if p >= inside_threshold and c > 0 else "outside" for c, p in zip(counts, atual_pct)]
            base_text_pos = ["outside" for _ in baseline_counts]
            # Contraste de texto: se cor (z) for clara, usar preto mesmo quando 'inside'
            def _text_color(i, pos):
                if pos != 'inside':
                    return 'black'
                try:
                    z = float(z_vals[i]) if i < len(z_vals) else 0.0
                except Exception:
                    z = 0.0
                return 'black' if z <= 0.45 else 'white'
            atual_text_colors = [_text_color(i, pos) for i, pos in enumerate(atual_text_pos)]
            base_text_colors = ["black" for _ in baseline_counts]
            # Hover por ponto (esconde quando contagem é zero)
            base_hover = [
                (
                    "Baseline<br>Faixa: %s<br>Qtd itens: %d<br>Participação: %.1f%%<extra></extra>"
                    % (xl, yc, (yc/total_baseline)*100)
                ) if yc > 0 else "<extra></extra>"
                for xl, yc in zip(x_labels, baseline_counts)
            ]
            atual_hover = [
                (
                    "Atual<br>Faixa: %s<br>Qtd itens: %d<br>Participação: %.1f%%<br>Recorrência norm.: %.2f<extra></extra>"
                    % (xl, yc, (yc/total_current)*100, (float(z_vals[i]) if i < len(z_vals) and z_vals[i] is not None and not pd.isna(z_vals[i]) else 0.0))
                ) if yc > 0 else "<extra></extra>"
                for i, (xl, yc) in enumerate(zip(x_labels, counts))
            ]

            # Opacidade por barra: atenuar bins com n=0
            base_opacity = [0.25 if yc > 0 else 0.12 for yc in baseline_counts]
            atual_opacity = [1.0 if yc > 0 else 0.15 for yc in counts]

            # Baseline
            hist_fig.add_trace(go.Bar(
                x=x_labels,
                y=baseline_counts,
                name="Baseline",
                text=base_text,
                textposition=base_text_pos,
                insidetextanchor="middle",
                textfont=dict(color=base_text_colors, size=11),
                marker=dict(color='rgba(120,120,120,1.0)', opacity=base_opacity),
                hovertemplate=base_hover,
                customdata=[c/total_baseline for c in baseline_counts]
            ))
            # Atual
            hist_fig.add_trace(go.Bar(
                x=x_labels,
                y=counts,
                name="Atual",
                text=atual_text,
                textposition=atual_text_pos,
                insidetextanchor="middle",
                textfont=dict(color=atual_text_colors, size=11),
                marker=dict(color=z_vals, coloraxis="coloraxis", line=dict(color="rgba(255,255,255,0.9)", width=1), opacity=atual_opacity),
                cliponaxis=False,
                hovertemplate=atual_hover,
                customdata=[c/total_current for c in counts]
            ))
            # Escala de cores dinâmica
            z_valid = [float(z) for z in z_vals if z is not None and not pd.isna(z)]
            if z_valid:
                zmin, zmax = min(z_valid), max(z_valid)
                cmin_dyn = max(0.0, zmin - 0.05)
                cmax_dyn = min(1.0, zmax + 0.05)
                if (cmax_dyn - cmin_dyn) < 0.1:
                    mid = (zmin + zmax) / 2.0
                    cmin_dyn = max(0.0, mid - 0.1)
                    cmax_dyn = min(1.0, mid + 0.1)
            else:
                cmin_dyn, cmax_dyn = 0.0, 1.0
            # Headroom para evitar corte dos rótulos no topo
            try:
                y_max = max(max(baseline_counts or [0]), max(counts or [0]), 1)
            except Exception:
                y_max = max(sum(baseline_counts), sum(counts), 1)
            hist_fig.update_layout(
                barmode='overlay',
                margin=dict(l=20, r=20, t=40, b=30),
                title=dict(text="Distribuição — Qtd Comprada vs Cotada (%)", x=0.01, xanchor='left', font=dict(size=14)),
                xaxis_title="Faixa (%)",
                yaxis_title="n",
                height=300,
                coloraxis=dict(colorscale='YlGnBu', colorbar=dict(title={"text": "Recorrência norm. (0–1)", "side": "right"}), cmin=cmin_dyn, cmax=cmax_dyn),
                showlegend=False,
                bargap=0.25,
                template='plotly_white'
            )
            hist_fig.update_yaxes(range=[0, y_max * 1.18])
            hist_fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels,
                                   tickangle=0, ticks='outside', showline=True,
                                   linecolor='rgba(0,0,0,0.1)')

            # Segundo gráfico: Distribuição por Categoria de Prioridade (Venda), cor = Prioridade (Cotação) normalizada
            try:
                cat_series = pd.to_numeric(filtered_data.get('prioridade_venda_cat', pd.Series(dtype=float)), errors='coerce').fillna(0).astype(int)
                cat_bins = [1, 2, 3, 4, 5]
                cat_labels = [str(c) for c in cat_bins]
                cat_counts = [int((cat_series == c).sum()) for c in cat_bins]
                # cor por prioridade de cotação normalizada (0..1)
                qscore = pd.to_numeric(filtered_data.get('q_prioridade_score', pd.Series(dtype=float)), errors='coerce').fillna(0) / 100.0
                z_cats = []
                for c in cat_bins:
                    subset = qscore[cat_series == c]
                    z_cats.append(float(subset.mean()) if not subset.empty else 0.0)
                pri_fig = go.Figure()
                total_c = max(sum(cat_counts), 1)
                text = [f"n={n} • {n/total_c:.0%}" if n > 0 else "" for n in cat_counts]
                text_pos = ["inside" if (n/total_c) >= 0.12 and n > 0 else "outside" for n in cat_counts]
                text_colors = ['white' if (z_cats[i] or 0) > 0.45 and text_pos[i] == 'inside' else 'black' for i in range(len(cat_counts))]
                hover = [
                    (
                        "Categoria: %s<br>Qtd itens: %d<br>Participação: %.1f%%<br>Prior. Cotação norm.: %.2f<extra></extra>"
                        % (xl, yc, (yc/total_c)*100, (float(z_cats[i]) if i < len(z_cats) else 0.0))
                    ) if yc > 0 else "<extra></extra>"
                    for i, (xl, yc) in enumerate(zip(cat_labels, cat_counts))
                ]
                pri_fig.add_trace(go.Bar(
                    x=cat_labels,
                    y=cat_counts,
                    name="Categorias",
                    text=text,
                    textposition=text_pos,
                    insidetextanchor="middle",
                    textfont=dict(color=text_colors, size=11),
                    marker=dict(color=z_cats, coloraxis="coloraxis", line=dict(color="rgba(255,255,255,0.9)", width=1), opacity=[1.0 if n>0 else 0.15 for n in cat_counts]),
                    hovertemplate=hover,
                ))
                z_valid2 = [float(z) for z in z_cats if z is not None and not pd.isna(z)]
                if z_valid2:
                    zmin2, zmax2 = min(z_valid2), max(z_valid2)
                    cmin2 = max(0.0, zmin2 - 0.05)
                    cmax2 = min(1.0, zmax2 + 0.05)
                    if (cmax2 - cmin2) < 0.1:
                        mid = (zmin2 + zmax2) / 2.0
                        cmin2 = max(0.0, mid - 0.1)
                        cmax2 = min(1.0, mid + 0.1)
                else:
                    cmin2, cmax2 = 0.0, 1.0
                pri_fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=30),
                    title=dict(text="Distribuição — Prioridade (Venda) Cat.", x=0.01, xanchor='left', font=dict(size=14)),
                    xaxis_title="Categoria (1–5)",
                    yaxis_title="n",
                    height=280,
                    coloraxis=dict(colorscale='YlGnBu', colorbar=dict(title={"text": "Prior. Cotação norm. (0–1)", "side": "right"}), cmin=cmin2, cmax=cmax2),
                    showlegend=False,
                    bargap=0.25,
                    template='plotly_white'
                )
                pri_fig.update_xaxes(type='category', categoryorder='array', categoryarray=cat_labels)
                pri_fig.update_yaxes(range=[0, max(cat_counts + [1]) * 1.18])
                priority_section = html.Div([
                    html.Div([
                        html.Div([
                            html.Span("Distribuição — Prioridade (Venda) Cat. "),
                            html.I(id="help-produtos-priority", className="fas fa-info-circle text-muted", style={"cursor": "pointer"}),
                            dbc.Tooltip(
                                "Barras = contagem por categoria 1–5 (RFV de vendas). Cor = Prioridade de Cotação normalizada (0–1). Clique para filtrar.",
                                target="help-produtos-priority",
                                placement="right",
                            ),
                            dbc.Button("Limpar filtro por prioridade", id="btn-clear-priority-filter", color="secondary", size="sm", className="ms-2")
                        ])
                    ], className="mb-2"),
                    dcc.Graph(id='produtos-priority-dist', figure=pri_fig, config={'displayModeBar': False})
                ], className="mt-4")
            except Exception as _:
                priority_section = html.Div()

            distribution_section = html.Div([
                html.Div([
                    html.Div([
                        html.Span("Distribuição — Qtd Comprada vs Cotada (%). "),
                        html.I(id="help-produtos-distribution", className="fas fa-info-circle text-muted", style={"cursor": "pointer"}),
                        dbc.Tooltip(
                            "Barras = contagem de materiais (n) por faixa. Cor da barra = Recorrência de Cotação/Mês normalizada (0–1): mais escuro = maior recorrência. "
                            "Clique em uma faixa para filtrar a tabela. A barra cinza (Baseline) mostra a distribuição no conjunto base (após filtros globais, antes da busca).",
                            target="help-produtos-distribution",
                            placement="right",
                        ),
                        dbc.Button("Limpar filtro do gráfico", id="btn-clear-distribution-filter", color="secondary", size="sm", className="ms-2")
                    ])
                ], className="mb-2"),
                dcc.Graph(id='produtos-distribution', figure=hist_fig, config={'displayModeBar': False})
            ], className="mt-4")
            # juntar as duas seções
        except Exception as dist_err:
            logger.error(f"Falha ao montar distribuição de produtos: {dist_err}")
            distribution_section = dbc.Alert([
                html.I(className="fas fa-circle-info me-2"),
                "Não foi possível renderizar o histograma de distribuição neste momento. "
                "A tabela continua funcional."
            ], color="warning")
        
        return html.Div([
            success_message,
            html.H6([
                html.I(className="fas fa-table me-2"),
                title_text
            ], className="mb-3"),
            data_table,
            html.Div([
                html.Small(
                    "Como ler as colunas: Material = código do item; Produto = descrição. "
                    "Oportunidade = score 0–100 que combina gaps de frequência, recência e valor (maior = priorize). "
                    "Status = recomendação baseada no score. "
                    "Prioridade (Venda/Cotação) = RFV de cada visão (0–100). "
                    "Recorrência/Mês = média de meses com movimento; Recência (Dias) = dias desde o último evento. "
                    "Freq. Compra/Cotação (Dias) = intervalo médio entre eventos (Dias). "
                    "Obs. Freq. Compra indica se o valor foi Calculado, Estimado (sem histórico suficiente) ou Sem histórico. "
                    "Conversão Valor (%) = vendas/cotações em valor. "
                    "Gaps (%) medem o espaço para recuperar frequência/recência/valor. "
                    "Meses Cotados Sem Compra = meses cotados sem compra na janela, "
                    "Qtd Comprada vs Cotada (%) = o quanto se converteu em quantidade (ideal próximo de 100%).",
                    className="text-muted"
                )
            ], className="mt-2"),
            distribution_section,
            priority_section if 'priority_section' in locals() else html.Span()
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
                               r_weight=0.4, f_weight=0.3, m_weight=0.3,
                               months_window: int = 12):
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
        
        # Normalizar chaves para merges robustos
        try:
            if 'material' in vendas_df.columns:
                vendas_df['material'] = vendas_df['material'].astype(str).str.strip()
            if 'produto' in vendas_df.columns:
                vendas_df['produto'] = vendas_df['produto'].astype(str).str.strip()
        except Exception:
            pass

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
        # Categoria 1..5 para prioridade de vendas
        def _rfv_cat(x):
            try:
                v = float(x)
            except Exception:
                return 1
            if v < 20: return 1
            if v < 40: return 2
            if v < 60: return 3
            if v < 80: return 4
            return 5
        produtos_stats['prioridade_venda_cat'] = produtos_stats['prioridade_score'].map(_rfv_cat)

        # ======================
        # Cotações (Q-RFV)
        # ======================
        quotes_df = None
        if produtos_cotados_df is not None and not produtos_cotados_df.empty:
            # Base principal: produtos cotados (tem material/quantidade/valores)
            quotes_df = produtos_cotados_df.copy()
            # Enriquecer com data da cotação (vem da tabela de cotações)
            try:
                if cotacoes_df is not None and not cotacoes_df.empty:
                    co = cotacoes_df.copy()
                    # Garantir tipos/nomes
                    if 'cotacao' in quotes_df.columns and 'numero_cotacao' in co.columns:
                        quotes_df['cotacao'] = quotes_df['cotacao'].astype(str).str.strip()
                        co['numero_cotacao'] = co['numero_cotacao'].astype(str).str.strip()
                        # Mantém apenas colunas necessárias para evitar explosão de colunas
                        co_slim_cols = ['numero_cotacao'] + ([c for c in ['data', 'data_cotacao', 'data_emissao', 'dt_cotacao', 'dt_emissao'] if c in co.columns])
                        co_slim = co[co_slim_cols].drop_duplicates('numero_cotacao') if co_slim_cols else co[['numero_cotacao']]
                        quotes_df = quotes_df.merge(co_slim, left_on='cotacao', right_on='numero_cotacao', how='left')
            except Exception as _merge_err:
                logger.warning(f"Falha ao enriquecer produtos_cotados com datas de cotações: {_merge_err}")
        elif cotacoes_df is not None and not cotacoes_df.empty:
            # Fallback: usar cotações diretamente (menos granular para material)
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

            # Normalizar chaves para merge consistente com vendas
            try:
                if 'material' in quotes_df.columns:
                    quotes_df['material'] = quotes_df['material'].astype(str).str.strip()
                if 'produto' in quotes_df.columns:
                    quotes_df['produto'] = quotes_df['produto'].astype(str).str.strip()
            except Exception:
                pass

            # Cascatear filtros globais: restringir cotações aos materiais presentes nas vendas filtradas
            # Isso garante consistência quando cliente/hierarquia/canal estão aplicados nos filtros globais
            try:
                if vendas_df is not None and not vendas_df.empty and 'material' in vendas_df.columns and 'material' in quotes_df.columns:
                    allowed_materials = set(vendas_df['material'].astype(str).str.strip().unique())
                    quotes_df = quotes_df[quotes_df['material'].isin(allowed_materials)].copy()
            except Exception:
                # Em caso de falha, segue sem a restrição (não quebra a pipeline)
                pass

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
            for c in ['data_cotacao', 'data_emissao', 'dt_cotacao', 'dt_emissao', 'data']:
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

            # Ticket Médio de Cotação (Ano Corrente ou filtro_ano)
            try:
                current_year = pd.Timestamp.today().year
                # Se existir filtro_ano no escopo exterior, tentamos detectá-lo via meses_janela já usado
                # Aqui usamos o ano atual por padrão
                year_series = pd.to_datetime(quotes_df[qdate_col], errors='coerce').dt.year if qdate_col is not None else pd.Series([], dtype=int)
                if year_series.notna().any():
                    mask_y = year_series == current_year
                    q_this_year = quotes_df[mask_y].copy()
                    if not q_this_year.empty:
                        # Identificar colunas de valor e quantidade
                        val_candidates = ['valor_total', 'vlr_total', 'valor', 'vlr_cotado', 'vlr_rol', 'preco_liquido_total']
                        qty_candidates = ['qtd_cotada', 'quantidade_cotada', 'qtd', 'quantidade', 'qtde', 'qty']
                        vcol = next((c for c in val_candidates if c in q_this_year.columns), None)
                        qcol = next((c for c in qty_candidates if c in q_this_year.columns), None)
                        if vcol is None and 'preco_liquido_unitario' in q_this_year.columns and 'quantidade' in q_this_year.columns:
                            q_this_year['__calc_total'] = pd.to_numeric(q_this_year['preco_liquido_unitario'], errors='coerce').fillna(0) * pd.to_numeric(q_this_year['quantidade'], errors='coerce').fillna(0)
                            vcol = '__calc_total'
                            qcol = 'quantidade'
                        if vcol is not None and qcol is not None:
                            q_this_year[vcol] = pd.to_numeric(q_this_year[vcol], errors='coerce').fillna(0)
                            q_this_year[qcol] = pd.to_numeric(q_this_year[qcol], errors='coerce').fillna(0)
                            g_ty = q_this_year.groupby('material').agg(valor_ano=(vcol,'sum'), qtd_ano=(qcol,'sum')).reset_index()
                            g_ty['ticket_medio_cotacao_ano'] = (g_ty['valor_ano'] / g_ty['qtd_ano'].replace(0, pd.NA)).astype(float)
                            produtos_stats = produtos_stats.merge(g_ty[['material','ticket_medio_cotacao_ano']], on='material', how='left')
            except Exception:
                produtos_stats['ticket_medio_cotacao_ano'] = None

            # Normalização Q-RFV
            q_r_norm = quantile_norm(q_stats['q_recency_days'].fillna(q_stats['q_recency_days'].max() or 0), invert=True)
            q_f_norm = quantile_norm(q_stats['q_recorrencia_mensal'].fillna(0))
            q_m_norm = quantile_norm(q_stats['valor_cotado_total'].fillna(0))
            q_stats['_r_norm_q'] = q_r_norm
            q_stats['_f_norm_q'] = q_f_norm
            q_stats['_m_norm_q'] = q_m_norm
            q_stats['q_prioridade_score'] = ((r_weight * q_r_norm) + (f_weight * q_f_norm) + (m_weight * q_m_norm)) * 100.0
            # Categoria 1..5 para prioridade de cotação
            q_stats['q_prioridade_cat'] = q_stats['q_prioridade_score'].map(_rfv_cat)

            # Merge com vendas usando somente 'material' (evita mismatch por descrições diferentes)
            produtos_stats = produtos_stats.merge(q_stats, on=['material'], how='left')
        else:
            # Se não há cotações, criar colunas vazias
            for col in ['valor_cotado_total', 'q_recorrencia_cotacao', 'q_recorrencia_mensal', 'q_recency_days', 'qtd_cotada_total', 'q_prioridade_score', '_r_norm_q', '_f_norm_q', '_m_norm_q', 'q_prioridade_cat']:
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

        # Meses com cotação mas sem compra (contagem inteira via conjuntos de meses)
        try:
            # Preparar meses de vendas
            v_months_df = pd.DataFrame({'material': [], 'month': []})
            v_ref = None
            if date_col is not None and date_col in vendas_df.columns:
                _vm = vendas_df[['material', date_col]].copy()
                _vm[date_col] = pd.to_datetime(_vm[date_col], errors='coerce')
                _vm = _vm.dropna(subset=[date_col])
                if not _vm.empty:
                    v_ref = _vm[date_col].max()
                    _vm['month'] = _vm[date_col].dt.to_period('M')
                    v_months_df = _vm[['material', 'month']].drop_duplicates()

            # Preparar meses de cotações
            q_months_df = pd.DataFrame({'material': [], 'month': []})
            q_ref = None
            if quotes_df is not None and qdate_col is not None and qdate_col in quotes_df.columns:
                _qm = quotes_df[['material', qdate_col]].copy()
                _qm[qdate_col] = pd.to_datetime(_qm[qdate_col], errors='coerce')
                _qm = _qm.dropna(subset=[qdate_col])
                if not _qm.empty:
                    q_ref = _qm[qdate_col].max()
                    _qm['month'] = _qm[qdate_col].dt.to_period('M')
                    q_months_df = _qm[['material', 'month']].drop_duplicates()

            # Janela dos últimos N meses baseada na data mais recente entre vendas e cotações
            if q_months_df.empty:
                produtos_stats['meses_cotados_sem_compra'] = 0
            else:
                try:
                    ref = None
                    if v_ref is not None and q_ref is not None:
                        ref = max(v_ref, q_ref)
                    elif v_ref is not None:
                        ref = v_ref
                    else:
                        ref = q_ref
                    if pd.isna(ref):
                        raise ValueError("Sem data de referência para janela de meses")
                    ref_month = pd.Period(pd.to_datetime(ref), freq='M')
                    start_month = ref_month - (months_window - 1)
                    # Filtrar dados para a janela
                    q_months_df = q_months_df[(q_months_df['month'] >= start_month) & (q_months_df['month'] <= ref_month)]
                    if not v_months_df.empty:
                        v_months_df = v_months_df[(v_months_df['month'] >= start_month) & (v_months_df['month'] <= ref_month)]

                    # Contar meses de cotação por material
                    q_counts = q_months_df.groupby('material').size().rename('q_month_count').reset_index()
                    # Interseção: meses com venda E cotação
                    if not v_months_df.empty:
                        intersect = q_months_df.merge(v_months_df, on=['material', 'month'], how='inner')
                        inter_counts = intersect.groupby('material').size().rename('inter_month_count').reset_index()
                    else:
                        inter_counts = pd.DataFrame({'material': [], 'inter_month_count': []})

                    meses_df = q_counts.merge(inter_counts, on='material', how='left')
                    meses_df['inter_month_count'] = pd.to_numeric(meses_df['inter_month_count'], errors='coerce').fillna(0)
                    meses_df['meses_cotados_sem_compra'] = (meses_df['q_month_count'] - meses_df['inter_month_count']).clip(lower=0).astype('Int64')
                    produtos_stats = produtos_stats.merge(meses_df[['material', 'meses_cotados_sem_compra']], on='material', how='left')
                    produtos_stats['meses_cotados_sem_compra'] = produtos_stats['meses_cotados_sem_compra'].fillna(0).astype('Int64')
                except Exception:
                    produtos_stats['meses_cotados_sem_compra'] = 0
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

        # Observação amigável sobre a frequência de compra
        if 'freq_compra_estimado' not in produtos_stats.columns:
            produtos_stats['freq_compra_estimado'] = False
        def _obs_freq_row(row):
            val = row.get('freq_media_compra_dias')
            est = bool(row.get('freq_compra_estimado'))
            if pd.notna(val):
                return 'Estimado' if est else 'Calculado'
            return 'Sem histórico'
        try:
            produtos_stats['obs_freq_compra'] = produtos_stats.apply(_obs_freq_row, axis=1)
        except Exception:
            # Fallback simples
            produtos_stats['obs_freq_compra'] = produtos_stats['freq_compra_estimado'].map(lambda x: 'Estimado' if bool(x) else 'Sem histórico')

        # Indicador solicitado (invertido): relação % entre quantidade COMPRADA e COTADA (0..100)
        # pct_qtd_comprada_vs_cotada = quantidade_total / qtd_cotada_total
        denom_qtd_cotada = produtos_stats.get('qtd_cotada_total', 0).replace(0, pd.NA)
        qtd_ratio_inv = (produtos_stats['quantidade_total'] / denom_qtd_cotada).fillna(0)
        produtos_stats['pct_qtd_comprada_vs_cotada'] = (qtd_ratio_inv.clip(lower=0) * 100).clip(upper=100).round(2)

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
        for col in ['q_prioridade_score', 'oportunidade_score', 'conversao_valor_percent', 'pct_qtd_comprada_vs_cotada', 'freq_media_compra_dias', 'freq_media_cotacao_dias']:
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
     Output("filter-top-produtos", "value")],
    [Input("btn-clear-filters-produtos", "n_clicks")],
    prevent_initial_call=True
)
def clear_table_filters(n_clicks):
    """
    Limpa todos os filtros da tabela de produtos
    """
    if n_clicks:
        print("🗑️ Limpando filtros da tabela de produtos...")
    # Top vazio = todos
    return "", None

# Callback para selecionar/desmarcar todas as linhas
@callback(
    Output("produtos-table", "selectedRows"),
    [Input("btn-select-all-produtos", "n_clicks"),
     Input("btn-deselect-all-produtos", "n_clicks")],
    [State("produtos-table", "rowData")],
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
        return table_data or []
    elif button_id == "btn-deselect-all-produtos" and deselect_clicks:
        print("❌ Desmarcando todas as linhas da tabela")
        return []
    
    return no_update

# Limpar filtros e ordenação do AG Grid (Produtos)
@callback(
    [Output('produtos-table', 'filterModel', allow_duplicate=True),
     Output('produtos-table', 'sortModel', allow_duplicate=True)],
    Input('btn-clear-filters-produtos', 'n_clicks'),
    prevent_initial_call=True
)
def clear_aggrid_filters_products(n_clicks):
    if not n_clicks:
        return no_update
    return {}, []

# Callback para filtrar a tabela ao clicar na distribuição (faixas 0-25, 25-50, 50-75, 75-100)
@callback(
    [Output("produtos-table", "filterModel", allow_duplicate=True), Output("produtos-table", "sortModel")],
    [
        Input("produtos-distribution", "clickData"),
        Input("btn-clear-distribution-filter", "n_clicks"),
    ],
    [
        State("produtos-table", "filterModel"),
        State("produtos-distribution", "figure"),
    ],
    prevent_initial_call=True
)
def filter_table_by_distribution(clickData, clear_clicks, current_filter, dist_fig):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # ID de coluna exibida na DataTable para o novo indicador
    col_field = 'Qtd Comprada vs Cotada (%)'

    if trig_id == 'btn-clear-distribution-filter':
        # Remover apenas o filtro desta coluna, mantendo outros filtros que o usuário tenha aplicado
        # Limpar filtros e ordenação
        return {}, []

    if trig_id == 'produtos-distribution' and clickData:
        try:
            point = clickData['points'][0]
            x = point.get('x')  # ex: "0-25"
            # Ignorar clique em barras com contagem zero
            y_val = point.get('y')
            if y_val is not None and isinstance(y_val, (int, float)) and y_val <= 0:
                return no_update
            if isinstance(x, str) and '-' in x:
                parts = x.split('-')
                lo = float(parts[0])
                hi = float(parts[1])
                # Construir filterModel do AG Grid
                # Usa filtro do tipo number com duas condições (>= lo) AND (< hi or <= hi)
                condition2_type = "lessThanOrEqual" if hi == 100 else "lessThan"
                return ({
                    col_field: {
                        "filterType": "number",
                        "type": "greaterThanOrEqual",
                        "filter": lo,
                        "operator": "AND",
                        "condition2": {"type": condition2_type, "filter": hi}
                    }
                }, [])
        except Exception:
            return no_update
    return no_update

# Callback para filtrar a tabela ao clicar na distribuição de Prioridade (Venda) Cat.
@callback(
    Output("produtos-table", "filterModel", allow_duplicate=True),
    [
        Input("produtos-priority-dist", "clickData"),
        Input("btn-clear-priority-filter", "n_clicks"),
    ],
    [
        State("produtos-table", "filterModel"),
    ],
    prevent_initial_call=True
)
def filter_table_by_priority(clickData, clear_clicks, current_filter):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]

    col_field = 'Prioridade (Venda) Cat.'

    if trig_id == 'btn-clear-priority-filter':
        return {}

    if trig_id == 'produtos-priority-dist' and clickData:
        try:
            point = clickData['points'][0]
            x = point.get('x')  # categoria '1'..'5'
            y_val = point.get('y')
            if y_val is not None and isinstance(y_val, (int, float)) and y_val <= 0:
                return no_update
            if isinstance(x, (int, float, str)):
                try:
                    cat = int(float(x))
                except Exception:
                    return no_update
                # Filter equals category on AG Grid
                return {col_field: {"filterType": "number", "type": "equals", "filter": cat}}
        except Exception:
            return no_update
    return no_update

if __name__ == "__main__":
    print("✅ Callback NOVO de produtos com filtros carregado!")

# Persistir estado do AG Grid (Produtos) em localStorage via dcc.Store
@callback(
    Output('produtos-grid-state', 'data'),
    [
        Input('produtos-table', 'filterModel'),
        Input('produtos-table', 'sortModel'),
        Input('produtos-table', 'columnState'),
    ],
    prevent_initial_call=True
)
def persist_products_grid_state(filter_model, sort_model, column_state):
    try:
        state = {
            'filterModel': filter_model or {},
            'sortModel': sort_model or [],
            'columnState': column_state or []
        }
        return state
    except Exception:
        return {}

# ----- Exportações (Produtos): CSV/PDF alinhados às colunas visíveis -----
@callback(
    Output('download-csv-produtos', 'data'),
    Input('btn-download-csv-produtos', 'n_clicks'),
    State('produtos-table', 'virtualRowData'),
    State('produtos-table', 'selectedRows'),
    State('produtos-table', 'columnDefs'),
    prevent_initial_call=True
)
def download_products_csv(n_clicks, derived_rows, selected_rows, columns_state):
    # Gera CSV com base nas linhas atualmente visíveis (filtros/ordenação) e nas colunas visíveis e em ordem
    from dash import dcc
    from dash.exceptions import PreventUpdate
    import pandas as pd
    from datetime import datetime
    if not n_clicks:
        raise PreventUpdate
    if not isinstance(derived_rows, list) or len(derived_rows) == 0:
        raise PreventUpdate
    # Ordem e IDs das colunas visíveis
    try:
        col_ids = [c.get('field') for c in (columns_state or []) if c and c.get('field')]
    except Exception:
        col_ids = []
    df = pd.DataFrame(derived_rows)
    # Se houver linhas selecionadas, exportar apenas as selecionadas
    if isinstance(selected_rows, (list, tuple)) and len(selected_rows) > 0:
        try:
            import pandas as pd
            sel_df = pd.DataFrame(list(selected_rows))
            if 'material' in df.columns and 'material' in sel_df.columns:
                df = df[df['material'].isin(sel_df['material'])]
            else:
                common = [c for c in sel_df.columns if c in df.columns]
                if common:
                    df = df.merge(sel_df[common].drop_duplicates(), on=common, how='inner')
        except Exception:
            pass
    # Manter somente colunas visíveis e na ordem atual
    if col_ids:
        cols_export = [c for c in col_ids if c in df.columns]
        if cols_export:
            df = df[cols_export]
    # Nome do arquivo com carimbo de data/hora
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"produtos_analise_{ts}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False, encoding='utf-8-sig')


@callback(
    Output('download-pdf-produtos', 'data'),
    Input('btn-pdf-cliente', 'n_clicks'),
    State('produtos-table', 'virtualRowData'),
    State('produtos-table', 'selectedRows'),
    State('produtos-table', 'columnDefs'),
    prevent_initial_call=True
)
def download_products_pdf(n_clicks, derived_rows, selected_rows, columns_state):
    # Gera PDF simples com as colunas visíveis e na ordem atual
    from dash import dcc
    from dash.exceptions import PreventUpdate
    import pandas as pd
    import io
    from datetime import datetime
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except Exception:
        # ReportLab não disponível
        raise PreventUpdate

    if not n_clicks:
        raise PreventUpdate
    if not isinstance(derived_rows, list) or len(derived_rows) == 0:
        raise PreventUpdate

    # Colunas visíveis e em ordem
    try:
        col_ids = [c.get('field') for c in (columns_state or []) if c and c.get('field')]
    except Exception:
        col_ids = []

    df = pd.DataFrame(derived_rows)
    # Aplicar seleção de linhas se houver
    if isinstance(selected_rows, (list, tuple)) and len(selected_rows) > 0:
        try:
            sel_df = pd.DataFrame(list(selected_rows))
            if 'material' in df.columns and 'material' in sel_df.columns:
                df = df[df['material'].isin(sel_df['material'])]
            else:
                common = [c for c in sel_df.columns if c in df.columns]
                if common:
                    df = df.merge(sel_df[common].drop_duplicates(), on=common, how='inner')
        except Exception:
            pass
    # Manter somente colunas visíveis e na ordem
    if col_ids:
        cols_export = [c for c in col_ids if c in df.columns]
        if cols_export:
            df = df[cols_export]

    # Limitar a um número razoável de linhas para PDF
    max_rows = 200
    df_print = df.head(max_rows).copy()
    # Stringify valores para evitar problemas de renderização
    df_print = df_print.applymap(lambda v: f"{v:.2f}" if isinstance(v, float) else (str(v) if v is not None else ''))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=54, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatório de Produtos", styles['Title']))
    story.append(Paragraph("Laura Representações - WEG", styles['Normal']))
    story.append(Spacer(1, 12))

    # Cabeçalhos são os IDs/nomes exibidos das colunas
    headers = list(df_print.columns)
    table_data = [headers]
    for _, row in df_print.iterrows():
        table_data.append([row.get(col, '') for col in headers])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total de itens listados: {len(df_print)}", styles['Italic']))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"produtos_relatorio_{ts}.pdf"
    return dcc.send_bytes(pdf_bytes, filename)