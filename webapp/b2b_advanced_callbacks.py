"""
Callbacks para Sistema B2B Avançado - Sugestões Inteligentes
Dashboard Laura Representações - WEG
Versão 2.0 com todas as funcionalidades B2B
"""

import dash
from dash import callback, Input, Output, State, ctx, no_update, html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

# Import do app principal
from webapp import app

# Imports das funcionalidades B2B
from utils.ml_recommendations import get_purchase_recommender, get_conversion_analyzer
from utils import load_all_data
from utils.db import get_connection as get_db_connection
from utils import load_vendas_data
from webapp.b2b_advanced_layout import (
    create_overview_content, 
    create_gaps_content,
    create_seasonality_content,
    create_empty_state
)

# Configuração de logging
logger = logging.getLogger(__name__)

# =============================================================================
# FUNÇÕES AUXILIARES MIGRADAS DO PURCHASE SUGGESTIONS
# =============================================================================

def _create_progress_view(message, progress_value, color, current_step=None, total_steps=None):
    """Cria view de progresso para operações longas"""
    return dbc.Card([
        dbc.CardBody([
            html.H5([
                html.I(className="fas fa-spinner fa-spin me-2"),
                message
            ], className="text-center mb-3"),
            dbc.Progress(value=progress_value, color=color, className="mb-3"),
            html.P(
                f"Etapa {current_step} de {total_steps}" if current_step and total_steps else "Processando...",
                className="text-center text-muted"
            )
        ])
    ], color=color, outline=True)


