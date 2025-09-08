"""
Módulo para cálculo de KPIs e métricas de negócio
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from utils.db import SENTINEL_ALL, _norm_year

class KPICalculator:
    """Classe para cálculo de KPIs"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
    
    def calculate_general_kpis(self, vendas_df: pd.DataFrame, 
                              cotacoes_df: pd.DataFrame,
                              produtos_cotados_df: pd.DataFrame,
                              filters: Dict = None) -> Dict:
        """Calcula KPIs gerais do sistema"""
        
        # Aplica filtros se fornecidos
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        cotacoes_filtered = self._apply_filters(cotacoes_df, filters, is_cotacoes=True) if filters else cotacoes_df
        
        # KPIs de vendas
        entrada_pedidos = vendas_filtered['vlr_entrada'].sum() if 'vlr_entrada' in vendas_filtered.columns else 0
        valor_carteira = vendas_filtered['vlr_carteira'].sum() if 'vlr_carteira' in vendas_filtered.columns else 0
        faturamento = vendas_filtered['vlr_rol'].sum() if 'vlr_rol' in vendas_filtered.columns else 0
        
        # Quantidade de clientes únicos
        total_clientes = vendas_filtered['cod_cliente'].nunique() if not vendas_filtered.empty else 0
        
        # Quantidade de produtos únicos
        total_produtos = vendas_filtered['material'].nunique() if not vendas_filtered.empty else 0
        
        # Frequência média de compra (em dias)
        freq_media = self._calculate_average_purchase_frequency(vendas_filtered)
        
        # Dias sem compra médios
        dias_sem_compra_medio = self._calculate_average_days_without_purchase(vendas_filtered)
        
        # Mix médio de produtos
        mix_medio = self._calculate_average_product_mix(vendas_filtered, cotacoes_filtered)
        
        # Comparação com ano anterior
        comparacao_ano_anterior = self._calculate_year_comparison(vendas_df, filters)
        
        return {
            'entrada_pedidos': {
                'valor': entrada_pedidos,
                'variacao': comparacao_ano_anterior.get('entrada_pedidos', 0)
            },
            'valor_carteira': {
                'valor': valor_carteira,
                'variacao': comparacao_ano_anterior.get('valor_carteira', 0)
            },
            'faturamento': {
                'valor': faturamento,
                'variacao': comparacao_ano_anterior.get('faturamento', 0)
            },
            'total_clientes': total_clientes,
            'total_produtos': total_produtos,
            'frequencia_media_compra': freq_media,
            'dias_sem_compra_medio': dias_sem_compra_medio,
            'mix_medio': mix_medio
        }
    
    def calculate_business_unit_kpis(self, vendas_df: pd.DataFrame, filters: Dict = None) -> Dict:
        """Calcula KPIs por unidade de negócio"""
        
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        
        if vendas_filtered.empty or 'unidade_negocio' not in vendas_filtered.columns:
            return {}
        
        # Agrupa por unidade de negócio
        un_kpis = {}
        for un in vendas_filtered['unidade_negocio'].unique():
            if pd.isna(un):
                continue
                
            un_data = vendas_filtered[vendas_filtered['unidade_negocio'] == un]
            
            faturamento_atual = un_data['vlr_rol'].sum() if 'vlr_rol' in un_data.columns else 0
            
            # Calcula variação com ano anterior
            variacao = self._calculate_un_year_comparison(vendas_df, un, filters)
            
            un_kpis[un] = {
                'faturamento': faturamento_atual,
                'variacao': variacao
            }
        
        return un_kpis
    
    def calculate_client_kpis(self, vendas_df: pd.DataFrame, 
                             cotacoes_df: pd.DataFrame,
                             produtos_cotados_df: pd.DataFrame,
                             filters: Dict = None) -> pd.DataFrame:
        """Calcula KPIs por cliente"""
        
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        cotacoes_filtered = self._apply_filters(cotacoes_df, filters, is_cotacoes=True) if filters else cotacoes_df
        
        if vendas_filtered.empty:
            return pd.DataFrame()
        
        # Agrupa por cliente
        client_kpis = []
        
        for cliente in vendas_filtered['cod_cliente'].unique():
            if pd.isna(cliente):
                continue
                
            cliente_vendas = vendas_filtered[vendas_filtered['cod_cliente'] == cliente]
            cliente_cotacoes = cotacoes_filtered[cotacoes_filtered['cod_cliente'] == cliente] if not cotacoes_filtered.empty else pd.DataFrame()
            
            # Nome do cliente
            nome_cliente = cliente_vendas['cliente'].iloc[0] if 'cliente' in cliente_vendas.columns and not cliente_vendas.empty else 'N/A'
            
            # Dias sem compra
            dias_sem_compra = self._calculate_days_without_purchase(cliente_vendas)
            
            # Frequência média de compra
            freq_compra = self._calculate_purchase_frequency(cliente_vendas)
            
            # Mix de produtos
            produtos_comprados = set(cliente_vendas['material'].unique())
            produtos_cotados = set(cliente_cotacoes['material'].unique()) if not cliente_cotacoes.empty else set()
            
            mix_produtos = len(produtos_comprados)
            total_cotados = len(produtos_cotados)
            total_comprados = len(produtos_comprados & produtos_cotados)
            
            # Percentual não comprado
            perc_nao_comprado = ((total_cotados - total_comprados) / total_cotados * 100) if total_cotados > 0 else 0
            
            # Unidades de negócio
            unidades = list(cliente_vendas['unidade_negocio'].unique()) if 'unidade_negocio' in cliente_vendas.columns else []
            unidades_str = ', '.join([str(un) for un in unidades if not pd.isna(un)])
            
            # Faturamento total
            faturamento_total = cliente_vendas['vlr_rol'].sum() if 'vlr_rol' in cliente_vendas.columns else 0
            
            client_kpis.append({
                'cod_cliente': cliente,
                'cliente': nome_cliente,
                'dias_sem_compra': dias_sem_compra,
                'frequencia_media_compra': freq_compra,
                'mix_produtos': mix_produtos,
                'percentual_mix': (mix_produtos / vendas_filtered['material'].nunique() * 100) if not vendas_filtered.empty else 0,
                'unidades_negocio': unidades_str,
                'produtos_cotados': total_cotados,
                'produtos_comprados': total_comprados,
                'perc_nao_comprado': perc_nao_comprado,
                'faturamento_total': faturamento_total
            })
        
        df_result = pd.DataFrame(client_kpis)
        
        # Ordena por faturamento total (maior para menor)
        if not df_result.empty:
            df_result = df_result.sort_values('faturamento_total', ascending=False)
        
        return df_result
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict, is_cotacoes: bool = False) -> pd.DataFrame:
        """Aplica filtros aos dados"""
        if df.empty:
            return df
            
        df_filtered = df.copy()
        
        # Filtro de ano
        if filters.get('ano') and filters['ano'] != SENTINEL_ALL:
            date_col = 'data' if is_cotacoes else 'data_faturamento'
            if date_col in df_filtered.columns:
                if isinstance(filters['ano'], list) and len(filters['ano']) == 2:
                    start_year, end_year = filters['ano']
                    df_filtered = df_filtered[
                        (df_filtered[date_col].dt.year >= start_year) &
                        (df_filtered[date_col].dt.year <= end_year)
                    ]
                else:
                    year = _norm_year(filters['ano'])
                    if year:
                        df_filtered = df_filtered[df_filtered[date_col].dt.year == year]
        
        # Filtro de mês
        if filters.get('mes') and filters['mes'] != SENTINEL_ALL:
            date_col = 'data' if is_cotacoes else 'data_faturamento'
            if date_col in df_filtered.columns:
                if isinstance(filters['mes'], list) and len(filters['mes']) == 2:
                    start_month, end_month = filters['mes']
                    df_filtered = df_filtered[
                        (df_filtered[date_col].dt.month >= start_month) &
                        (df_filtered[date_col].dt.month <= end_month)
                    ]
        
        # Filtro de cliente
        if filters.get('cliente') and filters['cliente'] != SENTINEL_ALL:
            if isinstance(filters['cliente'], list):
                df_filtered = df_filtered[df_filtered['cod_cliente'].isin(filters['cliente'])]
            else:
                df_filtered = df_filtered[df_filtered['cod_cliente'] == filters['cliente']]
        
        # Filtro de hierarquia de produto
        if filters.get('hierarquia_produto') and filters['hierarquia_produto'] != SENTINEL_ALL:
            if 'hier_produto_1' in df_filtered.columns:
                if isinstance(filters['hierarquia_produto'], list):
                    df_filtered = df_filtered[
                        df_filtered['hier_produto_1'].isin(filters['hierarquia_produto']) |
                        df_filtered.get('hier_produto_2', pd.Series()).isin(filters['hierarquia_produto']) |
                        df_filtered.get('hier_produto_3', pd.Series()).isin(filters['hierarquia_produto'])
                    ]
        
        # Filtro de canal
        if filters.get('canal') and filters['canal'] != SENTINEL_ALL and 'canal_distribuicao' in df_filtered.columns:
            if isinstance(filters['canal'], list):
                df_filtered = df_filtered[df_filtered['canal_distribuicao'].isin(filters['canal'])]
            else:
                df_filtered = df_filtered[df_filtered['canal_distribuicao'] == filters['canal']]
        
        return df_filtered
    
    def _calculate_days_without_purchase(self, cliente_vendas: pd.DataFrame) -> int:
        """Calcula dias sem compra para um cliente"""
        if cliente_vendas.empty or 'data_faturamento' not in cliente_vendas.columns:
            return 0
        
        last_purchase = cliente_vendas['data_faturamento'].max()
        if pd.isna(last_purchase):
            return 999  # Valor alto para indicar sem compras
        
        days_diff = (datetime.now() - last_purchase).days
        return max(0, days_diff)
    
    def _calculate_purchase_frequency(self, cliente_vendas: pd.DataFrame) -> float:
        """Calcula frequência média de compra para um cliente (em dias)"""
        if cliente_vendas.empty or 'data_faturamento' not in cliente_vendas.columns:
            return 0
        
        dates = cliente_vendas['data_faturamento'].dropna().sort_values()
        if len(dates) < 2:
            return 0
        
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates.iloc[i] - dates.iloc[i-1]).days
            intervals.append(interval)
        
        return np.mean(intervals) if intervals else 0
    
    def _calculate_average_purchase_frequency(self, vendas_df: pd.DataFrame) -> float:
        """Calcula frequência média global de compra"""
        if vendas_df.empty:
            return 0
        
        frequencies = []
        for cliente in vendas_df['cod_cliente'].unique():
            cliente_data = vendas_df[vendas_df['cod_cliente'] == cliente]
            freq = self._calculate_purchase_frequency(cliente_data)
            if freq > 0:
                frequencies.append(freq)
        
        return np.mean(frequencies) if frequencies else 0
    
    def _calculate_average_days_without_purchase(self, vendas_df: pd.DataFrame) -> float:
        """Calcula média de dias sem compra"""
        if vendas_df.empty:
            return 0
        
        days_list = []
        for cliente in vendas_df['cod_cliente'].unique():
            cliente_data = vendas_df[vendas_df['cod_cliente'] == cliente]
            days = self._calculate_days_without_purchase(cliente_data)
            days_list.append(days)
        
        return np.mean(days_list) if days_list else 0
    
    def _calculate_average_product_mix(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame) -> float:
        """Calcula mix médio de produtos"""
        if vendas_df.empty:
            return 0
        
        total_produtos_disponiveis = vendas_df['material'].nunique()
        if total_produtos_disponiveis == 0:
            return 0
        
        mix_list = []
        for cliente in vendas_df['cod_cliente'].unique():
            cliente_produtos = vendas_df[vendas_df['cod_cliente'] == cliente]['material'].nunique()
            mix_perc = (cliente_produtos / total_produtos_disponiveis) * 100
            mix_list.append(mix_perc)
        
        return np.mean(mix_list) if mix_list else 0
    
    def _calculate_year_comparison(self, vendas_df: pd.DataFrame, filters: Dict = None) -> Dict:
        """Calcula comparação com ano anterior"""
        if vendas_df.empty or 'data_faturamento' not in vendas_df.columns:
            return {}
        
        current_year = self.current_year
        previous_year = current_year - 1
        
        # Dados do ano atual
        current_year_data = vendas_df[vendas_df['data_faturamento'].dt.year == current_year]
        
        # Dados do ano anterior
        previous_year_data = vendas_df[vendas_df['data_faturamento'].dt.year == previous_year]
        
        def calculate_variation(current_value, previous_value):
            if previous_value == 0:
                return 0 if current_value == 0 else 100
            return ((current_value - previous_value) / previous_value) * 100
        
        # Entrada de pedidos
        entrada_atual = current_year_data['vlr_entrada'].sum() if 'vlr_entrada' in current_year_data.columns else 0
        entrada_anterior = previous_year_data['vlr_entrada'].sum() if 'vlr_entrada' in previous_year_data.columns else 0
        
        # Valor carteira
        carteira_atual = current_year_data['vlr_carteira'].sum() if 'vlr_carteira' in current_year_data.columns else 0
        carteira_anterior = previous_year_data['vlr_carteira'].sum() if 'vlr_carteira' in previous_year_data.columns else 0
        
        # Faturamento
        faturamento_atual = current_year_data['vlr_rol'].sum() if 'vlr_rol' in current_year_data.columns else 0
        faturamento_anterior = previous_year_data['vlr_rol'].sum() if 'vlr_rol' in previous_year_data.columns else 0
        
        return {
            'entrada_pedidos': calculate_variation(entrada_atual, entrada_anterior),
            'valor_carteira': calculate_variation(carteira_atual, carteira_anterior),
            'faturamento': calculate_variation(faturamento_atual, faturamento_anterior)
        }
    
    def _calculate_un_year_comparison(self, vendas_df: pd.DataFrame, unidade_negocio: str, filters: Dict = None) -> float:
        """Calcula comparação com ano anterior para uma unidade de negócio"""
        if vendas_df.empty or 'unidade_negocio' not in vendas_df.columns:
            return 0
        
        un_data = vendas_df[vendas_df['unidade_negocio'] == unidade_negocio]
        
        current_year = self.current_year
        previous_year = current_year - 1
        
        current_year_value = un_data[un_data['data_faturamento'].dt.year == current_year]['vlr_rol'].sum()
        previous_year_value = un_data[un_data['data_faturamento'].dt.year == previous_year]['vlr_rol'].sum()
        
        if previous_year_value == 0:
            return 0 if current_year_value == 0 else 100
        
        return ((current_year_value - previous_year_value) / previous_year_value) * 100
    
    def get_top_clients(self, vendas_df: pd.DataFrame, top_n: int = 10, filters: Dict = None) -> pd.DataFrame:
        """Retorna os top N clientes por faturamento"""
        vendas_filtered = self._apply_filters(vendas_df, filters) if filters else vendas_df
        
        if vendas_filtered.empty:
            return pd.DataFrame()
        
        top_clients = (vendas_filtered.groupby(['cod_cliente', 'cliente'])['vlr_rol']
                      .sum()
                      .reset_index()
                      .sort_values('vlr_rol', ascending=False)
                      .head(top_n))
        
        return top_clients
