"""
Callbacks principais da aplicação com performance otimizada
Integração com AI Framework para preparação evolutiva
"""

from dash import Input, Output, State, callback_context, dash_table, html
import dash
import pandas as pd
import dash_bootstrap_components as dbc
from webapp import app
from webapp.auth import authenticated_callback
from utils import (
    load_vendas_data, 
    load_cotacoes_data, 
    load_produtos_cotados_data,
    KPICalculator, 
    VisualizationGenerator,
    AdvancedAnalytics,
    SENTINEL_ALL
)
from utils.cache_manager import cached_dataframe, cached_result, cache_manager
from utils.ai_framework import ai_analytics, SimpleNLPMatcher, UserInteractionLogger

# Instâncias globais para IA
ai_logger = UserInteractionLogger()
nlp_matcher = SimpleNLPMatcher()

def apply_filters(df, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra=None):
    """Aplica todos os filtros ao DataFrame de vendas de forma otimizada"""
    print(f"🔍 APPLY_FILTERS iniciado - DataFrame original: {len(df)} registros")
    print(f"   📊 Filtros recebidos:")
    print(f"      • Ano: {filtro_ano}")
    print(f"      • Mês: {filtro_mes}")
    print(f"      • Cliente: {filtro_cliente} (tipo: {type(filtro_cliente)})")
    print(f"      • Hierarquia: {filtro_hierarquia}")
    print(f"      • Canal: {filtro_canal}")
    print(f"      • Top Clientes: {filtro_top_clientes}")
    print(f"      • Dias sem compra: {filtro_dias_sem_compra}")
    
    if df is None or df.empty:
        print("   ⚠️ DataFrame vazio ou None - retornando original")
        return df
    
    df_filtrado = df.copy()
    
    # Detecta automaticamente a coluna de data
    date_column = None
    for col in ['data_faturamento', 'data', 'data_venda']:
        if col in df_filtrado.columns:
            date_column = col
            print(f"   📅 Coluna de data detectada: {date_column}")
            break
    
    try:
        # Filtro por ano - se vazio considera todos os anos
        if filtro_ano and isinstance(filtro_ano, list) and len(filtro_ano) > 0 and date_column:
            print(f"   ✅ Aplicando filtro ano: {filtro_ano}")
            registros_antes = len(df_filtrado)
            # Converte para datetime se necessário
            if not pd.api.types.is_datetime64_any_dtype(df_filtrado[date_column]):
                df_filtrado[date_column] = pd.to_datetime(df_filtrado[date_column], errors='coerce')
            df_filtrado = df_filtrado[df_filtrado[date_column].dt.year.between(filtro_ano[0], filtro_ano[1])]
            registros_depois = len(df_filtrado)
            print(f"   ✅ Filtro ano aplicado: {registros_antes} → {registros_depois} registros")
        
        # Filtro por mês - se vazio considera todos os meses
        if filtro_mes and isinstance(filtro_mes, list) and len(filtro_mes) > 0 and date_column:
            print(f"   ✅ Aplicando filtro mês: {filtro_mes}")
            registros_antes = len(df_filtrado)
            # Converte para datetime se necessário
            if not pd.api.types.is_datetime64_any_dtype(df_filtrado[date_column]):
                df_filtrado[date_column] = pd.to_datetime(df_filtrado[date_column], errors='coerce')
            df_filtrado = df_filtrado[df_filtrado[date_column].dt.month.between(filtro_mes[0], filtro_mes[1])]
            registros_depois = len(df_filtrado)
            print(f"   ✅ Filtro mês aplicado: {registros_antes} → {registros_depois} registros")
        
        # Filtro por cliente - se vazio considera todos os clientes
        if filtro_cliente and isinstance(filtro_cliente, list) and len(filtro_cliente) > 0 and 'cod_cliente' in df_filtrado.columns:
            print(f"   ✅ Aplicando filtro cliente: {filtro_cliente}")
            registros_antes = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(filtro_cliente)]
            registros_depois = len(df_filtrado)
            print(f"   ✅ Filtro cliente aplicado: {registros_antes} → {registros_depois} registros")
        elif filtro_cliente:
            print(f"   ⚠️ Filtro cliente NÃO aplicado - cliente={bool(filtro_cliente)}, tipo={type(filtro_cliente)}, lista={isinstance(filtro_cliente, list) if filtro_cliente else 'N/A'}")
            if 'cod_cliente' not in df_filtrado.columns:
                print(f"   ⚠️ Coluna 'cod_cliente' não encontrada. Colunas disponíveis: {list(df_filtrado.columns)[:10]}")
        
        # Filtro por hierarquia - detecta automaticamente colunas de hierarquia
        if filtro_hierarquia and isinstance(filtro_hierarquia, list) and len(filtro_hierarquia) > 0:
            print(f"   ✅ Aplicando filtro hierarquia: {filtro_hierarquia}")
            registros_antes = len(df_filtrado)
            
            # Mapeia hierarquia para colunas disponíveis (detecta automaticamente)
            hier_cols = []
            for col in df_filtrado.columns:
                if any(keyword in col.lower() for keyword in ['hier', 'produto', 'material', 'categoria']):
                    hier_cols.append(col)
            
            if hier_cols:
                print(f"   📋 Colunas de hierarquia detectadas: {hier_cols}")
                mask = pd.Series(False, index=df_filtrado.index)
                for col in hier_cols:
                    mask |= df_filtrado[col].isin(filtro_hierarquia)
                if mask.any():
                    df_filtrado = df_filtrado[mask]
                    registros_depois = len(df_filtrado)
                    print(f"   ✅ Filtro hierarquia aplicado: {registros_antes} → {registros_depois} registros")
                else:
                    print(f"   ⚠️ Nenhum registro encontrado com hierarquia: {filtro_hierarquia}")
            else:
                print(f"   ⚠️ Nenhuma coluna de hierarquia detectada")
        
        # Filtro por canal - detecta automaticamente colunas de canal
        if filtro_canal and isinstance(filtro_canal, list) and len(filtro_canal) > 0:
            print(f"   ✅ Aplicando filtro canal: {filtro_canal}")
            registros_antes = len(df_filtrado)
            
            # Detecta coluna de canal automaticamente
            canal_col = None
            for col in ['canal_distribuicao', 'canal', 'distribui', 'vendedor']:
                if col in df_filtrado.columns:
                    canal_col = col
                    break
            
            if canal_col:
                print(f"   📋 Coluna de canal detectada: {canal_col}")
                df_filtrado = df_filtrado[df_filtrado[canal_col].isin(filtro_canal)]
                registros_depois = len(df_filtrado)
                print(f"   ✅ Filtro canal aplicado: {registros_antes} → {registros_depois} registros")
            else:
                print(f"   ⚠️ Coluna de canal não encontrada. Colunas disponíveis: {list(df_filtrado.columns)[:10]}")
        
        # Filtro por produto - permite análise granular por produtos específicos
        # (Não está nos filtros globais padrão, mas pode ser usado por análises específicas)
        if hasattr(filtro_top_clientes, '__iter__') and not isinstance(filtro_top_clientes, str):
            # Se filtro_top_clientes for uma lista de produtos (hack para reutilizar parâmetro)
            produto_filter = filtro_top_clientes if isinstance(filtro_top_clientes, list) else None
            if produto_filter and len(produto_filter) > 0:
                print(f"   ✅ Aplicando filtro produto: {produto_filter}")
                registros_antes = len(df_filtrado)
                
                # Detecta coluna de produto automaticamente
                produto_col = None
                for col in ['produto', 'material', 'item', 'descricao_produto']:
                    if col in df_filtrado.columns:
                        produto_col = col
                        break
                
                if produto_col:
                    print(f"   📋 Coluna de produto detectada: {produto_col}")
                    df_filtrado = df_filtrado[df_filtrado[produto_col].isin(produto_filter)]
                    registros_depois = len(df_filtrado)
                    print(f"   ✅ Filtro produto aplicado: {registros_antes} → {registros_depois} registros")
                else:
                    print(f"   ⚠️ Coluna de produto não encontrada. Colunas disponíveis: {list(df_filtrado.columns)[:10]}")
        
        # Filtro por dias sem compra - CORRIGIDO para RangeSlider
        if filtro_dias_sem_compra and isinstance(filtro_dias_sem_compra, list) and len(filtro_dias_sem_compra) == 2:
            min_dias, max_dias = filtro_dias_sem_compra
            print(f"   ✅ Aplicando filtro dias sem compra: {min_dias} a {max_dias} dias")
            
            # Se o range é o padrão [0, 1095], não aplica filtro
            if min_dias == 0 and max_dias == 1095:
                print(f"   ⚠️ Range padrão [0, 365] - não aplicando filtro")
            elif date_column and 'cod_cliente' in df_filtrado.columns:
                from datetime import datetime, timedelta
                
                # Converte a coluna data para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(df_filtrado[date_column]):
                    df_filtrado[date_column] = pd.to_datetime(df_filtrado[date_column], errors='coerce')
                
                # Calcula as datas limite
                data_limite_min = datetime.now() - timedelta(days=max_dias)  # Mais antiga (max dias atrás)
                data_limite_max = datetime.now() - timedelta(days=min_dias)  # Mais recente (min dias atrás)
                print(f"   📅 Data limite mínima: {data_limite_min.strftime('%Y-%m-%d')}")
                print(f"   📅 Data limite máxima: {data_limite_max.strftime('%Y-%m-%d')}")
                
                # Pega a última compra por cliente
                ultima_compra = df_filtrado.groupby('cod_cliente')[date_column].max()
                print(f"   👥 Total clientes antes do filtro: {len(ultima_compra)}")
                
                # Filtra clientes que não compraram no range especificado
                # última compra entre data_limite_min e data_limite_max
                clientes_filtrados = ultima_compra[
                    (ultima_compra >= data_limite_min) & (ultima_compra <= data_limite_max)
                ].index
                print(f"   👥 Clientes com última compra entre {min_dias} e {max_dias} dias atrás: {len(clientes_filtrados)}")
                
                # Aplica o filtro
                if len(clientes_filtrados) > 0:
                    registros_antes = len(df_filtrado)
                    df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(clientes_filtrados)]
                    registros_depois = len(df_filtrado)
                    print(f"   ✅ Filtro dias sem compra aplicado: {registros_antes} → {registros_depois} registros")
                else:
                    print("   ⚠️ Nenhum cliente encontrado no range especificado - retornando DataFrame vazio")
                    # Retorna DataFrame vazio mas com as mesmas colunas
                    df_filtrado = df_filtrado.iloc[0:0]
        else:
            if filtro_dias_sem_compra:
                print(f"   ⚠️ Filtro dias sem compra inválido: {filtro_dias_sem_compra} (tipo: {type(filtro_dias_sem_compra)})")
        
        # Filtro Top N clientes - só aplica se especificado E maior que 0
        # Se vazio ou 0, considera TODOS os clientes
        if filtro_top_clientes and isinstance(filtro_top_clientes, (int, float)) and filtro_top_clientes > 0:
            print(f"   ✅ Aplicando filtro top {filtro_top_clientes} clientes")
            registros_antes = len(df_filtrado)
            
            # Detecta coluna de valor automaticamente
            valor_col = None
            for col in ['vlr_rol', 'valor_liquido', 'vlr_entrada', 'vlr_carteira', 'faturamento']:
                if col in df_filtrado.columns:
                    valor_col = col
                    break
            
            if valor_col and 'cod_cliente' in df_filtrado.columns:
                print(f"   📋 Coluna de valor detectada: {valor_col}")
                # Agrupa por cliente e calcula o total faturado
                cliente_totals = df_filtrado.groupby('cod_cliente')[valor_col].sum()
                top_clientes = cliente_totals.nlargest(int(filtro_top_clientes)).index
                df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(top_clientes)]
                registros_depois = len(df_filtrado)
                print(f"   ✅ Filtro Top {filtro_top_clientes} aplicado: {registros_antes} → {registros_depois} registros - {len(top_clientes)} clientes selecionados")
            else:
                print(f"   ⚠️ Colunas necessárias não encontradas para filtro Top N (valor_col: {valor_col})")
        else:
            print(f"   📝 Top clientes vazio ou zero - considerando TODOS os clientes")
        
        print(f"🏁 APPLY_FILTERS finalizado - DataFrame resultante: {len(df_filtrado)} registros")
        if df_filtrado.empty:
            print(f"   ⚠️ ATENÇÃO: DataFrame final está VAZIO!")
        
        return df_filtrado
        
    except Exception as e:
        print(f"   ❌ Erro ao aplicar filtros: {e}")
        return df

