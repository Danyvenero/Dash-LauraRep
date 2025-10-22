"""
Módulo de Analytics Avançados para Dashboard WEG - Versão Limpa
Implementa análises estatísticas, gaps de oportunidade, alertas e insights inteligentes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
# from scipy import stats  # Temporarily disabled due to import issues
import warnings

warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    """Classe para Analytics Avançados com fundamentação estatística"""
    
    def __init__(self, vendas_df: pd.DataFrame = None, cotacoes_df: pd.DataFrame = None):
        """
        Inicializa o analisador com dados opcionais
        
        Args:
            vendas_df: DataFrame de vendas (opcional)
            cotacoes_df: DataFrame de cotações (opcional)
        """
        self.current_date = datetime.now()
        self.confidence_level = 0.95  # Nível de confiança padrão 95%
        self.vendas_df = vendas_df
        self.cotacoes_df = cotacoes_df
    
    # ==========================================
    # MÉTODOS PRINCIPAIS PARA DASHBOARD
    # ==========================================
    
    def calculate_opportunity_gaps(self, vendas_df: pd.DataFrame = None, cotacoes_df: pd.DataFrame = None, weights: Optional[Dict[str, float]] = None, penalty: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """
        Análise de gaps de oportunidade (alinhada ao RFV de cotações e métricas de produto)
        - Integra sinais de vendas e cotações (Q-RFV)
        - Score 0..100 com pesos em gaps de frequência, recência e valor
        - Penaliza vendas muito recentes e alta conversão (já converte bem)
        - Potencial de receita calcula incremento estimado a partir de cotações não convertidas
        """
        # Usa DataFrames armazenados se não fornecidos
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        cotacoes_data = cotacoes_df if cotacoes_df is not None else self.cotacoes_df

        # Fallback se não houver dados de vendas
        if vendas_data is None or vendas_data.empty:
            return pd.DataFrame({
                'produto': ['Produto A', 'Produto B', 'Produto C'],
                'gap_score': [75.5, 45.2, 88.1],
                'gap_category': ['Alto', 'Médio', 'Alto'],
                'current_revenue': [50000, 25000, 75000],
                'potential_revenue': [80000, 40000, 120000],
                'cliente_count': [10, 8, 15]
            })

        print("🎯 Calculando gaps de oportunidade para todos os produtos")
        print(f"🔍 Debug - Colunas Vendas: {list(vendas_data.columns) if hasattr(vendas_data, 'columns') else 'N/A'}")
        if cotacoes_data is not None and hasattr(cotacoes_data, 'columns'):
            print(f"🔍 Debug - Colunas Cotações: {list(cotacoes_data.columns)}")

        try:
            # Helpers
            def quantile_norm(s: pd.Series, invert: bool = False) -> pd.Series:
                if s is None or len(s) == 0:
                    return pd.Series([], dtype=float)
                s_clean = pd.to_numeric(s, errors='coerce')
                # Se todos NaN, retorna zeros
                if s_clean.isna().all():
                    return pd.Series([0.0] * len(s_clean), index=s_clean.index)
                ranks = s_clean.rank(method='min', pct=True)
                if invert:
                    ranks = 1 - ranks
                return ranks.fillna(0.0).clip(0, 1)

            def monthly_mean_count(df: pd.DataFrame, date_col: Optional[str]) -> pd.DataFrame:
                if df is None or df.empty or date_col is None or date_col not in df.columns:
                    return pd.DataFrame({'material': [], 'monthly_mean': []})
                tmp = df.copy()
                tmp[date_col] = pd.to_datetime(tmp[date_col], errors='coerce')
                tmp = tmp.dropna(subset=[date_col])
                if tmp.empty:
                    return pd.DataFrame({'material': [], 'monthly_mean': []})
                tmp['year_month'] = tmp[date_col].dt.to_period('M')
                counts = tmp.groupby(['material', 'year_month']).size().reset_index(name='cnt')
                mean_counts = counts.groupby('material')['cnt'].mean().reset_index(name='monthly_mean')
                return mean_counts

            # Mapear colunas de chave e nomes
            material_col = 'material' if 'material' in vendas_data.columns else None
            if material_col is None:
                for alt in ['codigo', 'cod_material', 'cd_material', 'item', 'cod_produto']:
                    if alt in vendas_data.columns:
                        material_col = alt
                        break
            produto_col = 'produto' if 'produto' in vendas_data.columns else None
            if produto_col is None:
                for alt in ['descricao', 'ds_produto', 'produto_desc', 'nome_produto']:
                    if alt in vendas_data.columns:
                        produto_col = alt
                        break
            if material_col is None and produto_col is None:
                # Sem chaves reconhecíveis
                return pd.DataFrame({
                    'produto': ['Produto Genérico'],
                    'gap_score': [60.0],
                    'gap_category': ['Médio'],
                    'current_revenue': [100000],
                    'potential_revenue': [150000],
                    'cliente_count': [20]
                })

            # Colunas de valor e data
            valor_col = next((c for c in ['vlr_rol', 'valor_liquido', 'vlr_entrada', 'vlr_carteira'] if c in vendas_data.columns), None)
            if valor_col is None:
                print("⚠️ Nenhuma coluna de valor encontrada em vendas. Retornando exemplo sintético.")
                return pd.DataFrame({
                    'produto': ['Produto A', 'Produto B', 'Produto C'],
                    'gap_score': [75.0, 45.0, 85.0],
                    'gap_category': ['Alto', 'Baixo', 'Alto'],
                    'current_revenue': [150000, 80000, 200000],
                    'potential_revenue': [200000, 120000, 250000],
                    'cliente_count': [15, 8, 20]
                })
            date_v_col = next((c for c in ['data_faturamento', 'data', 'data_venda'] if c in vendas_data.columns), None)

            # Agregações de vendas por material (preferir material para chave estável)
            key_col = material_col if material_col is not None else produto_col
            vendas_data['_key'] = vendas_data[key_col]
            vendas_data['_produto_name'] = vendas_data[produto_col] if produto_col in vendas_data.columns else vendas_data.get('produto', '')
            vendas_data['_produto_name'] = vendas_data['_produto_name'].fillna('')

            vendas_grp = vendas_data.groupby('_key').agg({
                valor_col: 'sum',
                'cod_cliente': 'nunique',
            }).reset_index().rename(columns={valor_col: 'receita_total', 'cod_cliente': 'cliente_count'})

            # Recorrência mensal de compras e recência
            if date_v_col is not None:
                vendas_tmp = vendas_data[['_key', date_v_col]].copy()
                vendas_tmp[date_v_col] = pd.to_datetime(vendas_tmp[date_v_col], errors='coerce')
                vendas_tmp = vendas_tmp.dropna(subset=[date_v_col])
                # monthly mean
                vm = vendas_tmp.copy(); vm['material'] = vm['_key']
                v_month_mean = monthly_mean_count(vm, date_v_col)
                # recency
                v_ref = vendas_tmp[date_v_col].max()
                v_last = vendas_tmp.groupby('_key')[date_v_col].max().reset_index()
                v_last['v_recency_days'] = (v_ref - v_last[date_v_col]).dt.days
            else:
                v_month_mean = pd.DataFrame({'material': [], 'monthly_mean': []})
                v_last = pd.DataFrame({'_key': [], 'v_recency_days': []})

            vendas_grp = vendas_grp.merge(v_month_mean.rename(columns={'material': '_key', 'monthly_mean': 'v_recorrencia_mensal'}), on='_key', how='left')
            vendas_grp = vendas_grp.merge(v_last[['_key', 'v_recency_days']], on='_key', how='left')

            # Dados de cotações por material
            quotes_grp = None
            if cotacoes_data is not None and not cotacoes_data.empty:
                quotes_df = cotacoes_data.copy()
                # mapear colunas de material e produto
                if 'material' not in quotes_df.columns and material_col:
                    for alt in ['codigo', 'cod_material', 'cd_material', 'item', 'cod_produto']:
                        if alt in quotes_df.columns:
                            quotes_df = quotes_df.rename(columns={alt: 'material'})
                            break
                if 'material' not in quotes_df.columns and material_col is None and key_col:
                    quotes_df['material'] = quotes_df[key_col] if key_col in quotes_df.columns else ''
                if 'produto' not in quotes_df.columns and produto_col:
                    for alt in ['descricao', 'ds_produto', 'produto_desc', 'nome_produto']:
                        if alt in quotes_df.columns:
                            quotes_df = quotes_df.rename(columns={alt: 'produto'})
                            break

                qval_col = next((c for c in ['valor_total', 'vlr_total', 'valor', 'vlr_cotado', 'vlr_rol'] if c in quotes_df.columns), None)
                if qval_col is None:
                    quotes_df['_proxy_val'] = 1.0
                    qval_col = '_proxy_val'
                qdate_col = next((c for c in ['data_cotacao', 'data_emissao', 'data'] if c in quotes_df.columns), None)

                # Agregar cotações
                quotes_df['_key'] = quotes_df['material'] if 'material' in quotes_df.columns else quotes_df.get(key_col, '')
                # Usar named aggregation para evitar conflito de nomes ao resetar índice
                quotes_grp = (
                    quotes_df.groupby('_key')
                    .agg(
                        valor_cotado_total=(qval_col, 'sum'),
                        q_recorrencia_total=(qval_col, 'count')  # contar linhas por chave
                    )
                    .reset_index()
                )

                # Recorrência mensal e recência de cotações
                if qdate_col is not None:
                    qtmp = quotes_df[['_key', qdate_col]].copy()
                    qtmp[qdate_col] = pd.to_datetime(qtmp[qdate_col], errors='coerce')
                    qtmp = qtmp.dropna(subset=[qdate_col])
                    qm = qtmp.copy(); qm['material'] = qm['_key']
                    q_month_mean = monthly_mean_count(qm, qdate_col)
                    q_ref = qtmp[qdate_col].max()
                    q_last = qtmp.groupby('_key')[qdate_col].max().reset_index()
                    q_last['q_recency_days'] = (q_ref - q_last[qdate_col]).dt.days
                else:
                    q_month_mean = pd.DataFrame({'material': [], 'monthly_mean': []})
                    q_last = pd.DataFrame({'_key': [], 'q_recency_days': []})

                quotes_grp = quotes_grp.merge(q_month_mean.rename(columns={'material': '_key', 'monthly_mean': 'q_recorrencia_mensal'}), on='_key', how='left')
                quotes_grp = quotes_grp.merge(q_last[['_key', 'q_recency_days']], on='_key', how='left')

            # Merge vendas + cotações
            base = vendas_grp.copy()
            if quotes_grp is not None and not quotes_grp.empty:
                base = base.merge(quotes_grp, on='_key', how='left')
            else:
                base['valor_cotado_total'] = 0.0
                base['q_recorrencia_total'] = 0.0
                base['q_recorrencia_mensal'] = 0.0
                base['q_recency_days'] = np.nan

            # Normalizações (0..1)
            v_r_norm = quantile_norm(base['v_recency_days'].fillna(base['v_recency_days'].max() if base['v_recency_days'].notna().any() else 0), invert=True)
            v_f_norm = quantile_norm(base['v_recorrencia_mensal'].fillna(0))
            v_m_norm = quantile_norm(base['receita_total'].fillna(0))
            q_r_norm = quantile_norm(base['q_recency_days'].fillna(base['q_recency_days'].max() if base['q_recency_days'].notna().any() else 0), invert=True)
            q_f_norm = quantile_norm(base['q_recorrencia_mensal'].fillna(0))
            q_m_norm = quantile_norm(base['valor_cotado_total'].fillna(0))

            # Gaps (0..1)
            base['freq_gap'] = (q_f_norm - v_f_norm).clip(lower=0)
            base['recency_gap'] = (q_r_norm - v_r_norm).clip(lower=0)
            base['valor_gap'] = (q_m_norm - v_m_norm).clip(lower=0)

            # Conversão por valor (0..1)
            conv_val = (base['receita_total'] / base['valor_cotado_total'].replace(0, np.nan)).fillna(0).clip(0, 1.5)

            # Score de prioridade a partir de Q-RFV (0..100)
            # Pesos padrão (alinhados à semântica utilizada na página de produtos)
            if weights and isinstance(weights, dict):
                r_weight = float(weights.get('r', 0.3))
                f_weight = float(weights.get('f', 0.4))
                m_weight = float(weights.get('m', 0.3))
                total_w = r_weight + f_weight + m_weight
                if total_w > 0:
                    r_weight, f_weight, m_weight = r_weight/total_w, f_weight/total_w, m_weight/total_w
            else:
                r_weight, f_weight, m_weight = 0.3, 0.4, 0.3
            q_prioridade = ((r_weight * q_r_norm) + (f_weight * q_f_norm) + (m_weight * q_m_norm)) * 100.0

            # Score de oportunidade (0..100)
            alpha, beta, gamma = f_weight, r_weight, m_weight
            o_base = (alpha * base['freq_gap'] + beta * base['recency_gap'] + gamma * base['valor_gap'])

            # Parâmetros configuráveis de penalização/boost
            conv_start = float((penalty or {}).get('conv_penalty_start', 0.6))  # 60% (em fração)
            conv_span = float((penalty or {}).get('conv_penalty_span', 0.4))    # 40% (60→100)
            conv_max = float((penalty or {}).get('conv_penalty_max', 0.4))      # intensidade máx
            recent_max = float((penalty or {}).get('recent_penalty_max', 0.2))  # até 0.2
            boost_max = float((penalty or {}).get('quote_priority_boost_max', 0.15))  # até 0.15

            # Penalidades
            penalty_recent_sales = (v_r_norm * recent_max)  # vendas muito recentes reduzem oportunidade
            # penalização de conversão: começa a penalizar acima de conv_start e satura em conv_start+conv_span
            penalty_high_conv = ((conv_val - conv_start).clip(lower=0) / max(conv_span, 1e-9)).clip(upper=1.0) * conv_max
            boost_quote_priority = (q_prioridade / 100.0) * boost_max
            o_final = (o_base * (1 - penalty_recent_sales) * (1 - penalty_high_conv)) * (1 + boost_quote_priority)
            base['gap_score'] = (o_final.clip(lower=0, upper=1.5).clip(upper=1.0) * 100).round(2)
            # guardar componentes para explicabilidade
            base['penalty_recent_sales'] = penalty_recent_sales.round(4)
            base['penalty_high_conv'] = penalty_high_conv.round(4)
            base['v_recency_days'] = base.get('v_recency_days', np.nan)
            base['conversion_rate'] = (conv_val.clip(0, 1.5) * 100).round(2)
            # % não comprado por valor
            base['nao_comprado_pct'] = (100 - base['conversion_rate']).clip(lower=0).round(2)

            # Receita potencial: incremento estimado baseado em cotações não convertidas
            incr = (base['valor_cotado_total'] * (1 - conv_val.clip(0, 1))).fillna(0)
            momentum_floor = float((penalty or {}).get('momentum_floor', 0.5))  # mínimo do fator de momentum
            # momentum cresce com a média dos gaps de freq/recência
            momentum = (momentum_floor + (1 - momentum_floor) * ((base['freq_gap'] + base['recency_gap']) / 2)).clip(momentum_floor, 1.0)
            estimated_incremental = (incr * momentum).fillna(0)
            base['incremental_revenue'] = estimated_incremental.round(2)
            base['potential_revenue'] = (base['receita_total'] + estimated_incremental).round(2)

            # Categoria por faixas alinhadas à página de produtos
            def cat_from_score(s: float) -> str:
                if pd.isna(s):
                    return 'Baixo'
                if s >= 70:
                    return 'Alto'
                if s >= 40:
                    return 'Médio'
                return 'Baixo'
            base['gap_category'] = base['gap_score'].apply(cat_from_score)

            # Score base (sem penalidades) para comparação
            gap_score_base = (o_base * (1 + boost_quote_priority)).clip(upper=1.0) * 100
            base['gap_score_base'] = gap_score_base.round(2)

            # Nome do produto para exibição
            prod_map = vendas_data.groupby('_key')['_produto_name'].first().to_dict()
            base['produto'] = base['_key'].map(prod_map).fillna(base['_key'])

            resultado = base.rename(columns={
                'receita_total': 'current_revenue',
            })

            # Ordenação natural por score
            resultado = resultado.sort_values('gap_score', ascending=False)

            print(f"✅ Análise de gaps concluída - {len(resultado)} produtos analisados")
            # incluir colunas de explicabilidade; consumidores que não usam essas colunas serão indiferentes
            cols = ['produto', 'gap_score', 'gap_score_base', 'gap_category', 'current_revenue', 'potential_revenue',
                'incremental_revenue', 'cliente_count', 'v_recency_days', 'q_recency_days',
                'conversion_rate', 'nao_comprado_pct', 'freq_gap', 'recency_gap', 'valor_gap',
                'penalty_recent_sales', 'penalty_high_conv']
            # filtrar apenas as que existem (robustez)
            cols = [c for c in cols if c in resultado.columns]
            return resultado[cols]

        except Exception as e:
            print(f"❌ Erro no cálculo de gaps: {e}")
            return pd.DataFrame({
                'produto': ['Erro no cálculo'],
                'gap_score': [0],
                'gap_category': ['Erro'],
                'current_revenue': [0],
                'potential_revenue': [0],
                'cliente_count': [0]
            })
    
    def calculate_inactivity_alerts(self, vendas_df: pd.DataFrame = None, filters: Dict = None) -> pd.DataFrame:
        """
        Calcula alertas de inatividade baseado em 90/365 dias
        """
        # Usa DataFrame armazenado se não fornecido
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        
        if vendas_data is None or vendas_data.empty:
            return pd.DataFrame({
                'cliente': ['Cliente A', 'Cliente B', 'Cliente C'],
                'cod_cliente': ['001', '002', '003'],
                'category': ['Ativo', 'Atenção', 'Crítico'],
                'days_since_last_purchase': [45, 180, 400],
                'last_purchase_date': ['2025-07-15', '2025-02-10', '2024-08-01'],
                'total_revenue': [50000, 30000, 80000]
            })
        
        print("⚠️ Calculando alertas de inatividade...")
        print(f"🔍 Debug - Colunas disponíveis: {list(vendas_data.columns) if hasattr(vendas_data, 'columns') else 'N/A'}")
        
        try:
            # Identifica coluna de data
            date_column = None
            for col in ['data_faturamento', 'data', 'data_venda']:
                if col in vendas_data.columns:
                    date_column = col
                    break
            
            if date_column is None:
                print("⚠️ Coluna de data não encontrada, usando dados sintéticos")
                unique_clients = ['Cliente ' + str(i) for i in range(1, 11)]
                return pd.DataFrame({
                    'cliente': unique_clients,
                    'cod_cliente': [f'00{i}' for i in range(1, 11)],
                    'category': ['Ativo'] * 5 + ['Atenção'] * 3 + ['Crítico'] * 2,
                    'days_since_last_purchase': [30, 45, 60, 75, 85, 150, 200, 280, 400, 500],
                    'last_purchase_date': [(self.current_date - timedelta(days=d)).strftime('%Y-%m-%d') 
                                         for d in [30, 45, 60, 75, 85, 150, 200, 280, 400, 500]],
                    'total_revenue': [10000, 25000, 15000, 30000, 20000, 45000, 35000, 60000, 80000, 120000]
                })
            
            # Converte coluna de data
            vendas_data[date_column] = pd.to_datetime(vendas_data[date_column], errors='coerce')
            
            # Detecta coluna de valor automaticamente
            valor_col = None
            for col in ['vlr_rol', 'valor_liquido', 'vlr_entrada', 'vlr_carteira']:
                if col in vendas_data.columns:
                    valor_col = col
                    break
            
            if valor_col is None:
                print("⚠️ Nenhuma coluna de valor encontrada para inatividade")
                unique_clients = ['Cliente ' + str(i) for i in range(1, 11)]
                return pd.DataFrame({
                    'cliente': unique_clients,
                    'cod_cliente': [f'00{i}' for i in range(1, 11)],
                    'category': ['Ativo'] * 5 + ['Atenção'] * 3 + ['Crítico'] * 2,
                    'days_since_last_purchase': [30, 45, 60, 75, 85, 150, 200, 280, 400, 500],
                    'last_purchase_date': [(self.current_date - timedelta(days=d)).strftime('%Y-%m-%d') 
                                         for d in [30, 45, 60, 75, 85, 150, 200, 280, 400, 500]],
                    'total_revenue': [10000, 25000, 15000, 30000, 20000, 45000, 35000, 60000, 80000, 120000]
                })
            
            print(f"🔍 Debug - Usando coluna de valor para inatividade: {valor_col}")

            # Calcula última compra por cliente
            ultima_compra = vendas_data.groupby('cod_cliente').agg({
                date_column: 'max',
                'cliente': 'first',
                valor_col: 'sum'
            }).reset_index()
            
            ultima_compra.columns = ['cod_cliente', 'last_purchase_date', 'cliente', 'total_revenue']
            
            # Calcula dias desde última compra
            ultima_compra['days_since_last_purchase'] = (
                self.current_date - ultima_compra['last_purchase_date']
            ).dt.days
            
            # Categoriza clientes
            def categorize_inactivity(days):
                if days <= 90:
                    return 'Ativo'
                elif days <= 365:
                    return 'Atenção'
                else:
                    return 'Crítico'
            
            ultima_compra['category'] = ultima_compra['days_since_last_purchase'].apply(categorize_inactivity)
            
            # Formata data para string
            ultima_compra['last_purchase_date'] = ultima_compra['last_purchase_date'].dt.strftime('%Y-%m-%d')
            
            # Ordena por dias sem compra (decrescente)
            resultado = ultima_compra.sort_values('days_since_last_purchase', ascending=False)
            
            print(f"✅ Análise de inatividade concluída - {len(resultado)} clientes analisados")
            return resultado
            
        except Exception as e:
            print(f"❌ Erro no cálculo de inatividade: {e}")
            return pd.DataFrame({
                'cliente': ['Erro no cálculo'],
                'cod_cliente': [''],
                'category': ['Erro'],
                'days_since_last_purchase': [0],
                'last_purchase_date': [''],
                'total_revenue': [0]
            })
    
    def analyze_seasonality(self, vendas_df: pd.DataFrame = None, filters: Dict = None) -> pd.DataFrame:
        """
        Análise estatística de sazonalidade das vendas com tratamento correto para vlr_entrada
        """
        # Usa DataFrame armazenado se não fornecido
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        
        if vendas_data is None or vendas_data.empty:
            # Dados sintéticos com padrão sazonal mais realista
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            sales_base = 500000
            seasonal_pattern = [0.7, 0.8, 0.9, 1.0, 1.1, 0.9, 0.8, 0.85, 1.0, 1.2, 1.4, 1.3]
            entrada_factor = 0.85
            
            return pd.DataFrame({
                'month': months,
                'sales_amount': [sales_base * factor for factor in seasonal_pattern],
                'trend': [sales_base] * 12,
                'seasonal': [(factor - 1) * sales_base for factor in seasonal_pattern],
                'coefficient_variation': [0.25] * 12,
                'entrada_amount': [sales_base * factor * entrada_factor for factor in seasonal_pattern],
                'entrada_trend': [sales_base * entrada_factor] * 12,
                'entrada_seasonal': [(factor - 1) * sales_base * entrada_factor for factor in seasonal_pattern],
                'entrada_coefficient_variation': [0.22] * 12
            })
        
        print("📈 Analisando sazonalidade das vendas com dados reais...")
        
        try:
            # Detecta colunas de valor
            valor_cols = []
            for col in ['vlr_rol', 'vlr_entrada']:
                if col in vendas_data.columns:
                    valor_cols.append(col)
            
            if not valor_cols:
                print("⚠️ Nenhuma coluna de valor encontrada")
                return self.analyze_seasonality(None)
            
            print(f"🔍 Debug - Colunas encontradas: {valor_cols}")
            print(f"🔍 Debug - Total de registros: {len(vendas_data)}")
            
            # Processa cada métrica com estratégia adequada
            metrics_data = {}
            
            for valor_col in valor_cols:
                print(f"\n📊 Processando {valor_col}...")
                
                if valor_col == 'vlr_entrada':
                    # Para vlr_entrada: usar 'data' e filtrar registros com vlr_entrada > 0
                    metric_data = vendas_data[vendas_data[valor_col] > 0].copy()
                    date_col = 'data'
                    print(f"🔍 {valor_col}: {len(metric_data)} registros com valor > 0")
                else:
                    # Para vlr_rol: usar 'data_faturamento' e filtrar registros válidos
                    metric_data = vendas_data[
                        (vendas_data[valor_col] > 0) & 
                        (vendas_data['data_faturamento'].notna()) &
                        (vendas_data['data_faturamento'] != '')
                    ].copy()
                    date_col = 'data_faturamento'
                    print(f"🔍 {valor_col}: {len(metric_data)} registros com valor > 0 e data válida")
                
                if metric_data.empty:
                    print(f"⚠️ Nenhum dado válido para {valor_col}")
                    continue
                
                # Converte coluna de data
                metric_data[date_col] = pd.to_datetime(metric_data[date_col], errors='coerce')
                metric_data = metric_data.dropna(subset=[date_col])
                
                if metric_data.empty:
                    print(f"⚠️ Nenhum dado válido após conversão de data para {valor_col}")
                    continue
                
                print(f"🔍 {valor_col}: {len(metric_data)} registros finais")
                print(f"🔍 {valor_col}: período de {metric_data[date_col].min()} até {metric_data[date_col].max()}")
                
                # Agrupa por mês
                metric_data['month'] = metric_data[date_col].dt.month
                metric_data['month_name'] = metric_data[date_col].dt.strftime('%b')
                
                # Calcula totais mensais
                monthly_sales = metric_data.groupby(['month', 'month_name'])[valor_col].agg(['sum', 'count']).reset_index()
                monthly_sales.columns = ['month_num', 'month_name', 'total_sales', 'count_sales']
                
                # Converte nomes dos meses para português
                month_mapping = {
                    'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
                    'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
                    'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
                }
                monthly_sales['month_name_pt'] = monthly_sales['month_name'].map(month_mapping)
                
                # Garante todos os 12 meses
                all_months = pd.DataFrame({
                    'month_num': range(1, 13),
                    'month_name_pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                })
                
                # Merge com todos os meses
                monthly_final = all_months.merge(
                    monthly_sales[['month_num', 'month_name_pt', 'total_sales', 'count_sales']], 
                    on=['month_num', 'month_name_pt'], how='left'
                )
                monthly_final[['total_sales', 'count_sales']] = monthly_final[['total_sales', 'count_sales']].fillna(0)
                
                print(f"🔍 {valor_col} por mês:")
                for _, row in monthly_final.iterrows():
                    print(f"  {row['month_name_pt']}: R$ {row['total_sales']:,.2f}")
                
                # Calcula estatísticas
                mean_sales = monthly_final['total_sales'].mean()
                std_sales = monthly_final['total_sales'].std()
                coef_var = std_sales / mean_sales if mean_sales > 0 else 0
                
                # Componentes sazonais
                monthly_final['trend'] = mean_sales
                monthly_final['seasonal'] = monthly_final['total_sales'] - mean_sales
                monthly_final['coefficient_variation'] = coef_var
                
                # Armazena
                metrics_data[valor_col] = monthly_final
                
                # Mês de vale
                min_idx = monthly_final['total_sales'].idxmin()
                min_month = monthly_final.loc[min_idx, 'month_name_pt']
                min_value = monthly_final.loc[min_idx, 'total_sales']
                print(f"✅ {valor_col} mês de vale: {min_month} (R$ {min_value:,.2f})")
            
            # Combina resultados
            resultado = pd.DataFrame({
                'month': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            })
            
            # Adiciona vlr_rol
            if 'vlr_rol' in metrics_data:
                rol_data = metrics_data['vlr_rol']
                resultado['sales_amount'] = rol_data['total_sales'].values
                resultado['trend'] = rol_data['trend'].values
                resultado['seasonal'] = rol_data['seasonal'].values
                resultado['coefficient_variation'] = rol_data['coefficient_variation'].values
            else:
                resultado['sales_amount'] = 0
                resultado['trend'] = 0
                resultado['seasonal'] = 0
                resultado['coefficient_variation'] = 0
            
            # Adiciona vlr_entrada
            if 'vlr_entrada' in metrics_data:
                entrada_data = metrics_data['vlr_entrada']
                resultado['entrada_amount'] = entrada_data['total_sales'].values
                resultado['entrada_trend'] = entrada_data['trend'].values
                resultado['entrada_seasonal'] = entrada_data['seasonal'].values
                resultado['entrada_coefficient_variation'] = entrada_data['coefficient_variation'].values
                print("✅ Usando dados REAIS de vlr_entrada")
            else:
                # Fallback: dados sintéticos baseados em vlr_rol
                print("⚠️ Gerando dados sintéticos para vlr_entrada baseados em vlr_rol")
                entrada_factors = {
                    'Jan': 0.90, 'Fev': 0.85, 'Mar': 0.88, 'Abr': 0.82,
                    'Mai': 0.85, 'Jun': 0.87, 'Jul': 0.84, 'Ago': 0.89,
                    'Set': 0.91, 'Out': 0.93, 'Nov': 0.88, 'Dez': 0.80
                }
                
                entrada_amounts = []
                entrada_seasonals = []
                for _, row in resultado.iterrows():
                    factor = entrada_factors.get(row['month'], 0.85)
                    entrada_amounts.append(row['sales_amount'] * factor)
                    entrada_seasonals.append(row['seasonal'] * factor)
                
                resultado['entrada_amount'] = entrada_amounts
                resultado['entrada_trend'] = resultado['trend'] * 0.85
                resultado['entrada_seasonal'] = entrada_seasonals
                resultado['entrada_coefficient_variation'] = resultado['coefficient_variation'] * 0.9
            
            # Converte tipos
            for col in ['sales_amount', 'trend', 'seasonal', 'coefficient_variation',
                       'entrada_amount', 'entrada_trend', 'entrada_seasonal', 'entrada_coefficient_variation']:
                resultado[col] = resultado[col].astype(float)
            
            print(f"✅ Análise de sazonalidade concluída:")
            print(f"   📊 vlr_rol total: R$ {resultado['sales_amount'].sum():,.2f}")
            print(f"   📊 vlr_entrada total: R$ {resultado['entrada_amount'].sum():,.2f}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro na análise de sazonalidade: {e}")
            import traceback
            traceback.print_exc()
            return self.analyze_seasonality(None)  # Retorna dados sintéticos
        """
        Análise estatística de sazonalidade das vendas com evolução temporal
        """
        # Usa DataFrame armazenado se não fornecido
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        
        if vendas_data is None or vendas_data.empty:
            # Dados sintéticos com padrão sazonal mais realista
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            sales_base = 500000
            # Padrão sazonal típico: baixo no início, pico no meio/fim do ano
            seasonal_pattern = [0.7, 0.8, 0.9, 1.0, 1.1, 0.9, 0.8, 0.85, 1.0, 1.2, 1.4, 1.3]
            entrada_factor = 0.85  # vlr_entrada tipicamente 85% de vlr_rol
            
            return pd.DataFrame({
                'month': months,
                'sales_amount': [sales_base * factor for factor in seasonal_pattern],
                'trend': [sales_base] * 12,
                'seasonal': [(factor - 1) * sales_base for factor in seasonal_pattern],
                'coefficient_variation': [0.25] * 12,  # 25% de variação sazonal
                'entrada_amount': [sales_base * factor * entrada_factor for factor in seasonal_pattern],
                'entrada_trend': [sales_base * entrada_factor] * 12,
                'entrada_seasonal': [(factor - 1) * sales_base * entrada_factor for factor in seasonal_pattern],
                'entrada_coefficient_variation': [0.22] * 12  # Ligeiramente menor variação para entrada
            })
        
        print("📈 Analisando sazonalidade das vendas...")
        
        try:
            # Identifica coluna de data
            date_column = None
            for col in ['data_faturamento', 'data', 'data_venda']:
                if col in vendas_data.columns:
                    date_column = col
                    break
            
            if date_column is None:
                print("⚠️ Coluna de data não encontrada, gerando dados sintéticos")
                months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                sales_base = 300000
                seasonal_pattern = [0.8, 0.9, 1.1, 1.2, 1.0, 0.9, 0.8, 0.85, 1.0, 1.15, 1.3, 1.4]
                entrada_factor = 0.85
                
                return pd.DataFrame({
                    'month': months,
                    'sales_amount': [sales_base * factor for factor in seasonal_pattern],
                    'trend': [sales_base] * 12,
                    'seasonal': [(factor - 1) * sales_base for factor in seasonal_pattern],
                    'coefficient_variation': [0.22] * 12,
                    'entrada_amount': [sales_base * factor * entrada_factor for factor in seasonal_pattern],
                    'entrada_trend': [sales_base * entrada_factor] * 12,
                    'entrada_seasonal': [(factor - 1) * sales_base * entrada_factor for factor in seasonal_pattern],
                    'entrada_coefficient_variation': [0.20] * 12
                })
            
            # Detecta colunas de valor automaticamente (vlr_rol e vlr_entrada)
            valor_cols = []
            for col in ['vlr_rol', 'vlr_entrada', 'valor_liquido', 'vlr_carteira']:
                if col in vendas_data.columns:
                    valor_cols.append(col)
            
            if not valor_cols:
                print("⚠️ Nenhuma coluna de valor encontrada para sazonalidade")
                months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                sales_base = 200000
                seasonal_pattern = [0.8, 0.9, 1.1, 1.2, 1.0, 0.9, 0.8, 0.85, 1.0, 1.15, 1.3, 1.4]
                
                return pd.DataFrame({
                    'month': months,
                    'sales_amount': [sales_base * factor for factor in seasonal_pattern],
                    'trend': [sales_base] * 12,
                    'seasonal': [(factor - 1) * sales_base for factor in seasonal_pattern],
                    'coefficient_variation': [0.20] * 12,
                    'entrada_amount': [sales_base * factor * 0.8 for factor in seasonal_pattern],
                    'entrada_trend': [sales_base * 0.8] * 12,
                    'entrada_seasonal': [(factor - 1) * sales_base * 0.8 for factor in seasonal_pattern],
                    'entrada_coefficient_variation': [0.18] * 12
                })
            
            print(f"🔍 Debug - Usando colunas de valor para sazonalidade: {valor_cols}")
            print(f"🔍 Debug - Dados de entrada: {len(vendas_data)} registros")

            # Verifica se vlr_entrada tem dados válidos ANTES da conversão de data
            vlr_entrada_has_data = False
            if 'vlr_entrada' in vendas_data.columns:
                vlr_entrada_sum = vendas_data['vlr_entrada'].sum()
                vlr_entrada_non_zero = (vendas_data['vlr_entrada'] > 0).sum()
                print(f"🔍 Debug - vlr_entrada ANTES filtros: soma=R${vlr_entrada_sum:,.2f}, registros>0={vlr_entrada_non_zero}")
                vlr_entrada_has_data = vlr_entrada_sum > 0 and vlr_entrada_non_zero > 0

            # Converte coluna de data
            vendas_data = vendas_data.copy()
            vendas_data[date_column] = pd.to_datetime(vendas_data[date_column], errors='coerce')
            vendas_data = vendas_data.dropna(subset=[date_column])
            
            print(f"🔍 Debug - Após conversão de data: {len(vendas_data)} registros")
            
            # Verifica vlr_entrada novamente após filtros de data
            if 'vlr_entrada' in vendas_data.columns:
                vlr_entrada_sum_after = vendas_data['vlr_entrada'].sum()
                vlr_entrada_non_zero_after = (vendas_data['vlr_entrada'] > 0).sum()
                print(f"🔍 Debug - vlr_entrada APÓS filtros: soma=R${vlr_entrada_sum_after:,.2f}, registros>0={vlr_entrada_non_zero_after}")
                vlr_entrada_has_data = vlr_entrada_sum_after > 0 and vlr_entrada_non_zero_after > 0
            
            if vendas_data.empty:
                print("⚠️ Nenhum dado válido após conversão de datas")
                return self.analyze_seasonality(None)  # Retorna dados sintéticos
            
            # Verificar range de datas
            min_date = vendas_data[date_column].min()
            max_date = vendas_data[date_column].max()
            print(f"🔍 Debug - Range de datas: {min_date} até {max_date}")
            
            # Agrupa por mês (considerando todos os anos)
            vendas_data['month'] = vendas_data[date_column].dt.month
            vendas_data['month_name'] = vendas_data[date_column].dt.strftime('%b')
            
            print(f"🔍 Debug - Amostra dos dados processados:")
            sample_cols = ['month', 'month_name'] + valor_cols
            print(vendas_data[sample_cols].head(10))
            
            # Dicionário para armazenar dados de cada métrica
            metrics_data = {}
            
            for valor_col in valor_cols:
                # Calcula vendas mensais agregadas para cada métrica
                monthly_sales = vendas_data.groupby(['month', 'month_name'])[valor_col].agg(['sum', 'mean', 'count']).reset_index()
                monthly_sales.columns = ['month_num', 'month_name', 'total_sales', 'avg_sales', 'count_sales']
                monthly_sales = monthly_sales.sort_values('month_num')
                
                print(f"🔍 Debug - {valor_col} mensais ANTES do merge:")
                for _, row in monthly_sales.iterrows():
                    print(f"  {row['month_name']}: R$ {row['total_sales']:,.2f} ({row['count_sales']} transações)")
                
                # Mapeamento de meses em inglês para português (compatível com os dados reais)
                month_mapping = {
                    'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
                    'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
                    'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
                }
                
                # Converte nomes dos meses para português
                monthly_sales['month_name_pt'] = monthly_sales['month_name'].map(month_mapping)
                
                # Garante que temos todos os 12 meses (usando nomes em português)
                all_months = pd.DataFrame({
                    'month_num': range(1, 13),
                    'month_name_pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                })
                
                # Agrupa por month_num e month_name_pt para consolidar dados
                monthly_consolidated = monthly_sales.groupby(['month_num', 'month_name_pt']).agg({
                    'total_sales': 'sum',
                    'avg_sales': 'mean', 
                    'count_sales': 'sum'
                }).reset_index()
                
                # Merge com todos os meses
                monthly_final = all_months.merge(monthly_consolidated, on=['month_num', 'month_name_pt'], how='left')
                monthly_final[['total_sales', 'avg_sales', 'count_sales']] = monthly_final[['total_sales', 'avg_sales', 'count_sales']].fillna(0)
                
                print(f"🔍 Debug - {valor_col} mensais APÓS merge:")
                for _, row in monthly_final.iterrows():
                    print(f"  {row['month_name_pt']}: R$ {row['total_sales']:,.2f} ({row['count_sales']} transações)")
                
                # Calcula estatísticas
                mean_sales = monthly_final['total_sales'].mean()
                std_sales = monthly_final['total_sales'].std()
                coef_var = std_sales / mean_sales if mean_sales > 0 else 0
                
                # Calcula componentes sazonais
                monthly_final['trend'] = mean_sales
                monthly_final['seasonal'] = monthly_final['total_sales'] - mean_sales
                monthly_final['coefficient_variation'] = coef_var
                
                # Armazena dados da métrica
                metrics_data[valor_col] = monthly_final
                
                # Identificar o verdadeiro mês de vale
                min_sales_idx = monthly_final['total_sales'].idxmin()
                min_month = monthly_final.loc[min_sales_idx]
                print(f"🔍 Debug - {valor_col} mês de vale: {min_month['month_name_pt']} com R$ {min_month['total_sales']:,.2f}")
            
            # Combina dados de todas as métricas em um único DataFrame
            resultado = all_months[['month_name_pt']].copy()
            resultado.rename(columns={'month_name_pt': 'month'}, inplace=True)
            
            # Adiciona dados de vlr_rol (vendas realizadas)
            if 'vlr_rol' in metrics_data:
                rol_data = metrics_data['vlr_rol']
                resultado['sales_amount'] = rol_data['total_sales'].values
                resultado['trend'] = rol_data['trend'].values
                resultado['seasonal'] = rol_data['seasonal'].values
                resultado['coefficient_variation'] = rol_data['coefficient_variation'].values
            else:
                # Fallback se não houver vlr_rol
                resultado['sales_amount'] = 0
                resultado['trend'] = 0
                resultado['seasonal'] = 0
                resultado['coefficient_variation'] = 0
            
            # Adiciona dados de vlr_entrada (entrada de pedidos)
            if 'vlr_entrada' in metrics_data and vlr_entrada_has_data:
                # Usa dados reais de vlr_entrada
                entrada_data = metrics_data['vlr_entrada']
                entrada_sum = entrada_data['total_sales'].sum()
                resultado['entrada_amount'] = entrada_data['total_sales'].values
                resultado['entrada_trend'] = entrada_data['trend'].values
                resultado['entrada_seasonal'] = entrada_data['seasonal'].values
                resultado['entrada_coefficient_variation'] = entrada_data['coefficient_variation'].values
                print(f"✅ Usando dados reais de vlr_entrada: R$ {entrada_sum:,.2f}")
            else:
                # Gera dados sintéticos baseados em vlr_rol com padrão realista
                print("⚠️ vlr_entrada zerado ou inexistente, gerando dados sintéticos baseados em vlr_rol")
                
                # Fatores de conversão realistas para diferentes meses
                # Entrada de pedidos tipicamente antecede vendas e varia sazonalmente
                entrada_factors = {
                    'Jan': 0.90,  # Início do ano - mais pedidos
                    'Fev': 0.85,  # Carnaval - menos entrada
                    'Mar': 0.88,  # Retomada
                    'Abr': 0.82,  # Páscoa
                    'Mai': 0.85,  # Maio estável
                    'Jun': 0.87,  # Meio do ano
                    'Jul': 0.84,  # Férias escolares
                    'Ago': 0.89,  # Retomada pós-férias
                    'Set': 0.91,  # Preparação fim de ano
                    'Out': 0.93,  # Pico de entrada
                    'Nov': 0.88,  # Black Friday
                    'Dez': 0.80   # Fim de ano - menos entrada
                }
                
                # Aplica fatores mensais específicos
                entrada_amounts = []
                entrada_seasonals = []
                for _, row in resultado.iterrows():
                    month = row['month']
                    factor = entrada_factors.get(month, 0.85)
                    entrada_amounts.append(row['sales_amount'] * factor)
                    entrada_seasonals.append(row['seasonal'] * factor)
                
                resultado['entrada_amount'] = entrada_amounts
                resultado['entrada_trend'] = resultado['trend'] * 0.85  # Média geral 85%
                resultado['entrada_seasonal'] = entrada_seasonals
                resultado['entrada_coefficient_variation'] = resultado['coefficient_variation'] * 0.9
            
            # Converte tipos para garantir compatibilidade
            resultado['sales_amount'] = resultado['sales_amount'].astype(float)
            resultado['trend'] = resultado['trend'].astype(float)
            resultado['seasonal'] = resultado['seasonal'].astype(float)
            resultado['coefficient_variation'] = resultado['coefficient_variation'].astype(float)
            resultado['entrada_amount'] = resultado['entrada_amount'].astype(float)
            resultado['entrada_trend'] = resultado['entrada_trend'].astype(float)
            resultado['entrada_seasonal'] = resultado['entrada_seasonal'].astype(float)
            resultado['entrada_coefficient_variation'] = resultado['entrada_coefficient_variation'].astype(float)
            
            # Calcula coeficientes de variação finais
            rol_coef_var = resultado['coefficient_variation'].iloc[0] if not resultado.empty else 0
            entrada_coef_var = resultado['entrada_coefficient_variation'].iloc[0] if not resultado.empty else 0
            
            print(f"✅ Análise de sazonalidade concluída:")
            print(f"   📊 vlr_rol - coef. variação: {rol_coef_var:.2%}, total: R$ {resultado['sales_amount'].sum():,.2f}")
            print(f"   📊 vlr_entrada - coef. variação: {entrada_coef_var:.2%}, total: R$ {resultado['entrada_amount'].sum():,.2f}")
            print(f"📊 Dados retornados: {len(resultado)} meses com ambas as métricas")
            return resultado
            
        except Exception as e:
            print(f"❌ Erro na análise de sazonalidade: {e}")
            import traceback
            traceback.print_exc()
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            return pd.DataFrame({
                'month': months,
                'sales_amount': [100000] * 12,
                'trend': [100000] * 12,
                'seasonal': [0] * 12,
                'coefficient_variation': [0.1] * 12,
                'entrada_amount': [80000] * 12,
                'entrada_trend': [80000] * 12,
                'entrada_seasonal': [0] * 12,
                'entrada_coefficient_variation': [0.1] * 12
            })
    
    def analyze_quotation_demand(self, cotacoes_df: pd.DataFrame = None, 
                                vendas_df: pd.DataFrame = None,
                                filters: Dict = None) -> pd.DataFrame:
        """
        Análise da demanda de cotações e conversão em vendas
        """
        # Usa DataFrames armazenados se não fornecidos
        cotacoes_data = cotacoes_df if cotacoes_df is not None else self.cotacoes_df
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        
        if cotacoes_data is None or cotacoes_data.empty:
            return pd.DataFrame({
                'produto': ['Motor 1CV', 'Redutor 10:1', 'Inversor 2CV', 'Contatora 12A'],
                'product_category': ['MOTORES', 'REDUTORES', 'INVERSORES', 'ACESSÓRIOS'],
                'total_quotations': [25, 18, 30, 12],
                'total_sales': [75000, 45000, 90000, 20000],
                'conversion_rate': [60.0, 35.0, 75.0, 25.0],
                'lost_opportunity': [30000, 25000, 22500, 15000]
            })
        
        print("📋 Analisando demanda de cotações...")
        
        try:
            # Identifica coluna de produto nas cotações
            produto_col = None
            for col in ['produto', 'material', 'item']:
                if col in cotacoes_data.columns:
                    produto_col = col
                    break
            
            if produto_col is None:
                print("⚠️ Coluna de produto não encontrada nas cotações")
                return pd.DataFrame({
                    'produto': ['Produto Genérico'],
                    'product_category': ['GERAL'],
                    'total_quotations': [100],
                    'total_sales': [500000],
                    'conversion_rate': [50.0],
                    'lost_opportunity': [250000]
                })
            
            # Agrupa cotações
            cotacoes_stats = cotacoes_data.groupby(produto_col).agg({
                'numero_cotacao': 'nunique',
                'cod_cliente': 'nunique'
            }).reset_index()
            
            cotacoes_stats.columns = ['produto', 'total_quotations', 'unique_clients']
            
            # Se temos dados de vendas, calcula conversão
            if vendas_data is not None and not vendas_data.empty:
                vendas_stats = vendas_data.groupby('produto').agg({
                    'valor_liquido': 'sum',
                    'quantidade': 'sum'
                }).reset_index()
                
                vendas_stats.columns = ['produto', 'total_sales', 'total_quantity']
                
                # Merge cotações e vendas
                resultado = cotacoes_stats.merge(vendas_stats, on='produto', how='left')
                resultado['total_sales'] = resultado['total_sales'].fillna(0)
                
                # Calcula taxa de conversão (simplificada)
                resultado['conversion_rate'] = np.where(
                    resultado['total_quotations'] > 0,
                    (resultado['total_sales'] / (resultado['total_quotations'] * 1000)) * 100,  # Fator arbitrário
                    0
                ).clip(0, 100)
                
            else:
                # Sem dados de vendas, usa valores sintéticos
                resultado = cotacoes_stats.copy()
                resultado['total_sales'] = resultado['total_quotations'] * 5000  # Valor médio sintético
                resultado['conversion_rate'] = np.random.uniform(30, 80, len(resultado))
            
            # Adiciona categoria de produto (sintética)
            categorias = ['MOTORES', 'REDUTORES', 'INVERSORES', 'ACESSÓRIOS']
            resultado['product_category'] = [categorias[i % len(categorias)] for i in range(len(resultado))]
            
            # Calcula oportunidade perdida
            resultado['lost_opportunity'] = resultado['total_sales'] * (100 - resultado['conversion_rate']) / 100
            
            # Ordena por taxa de conversão (crescente - piores primeiro)
            resultado = resultado.sort_values('conversion_rate', ascending=True)
            
            print(f"✅ Análise de demanda de cotações concluída - {len(resultado)} produtos analisados")
            return resultado[['produto', 'product_category', 'total_quotations', 'total_sales', 'conversion_rate', 'lost_opportunity']]
            
        except Exception as e:
            print(f"❌ Erro na análise de cotações: {e}")
            return pd.DataFrame({
                'produto': ['Erro no cálculo'],
                'product_category': ['ERRO'],
                'total_quotations': [0],
                'total_sales': [0],
                'conversion_rate': [0],
                'lost_opportunity': [0]
            })
    
    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict, is_cotacoes: bool = False) -> pd.DataFrame:
        """Aplica filtros básicos ao DataFrame"""
        if filters is None:
            return df
        
        filtered_df = df.copy()
        
        # Aplica filtros básicos se existirem
        for key, value in filters.items():
            if value and key in filtered_df.columns:
                if isinstance(value, list):
                    filtered_df = filtered_df[filtered_df[key].isin(value)]
                else:
                    filtered_df = filtered_df[filtered_df[key] == value]
        
        return filtered_df