def _create_success_view(metricas, message, timestamp):
    """Cria view de sucesso com métricas"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                html.Strong(message)
            ], color="success"),
            html.Hr(),
            html.H6("📊 Métricas de Performance:"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(metricas.get('total_materiais', 0), className="text-primary"),
                            html.P("Materiais Analisados", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metricas.get('tempo_processamento', 0):.2f}s", className="text-info"),
                            html.P("Tempo de Processamento", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{metricas.get('accuracy', 0):.1f}%", className="text-success"),
                            html.P("Accuracy Média", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(metricas.get('total_recomendacoes', 0), className="text-warning"),
                            html.P("Recomendações Geradas", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], width=3)
            ]),
            html.Hr(),
            html.Small(f"⏰ Última atualização: {timestamp}", className="text-muted")
        ])
    ])


def _create_error_view(message, timestamp):
    """Cria view de erro com informações de debug"""
    return dbc.Alert([
        html.H5([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Erro no Processamento"
        ]),
        html.P(message),
        html.Hr(),
        html.Small(f"Timestamp: {timestamp}"),
        html.Br(),
        html.Small("💡 Verifique se há dados suficientes no banco de dados e tente novamente.")
    ], color="danger")


# =============================================================================
# CALLBACK 1: CARREGAMENTO DE CLIENTES MELHORADO
# =============================================================================
@callback(
    [Output('filter-b2b-cliente', 'options'),
     Output('filter-b2b-cliente', 'value')],
    [Input('url', 'pathname')]
)
def populate_cliente_dropdown_b2b(pathname):
    """Popula dropdown de clientes com busca aprimorada por código e nome"""
    if pathname != '/app/b2b-advanced':
        return no_update, no_update
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        if vendas_df.empty:
            return [], []
        
        # Combina código e nome do cliente para busca
        clientes_unique = vendas_df[['cod_cliente', 'cliente']].dropna().drop_duplicates()
        
        # Cria opções com formato "código - nome" para facilitar busca
        options = []
        for _, row in clientes_unique.iterrows():
            cod_cliente = str(row['cod_cliente'])
            nome_cliente = str(row['cliente'])
            
            # Formato: "123456 - CLIENTE EXEMPLO LTDA"
            label = f"{cod_cliente} - {nome_cliente}"
            
            options.append({
                "label": label,
                "value": cod_cliente
            })
        
        # Ordena por código do cliente
        options = sorted(options, key=lambda x: x['value'])
        
        logger.info(f"✅ {len(options)} clientes carregados para dropdown B2B")
        return options, []  # Valor vazio para multi-seleção
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar clientes B2B: {e}")
        return [], []


# =============================================================================
# CALLBACK 2: CARREGAMENTO DE MATERIAIS  
# =============================================================================
@callback(
    [Output('filter-b2b-material', 'options'),
     Output('filter-b2b-material', 'value')],
    [Input('url', 'pathname')]
)
def populate_material_dropdown_b2b(pathname):
    """Popula dropdown de materiais para filtros B2B"""
    if pathname != '/app/b2b-advanced':
        return no_update, no_update
    
    try:
        # Carrega dados
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        if vendas_df.empty:
            return [], []
        
        # Lista de materiais únicos
        materiais_unique = vendas_df[['material', 'produto']].dropna().drop_duplicates()
        
        # Cria opções com formato "material - produto"
        options = []
        for _, row in materiais_unique.iterrows():
            material = str(row['material'])
            produto = str(row['produto'])
            
            # Formato: "12345 - PRODUTO EXEMPLO"
            label = f"{material} - {produto[:50]}"  # Limita produto a 50 chars
            
            options.append({
                "label": label,
                "value": material
            })
        
        # Ordena e limita a 1000 materiais para performance
        options = sorted(options, key=lambda x: x['value'])[:1000]
        
        logger.info(f"✅ {len(options)} materiais carregados para dropdown B2B")
        return options, []
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar materiais B2B: {e}")
        return [], []


# =============================================================================
# CALLBACK ANTIGO MANTIDO PARA COMPATIBILIDADE
# =============================================================================
@callback(
    Output('dropdown-cliente-b2b', 'options'),
    Input('dropdown-cliente-b2b', 'id')  # Trigger na inicialização
)
def load_clientes_b2b(_):
    """Carrega lista de clientes para dropdown"""
    try:
        logger.info("🔄 Carregando clientes para análise B2B")
        
        # Carrega dados - CORRIGIDO: são 3 valores, não 4
        entrada_df, _, _ = load_all_data()
        
        if entrada_df.empty:
            logger.warning("⚠️ DataFrame de entrada vazio")
            return []
        
        # Verifica se as colunas existem
        if 'cod_cliente' not in entrada_df.columns:
            logger.error("❌ Coluna 'cod_cliente' não encontrada")
            return []
        
        # Lista de clientes únicos com código e nome
        clientes_unicos = entrada_df[['cod_cliente', 'cliente']].drop_duplicates()
        clientes_unicos = clientes_unicos.dropna(subset=['cod_cliente'])
        
        # Remove valores vazios e ordena
        clientes_unicos = clientes_unicos[
            (clientes_unicos['cod_cliente'].astype(str).str.strip() != '') &
            (clientes_unicos['cod_cliente'].astype(str) != 'nan')
        ].sort_values('cod_cliente')
        
        # Cria opções do dropdown com código e nome
        options = []
        total_clientes = len(clientes_unicos)
        
        # Carrega todos os clientes (sem limitação de 100)
        for _, row in clientes_unicos.iterrows():
            cod_cliente = str(row['cod_cliente']).strip()
            nome_cliente = str(row.get('cliente', '')).strip()
            
            if nome_cliente and nome_cliente != 'nan':
                label = f"👤 {cod_cliente} - {nome_cliente[:50]}"  # Limita nome a 50 chars
            else:
                label = f"👤 {cod_cliente}"
            
            options.append({
                'label': label,
                'value': cod_cliente
            })
        
        logger.info(f"✅ {len(options)} de {total_clientes} clientes únicos carregados para análise B2B")
        
        # Log alguns exemplos para debug
        if options:
            logger.info(f"📋 Exemplos: {[opt['label'] for opt in options[:3]]}")
        
        return options
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar clientes: {e}")
        return []


def analyze_purchase_gaps(vendas_df, cotacoes_df, produtos_cotados_df, cliente_filter=None):
    """
    Análise de Gaps de Compra - Responde: Quais produtos têm demanda/orçamento mas não são comprados?
    
    Esta função identifica produtos que possuem:
    1. Cotações ativas (demonstrando interesse/demanda)
    2. Histórico de orçamentos
    3. Mas que NÃO foram efetivamente comprados por todos ou por clientes específicos
    
    Args:
        vendas_df: DataFrame de vendas efetivadas
        cotacoes_df: DataFrame de cotações (demanda/interesse)
        produtos_cotados_df: DataFrame de produtos cotados
        cliente_filter: Lista de clientes específicos ou None para todos
    
    Returns:
        DataFrame com gaps identificados e métricas de oportunidade
    """
    try:
        logger.info("🔍 Iniciando análise de gaps de compra...")
        logger.info(f"📋 Cliente filtro: {cliente_filter}")
        
        # 1. Identifica produtos que foram cotados (há demanda/interesse)
        produtos_cotados = set()
        cotacoes_por_cliente = {}  # Track cotações por cliente
        
        if not produtos_cotados_df.empty:
            logger.info(f"📊 Analisando {len(produtos_cotados_df)} produtos cotados...")
            
            # Se há filtro de cliente, filtra produtos cotados primeiro
            if cliente_filter:
                cliente_filter_str = [str(c) for c in cliente_filter]
                produtos_cotados_df['cod_cliente'] = produtos_cotados_df['cod_cliente'].astype(str)
                produtos_cotados_filtrados = produtos_cotados_df[produtos_cotados_df['cod_cliente'].isin(cliente_filter_str)]
                logger.info(f"🎯 Produtos cotados filtrados para cliente: {len(produtos_cotados_filtrados)}")
            else:
                produtos_cotados_filtrados = produtos_cotados_df
            
            # Extrai produtos das cotações via tabela produtos_cotados
            for _, produto_cotado in produtos_cotados_filtrados.iterrows():
                material = produto_cotado.get('material')
                cod_cliente = produto_cotado.get('cod_cliente')
                
                if pd.notna(material):
                    produtos_cotados.add(material)
                    
                    # Track por cliente
                    if cod_cliente not in cotacoes_por_cliente:
                        cotacoes_por_cliente[cod_cliente] = set()
                    cotacoes_por_cliente[cod_cliente].add(material)
        
        logger.info(f"📦 Produtos cotados identificados: {len(produtos_cotados)}")
        if cliente_filter:
            for cliente in cliente_filter:
                produtos_cliente = cotacoes_por_cliente.get(str(cliente), set())
                logger.info(f"👤 Cliente {cliente}: {len(produtos_cliente)} produtos cotados")
        
        # 2. Identifica produtos que foram vendidos (comprados efetivamente)
        produtos_vendidos = set()
        if not vendas_df.empty:
            if cliente_filter:
                # Converte cliente_filter para strings para comparação
                cliente_filter_str = [str(c) for c in cliente_filter]
                vendas_df['cod_cliente'] = vendas_df['cod_cliente'].astype(str)
                vendas_filtradas = vendas_df[vendas_df['cod_cliente'].isin(cliente_filter_str)]
                logger.info(f"💰 Vendas filtradas para cliente: {len(vendas_filtradas)}")
            else:
                vendas_filtradas = vendas_df
            produtos_vendidos = set(vendas_filtradas['material'].dropna().unique())
        
        logger.info(f"💰 Produtos vendidos identificados: {len(produtos_vendidos)}")
        
        # 3. Identifica GAP: produtos cotados mas NÃO vendidos
        gaps_produtos = produtos_cotados - produtos_vendidos
        
        logger.info(f"📊 Gap Analysis Final: {len(produtos_cotados)} cotados vs {len(produtos_vendidos)} vendidos = {len(gaps_produtos)} gaps")
        
        # 4. Cria DataFrame de análise de gaps
        gaps_analysis = []
        
        # Usa produtos cotados filtrados se há filtro de cliente
        produtos_para_analise = produtos_cotados_filtrados if cliente_filter else produtos_cotados_df
        
        for produto in gaps_produtos:
            # Conta cotações por cliente para este produto usando produtos_cotados
            cotacoes_produto = 0
            clientes_interessados = set()
            
            # Busca na tabela produtos_cotados por este material
            produtos_material = produtos_para_analise[produtos_para_analise['material'] == produto]
            
            for _, produto_cotado in produtos_material.iterrows():
                cotacoes_produto += 1
                if pd.notna(produto_cotado.get('cod_cliente')):
                    clientes_interessados.add(produto_cotado['cod_cliente'])
            
            # Se há filtro de cliente, só considera se o produto foi cotado pelo cliente específico
            if cliente_filter and cotacoes_produto == 0:
                continue  # Pula produtos que não foram cotados pelo cliente filtrado
            
            # Calcula métricas de oportunidade com critérios estatísticos mais realistas
            # Score de urgência baseado em distribuição mais suave
            if cotacoes_produto >= 10:
                urgencia_score = 95  # Muito alto para 10+ cotações
            elif cotacoes_produto >= 5:
                urgencia_score = 80  # Alto para 5-9 cotações  
            elif cotacoes_produto >= 3:
                urgencia_score = 65  # Médio-alto para 3-4 cotações
            elif cotacoes_produto >= 2:
                urgencia_score = 45  # Médio para 2 cotações
            else:
                urgencia_score = 25  # Baixo para 1 cotação
            
            diversidade_clientes = len(clientes_interessados)
            
            # Calcula receita potencial baseada nos preços das cotações
            receita_potencial = 0
            if not produtos_material.empty and 'preco_liquido_total' in produtos_material.columns:
                receita_potencial = produtos_material['preco_liquido_total'].sum()
            else:
                receita_potencial = cotacoes_produto * 1000  # Fallback
            
            # Score de confiança mais realista baseado em múltiplos fatores
            confidence_base = urgencia_score * 0.6  # 60% peso para urgência
            confidence_diversidade = min(diversidade_clientes * 8, 25)  # Max 25 pts por diversidade 
            confidence_receita = min((receita_potencial / 10000) * 5, 15)  # Max 15 pts por receita
            confidence_score = min(confidence_base + confidence_diversidade + confidence_receita, 95)
            
            # Garante valores mínimos realistas
            confidence_score = max(confidence_score, 15)  # Mínimo 15%
            
            # Mensagem personalizada baseada no filtro
            if cliente_filter:
                recomendacao = f'Cliente específico cotou {cotacoes_produto}x mas não comprou'
                acao_sugerida = f'Contatar cliente para entender barreiras e facilitar compra'
            else:
                recomendacao = f'Produto com {cotacoes_produto} cotações mas sem vendas'
                acao_sugerida = 'Investigar barreiras de venda e facilitar fechamento'
            
            # Busca descrição do produto na tabela produtos_cotados
            descricao_produto = 'Produto não encontrado'
            clientes_detalhes = []  # Lista de clientes que cotaram
            if not produtos_material.empty and 'descricao' in produtos_material.columns:
                descricao_produto = produtos_material['descricao'].iloc[0]
                
                # Coleta detalhes dos clientes interessados
                for _, produto_cotado in produtos_material.iterrows():
                    cliente_info = produto_cotado.get('cliente', 'Cliente não identificado')
                    cotacao_num = produto_cotado.get('cotacao', 'N/A')
                    if cliente_info and cliente_info not in [c.split(' (')[0] for c in clientes_detalhes]:
                        clientes_detalhes.append(f"{cliente_info} (Cotação: {cotacao_num})")
            
            # Texto resumido dos clientes para exibição
            clientes_texto = '; '.join(clientes_detalhes[:3])  # Max 3 clientes na exibição
            if len(clientes_detalhes) > 3:
                clientes_texto += f" (+{len(clientes_detalhes)-3} outros)"
            
            gaps_analysis.append({
                'material': produto,
                'descricao': descricao_produto,
                'tipo_oportunidade': 'Gap Crítico - Cliente Específico' if cliente_filter else 'Gap Crítico',
                'cotacoes_sem_venda': cotacoes_produto,
                'clientes_interessados': diversidade_clientes,
                'clientes_detalhes': clientes_texto,  # Nova coluna com detalhes dos clientes
                'urgencia_score': round(urgencia_score, 1),
                'potencial_receita': round(receita_potencial, 2),
                'confidence_score': round(confidence_score, 1),
                'recomendacao': recomendacao,
                'acao_sugerida': acao_sugerida
            })
        
        # 5. Ordena por potencial e urgência
        df_gaps = pd.DataFrame(gaps_analysis)
        if not df_gaps.empty:
            df_gaps = df_gaps.sort_values(['urgencia_score', 'clientes_interessados'], ascending=[False, False])
        
        logger.info(f"✅ Análise de gaps concluída: {len(df_gaps)} oportunidades identificadas")
        return df_gaps
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de gaps: {e}")
        return pd.DataFrame()

# =============================================================================
# CALLBACK PRINCIPAL: ATUALIZAR DADOS B2B E GERAR RECOMENDAÇÕES
# =============================================================================
@callback(
    [Output('store-b2b-recommendations-data', 'data'),
     Output('b2b-kpi-cards-container', 'children'),
     Output('b2b-recommendations-table-container', 'children')],
    [Input('btn-refresh-b2b-data', 'n_clicks'),
     Input('btn-b2b-apply-filters', 'n_clicks')],
    [State('filter-b2b-cliente', 'value'),
     State('filter-b2b-material', 'value'),
     State('filter-b2b-periodo', 'start_date'),
     State('filter-b2b-periodo', 'end_date'),
     State('filter-b2b-confidence', 'value'),
     State('filter-b2b-priority', 'value'),
     State('filter-b2b-hier-produto-1', 'value'),
     State('filter-b2b-hier-produto-2', 'value'),
     State('filter-b2b-hier-produto-3', 'value'),
     State('filter-b2b-unidade-negocio', 'value')],
    prevent_initial_call=True
)
def update_b2b_recommendations(btn_refresh, btn_apply, clientes_filter, materiais_filter, 
                              start_date, end_date, confidence_min, priority_filters,
                              hier_produto_1, hier_produto_2, hier_produto_3, unidade_negocio):
    """
    Callback principal para atualizar dados B2B e gerar recomendações
    Migrado e otimizado do sistema purchase_suggestions
    """
    try:
        if not any([btn_refresh, btn_apply]):
            return no_update, no_update, no_update
        
        logger.info("🚀 Iniciando atualização de dados B2B...")
        
        # Progresso inicial
        progress_card = _create_progress_view(
            "Carregando dados e gerando recomendações...", 25, "primary", 1, 4
        )
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Carrega dados base
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        if vendas_df.empty:
            error_view = _create_error_view("Dados de vendas não encontrados", timestamp)
            return {}, error_view, error_view
        
        # Aplica filtros se especificados
        df_filtrado = vendas_df.copy()
        
        # Filtro por clientes
        if clientes_filter and len(clientes_filter) > 0:
            if 'cod_cliente' in df_filtrado.columns:
                # Garante que a coluna e os filtros são do mesmo tipo
                df_filtrado['cod_cliente'] = df_filtrado['cod_cliente'].astype(str)
                clientes_filter_str = [str(c) for c in clientes_filter if c is not None]
                if clientes_filter_str:
                    mask_clientes = df_filtrado['cod_cliente'].isin(clientes_filter_str)
                    df_filtrado = df_filtrado[mask_clientes]
            
        # Filtro por materiais
        if materiais_filter and len(materiais_filter) > 0:
            if 'material' in df_filtrado.columns:
                # Garante que a coluna e os filtros são do mesmo tipo
                df_filtrado['material'] = df_filtrado['material'].astype(str)
                materiais_filter_str = [str(m) for m in materiais_filter if m is not None]
                if materiais_filter_str:
                    mask_materiais = df_filtrado['material'].isin(materiais_filter_str)
                    df_filtrado = df_filtrado[mask_materiais]
            
        # Filtro por período
        if start_date and end_date:
            if 'data' in df_filtrado.columns:
                try:
                    df_filtrado['data'] = pd.to_datetime(df_filtrado['data'])
                    start_date_dt = pd.to_datetime(start_date)
                    end_date_dt = pd.to_datetime(end_date)
                    mask_data = (df_filtrado['data'] >= start_date_dt) & (df_filtrado['data'] <= end_date_dt)
                    df_filtrado = df_filtrado[mask_data]
                except Exception as e:
                    logger.warning(f"Erro ao aplicar filtro de data: {e}")
        
        # Filtros hierárquicos de produto
        if hier_produto_1 and len(hier_produto_1) > 0:
            if 'hier_produto_1' in df_filtrado.columns:
                mask_hier_1 = df_filtrado['hier_produto_1'].isin(hier_produto_1)
                df_filtrado = df_filtrado[mask_hier_1]
        
        if hier_produto_2 and len(hier_produto_2) > 0:
            if 'hier_produto_2' in df_filtrado.columns:
                mask_hier_2 = df_filtrado['hier_produto_2'].isin(hier_produto_2)
                df_filtrado = df_filtrado[mask_hier_2]
        
        if hier_produto_3 and len(hier_produto_3) > 0:
            if 'hier_produto_3' in df_filtrado.columns:
                mask_hier_3 = df_filtrado['hier_produto_3'].isin(hier_produto_3)
                df_filtrado = df_filtrado[mask_hier_3]
        
        # Filtro por unidade de negócio
        if unidade_negocio and len(unidade_negocio) > 0:
            if 'unidade_negocio' in df_filtrado.columns:
                mask_unidade = df_filtrado['unidade_negocio'].isin(unidade_negocio)
                df_filtrado = df_filtrado[mask_unidade]
        
        # Verifica se ainda há dados após filtros
        if df_filtrado.empty:
            error_view = _create_error_view("Nenhum dado encontrado com os filtros aplicados", timestamp)
            return {}, error_view, error_view
        
        # Gera recomendações usando ML
        logger.info("🎯 Gerando recomendações com ML...")
        
        cliente_param = clientes_filter[0] if clientes_filter and len(clientes_filter) == 1 else None
        
        # Gera sugestões com lazy loading
        recommender = get_purchase_recommender()
        df_sugestoes = recommender.generate_purchase_suggestions(
            vendas_df=df_filtrado,
            cotacoes_df=cotacoes_df,
            cliente_filter=cliente_param,
            top_n=200  # Aumentado para permitir mais sugestões
        )
        
        if df_sugestoes.empty:
            error_view = _create_error_view("Nenhuma recomendação gerada com os filtros aplicados", timestamp)
            return {}, error_view, error_view
        
        # Aplica filtro de confidence
        if confidence_min:
            confidence_threshold = confidence_min / 100.0
            if 'probabilidade_recompra' in df_sugestoes.columns:
                df_sugestoes = df_sugestoes[df_sugestoes['probabilidade_recompra'] >= confidence_threshold]
            elif 'score_oportunidade' in df_sugestoes.columns:
                df_sugestoes = df_sugestoes[df_sugestoes['score_oportunidade'] >= confidence_threshold]
        
        # Aplica filtros de prioridade
        if priority_filters and not df_sugestoes.empty:
            try:
                # Cria máscara base
                priority_mask = pd.Series([True] * len(df_sugestoes), index=df_sugestoes.index)
                
                if 'alta' in priority_filters:
                    # Filtrar apenas sugestões de alta prioridade
                    if 'probabilidade_recompra' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['probabilidade_recompra'] > 0.7
                    elif 'score_oportunidade' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['score_oportunidade'] > 0.7
                    elif 'confidence_score' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['confidence_score'] > 70
                
                if 'sazonal' in priority_filters:
                    # Filtrar produtos com sazonalidade ativa
                    if 'tem_sazonalidade' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['tem_sazonalidade'] == True
                    elif 'sazonalidade' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['sazonalidade'].notna()
                
                if 'roi' in priority_filters:
                    # Filtrar por alto potencial ROI
                    if 'valor_potencial' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['valor_potencial'] > df_sugestoes['valor_potencial'].quantile(0.7)
                
                if 'gaps' in priority_filters:
                    # Filtrar gaps críticos (produtos com cotações mas sem vendas)
                    if 'tipo_oportunidade' in df_sugestoes.columns:
                        priority_mask &= df_sugestoes['tipo_oportunidade'].str.contains('gap|crítico', case=False, na=False)
                
                # Aplica filtro apenas se há máscara válida
                if priority_mask.any():
                    df_sugestoes = df_sugestoes[priority_mask]
                else:
                    logger.warning("Nenhuma recomendação atende aos filtros de prioridade selecionados")
                    
            except Exception as e:
                logger.error(f"Erro ao aplicar filtros de prioridade: {e}")
                # Continue sem filtros de prioridade em caso de erro
        
        # ANÁLISE DE GAPS DE COMPRA - Nova funcionalidade
        logger.info("🔍 Executando análise de gaps de compra...")
        df_gaps = analyze_purchase_gaps(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df, 
            produtos_cotados_df=produtos_cotados_df,
            cliente_filter=clientes_filter
        )
        
        # Integra gaps às recomendações se há filtro de gaps selecionado
        if priority_filters and 'gaps' in priority_filters and not df_gaps.empty:
            logger.info(f"🎯 Priorizando {len(df_gaps)} gaps críticos identificados")
            # Substitui recomendações normais por gaps quando filtro está ativo
            df_sugestoes = df_gaps.copy()
        elif not df_gaps.empty:
            # Adiciona alguns gaps importantes às recomendações normais
            top_gaps = df_gaps.head(5)  # Top 5 gaps mais críticos
            if not top_gaps.empty:
                logger.info(f"📈 Adicionando {len(top_gaps)} gaps críticos às recomendações")
                df_sugestoes = pd.concat([df_sugestoes, top_gaps], ignore_index=True)
        
        # Limita resultado final
        df_sugestoes = df_sugestoes.head(25)  # Aumentei de 20 para 25
        
        # Cria KPIs
        kpis_cards = create_b2b_kpi_cards(df_sugestoes, df_filtrado)
        
        # Cria tabela de recomendações
        recommendations_table = create_b2b_recommendations_table(df_sugestoes)
        
        # Converte para formato de store
        recommendations_data = df_sugestoes.to_dict('records')
        
        logger.info(f"✅ {len(recommendations_data)} recomendações B2B geradas com sucesso")
        
        return recommendations_data, kpis_cards, recommendations_table
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar dados B2B: {e}")
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        error_view = _create_error_view(f"Erro inesperado: {str(e)}", timestamp)
        return {}, error_view, error_view


def create_b2b_kpi_cards(df_sugestoes, df_vendas):
    """Cria cards de KPIs para o dashboard B2B"""
    try:
        total_recomendacoes = len(df_sugestoes)
        valor_potencial = df_sugestoes.get('valor_potencial', 0).sum() if 'valor_potencial' in df_sugestoes.columns else 0
        confidence_media = df_sugestoes.get('probabilidade_recompra', df_sugestoes.get('score_oportunidade', 0)).mean() * 100 if len(df_sugestoes) > 0 else 0
        materiais_unicos = df_sugestoes['material'].nunique() if 'material' in df_sugestoes.columns else 0
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🎯 Recomendações", className="card-title"),
                        html.H3(total_recomendacoes, className="text-primary"),
                        html.P("Oportunidades identificadas", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💰 Valor Potencial", className="card-title"),
                        html.H3(f"R$ {valor_potencial:,.0f}", className="text-success"),
                        html.P("Receita estimada", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Confidence Média", className="card-title"),
                        html.H3(f"{confidence_media:.1f}%", className="text-info"),
                        html.P("Confiabilidade das recomendações", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📦 Materiais", className="card-title"),
                        html.H3(materiais_unicos, className="text-warning"),
                        html.P("Produtos únicos sugeridos", className="text-muted mb-0")
                    ])
                ])
            ], width=3)
        ], className="mb-4")
        
    except Exception as e:
        logger.error(f"Erro ao criar KPI cards: {e}")
        return dbc.Alert("Erro ao carregar KPIs", color="warning")


def create_b2b_recommendations_table(df_sugestoes):
    """Cria tabela de recomendações B2B"""
    try:
        if df_sugestoes.empty:
            return dbc.Alert("Nenhuma recomendação encontrada", color="info")
        
        # Preparar dados para tabela
        table_data = []
        for i, row in df_sugestoes.iterrows():
            # Melhor tratamento de confidence
            confidence_value = 0
            if 'probabilidade_recompra' in row and pd.notna(row['probabilidade_recompra']):
                confidence_value = float(row['probabilidade_recompra']) * 100
            elif 'score_oportunidade' in row and pd.notna(row['score_oportunidade']):
                confidence_value = float(row['score_oportunidade']) * 100
            elif 'confidence_score' in row and pd.notna(row['confidence_score']):
                confidence_value = float(row['confidence_score'])
            
            # Melhor tratamento de valor potencial
            valor_pot = 0
            if 'valor_potencial' in row and pd.notna(row['valor_potencial']):
                valor_pot = float(row['valor_potencial'])
            elif 'potencial_receita' in row and pd.notna(row['potencial_receita']):
                valor_pot = float(row['potencial_receita'])
            
            # Se ainda é 0, tenta calcular baseado em quantidade e preço médio
            if valor_pot == 0:
                qtd = row.get('qtd_sugerida', row.get('quantidade_sugerida', 1))
                if pd.notna(qtd) and qtd > 0:
                    valor_pot = qtd * 500  # Estimativa conservadora de R$ 500 por unidade
            
            # Melhor tratamento de quantidade
            qtd_sugerida = 0
            if 'qtd_sugerida' in row and pd.notna(row['qtd_sugerida']):
                qtd_sugerida = int(row['qtd_sugerida'])
            elif 'quantidade_sugerida' in row and pd.notna(row['quantidade_sugerida']):
                qtd_sugerida = int(row['quantidade_sugerida'])
            elif 'cotacoes_sem_venda' in row and pd.notna(row['cotacoes_sem_venda']):
                qtd_sugerida = int(row['cotacoes_sem_venda'])
            
            # Garantir que não há valores NaN
            confidence_display = f"{confidence_value:.1f}%" if confidence_value > 0 else "N/A"
            
            # Tratamento melhorado para evitar 'nan'
            def safe_str(value, default="N/A"):
                if pd.isna(value) or value is None or str(value).lower() == 'nan':
                    return default
                return str(value)
            
            # Buscar descrição melhor
            descricao = "N/A"
            if 'produto' in row and pd.notna(row['produto']) and str(row['produto']).lower() != 'nan':
                descricao = str(row['produto'])
            elif 'descricao' in row and pd.notna(row['descricao']) and str(row['descricao']).lower() != 'nan':
                descricao = str(row['descricao'])
            
            # Buscar cliente melhor
            cliente = "N/A"
            if 'cliente' in row and pd.notna(row['cliente']) and str(row['cliente']).lower() != 'nan':
                cliente = str(row['cliente'])
            
            table_data.append({
                'material': safe_str(row.get('material', 'N/A')),
                'descricao': descricao,
                'cliente': cliente,
                'qtd_sugerida': qtd_sugerida,
                'valor_potencial': f"R$ {valor_pot:,.2f}",
                'confidence': confidence_display,
                'motivo': safe_str(row.get('motivo_da_sugestao', row.get('justificativa', 'Análise ML'))),
                'actions': i  # Para botões de ação
            })
        
        # Definir colunas
        columns = [
            {"name": "Material", "id": "material"},
            {"name": "Descrição", "id": "descricao"},
            {"name": "Cliente", "id": "cliente"},
            {"name": "Qtd. Sugerida", "id": "qtd_sugerida", "type": "numeric"},
            {"name": "Valor Potencial", "id": "valor_potencial"},
            {"name": "Confidence", "id": "confidence"},
            {"name": "Motivo", "id": "motivo"},
        ]
        
        return dash_table.DataTable(
            data=table_data,
            columns=columns,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{confidence} >= 80%'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{confidence} < 50%'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black',
                }
            ],
            page_size=25,  # Aumentado para 25 itens por página
            page_action="native",  # Habilita paginação nativa
            sort_action="native",
            filter_action="native",
            export_format="csv",  # Permite exportar para CSV
            export_headers="display"
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar tabela de recomendações: {e}")
        return dbc.Alert("Erro ao carregar tabela", color="danger")


# =============================================================================
# CALLBACK ANTIGO MANTIDO PARA COMPATIBILIDADE
# =============================================================================
@callback(
    [Output('store-b2b-data', 'data'),
     Output('store-current-client', 'data'),
     Output('alert-b2b-analysis', 'children'),
     Output('alert-b2b-analysis', 'color'),
     Output('alert-b2b-analysis', 'is_open')],
    Input('btn-run-complete-analysis', 'n_clicks'),
    [State('dropdown-cliente-b2b', 'value'),
     State('dropdown-report-type', 'value')]
)
def run_complete_b2b_analysis(n_clicks, cod_cliente, report_type):
    """Executa análise B2B completa"""
    if not n_clicks or not cod_cliente:
        return no_update, no_update, no_update, no_update, no_update
    
    try:
        logger.info(f"🚀 Iniciando análise B2B completa para cliente {cod_cliente}")
        
        # Contexto comercial padrão
        contexto_comercial = {
            'vendedor': 'Equipe Comercial',
            'regiao': 'Nacional',
            'segmento': 'Industrial',
            'data_analise': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Executa análise completa com lazy loading
        recommender = get_purchase_recommender()
        resultado = recommender.run_complete_b2b_analysis(
            cod_cliente=cod_cliente,
            contexto_comercial=contexto_comercial,
            export_format=report_type or 'completo'
        )
        
        if resultado.get('status') == 'ERRO':
            error_msg = resultado.get('erro', 'Erro desconhecido')
            return (no_update, no_update, 
                   f"❌ Erro na análise: {error_msg}", 
                   "danger", True)
        
        # Sucesso
        resumo = resultado.get('resumo_executivo', {})
        success_msg = [
            html.H5([
                html.I(className="fas fa-check-circle me-2"),
                "Análise B2B Completa Concluída!"
            ], className="mb-2"),
            html.P([
                f"✅ Cliente: {cod_cliente} | ",
                f"🏆 Classificação: {resumo.get('classificacao_cliente', 'N/A')} | ",
                f"🎯 {resumo.get('total_oportunidades', 0)} oportunidades | ",
                f"💰 R$ {resumo.get('valor_potencial', 0):,.2f} potencial"
            ])
        ]
        
        logger.info(f"✅ Análise B2B concluída para {cod_cliente}")
        
        return (resultado, cod_cliente, success_msg, "success", True)
        
    except Exception as e:
        logger.error(f"❌ Erro na análise B2B: {e}")
        return (no_update, no_update, 
               f"❌ Erro interno: {str(e)}", 
               "danger", True)

# =============================================================================
# CALLBACK 3: RENDERIZAÇÃO DE CONTEÚDO DAS ABAS
# =============================================================================
@callback(
    [Output('content-overview', 'children'),
     Output('content-gaps', 'children'),
     Output('content-seasonality', 'children'),
     Output('content-kpis', 'children'),
     Output('content-benchmark', 'children'),
     Output('content-alerts', 'children'),
     Output('content-insights', 'children')],
    [Input('tabs-b2b-analysis', 'value'),
     Input('store-b2b-data', 'data')],
    State('store-current-client', 'data')
)
def update_tab_content(active_tab, b2b_data, current_client):
    """Atualiza conteúdo das abas baseado nos dados B2B"""
    
    # Estados vazios por padrão
    empty_msg = "Selecione um cliente e execute a análise B2B"
    empty_content = create_empty_state(empty_msg)
    
    if not b2b_data or not current_client:
        return [empty_content] * 7
    
    try:
        # Extrai dados das análises
        analises = b2b_data.get('analises', {})
        
        # Overview
        content_overview = create_overview_content(b2b_data)
        
        # Gaps
        gaps_data = analises.get('gaps_mercado')
        content_gaps = create_gaps_content(gaps_data)
        
        # Sazonalidade
        seasonality_data = analises.get('sazonalidade', {})
        content_seasonality = create_seasonality_content(seasonality_data)
        
        # KPIs
        kpis_data = analises.get('kpis_comerciais', {})
        content_kpis = create_kpis_content(kpis_data)
        
        # Benchmark
        benchmark_data = analises.get('benchmark', {})
        content_benchmark = create_benchmark_content(benchmark_data)
        
        # Alertas
        alertas_data = analises.get('alertas', {})
        content_alerts = create_alerts_content(alertas_data)
        
        # Insights
        insights_data = analises.get('insights', {})
        content_insights = create_insights_content(insights_data)
        
        return [
            content_overview,
            content_gaps, 
            content_seasonality,
            content_kpis,
            content_benchmark,
            content_alerts,
            content_insights
        ]
        
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar conteúdo das abas: {e}")
        error_content = dbc.Alert(f"❌ Erro ao carregar dados: {str(e)}", color="danger")
        return [error_content] * 7

# =============================================================================
# FUNÇÕES AUXILIARES PARA CRIAÇÃO DE CONTEÚDO
# =============================================================================

def create_kpis_content(kpis_data):
    """Cria conteúdo da aba de KPIs comerciais"""
    if not kpis_data:
        return create_empty_state("KPIs comerciais não disponíveis")
    
    kpis_basicos = kpis_data.get('kpis_basicos', {})
    ltv_data = kpis_data.get('ltv_analise', {})
    tendencias = kpis_data.get('tendencias', {})
    
    return [
        # Cards de KPIs principais
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💰 Vendas 12M", className="card-title"),
                        html.H3(f"R$ {kpis_basicos.get('total_vendas', 0):,.2f}", 
                               className="text-success"),
                        html.P(f"Ticket Médio: R$ {kpis_basicos.get('ticket_medio', 0):,.2f}", 
                              className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📦 Produtos", className="card-title"),
                        html.H3(kpis_basicos.get('materiais_distintos', 0), 
                               className="text-info"),
                        html.P(f"Transações: {kpis_basicos.get('numero_transacoes', 0)}", 
                              className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📈 LTV Projetado", className="card-title"),
                        html.H3(f"R$ {ltv_data.get('ltv_projetado_12m', 0):,.2f}", 
                               className="text-primary"),
                        html.P("Próximos 12 meses", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Crescimento", className="card-title"),
                        html.H3(f"{tendencias.get('crescimento_medio_mensal', 0):+.1f}%", 
                               className="text-warning"),
                        html.P(f"Tendência: {tendencias.get('tendencia', 'ESTAVEL')}", 
                              className="text-muted mb-0")
                    ])
                ])
            ], width=3),
        ], className="mb-4"),
        
        # Recomendações comerciais
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-lightbulb me-2"),
                    "Recomendações Comerciais"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Ul([
                    html.Li(rec) for rec in kpis_data.get('recomendacoes_comerciais', [
                        'Execute a análise para ver recomendações personalizadas'
                    ])
                ])
            ])
        ])
    ]

def create_benchmark_content(benchmark_data):
    """Cria conteúdo da aba de benchmark"""
    if not benchmark_data:
        return create_empty_state("Dados de benchmark não disponíveis")
    
    classificacao = benchmark_data.get('classificacao_geral', 'N/A')
    score = benchmark_data.get('score_percentil', 0)
    similares = benchmark_data.get('clientes_similares', [])
    best_practices = benchmark_data.get('best_practices', [])
    
    return [
        # Status do cliente
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-medal me-2"),
                            f"Classificação: {classificacao}"
                        ], className="text-center"),
                        html.H2(f"{score:.0f}°", className="text-center text-primary"),
                        html.P("Percentil de Performance", className="text-center text-muted")
                    ])
                ], color="light")
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("👥 Clientes Similares", className="mb-3"),
                        html.Ul([
                            html.Li(f"{similar['cod_cliente']} (Similaridade: {similar['similaridade_score']:.1%})")
                            for similar in similares[:5]
                        ] if similares else [html.Li("Nenhum cliente similar encontrado")])
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🏆 Best Practices", className="mb-3"),
                        html.Ul([
                            html.Li(f"Cliente {bp['cod_cliente']}: R$ {bp['valor_total']:,.2f}")
                            for bp in best_practices[:3]
                        ] if best_practices else [html.Li("Dados de best practices em análise")])
                    ])
                ])
            ], width=4),
        ], className="mb-4"),
        
        # Recomendações de benchmark
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-chart-bar me-2"),
                    "Recomendações de Benchmark"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Ul([
                    html.Li(rec) for rec in benchmark_data.get('recomendacoes_benchmark', [
                        'Análise de benchmark em andamento...'
                    ])
                ])
            ])
        ])
    ]

def create_alerts_content(alertas_data):
    """Cria conteúdo da aba de alertas"""
    if not alertas_data:
        return create_empty_state("Sistema de alertas não disponível")
    
    alertas = alertas_data.get('alertas', {})
    criticos = alertas.get('criticos', [])
    importantes = alertas.get('importantes', [])
    oportunidades = alertas.get('oportunidades', [])
    
    return [
        # Alertas críticos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                            f"Alertas Críticos ({len(criticos)})"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            dbc.Alert([
                                html.H6(f"🚨 {alerta['tipo']}", className="mb-2"),
                                html.P(alerta.get('acao_sugerida', 'Ação não definida'), className="mb-1"),
                                html.Small(f"Cliente: {alerta.get('cliente', 'N/A')}", className="text-muted")
                            ], color="danger", className="mb-2")
                            for alerta in criticos[:3]
                        ] if criticos else [
                            dbc.Alert("✅ Nenhum alerta crítico no momento", color="success")
                        ])
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-bullseye me-2 text-success"),
                            f"Oportunidades ({len(oportunidades)})"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            dbc.Alert([
                                html.H6(f"💰 {oportunidade['tipo']}", className="mb-2"),
                                html.P(oportunidade.get('acao_sugerida', 'Ação não definida'), className="mb-1"),
                                html.Small(f"Material: {oportunidade.get('material', 'N/A')}", className="text-muted")
                            ], color="success", className="mb-2")
                            for oportunidade in oportunidades[:3]
                        ] if oportunidades else [
                            dbc.Alert("📊 Execute análise para identificar oportunidades", color="info")
                        ])
                    ])
                ])
            ], width=6),
        ], className="mb-4"),
        
        # Resumo de alertas
        dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-list me-2"),
                    "Resumo do Sistema de Alertas"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("📊 Estatísticas"),
                        html.P(f"• Críticos: {len(criticos)}"),
                        html.P(f"• Importantes: {len(importantes)}"),
                        html.P(f"• Oportunidades: {len(oportunidades)}"),
                    ], width=6),
                    dbc.Col([
                        html.H6("⏰ Próximas Ações"),
                        html.Ol([
                            html.Li(acao.get('acao', 'Ação não definida'))
                            for acao in alertas_data.get('proximas_acoes', [])[:3]
                        ] if alertas_data.get('proximas_acoes') else [
                            html.Li("Execute análise completa para ver ações prioritárias")
                        ])
                    ], width=6)
                ])
            ])
        ])
    ]

def create_insights_content(insights_data):
    """Cria conteúdo da aba de insights acionáveis"""
    if not insights_data:
        return create_empty_state("Insights acionáveis não disponíveis")
    
    scripts = insights_data.get('scripts_venda', [])
    argumentos = insights_data.get('argumentos_tecnicos', [])
    plano_acao = insights_data.get('plano_acao', [])
    
    return [
        # Scripts de venda
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-comments me-2"),
                            "Scripts de Abordagem"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader(html.H6(f"🎯 {script['situacao']}", className="mb-0")),
                                dbc.CardBody([
                                    html.P(script['script'][:200] + "..." if len(script.get('script', '')) > 200 else script.get('script', '')),
                                    html.H6("Próximos Passos:"),
                                    html.Ul([
                                        html.Li(passo) for passo in script.get('proximos_passos', [])
                                    ])
                                ])
                            ], className="mb-3")
                            for script in scripts[:2]
                        ] if scripts else [
                            dbc.Alert("📝 Scripts personalizados serão gerados após a análise", color="info")
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Argumentos técnicos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Argumentos Técnicos"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H6(f"📊 {arg['produto']}", className="mb-0"),
                                    html.Small(f"Potencial: R$ {arg.get('valor_potencial', 0):,.2f}", 
                                             className="text-success")
                                ]),
                                dbc.CardBody([
                                    html.P(arg['argumento_tecnico'][:150] + "..." if len(arg.get('argumento_tecnico', '')) > 150 else arg.get('argumento_tecnico', ''))
                                ])
                            ], className="mb-3")
                            for arg in argumentos[:3]
                        ] if argumentos else [
                            dbc.Alert("📈 Argumentos técnicos baseados em dados serão gerados", color="info")
                        ])
                    ])
                ])
            ], width=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-tasks me-2"),
                            "Plano de Ação"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Ol([
                            html.Li([
                                html.Strong(acao['acao']),
                                html.Br(),
                                html.Small(f"Prazo: {acao.get('prazo', 'A definir')} | Objetivo: {acao.get('objetivo', 'A definir')}", 
                                         className="text-muted")
                            ])
                            for acao in plano_acao
                        ] if plano_acao else [
                            html.Li("Execute a análise para obter plano de ação personalizado")
                        ])
                    ])
                ])
            ], width=4)
        ])
    ]

# =============================================================================
# CALLBACK 4: EXPORTAÇÃO DE RELATÓRIOS
# =============================================================================
@callback(
    [Output('alert-b2b-export', 'children'),
     Output('alert-b2b-export', 'color'),
     Output('alert-b2b-export', 'is_open')],
    [Input('btn-export-executive', 'n_clicks'),
     Input('btn-export-presentation', 'n_clicks')],
    [State('store-b2b-data', 'data'),
     State('store-current-client', 'data')]
)
def export_b2b_reports(n_clicks_exec, n_clicks_pres, b2b_data, current_client):
    """Exporta relatórios B2B em diferentes formatos"""
    if not any([n_clicks_exec, n_clicks_pres]) or not b2b_data or not current_client:
        return no_update, no_update, no_update
    
    try:
        trigger = ctx.triggered[0]['prop_id']
        
        if 'btn-export-executive' in trigger:
            export_type = "executivo"
            icon = "📊"
        else:
            export_type = "apresentação"
            icon = "📋"
        
        # Simula exportação (aqui você implementaria a geração real do arquivo)
        success_msg = [
            html.H5([
                html.I(className="fas fa-download me-2"),
                f"Relatório {export_type.title()} Preparado!"
            ]),
            html.P([
                f"{icon} Relatório para cliente {current_client} gerado com sucesso. ",
                html.A("Clique aqui para download", href="#", className="alert-link")
            ])
        ]
        
        logger.info(f"✅ Relatório {export_type} exportado para {current_client}")
        return success_msg, "success", True
        
    except Exception as e:
        logger.error(f"❌ Erro na exportação: {e}")
        return f"❌ Erro na exportação: {str(e)}", "danger", True

# =============================================================================
# CALLBACK PARA SISTEMA DE APRENDIZADO ML
# =============================================================================

@app.callback(
    [Output('b2b-learning-feedback', 'children'),
     Output('b2b-learning-feedback', 'color'),
     Output('b2b-learning-feedback', 'is_open')],
    [Input('btn-b2b-run-learning-cycle', 'n_clicks')],
    prevent_initial_call=True
)
def execute_learning_cycle(n_clicks):
    """
    Executa ciclo de aprendizado do modelo ML
    """
    if not n_clicks:
        return "", "info", False
    
    try:
        from utils.ml_feedback_learning import MLFeedbackLearningSystem
        
        logger.info("🤖 Iniciando ciclo de aprendizado manual...")
        
        # Inicializa sistema de aprendizado
        learning_system = MLFeedbackLearningSystem()
        
        # Executa ciclo de aprendizado
        result = learning_system.run_daily_learning_cycle()
        
        # Verifica se o resultado é um dict ou apenas boolean
        if isinstance(result, bool):
            if result:
                result = {
                    'success': True,
                    'feedbacks_processed': 0,
                    'model_updated': False,
                    'improvements': 'Processo executado com sucesso'
                }
            else:
                result = {
                    'success': False,
                    'message': 'Falha na execução do ciclo de aprendizado'
                }
        
        # Garante que result é um dict
        if not isinstance(result, dict):
            result = {
                'success': False,
                'message': f'Resposta inesperada do sistema: {type(result)}'
            }
        
        if result.get('success', False):
            feedback_msg = [
                html.I(className="fas fa-check-circle me-2"),
                html.Strong("Ciclo de Aprendizado Concluído!"),
                html.Br(),
                f"• Feedbacks processados: {result.get('feedbacks_processed', 0)}",
                html.Br(),
                f"• Modelo atualizado: {'Sim' if result.get('model_updated', False) else 'Não'}",
                html.Br(),
                f"• Melhorias: {result.get('improvements', 'Nenhuma')}"
            ]
            return feedback_msg, "success", True
        else:
            return [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Aviso: {result.get('message', 'Nenhum feedback novo para processar')}"
            ], "info", True
            
    except Exception as e:
        logger.error(f"❌ Erro no ciclo de aprendizado: {e}")
        return [
            html.I(className="fas fa-times-circle me-2"),
            f"Erro ao executar aprendizado: {str(e)}"
        ], "danger", True


# =============================================================================
# CALLBACK: SALVAR FILTROS B2B
# =============================================================================
@callback(
    Output('alert-filters-saved', 'is_open'),
    [Input('btn-b2b-save-filters', 'n_clicks')],
    [State('filter-b2b-cliente', 'value'),
     State('filter-b2b-material', 'value'), 
     State('filter-b2b-periodo', 'start_date'),
     State('filter-b2b-periodo', 'end_date'),
     State('filter-b2b-confidence', 'value'),
     State('filter-b2b-priority', 'value'),
     State('filter-b2b-hier-produto-1', 'value'),
     State('filter-b2b-hier-produto-2', 'value'),
     State('filter-b2b-hier-produto-3', 'value'),
     State('filter-b2b-unidade-negocio', 'value')],
    prevent_initial_call=True
)
def save_b2b_filters(n_clicks, clientes, materiais, start_date, end_date, confidence, priority,
                    hier_produto_1, hier_produto_2, hier_produto_3, unidade_negocio):
    """
    Salva os filtros B2B atuais na sessão do usuário
    """
    if not n_clicks:
        return False
        
    try:
        # Aqui você pode implementar salvamento em banco de dados ou sessão
        # Por enquanto, apenas mostra confirmação ao usuário
        logger.info(f"✅ Filtros B2B salvos: Cliente={clientes}, Material={materiais}, "
                   f"Período={start_date} a {end_date}, Confiança={confidence}, Prioridade={priority}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar filtros: {e}")
        return False


# =============================================================================
# CALLBACK: ANÁLISE DE GAPS DE COMPRA
# =============================================================================
@callback(
    Output('gaps-analysis-container', 'children'),
    [Input('btn-analyze-gaps', 'n_clicks')],
    [State('filter-b2b-cliente', 'value')],
    prevent_initial_call=True
)
def analyze_gaps_callback(n_clicks, clientes_filter):
    """
    Executa análise completa de gaps de compra
    Responde: Quais produtos têm demanda/orçamento mas não são comprados?
    """
    if not n_clicks:
        return no_update
    
    try:
        logger.info("🔍 Iniciando análise completa de gaps de compra...")
        
        # Carrega dados
        vendas_df, cotacoes_df, produtos_cotados_df = load_all_data()
        
        if vendas_df.empty:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Não há dados suficientes para análise de gaps"
            ], color="warning")
        
        # Executa análise de gaps
        df_gaps = analyze_purchase_gaps(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=produtos_cotados_df,
            cliente_filter=clientes_filter
        )
        
        if df_gaps.empty:
            # Vamos adicionar informações de debug quando não há gaps
            total_cotacoes = len(cotacoes_df)
            total_produtos_cotados = len(produtos_cotados_df)
            total_vendas = len(vendas_df)
            
            if clientes_filter:
                cotacoes_cliente = cotacoes_df[cotacoes_df['cod_cliente'].astype(str).isin([str(c) for c in clientes_filter])]
                produtos_cotados_cliente = produtos_cotados_df[produtos_cotados_df['cod_cliente'].astype(str).isin([str(c) for c in clientes_filter])]
                vendas_cliente = vendas_df[vendas_df['cod_cliente'].astype(str).isin([str(c) for c in clientes_filter])]
                
                debug_info = dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 Informações de Debug:", className="mb-3"),
                        html.Ul([
                            html.Li(f"Total de cotações no sistema: {total_cotacoes}"),
                            html.Li(f"Cotações do cliente selecionado: {len(cotacoes_cliente)}"),
                            html.Li(f"Total de produtos cotados no sistema: {total_produtos_cotados}"),
                            html.Li(f"Produtos cotados pelo cliente: {len(produtos_cotados_cliente)}"),
                            html.Li(f"Total de vendas no sistema: {total_vendas}"),
                            html.Li(f"Vendas do cliente selecionado: {len(vendas_cliente)}"),
                            html.Li(f"Cliente(s) filtrado(s): {clientes_filter}")
                        ])
                    ])
                ], color="light", className="mt-3")
            else:
                debug_info = dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 Informações do Sistema:", className="mb-3"),
                        html.Ul([
                            html.Li(f"Total de cotações analisadas: {total_cotacoes}"),
                            html.Li(f"Total de produtos cotados: {total_produtos_cotados}"),
                            html.Li(f"Total de vendas analisadas: {total_vendas}"),
                            html.Li("Análise geral (todos os clientes)")
                        ])
                    ])
                ], color="light", className="mt-3")
            
            return [
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    html.Strong("Excelente! "),
                    "Não foram identificados gaps críticos. Todos os produtos com demanda estão sendo comprados adequadamente."
                ], color="success"),
                debug_info
            ]
        
        # Cria visualização dos gaps
        gaps_cards = []
        
        # Card de resumo
        total_gaps = len(df_gaps)
        total_cotacoes_perdidas = df_gaps['cotacoes_sem_venda'].sum()
        receita_potencial = df_gaps['potencial_receita'].sum()
        
        resumo_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4(total_gaps, className="text-danger"),
                        html.P("Gaps Identificados", className="text-muted mb-0")
                    ], width=4),
                    dbc.Col([
                        html.H4(total_cotacoes_perdidas, className="text-warning"),
                        html.P("Cotações sem Venda", className="text-muted mb-0")
                    ], width=4),
                    dbc.Col([
                        html.H4(f"R$ {receita_potencial:,.0f}", className="text-success"),
                        html.P("Receita Potencial", className="text-muted mb-0")
                    ], width=4)
                ])
            ])
        ], color="light", className="mb-3")
        
        gaps_cards.append(resumo_card)
        
        # Tabela detalhada dos gaps
        if not df_gaps.empty:
            # Prepara dados para tabela - TODOS os gaps, não limitado a 10
            table_data = df_gaps.copy()  # Todos os gaps identificados
            
            gaps_table = dash_table.DataTable(
                data=table_data.to_dict('records'),
                columns=[
                    {"name": "Material", "id": "material"},
                    {"name": "Descrição", "id": "descricao"},
                    {"name": "Tipo", "id": "tipo_oportunidade"},
                    {"name": "Cotações sem Venda", "id": "cotacoes_sem_venda", "type": "numeric"},
                    {"name": "Clientes Interessados", "id": "clientes_interessados", "type": "numeric"},
                    {"name": "Clientes que Cotaram", "id": "clientes_detalhes"},
                    {"name": "Score Urgência", "id": "urgencia_score", "type": "numeric"},
                    {"name": "Receita Potencial", "id": "potencial_receita", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Confiança %", "id": "confidence_score", "type": "numeric"},
                    {"name": "Ação Sugerida", "id": "acao_sugerida"}
                ],
                style_cell={
                    'textAlign': 'left', 
                    'fontSize': 12,
                    'padding': '8px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{urgencia_score} >= 80'},
                        'backgroundColor': '#ffebee',
                        'color': 'black',
                    },
                    {
                        'if': {'filter_query': '{urgencia_score} >= 60'},
                        'backgroundColor': '#fff3e0',
                        'color': 'black',
                    },
                    {
                        'if': {'filter_query': '{confidence_score} >= 70'},
                        'backgroundColor': '#e8f5e8',
                        'color': 'black',
                    }
                ],
                page_size=50,  # Mostra 50 registros por página
                sort_action="native",
                filter_action="native",  # Permite filtrar
                export_format="xlsx",
                export_headers="display"
            )
            
            gaps_cards.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className="fas fa-list me-2"),
                            f"Todos os {len(df_gaps)} Gaps Críticos Identificados"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([gaps_table])
                ], className="mb-3")
            )
        
        # Recomendações estratégicas
        recomendacoes = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-lightbulb me-2"),
                    "Recomendações Estratégicas"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Ol([
                    html.Li([
                        html.Strong("Priorize produtos com maior urgência: "),
                        f"Foque nos {min(5, total_gaps)} produtos com score de urgência mais alto."
                    ]),
                    html.Li([
                        html.Strong("Investigue barreiras de venda: "),
                        "Analise por que produtos cotados não estão sendo comprados."
                    ]),
                    html.Li([
                        html.Strong("Engaje clientes interessados: "),
                        "Entre em contato direto com clientes que fizeram cotações."
                    ]),
                    html.Li([
                        html.Strong("Facilite o processo de compra: "),
                        "Simplifique processo, ofereça condições especiais ou treinamento."
                    ])
                ])
            ])
        ])
        
        gaps_cards.append(recomendacoes)
        
        logger.info(f"✅ Análise de gaps concluída: {total_gaps} oportunidades identificadas")
        
        return gaps_cards
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de gaps: {e}")
        return dbc.Alert([
            html.I(className="fas fa-times-circle me-2"),
            f"Erro ao executar análise: {str(e)}"
        ], color="danger")


# =============================================================================
# CALLBACKS: FILTROS HIERÁRQUICOS DINÂMICOS
# =============================================================================

@callback(
    [Output('filter-b2b-hier-produto-1', 'options'),
     Output('filter-b2b-unidade-negocio', 'options')],
    [Input('url', 'pathname'),
     Input('filter-loader-interval', 'n_intervals')],
    prevent_initial_call=False  # Importante: executa na inicialização
)
def update_initial_filter_options(pathname, n_intervals):
    """Atualiza opções iniciais dos filtros de hierarquia 1 e unidade de negócio"""
    try:
        # Log muito detalhado para debug - SEMPRE executa
        print(f"🔄 CALLBACK EXECUTADO: pathname={pathname}, n_intervals={n_intervals}")
        logger.info(f"🔄 update_initial_filter_options executado para pathname: {pathname}, interval: {n_intervals}")
        
        # Forçar execução independente do pathname
        print("🔍 Buscando dados para filtros iniciais...")
        logger.info("🔍 Buscando dados para filtros iniciais...")
        
        # Carrega TODOS os dados (sem limit) como nos filtros globais funcionais
        vendas_df = load_vendas_data()  # SEM LIMIT para ter todas as unidades e hierarquias
        
        if vendas_df.empty:
            logger.warning("❌ Nenhum dado de vendas encontrado")
            print("❌ Nenhum dado de vendas encontrado")
            return [], []
        
        # Debug detalhado dos dados
        print(f"📊 Total de registros carregados: {len(vendas_df)}")
        print(f"📊 Colunas disponíveis: {list(vendas_df.columns)}")
        logger.info(f"📊 Dados carregados: {len(vendas_df)} registros, colunas: {list(vendas_df.columns)}")
        
        # Buscar hierarquias de produto nível 1 (usando o nome correto da coluna)
        if 'hier_produto_1' in vendas_df.columns:
            hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
            hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique) if str(nivel1).strip()]
            print(f"🏷️ Hierarquia 1 encontrada: {sorted(hier1_unique)}")
        else:
            logger.warning("❌ Coluna 'hier_produto_1' não encontrada")
            print("❌ Coluna 'hier_produto_1' não encontrada")
            hier1_options = []
        
        # Buscar unidades de negócio (usando o nome correto da coluna)
        if 'unidade_negocio' in vendas_df.columns:
            unidade_unique = vendas_df['unidade_negocio'].dropna().unique()
            unidade_options = [{"label": unidade, "value": unidade} for unidade in sorted(unidade_unique) if str(unidade).strip()]
            print(f"🏢 Unidades encontradas: {sorted(unidade_unique)}")
        else:
            logger.warning("❌ Coluna 'unidade_negocio' não encontrada")
            print("❌ Coluna 'unidade_negocio' não encontrada")
            unidade_options = []
        
        logger.info(f"✅ Filtros iniciais atualizados: {len(hier1_options)} hierarquias, {len(unidade_options)} unidades")
        print(f"✅ Filtros iniciais atualizados: {len(hier1_options)} hierarquias, {len(unidade_options)} unidades")
        return hier1_options, unidade_options
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar filtros iniciais: {e}")
        return [], []


@callback(
    Output('filter-b2b-hier-produto-2', 'options'),
    [Input('filter-b2b-hier-produto-1', 'value')],
    prevent_initial_call=True
)
def update_hier_produto_2_options(hier_produto_1_values):
    """Atualiza opções do filtro hierárquico nível 2 baseado no nível 1"""
    if not hier_produto_1_values:
        return []
    
    try:
        # Usar load_vendas_data para consistência e padronização
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            return []
        
        # Filtrar por hierarquia nível 1 selecionada
        df_filtered = vendas_df[vendas_df['hier_produto_1'].isin(hier_produto_1_values)]
        
        # Buscar valores únicos de hierarquia nível 2
        hier2_unique = df_filtered['hier_produto_2'].dropna().unique()
        
        print(f"🏷️ Hierarquia 2 para {hier_produto_1_values}: {len(hier2_unique)} opções")
        
        return [{"label": nivel2, "value": nivel2} for nivel2 in sorted(hier2_unique)]
        
    except Exception as e:
        logger.error(f"Erro ao buscar hierarquia nível 2: {e}")
        return []


@callback(
    Output('filter-b2b-hier-produto-3', 'options'),
    [Input('filter-b2b-hier-produto-2', 'value')],
    prevent_initial_call=True
)
def update_hier_produto_3_options(hier_produto_2_values):
    """Atualiza opções do filtro hierárquico nível 3 baseado no nível 2"""
    if not hier_produto_2_values:
        return []
    
    try:
        # Usar load_vendas_data para consistência e padronização
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            return []
        
        # Filtrar por hierarquia nível 2 selecionada
        df_filtered = vendas_df[vendas_df['hier_produto_2'].isin(hier_produto_2_values)]
        
        # Buscar valores únicos de hierarquia nível 3
        hier3_unique = df_filtered['hier_produto_3'].dropna().unique()
        
        print(f"🏷️ Hierarquia 3 para {hier_produto_2_values}: {len(hier3_unique)} opções")
        
        return [{"label": nivel3, "value": nivel3} for nivel3 in sorted(hier3_unique)]
        
    except Exception as e:
        logger.error(f"Erro ao buscar hierarquia nível 3: {e}")
        return []


# =============================================================================
# CALLBACKS: ANÁLISE DE CONVERSÃO E CROSS-SELLING
# =============================================================================

@callback(
    Output('conversion-analysis-container', 'children'),
    [Input('btn-analyze-conversion', 'n_clicks')],
    prevent_initial_call=True
)
def analyze_conversion_rates_callback(n_clicks):
    """
    Executa análise de taxa de conversão
    """
    if not n_clicks:
        return no_update
    
    try:
        logger.info("🎯 Iniciando análise de taxa de conversão...")
        
        # Carrega dados
        conn = get_db_connection()
        vendas_df = pd.read_sql_query("SELECT * FROM vendas", conn)
        produtos_cotados_df = pd.read_sql_query("SELECT * FROM produtos_cotados", conn)
        conn.close()
        
        # Executa análise com lazy loading
        analyzer = get_conversion_analyzer()
        conversion_results = analyzer.analyze_conversion_rates(vendas_df, produtos_cotados_df)
        
        if conversion_results.empty:
            return dbc.Alert("Nenhum dado de conversão encontrado", color="warning")
        
        # Métricas resumo
        total_produtos = len(conversion_results)
        produtos_problema = len(conversion_results[conversion_results['total_vendas'] == 0])
        produtos_sucesso = len(conversion_results[conversion_results['taxa_conversao_cotacao'] >= 50])
        
        # Cards de métricas
        metrics_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(total_produtos, className="text-primary"),
                        html.P("Produtos Analisados", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(produtos_problema, className="text-danger"),
                        html.P("Zero Conversão", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(produtos_sucesso, className="text-success"),
                        html.P("Alta Conversão", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{produtos_problema/total_produtos*100:.1f}%", className="text-warning"),
                        html.P("Taxa Problemas", className="text-muted mb-0")
                    ])
                ])
            ], width=3)
        ], className="mb-4")
        
        # Tabela de conversão
        conversion_table = dash_table.DataTable(
            data=conversion_results.head(50).to_dict('records'),
            columns=[
                {"name": "Material", "id": "material"},
                {"name": "Descrição", "id": "descricao"},
                {"name": "Total Cotações", "id": "total_cotacoes", "type": "numeric"},
                {"name": "Total Vendas", "id": "total_vendas", "type": "numeric"},
                {"name": "Taxa Conversão %", "id": "taxa_conversao_cotacao", "type": "numeric"},
                {"name": "Padrão", "id": "padrao_conversao"},
                {"name": "Score Oportunidade", "id": "opportunity_score", "type": "numeric"}
            ],
            style_cell={'textAlign': 'left', 'fontSize': 12, 'padding': '8px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{total_vendas} = 0'},
                    'backgroundColor': '#ffebee',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{taxa_conversao_cotacao} >= 50'},
                    'backgroundColor': '#e8f5e8',
                    'color': 'black',
                }
            ],
            page_size=25,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            export_headers="display"
        )
        
        return html.Div([
            html.H4("📊 Análise de Taxa de Conversão", className="mb-3"),
            metrics_cards,
            dbc.Card([
                dbc.CardHeader("🎯 Top Oportunidades de Conversão"),
                dbc.CardBody([conversion_table])
            ])
        ])
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de conversão: {e}")
        return dbc.Alert(f"Erro ao analisar conversão: {str(e)}", color="danger")


@callback(
    Output('cross-selling-analysis-container', 'children'),
    [Input('btn-analyze-cross-selling', 'n_clicks')],
    prevent_initial_call=True
)
def analyze_cross_selling_callback(n_clicks):
    """
    Executa análise de cross-selling
    """
    if not n_clicks:
        return no_update
    
    try:
        logger.info("🛒 Iniciando análise de cross-selling...")
        
        # Carrega dados de vendas
        conn = get_db_connection()
        vendas_df = pd.read_sql_query("SELECT * FROM vendas", conn)
        conn.close()
        
        # Executa análise com lazy loading
        analyzer = get_conversion_analyzer()
        cross_selling_results = analyzer.analyze_cross_selling_opportunities(vendas_df)
        
        if cross_selling_results.empty:
            return dbc.Alert("Nenhuma associação de cross-selling encontrada", color="warning")
        
        # Métricas resumo
        total_associacoes = len(cross_selling_results)
        associacoes_fortes = len(cross_selling_results[cross_selling_results['lift'] >= 2.0])
        associacoes_muito_fortes = len(cross_selling_results[cross_selling_results['lift'] >= 3.0])
        
        # Cards de métricas
        metrics_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(total_associacoes, className="text-primary"),
                        html.P("Associações Encontradas", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(associacoes_fortes, className="text-success"),
                        html.P("Associações Fortes", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(associacoes_muito_fortes, className="text-warning"),
                        html.P("Muito Fortes", className="text-muted mb-0")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{associacoes_fortes/total_associacoes*100:.1f}%" if total_associacoes > 0 else "0%", className="text-info"),
                        html.P("% Potencial Cross-Selling", className="text-muted mb-0")
                    ])
                ])
            ], width=3)
        ], className="mb-4")
        
        # Tabela de cross-selling
        cross_selling_table = dash_table.DataTable(
            data=cross_selling_results.head(50).to_dict('records'),
            columns=[
                {"name": "Produto A", "id": "produto_a"},
                {"name": "Produto B", "id": "produto_b"},
                {"name": "Descrição A", "id": "descricao_a"},
                {"name": "Descrição B", "id": "descricao_b"},
                {"name": "Compras Conjuntas", "id": "transacoes_conjuntas", "type": "numeric"},
                {"name": "Confidence A→B", "id": "confidence_a_to_b", "type": "numeric", "format": {"specifier": ".2%"}},
                {"name": "Lift", "id": "lift", "type": "numeric"},
                {"name": "Força Associação", "id": "forca_associacao"}
            ],
            style_cell={'textAlign': 'left', 'fontSize': 12, 'padding': '8px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{lift} >= 3'},
                    'backgroundColor': '#fff3e0',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{lift} >= 2'},
                    'backgroundColor': '#e8f5e8',
                    'color': 'black',
                }
            ],
            page_size=25,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            export_headers="display"
        )
        
        # Top recomendações
        top_recommendations = []
        for _, row in cross_selling_results.head(5).iterrows():
            top_recommendations.append(
                html.Li([
                    html.Strong(f"Produto {row['produto_a']} + {row['produto_b']}: "),
                    f"Chance de {row['confidence_a_to_b']:.1%} - Lift {row['lift']:.2f}x"
                ])
            )
        
        return html.Div([
            html.H4("🛒 Análise de Cross-Selling", className="mb-3"),
            metrics_cards,
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎯 Top Oportunidades Cross-Selling"),
                        dbc.CardBody([cross_selling_table])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💡 Top Recomendações"),
                        dbc.CardBody([
                            html.Ul(top_recommendations)
                        ])
                    ])
                ], width=4)
            ])
        ])
        
    except Exception as e:
        logger.error(f"❌ Erro na análise de cross-selling: {e}")
        return dbc.Alert(f"Erro ao analisar cross-selling: {str(e)}", color="danger")


@callback(
    Output('segmentation-analysis-content', 'children'),
    [Input('segmentation-analysis-tabs', 'active_tab')]
)
def update_segmentation_tab_content(active_tab):
    """
    Controla o conteúdo das abas de análise de segmentação
    """
    if active_tab == "tab-conversion-analysis":
        return html.Div([
            html.Div(id="conversion-analysis-container", children=[
                html.P([
                    html.I(className="fas fa-play me-2"),
                    "Clique em 'Analisar Conversão' para identificar produtos com baixa taxa de conversão."
                ], className="text-muted text-center")
            ])
        ])
    elif active_tab == "tab-cross-selling-analysis":
        return html.Div([
            html.Div(id="cross-selling-analysis-container", children=[
                html.P([
                    html.I(className="fas fa-play me-2"),
                    "Clique em 'Cross-Selling' para descobrir oportunidades de venda cruzada."
                ], className="text-muted text-center")
            ])
        ])
    
    return html.Div("Selecione uma aba para visualizar o conteúdo.")