def determine_hierarchy_level(df_filtrado, filtro_hierarquia):
    """
    Determina qual nível de hierarquia usar baseado na lógica inteligente:
    - Se nenhum filtro: mostra hier_produto_1
    - Se filtro de hier_produto_1: mostra hier_produto_2
    - Se filtro de hier_produto_2: mostra hier_produto_3
    - Se filtro de hier_produto_3: mostra produtos individuais (top N)
    """
    
    # Se não há filtro de hierarquia, usa o nível 1 (padrão)
    if not filtro_hierarquia or not isinstance(filtro_hierarquia, list) or len(filtro_hierarquia) == 0:
        print("   🎯 Sem filtro hierarquia - usando hier_produto_1")
        return 1, 'hier_produto_1'
    
    # Verifica em qual nível de hierarquia estão os valores filtrados
    hierarchy_cols = ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']
    
    for level, col in enumerate(hierarchy_cols, 1):
        if col in df_filtrado.columns:
            # Verifica se algum valor do filtro está nesta coluna
            unique_values = df_filtrado[col].dropna().unique()
            if any(valor in unique_values for valor in filtro_hierarquia):
                next_level = level + 1
                next_col = f'hier_produto_{next_level}' if next_level <= 3 else 'produto'
                
                print(f"   🎯 Filtro encontrado no nível {level} ({col}) - próximo nível: {next_level} ({next_col})")
                
                # Se estamos no nível 3, retornamos produtos individuais
                if next_level > 3:
                    return 4, 'produto'  # Produtos individuais
                else:
                    return next_level, next_col
    
    # Se não encontrou correspondência, usa o padrão
    print("   🎯 Filtro não encontrado em hierarquias - usando hier_produto_1")
    return 1, 'hier_produto_1'

# Importa outros módulos de callbacks
try:
    import webapp.callbacks_uploads
    print("✅ Callbacks de upload carregados")
except ImportError as e:
    print(f"⚠️ Erro ao carregar callbacks de upload: {e}")

try:
    import webapp.callbacks_downloads
    print("✅ Callbacks de download carregados")  
except ImportError as e:
    print(f"⚠️ Callbacks de download não disponíveis: {e}")

# Instâncias dos calculadores
kpi_calc = KPICalculator()
viz_gen = VisualizationGenerator()

# Stores para dados
from dash import dcc
import dash_bootstrap_components as dbc

# =======================================
# CALLBACKS INDIVIDUAIS PARA CADA COMPONENTE
# =======================================
# CALLBACKS INDIVIDUAIS PARA OVERVIEW
# =======================================

# Callback para KPI de Entrada de Pedidos - REATIVO A FILTROS
@app.callback(
    Output('kpi-entrada-pedidos', 'children'),
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value')],
    prevent_initial_call=False
)
def update_kpi_entrada(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra):
    """Atualiza KPI de Entrada de Pedidos - Thread Safe"""
    print(f"🔄 UPDATE_KPI_ENTRADA executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros adicionais: hierarquia={filtro_hierarquia}, canal={filtro_canal}, top_clientes={filtro_top_clientes}")
    
    if pathname not in ['/', '/app', '/app/', '/app/overview']:
        return "R$ 0"
    
    try:
        vendas_df = load_vendas_data()
        if vendas_df.empty:
            return "R$ 0"
            
        # Aplica todos os filtros usando função auxiliar
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        entrada_valor = df_filtrado['vlr_entrada'].sum() if 'vlr_entrada' in df_filtrado.columns else 0
        print(f"💰 KPI Entrada calculado: {entrada_valor:,.0f} (de {len(df_filtrado)} registros)")
        return f"R$ {entrada_valor:,.0f}"
        
    except Exception as e:
        print(f"❌ Erro em update_kpi_entrada: {e}")
        return "Erro"

# Callback para KPI de Carteira - REATIVO A FILTROS
@app.callback(
    Output('kpi-valor-carteira', 'children'),
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value')],
    prevent_initial_call=False
)
def update_kpi_carteira(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra):
    """Atualiza KPI de Valor Carteira - Thread Safe"""
    print(f"🔄 UPDATE_KPI_CARTEIRA executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros adicionais: hierarquia={filtro_hierarquia}, canal={filtro_canal}, top_clientes={filtro_top_clientes}")
    
    if pathname not in ['/', '/app', '/app/', '/app/overview']:
        return "R$ 0"
    
    try:
        vendas_df = load_vendas_data()
        if vendas_df.empty:
            return "R$ 0"
            
        # Aplica todos os filtros usando função auxiliar
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        carteira_valor = df_filtrado['vlr_carteira'].sum() if 'vlr_carteira' in df_filtrado.columns else 0
        print(f"💰 KPI Carteira calculado: {carteira_valor:,.0f} (de {len(df_filtrado)} registros)")
        return f"R$ {carteira_valor:,.0f}"
        
    except Exception as e:
        print(f"❌ Erro em update_kpi_carteira: {e}")
        return "Erro"

# Callback para KPI de Faturamento - REATIVO A FILTROS
@app.callback(
    Output('kpi-faturamento', 'children'),
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value')],
    prevent_initial_call=False
)
def update_kpi_faturamento(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra):
    """Atualiza KPI de Faturamento - Thread Safe"""
    print(f"🔄 UPDATE_KPI_FATURAMENTO executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros adicionais: hierarquia={filtro_hierarquia}, canal={filtro_canal}, top_clientes={filtro_top_clientes}")
    
    if pathname not in ['/', '/app', '/app/', '/app/overview']:
        return "R$ 0"
    
    try:
        vendas_df = load_vendas_data()
        if vendas_df.empty:
            return "R$ 0"
            
        # Aplica todos os filtros usando função auxiliar
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        faturamento_valor = df_filtrado['vlr_rol'].sum() if 'vlr_rol' in df_filtrado.columns else 0
        print(f"💰 KPI Faturamento calculado: {faturamento_valor:,.0f} (de {len(df_filtrado)} registros)")
        return f"R$ {faturamento_valor:,.0f}"
        
    except Exception as e:
        print(f"❌ Erro em update_kpi_faturamento: {e}")
        return "Erro"

# Callback para gráfico de evolução - REATIVO A FILTROS
@app.callback(
    Output('grafico-evolucao-vendas', 'figure'),
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value')],
    prevent_initial_call=False
)
def update_grafico_evolucao(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra):
    """Atualiza gráfico de evolução de vendas"""
    print(f"🔄 UPDATE_GRAFICO_EVOLUCAO executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros adicionais: hierarquia={filtro_hierarquia}, canal={filtro_canal}, top_clientes={filtro_top_clientes}")
    
    if pathname not in ['/', '/app', '/app/', '/app/overview']:
        import plotly.graph_objects as go
        return go.Figure()
    
    try:
        vendas_df = load_vendas_data()
        if vendas_df.empty:
            import plotly.graph_objects as go
            return go.Figure()
            
        # Aplica todos os filtros usando função auxiliar
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        # Gráfico de evolução
        import plotly.graph_objects as go
        fig_vendas = go.Figure()
        if not df_filtrado.empty and 'data' in df_filtrado.columns:
            vendas_mes = df_filtrado.groupby(df_filtrado['data'].dt.strftime('%Y-%m'))['vlr_rol'].sum().sort_index()
            fig_vendas.add_trace(go.Scatter(
                x=vendas_mes.index, 
                y=vendas_mes.values,
                mode='lines+markers',
                name='Vendas',
                line=dict(color='#007bff', width=3),
                marker=dict(size=8)
            ))
            fig_vendas.update_layout(
                title="Evolução de Vendas",
                xaxis_title="Período",
                yaxis_title="Valor (R$)",
                template="plotly_white",
                height=400
            )
        
        print(f"📈 Gráfico de evolução criado com {len(vendas_mes) if 'vendas_mes' in locals() else 0} pontos (de {len(df_filtrado)} registros)")
        return fig_vendas
        
    except Exception as e:
        print(f"❌ Erro em update_grafico_evolucao: {e}")
        import plotly.graph_objects as go
        return go.Figure()

# Callback para KPIs por Unidade de Negócio - REATIVO A FILTROS
@app.callback(
    Output('kpis-unidades-negocio', 'children'),
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value')],
    prevent_initial_call=False
)
def update_kpis_unidades_negocio(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra):
    """Atualiza KPIs por Unidade de Negócio - Corrigido"""
    print(f"🔄 UPDATE_KPIS_UNIDADES_NEGOCIO executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros adicionais: hierarquia={filtro_hierarquia}, canal={filtro_canal}, top_clientes={filtro_top_clientes}")
    
    if pathname not in ['/', '/app', '/app/', '/app/overview']:
        return []
    
    try:
        vendas_df = load_vendas_data()
        if vendas_df.empty:
            return []
            
        # Aplica todos os filtros usando função auxiliar
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        # KPIs por Unidade de Negócio
        kpis_un = []
        if not df_filtrado.empty and 'unidade_negocio' in df_filtrado.columns:
            un_stats = df_filtrado.groupby('unidade_negocio')['vlr_rol'].sum().sort_values(ascending=False)
            
            import dash_bootstrap_components as dbc
            for un, valor in un_stats.head(6).items():
                kpi_card = dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6(f"R$ {valor:,.0f}", className="card-title text-secondary"),
                            html.P(str(un), className="card-text small")
                        ])
                    ], className="text-center h-100 mb-2")
                ], width=12, md=2)
                kpis_un.append(kpi_card)
        
        print(f"🏢 KPIs por Unidade de Negócio criados: {len(kpis_un)} cards (de {len(df_filtrado)} registros)")
        return kpis_un
        
    except Exception as e:
        print(f"❌ Erro em update_kpis_unidades_negocio: {e}")
        return []

# Registrar callbacks do chat
try:
    from webapp.chat_interface import register_chat_callbacks
    register_chat_callbacks(app)
    print("✅ Callbacks do chat registrados com sucesso")
except Exception as e:
    print(f"⚠️ Erro ao registrar callbacks do chat: {e}")

# Callback para mostrar conteúdo baseado na página
@app.callback(
    Output('page-main-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
def display_page_content(pathname):
    """Mostra o conteúdo correto baseado na URL"""
    print(f"🔄 DISPLAY_PAGE_CONTENT executado para: {pathname}")
    
    try:
        if pathname == '/app/chat':
            from webapp.layouts import create_chat_layout
            return create_chat_layout()
        elif pathname == '/app/overview' or pathname == '/app' or pathname == '/':
            from webapp.layouts import create_overview_layout
            return create_overview_layout()
        elif pathname == '/app/clients':
            from webapp.layouts import create_clients_layout
            return create_clients_layout()
        elif pathname == '/app/products':
            from webapp.layouts import create_products_layout
            return create_products_layout()
        elif pathname == '/app/funnel':
            from webapp.layouts import create_funnel_layout
            return create_funnel_layout()
        elif pathname == '/app/insights':
            from webapp.layouts import create_insights_layout
            return create_insights_layout()
        elif pathname == '/app/analytics':
            from webapp.layouts import create_analytics_layout
            return create_analytics_layout()
        elif pathname == '/app/config':
            from webapp.layouts import create_config_layout
            return create_config_layout()
        else:
            return html.Div([
                dbc.Alert("Página não encontrada", color="warning")
            ])
    except Exception as e:
        print(f"❌ Erro em display_page_content: {e}")
        return html.Div([
            dbc.Alert(f"Erro ao carregar página: {str(e)}", color="danger")
        ])

print("✅ Callbacks principais registrados com sucesso")
