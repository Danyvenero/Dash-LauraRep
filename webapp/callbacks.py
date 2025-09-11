"""
Callbacks principais da aplicação com performance otimizada
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
    SENTINEL_ALL
)
from utils.cache_manager import cached_dataframe, cached_result, cache_manager

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
    
    df_filtrado = df.copy()
    
    try:
        # Filtro por ano - se vazio considera todos os anos
        if filtro_ano and isinstance(filtro_ano, list) and len(filtro_ano) > 0 and 'data' in df_filtrado.columns:
            print(f"   Aplicando filtro ano: {filtro_ano}")
            df_filtrado = df_filtrado[df_filtrado['data'].dt.year.between(filtro_ano[0], filtro_ano[1])]
        
        # Filtro por mês - se vazio considera todos os meses
        if filtro_mes and isinstance(filtro_mes, list) and len(filtro_mes) > 0 and 'data' in df_filtrado.columns:
            print(f"   Aplicando filtro mes: {filtro_mes}")
            df_filtrado = df_filtrado[df_filtrado['data'].dt.month.between(filtro_mes[0], filtro_mes[1])]
        
        # Filtro por cliente - se vazio considera todos os clientes
        if filtro_cliente and isinstance(filtro_cliente, list) and len(filtro_cliente) > 0 and 'cod_cliente' in df_filtrado.columns:
            print(f"   ✅ Aplicando filtro cliente: {filtro_cliente}")
            registros_antes = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(filtro_cliente)]
            registros_depois = len(df_filtrado)
            print(f"   ✅ Filtro cliente aplicado: {registros_antes} → {registros_depois} registros")
        else:
            print(f"   ⚠️ Filtro cliente NÃO aplicado - Motivo: cliente={filtro_cliente}, tipo={type(filtro_cliente)}, vazio={not filtro_cliente}, lista={isinstance(filtro_cliente, list) if filtro_cliente else 'N/A'}")
            if filtro_cliente and isinstance(filtro_cliente, list):
                print(f"   ⚠️ Tamanho da lista: {len(filtro_cliente)}")
            if 'cod_cliente' not in df_filtrado.columns:
                print(f"   ⚠️ Coluna 'cod_cliente' não encontrada nas colunas: {list(df_filtrado.columns)[:5]}...")
        
        # Filtro por hierarquia - se vazio considera todas as hierarquias
        if filtro_hierarquia and isinstance(filtro_hierarquia, list) and len(filtro_hierarquia) > 0:
            print(f"   Aplicando filtro hierarquia: {filtro_hierarquia}")
            # Mapeia hierarquia para colunas disponíveis
            hier_cols = ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']
            mask = pd.Series(False, index=df_filtrado.index)
            for col in hier_cols:
                if col in df_filtrado.columns:
                    mask |= df_filtrado[col].isin(filtro_hierarquia)
            if mask.any():
                df_filtrado = df_filtrado[mask]
        
        # Filtro por canal - se vazio considera todos os canais
        if filtro_canal and isinstance(filtro_canal, list) and len(filtro_canal) > 0:
            print(f"   Aplicando filtro canal: {filtro_canal}")
            if 'canal_distribuicao' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['canal_distribuicao'].isin(filtro_canal)]
        
        # Filtro por dias sem compra - CORRIGIDO para RangeSlider
        if filtro_dias_sem_compra and isinstance(filtro_dias_sem_compra, list) and len(filtro_dias_sem_compra) == 2:
            min_dias, max_dias = filtro_dias_sem_compra
            print(f"   Aplicando filtro dias sem compra: {min_dias} a {max_dias} dias")
            
            # Se o range é o padrão [0, 365], não aplica filtro
            if min_dias == 0 and max_dias == 365:
                print(f"   ⚠️ Range padrão [0, 365] - não aplicando filtro")
            elif 'data' in df_filtrado.columns and 'cod_cliente' in df_filtrado.columns:
                from datetime import datetime, timedelta
                
                # Converte a coluna data para datetime se necessário
                df_filtrado['data'] = pd.to_datetime(df_filtrado['data'])
                
                # Calcula as datas limite
                data_limite_min = datetime.now() - timedelta(days=max_dias)  # Mais antiga (max dias atrás)
                data_limite_max = datetime.now() - timedelta(days=min_dias)  # Mais recente (min dias atrás)
                print(f"   Data limite mínima: {data_limite_min}")
                print(f"   Data limite máxima: {data_limite_max}")
                
                # Pega a última compra por cliente
                ultima_compra = df_filtrado.groupby('cod_cliente')['data'].max()
                print(f"   Total clientes antes do filtro: {len(ultima_compra)}")
                
                # Filtra clientes que não compraram no range especificado
                # última compra entre data_limite_min e data_limite_max
                clientes_filtrados = ultima_compra[
                    (ultima_compra >= data_limite_min) & (ultima_compra <= data_limite_max)
                ].index
                print(f"   Clientes com última compra entre {min_dias} e {max_dias} dias atrás: {len(clientes_filtrados)}")
                
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
            print(f"   Aplicando filtro top {filtro_top_clientes} clientes")
            # Usar vlr_rol ao invés de vlr_faturamento
            if 'vlr_rol' in df_filtrado.columns and 'cod_cliente' in df_filtrado.columns:
                # Agrupa por cliente e calcula o total faturado
                cliente_totals = df_filtrado.groupby('cod_cliente')['vlr_rol'].sum()
                top_clientes = cliente_totals.nlargest(int(filtro_top_clientes)).index
                df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(top_clientes)]
                print(f"   ✅ Filtro Top {filtro_top_clientes} aplicado - {len(top_clientes)} clientes selecionados")
            else:
                print(f"   ⚠️ Colunas necessárias não encontradas para filtro Top N")
        else:
            print(f"   📝 Top clientes vazio ou zero - considerando TODOS os clientes")
        
        print(f"🏁 APPLY_FILTERS finalizado - DataFrame resultante: {len(df_filtrado)} registros")
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
                            html.H6(f"R$ {valor:,.0f}", className="card-title text-primary"),
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
    # print(f"🔄 UPDATE_OVERVIEW_KPIS EXECUTADO!")
    # print(f"   pathname: {pathname}")
    # print(f"   ano={filtro_ano} (tipo: {type(filtro_ano)})")
    # print(f"   mes={filtro_mes} (tipo: {type(filtro_mes)})")
    # print(f"   cliente={filtro_cliente} (tipo: {type(filtro_cliente)})")
    # print(f"   hierarquia={filtro_hierarquia} (tipo: {type(filtro_hierarquia)})")
    # print(f"   canal={filtro_canal} (tipo: {type(filtro_canal)})")
    
    # # Só executa se estiver na página Overview
    # if pathname and pathname not in ['/', '/app', '/app/', '/app/overview']:
    #     print(f"❌ Não é página Overview: {pathname} - retornando valores vazios")
    #     import plotly.graph_objects as go
    #     empty_fig = go.Figure()
    #     return "R$ 0", "R$ 0", "R$ 0", [], empty_fig
    
    # try:
    #     # Carrega dados
    #     vendas_df = load_vendas_data()
    #     print(f"📊 Dados carregados - Shape: {vendas_df.shape}")
    #     print(f"📊 Colunas disponíveis: {list(vendas_df.columns)}")
        
    #     if vendas_df.empty:
    #         print("❌ Dados de vendas vazios")
    #         return "R$ 0", "R$ 0", "R$ 0", [], {}
            
    #     # Debug: valores originais antes dos filtros
    #     print(f"💰 Valores ANTES dos filtros:")
    #     entrada_original = vendas_df['vlr_entrada'].sum() if 'vlr_entrada' in vendas_df.columns else 0
    #     carteira_original = vendas_df['vlr_carteira'].sum() if 'vlr_carteira' in vendas_df.columns else 0  
    #     faturamento_original = vendas_df['vlr_rol'].sum() if 'vlr_rol' in vendas_df.columns else 0
    #     print(f"   Entrada: {entrada_original:,.0f}")
    #     print(f"   Carteira: {carteira_original:,.0f}") 
    #     print(f"   Faturamento: {faturamento_original:,.0f}")
            
    #     # Aplica filtros
    #     df_filtrado = vendas_df.copy()
    #     registros_inicial = len(df_filtrado)
        
    #     # Filtro por ano
    #     if filtro_ano and 'data' in df_filtrado.columns:
    #         print(f"🔍 Aplicando filtro de ano: {filtro_ano}")
    #         df_filtrado = df_filtrado[df_filtrado['data'].dt.year.isin(filtro_ano)]
    #         print(f"   Registros após filtro ano: {len(df_filtrado)} de {registros_inicial}")
            
    #     # Filtro por mês
    #     if filtro_mes and 'data' in df_filtrado.columns:
    #         print(f"🔍 Aplicando filtro de mês: {filtro_mes}")
    #         df_filtrado = df_filtrado[df_filtrado['data'].dt.month.isin(filtro_mes)]
    #         print(f"   Registros após filtro mês: {len(df_filtrado)}")
            
    #     # Filtro por cliente
    #     if filtro_cliente and 'cod_cliente' in df_filtrado.columns:
    #         print(f"🔍 Aplicando filtro de cliente: {filtro_cliente}")
    #         df_filtrado = df_filtrado[df_filtrado['cod_cliente'].isin(filtro_cliente)]
    #         print(f"   Registros após filtro cliente: {len(df_filtrado)}")
            
    #     # Filtro por hierarquia
    #     if filtro_hierarquia and 'hierarquia_produto' in df_filtrado.columns:
    #         print(f"🔍 Aplicando filtro de hierarquia: {filtro_hierarquia}")
    #         df_filtrado = df_filtrado[df_filtrado['hierarquia_produto'].isin(filtro_hierarquia)]
    #         print(f"   Registros após filtro hierarquia: {len(df_filtrado)}")
            
    #     # Filtro por canal
    #     if filtro_canal and 'canal' in df_filtrado.columns:
    #         print(f"🔍 Aplicando filtro de canal: {filtro_canal}")
    #         df_filtrado = df_filtrado[df_filtrado['canal'].isin(filtro_canal)]
    #         print(f"   Registros após filtro canal: {len(df_filtrado)}")
        
    #     print(f"📊 RESULTADO FINAL: {len(df_filtrado)} registros de {len(vendas_df)} originais")
        
    #     # Calcula KPIs
    #     if not df_filtrado.empty:
    #         entrada_valor = df_filtrado['vlr_entrada'].sum() if 'vlr_entrada' in df_filtrado.columns else 0
    #         carteira_valor = df_filtrado['vlr_carteira'].sum() if 'vlr_carteira' in df_filtrado.columns else 0
    #         faturamento_valor = df_filtrado['vlr_rol'].sum() if 'vlr_rol' in df_filtrado.columns else 0
            
    #         print(f"💰 Valores APÓS filtros:")
    #         print(f"   Entrada: {entrada_valor:,.0f}")
    #         print(f"   Carteira: {carteira_valor:,.0f}")
    #         print(f"   Faturamento: {faturamento_valor:,.0f}")
    #         carteira_valor = df_filtrado['vlr_carteira'].sum() if 'vlr_carteira' in df_filtrado.columns else 0
    #         faturamento_valor = df_filtrado['vlr_rol'].sum() if 'vlr_rol' in df_filtrado.columns else 0
            
    #         entrada_str = f"R$ {entrada_valor:,.0f}"
    #         carteira_str = f"R$ {carteira_valor:,.0f}"
    #         faturamento_str = f"R$ {faturamento_valor:,.0f}"
    #     else:
    #         entrada_str = carteira_str = faturamento_str = "R$ 0"
        
    #     # KPIs por Unidade de Negócio
    #     kpis_un = []
    #     if not df_filtrado.empty and 'unidade_negocio' in df_filtrado.columns:
    #         un_stats = df_filtrado.groupby('unidade_negocio')['vlr_rol'].sum().sort_values(ascending=False)
            
    #         import dash_bootstrap_components as dbc
    #         for un, valor in un_stats.head(6).items():
    #             kpi_card = dbc.Col([
    #                 dbc.Card([
    #                     dbc.CardBody([
    #                         html.H6(f"R$ {valor:,.0f}", className="card-title text-primary"),
    #                         html.P(str(un), className="card-text small")
    #                     ])
    #                 ], className="text-center h-100")
    #             ], width=12, md=2)
    #             kpis_un.append(kpi_card)
        
    #     # Gráfico de evolução
    #     import plotly.graph_objects as go
    #     fig_vendas = go.Figure()
    #     if not df_filtrado.empty and 'data' in df_filtrado.columns:
    #         vendas_mes = df_filtrado.groupby(df_filtrado['data'].dt.strftime('%Y-%m'))['vlr_rol'].sum().sort_index()
    #         fig_vendas.add_trace(go.Scatter(
    #             x=vendas_mes.index, 
    #             y=vendas_mes.values,
    #             mode='lines+markers',
    #             name='Vendas',
    #             line=dict(color='#007bff', width=3),
    #             marker=dict(size=8)
    #         ))
    #         fig_vendas.update_layout(
    #             title="Evolução de Vendas",
    #             xaxis_title="Período",
    #             yaxis_title="Valor (R$)",
    #             template="plotly_white",
    #             height=400
    #         )
        
    #     print(f"✅ KPIs calculados: Entrada={entrada_str}, Carteira={carteira_str}, Faturamento={faturamento_str}")
        
    #     return entrada_str, carteira_str, faturamento_str, kpis_un, fig_vendas
        
    # except Exception as e:
    #     print(f"❌ Erro no update_overview_kpis: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     import plotly.graph_objects as go
    #     empty_fig = go.Figure()
    #     return "Erro", "Erro", "Erro", [], empty_fig

# Callback para carregar opções dos filtros globais
@app.callback(
    [Output('global-filtro-cliente', 'options'),
     Output('global-filtro-hierarquia', 'options'),
     Output('global-filtro-canal', 'options')],
    [Input('url', 'pathname')],
    prevent_initial_call=False  # MUDANÇA: Permitir execução inicial
)
# @authenticated_callback  # TEMPORARIAMENTE REMOVIDO PARA TESTE
def update_filter_options(pathname):
    """Atualiza opções dos filtros globais"""
    print(f"🔄 update_filter_options executado para pathname: {pathname}")
    try:
        # Carrega dados
        vendas_df = load_vendas_data()
        print(f"📊 Dados carregados: {len(vendas_df)} registros de vendas")
        
        if vendas_df.empty:
            print("❌ Nenhum dado de vendas encontrado")
            return [], [], []
        
        # Opções de clientes
        cliente_options = []
        if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
            clientes_unique = vendas_df[['cod_cliente', 'cliente']].drop_duplicates()
            cliente_options = [
                {'label': f"{row['cod_cliente']} -- {row['cliente']}", 'value': row['cod_cliente']}
                for _, row in clientes_unique.iterrows()
                if not pd.isna(row['cod_cliente']) and not pd.isna(row['cliente'])
            ]
        print(f"✅ Clientes: {len(cliente_options)} opções")
        
        # Opções de hierarquia de produto
        hierarquia_options = []
        for col in ['hier_produto_1', 'hier_produto_2', 'hier_produto_3']:
            if col in vendas_df.columns:
                unique_vals = vendas_df[col].dropna().unique()
                for val in unique_vals:
                    if val not in [opt['value'] for opt in hierarquia_options]:
                        hierarquia_options.append({'label': str(val), 'value': str(val)})
        print(f"✅ Hierarquia: {len(hierarquia_options)} opções")
        
        # Opções de canal
        canal_options = []
        if 'canal_distribuicao' in vendas_df.columns:
            unique_canais = vendas_df['canal_distribuicao'].dropna().unique()
            canal_options = [{'label': str(canal), 'value': str(canal)} for canal in unique_canais]
        print(f"✅ Canais: {len(canal_options)} opções")
        
        return cliente_options, hierarquia_options, canal_options
        
    except Exception as e:
        print(f"❌ Erro ao atualizar filtros: {e}")
        import traceback
        traceback.print_exc()
        return [], [], []

# TEMPORARIAMENTE DESABILITADO - callback agora está no force_update_all_components
# Callback para KPIs da visão geral
# @app.callback(
#     [Output('kpi-entrada-pedidos', 'children'),
#      Output('kpi-valor-carteira', 'children'), 
#      Output('kpi-faturamento', 'children'),
#      Output('kpi-entrada-variacao', 'children'),
#      Output('kpi-carteira-variacao', 'children'),
#      Output('kpi-faturamento-variacao', 'children'),
#      Output('kpis-unidades-negocio', 'children')],
#     [Input('url', 'pathname'),  # Trigger principal
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value')],
#     prevent_initial_call=False  # SEMPRE executa
# )
# def update_overview_kpis(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal):
# def update_overview_kpis(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal):
#     """Atualiza KPIs da visão geral"""
#     print(f"🔄 update_overview_kpis EXECUTADO para {pathname} com filtros: ano={filtro_ano}, mes={filtro_mes}")
#     
#     # MUDANÇA: Sempre calcula se for página da visão geral
#     if pathname and not any(x in pathname for x in ["/app/overview", "/app", "/"]):
#         print(f"❌ Página {pathname} não é visão geral - retornando valores vazios")
#         return "R$ 0", "R$ 0", "R$ 0", "0%", "0%", "0%", []
#     
#     try:
#         # Carrega dados
#         vendas_df = load_vendas_data()
#         cotacoes_df = load_cotacoes_data()
#         produtos_df = load_produtos_cotados_data()
#         
#         print(f"📊 Dados carregados - Vendas: {len(vendas_df)}, Cotações: {len(cotacoes_df)}, Produtos: {len(produtos_df)}")
#         
#         # VERSÃO SIMPLIFICADA TEMPORÁRIA - sem usar KPICalculator
#         if vendas_df.empty:
#             print("❌ Dados de vendas vazios")
#             return "R$ 0", "R$ 0", "R$ 0", "0%", "0%", "0%", []
#         
#         # Cálculos básicos sem filtros por enquanto
#         entrada_valor = vendas_df['vlr_entrada'].sum() if 'vlr_entrada' in vendas_df.columns else 0
#         carteira_valor = vendas_df['vlr_carteira'].sum() if 'vlr_carteira' in vendas_df.columns else 0
#         faturamento_valor = vendas_df['vlr_rol'].sum() if 'vlr_rol' in vendas_df.columns else 0
#         
#         print(f"💰 Valores calculados - Entrada: {entrada_valor:,.0f}, Carteira: {carteira_valor:,.0f}, Faturamento: {faturamento_valor:,.0f}")
#         
#         # Formata valores
#         entrada_str = f"R$ {entrada_valor:,.0f}"
#         carteira_str = f"R$ {carteira_valor:,.0f}"
#         faturamento_str = f"R$ {faturamento_valor:,.0f}"
#         
#         # Variações temporárias
#         entrada_var = "➡️ 0%"
#         carteira_var = "➡️ 0%"
#         faturamento_var = "➡️ 0%"
#         
#         # KPIs por unidade de negócio (simplificado)
#         un_cards = []
#         if 'unidade_negocio' in vendas_df.columns:
#             unidades = vendas_df['unidade_negocio'].unique()[:3]  # Apenas primeiras 3
#             print(f"🏢 Unidades de negócio encontradas: {list(unidades)}")
#             for un in unidades:
#                 un_data = vendas_df[vendas_df['unidade_negocio'] == un]
#                 un_faturamento = un_data['vlr_rol'].sum() if 'vlr_rol' in un_data.columns else 0
#                 
#                 card = dbc.Card([
#                     dbc.CardBody([
#                         html.H6(str(un), className="card-title"),
#                         html.H4(f"R$ {un_faturamento:,.0f}", className="text-primary"),
#                         html.P("Faturamento", className="card-text text-muted")
#                     ])
#                 ], className="mb-2")
#                 un_cards.append(card)
#         
#         print(f"✅ KPIs calculados com sucesso - {len(un_cards)} unidades de negócio")
#         
#         return entrada_str, carteira_str, faturamento_str, entrada_var, carteira_var, faturamento_var, un_cards
#         
#     except Exception as e:
#         print(f"❌ Erro ao calcular KPIs: {e}")
#         import traceback
#         traceback.print_exc()
#         return "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", []

# Callback para gráfico de evolução

# TEMPORARIAMENTE DESABILITADO - gráfico agora está no force_update_all_components
# Callback para gráfico de evolução
# @app.callback(
#     Output('grafico-evolucao-vendas', 'figure'),
#     [Input('url', 'pathname')],  # Simplificado para usar apenas URL
#     prevent_initial_call=False
# )
# def update_evolution_chart(pathname):
#     """Atualiza gráfico de evolução de vendas"""
#     print(f"🔄 update_evolution_chart EXECUTADO para {pathname}")
#     
#     # Só atualiza se estiver na página principal (Overview)
#     if pathname and not any(x in pathname for x in ["/app/overview", "/app", "/"]):
#         print(f"❌ Página {pathname} não é overview - retornando gráfico vazio")
#         import plotly.graph_objects as go
#         return go.Figure()
#     
#     try:
#         vendas_df = load_vendas_data()
#         
#         if vendas_df.empty or 'data' not in vendas_df.columns:
#             print("❌ Dados insuficientes para gráfico de evolução")
#             import plotly.graph_objects as go
#             fig = go.Figure()
#             fig.add_annotation(text="Sem dados disponíveis", 
#                              xref="paper", yref="paper",
#                              x=0.5, y=0.5, showarrow=False)
#             return fig
#         
#         # Versão simplificada - evolução mensal de faturamento
#         vendas_df['ano_mes'] = pd.to_datetime(vendas_df['data']).dt.to_period('M').astype(str)
#         evolucao = vendas_df.groupby('ano_mes')['vlr_rol'].sum().reset_index()
#         
#         import plotly.express as px
#         fig = px.line(evolucao, x='ano_mes', y='vlr_rol', 
#                      title='Evolução do Faturamento',
#                      labels={'vlr_rol': 'Faturamento (R$)', 'ano_mes': 'Período'})
#         
#         fig.update_layout(
#             height=400,
#             showlegend=False,
#             xaxis_title="Período",
#             yaxis_title="Faturamento (R$)"
#         )
#         
#         print(f"✅ Gráfico de evolução criado com {len(evolucao)} pontos")
#         return fig
#         
#     except Exception as e:
#         print(f"❌ Erro ao criar gráfico de evolução: {e}")
        # import traceback
        # traceback.print_exc()
        # import plotly.graph_objects as go
        # fig = go.Figure()
        # fig.add_annotation(text=f"Erro: {str(e)}", 
        #                  xref="paper", yref="paper",
        #                  x=0.5, y=0.5, showarrow=False)
        # return fig
        # return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de evolução: {e}")
        return viz_gen._create_empty_chart("Erro ao carregar dados")

# TEMPORARIAMENTE DESABILITADO - tabela agora está no force_update_all_components
# Callback para tabela de KPIs por cliente
# @app.callback(
#     [Output('tabela-kpis-clientes', 'data'),
#      Output('tabela-kpis-clientes', 'page_size')],
#     [Input('url', 'pathname'),  # ADICIONA URL como trigger
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value'),
#      Input('table-page-size-clientes', 'value')],
#     prevent_initial_call=False  # SEMPRE executa
# )
# def update_clients_table(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, page_size):
    # """Atualiza tabela de KPIs por cliente"""
    # print(f"🔄 update_clients_table EXECUTADO para {pathname}")
    
    # # Só atualiza se estiver na página de clientes
    # if pathname and "/app/clients" not in pathname:
    #     print(f"❌ Página {pathname} não é clientes - retornando vazio")
    #     return [], 10
    # """Atualiza tabela de KPIs por cliente"""
    # try:
    #     vendas_df = load_vendas_data()
        
    #     # VERSÃO SIMPLIFICADA TEMPORÁRIA
    #     if vendas_df.empty:
    #         print("❌ Dados de vendas vazios para clientes")
    #         return [], page_size or 25
        
    #     # Gera dados básicos de clientes sem usar KPICalculator
    #     if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
    #         client_summary = vendas_df.groupby(['cod_cliente', 'cliente']).agg({
    #             'vlr_rol': 'sum',
    #             'vlr_entrada': 'sum',
    #             'vlr_carteira': 'sum'
    #         }).reset_index()
            
    #         client_summary = client_summary.head(100)  # Limita a 100 clientes
            
    #         client_data = []
    #         for _, row in client_summary.iterrows():
    #             client_data.append({
    #                 'codigo': row['cod_cliente'],
    #                 'cliente': row['cliente'],
    #                 'faturamento': row['vlr_rol'],
    #                 'entrada': row['vlr_entrada'],
    #                 'carteira': row['vlr_carteira']
    #             })
            
    #         print(f"✅ Dados de clientes gerados: {len(client_data)} registros")
    #         return client_data, page_size or 25
    #     else:
    #         print("❌ Colunas de cliente não encontradas")
    #         return [], page_size or 25
        
    # except Exception as e:
    #     print(f"❌ Erro ao calcular KPIs de clientes: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     return [], 25

# Callback para gráfico de status dos clientes
@app.callback(
    Output('grafico-status-clientes', 'figure'),
    [Input('tabela-kpis-clientes', 'data')],
    prevent_initial_call=True
)
@authenticated_callback
def update_client_status_chart(table_data):
    """Atualiza gráfico de status dos clientes"""
    try:
        if not table_data:
            return viz_gen._create_empty_chart("Sem dados de clientes")
        
        client_kpis_df = pd.DataFrame(table_data)
        fig = viz_gen.create_client_status_chart(client_kpis_df)
        return fig
        
    except Exception as e:
        print(f"Erro ao criar gráfico de status: {e}")
        return viz_gen._create_empty_chart("Erro ao processar dados")

# TEMPORARIAMENTE DESABILITADO - gráfico agora está no force_update_all_components
# Callback para gráfico de bolhas de produtos
# @app.callback(
#     Output('grafico-bolhas-produtos', 'figure'),
#     [Input('url', 'pathname'),  # ADICIONA URL como trigger
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('filter-top-produtos', 'value'),
#      Input('filter-top-clientes-bolhas', 'value'),
#      Input('filter-color-scale', 'value')],
#     prevent_initial_call=False  # SEMPRE executa
# )
# def update_bubble_chart(pathname, filtro_ano, filtro_mes, filtro_cliente, top_produtos, top_clientes, color_scale):
#     """Atualiza gráfico de bolhas de produtos"""
#     print(f"🔄 update_bubble_chart EXECUTADO para {pathname}")
#     
#     # Só atualiza se estiver na página de produtos
#     if pathname and "/app/products" not in pathname:
#         print(f"❌ Página {pathname} não é produtos - retornando gráfico vazio")
#         return {'data': [], 'layout': {'title': 'Selecione a página de produtos'}}
#     """Atualiza gráfico de bolhas de produtos"""
#     try:
#         vendas_df = load_vendas_data()
#         cotacoes_df = load_cotacoes_data()
#         
#         filters = {
#             'ano': filtro_ano,
#             'mes': filtro_mes,
#             'cliente': filtro_cliente
#         }
#         
#         fig = viz_gen.create_bubble_chart(
#             vendas_df, cotacoes_df, produtos_df,
#             top_produtos or 20, top_clientes or 20, 
#             color_scale or 'weg_blue', filters
#         )
#         return fig
#         
#     except Exception as e:
#         print(f"Erro ao criar gráfico de bolhas: {e}")
#         return viz_gen._create_empty_chart("Erro ao carregar dados de produtos")

# TEMPORARIAMENTE DESABILITADO - gráfico agora está no force_update_all_components
# Callback para gráfico de Pareto
# @app.callback(
#     Output('grafico-pareto-produtos', 'figure'),
#     [Input('url', 'pathname'),  # ADICIONA URL como trigger
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value')],
#     prevent_initial_call=False  # SEMPRE executa
# )
# def update_pareto_chart(pathname, filtro_ano, filtro_mes, filtro_cliente):
#     """Atualiza gráfico de Pareto de produtos"""
#     print(f"🔄 update_pareto_chart EXECUTADO para {pathname}")
#     
#     # Só atualiza se estiver na página de produtos
#     if pathname and "/app/products" not in pathname:
#         print(f"❌ Página {pathname} não é produtos - retornando gráfico vazio")
#         return {'data': [], 'layout': {'title': 'Selecione a página de produtos'}}
#     """Atualiza gráfico de Pareto de produtos"""
#     try:
#         vendas_df = load_vendas_data()
#         
#         filters = {
#             'ano': filtro_ano,
#             'mes': filtro_mes,
#             'cliente': filtro_cliente
#         }
#         
#         fig = viz_gen.create_pareto_chart(vendas_df, filters)
#         return fig
#         
#     except Exception as e:
#         print(f"Erro ao criar gráfico de Pareto: {e}")
#         return viz_gen._create_empty_chart("Erro ao processar dados de produtos")


# Callback para atualizar título da página
@app.callback(
    Output('page-title', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def update_page_title(pathname):
    """Atualiza o título da página baseado na URL"""
    
    titles = {
        '/app/overview': 'Visão Geral',
        '/app/clients': 'KPIs por Cliente', 
        '/app/products': 'Mix de Produtos',
        '/app/funnel': 'Funil & Ações',
        '/app/insights': 'Insights IA',
        '/app/config': 'Configurações',
        '/app': 'Visão Geral',
        '/': 'Visão Geral'
    }
    
    return titles.get(pathname, 'Dashboard WEG')

# Callbacks para limpeza de dados
@app.callback(
    [Output('modal-confirm-clear-vendas', 'is_open'),
     Output('modal-confirm-clear-cotacoes', 'is_open'),
     Output('modal-confirm-clear-materiais', 'is_open'),
     Output('modal-confirm-clear-all', 'is_open')],
    [Input('btn-clear-vendas', 'n_clicks'),
     Input('btn-clear-cotacoes', 'n_clicks'),
     Input('btn-clear-materiais', 'n_clicks'),
     Input('btn-clear-all-data', 'n_clicks'),
     Input('modal-cancel-vendas', 'n_clicks'),
     Input('modal-cancel-cotacoes', 'n_clicks'),
     Input('modal-cancel-materiais', 'n_clicks'),
     Input('modal-cancel-all', 'n_clicks')],
    [State('modal-confirm-clear-vendas', 'is_open'),
     State('modal-confirm-clear-cotacoes', 'is_open'),
     State('modal-confirm-clear-materiais', 'is_open'),
     State('modal-confirm-clear-all', 'is_open')],
    prevent_initial_call=True
)
@authenticated_callback
def toggle_clear_data_modals(btn_vendas, btn_cotacoes, btn_materiais, btn_all,
                           cancel_vendas, cancel_cotacoes, cancel_materiais, cancel_all,
                           modal_vendas_open, modal_cotacoes_open, modal_materiais_open, modal_all_open):
    """Gerencia abertura e fechamento dos modais de confirmação"""
    ctx = callback_context
    if not ctx.triggered:
        return False, False, False, False
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Abrir modais
    if button_id == 'btn-clear-vendas':
        return True, False, False, False
    elif button_id == 'btn-clear-cotacoes':
        return False, True, False, False
    elif button_id == 'btn-clear-materiais':
        return False, False, True, False
    elif button_id == 'btn-clear-all-data':
        return False, False, False, True
    
    # Fechar modais (cancelar)
    elif button_id == 'modal-cancel-vendas':
        return False, modal_cotacoes_open, modal_materiais_open, modal_all_open
    elif button_id == 'modal-cancel-cotacoes':
        return modal_vendas_open, False, modal_materiais_open, modal_all_open
    elif button_id == 'modal-cancel-materiais':
        return modal_vendas_open, modal_cotacoes_open, False, modal_all_open
    elif button_id == 'modal-cancel-all':
        return modal_vendas_open, modal_cotacoes_open, modal_materiais_open, False
    
    return modal_vendas_open, modal_cotacoes_open, modal_materiais_open, modal_all_open

@app.callback(
    Output('clear-data-status', 'children'),
    [Input('modal-confirm-vendas', 'n_clicks'),
     Input('modal-confirm-cotacoes', 'n_clicks'),
     Input('modal-confirm-materiais', 'n_clicks'),
     Input('modal-confirm-all', 'n_clicks')],
    prevent_initial_call=True
)
@authenticated_callback
def execute_data_clearing(confirm_vendas, confirm_cotacoes, confirm_materiais, confirm_all):
    """Executa a limpeza de dados baseado na confirmação"""
    from utils.db import clear_vendas_data, clear_cotacoes_data, clear_materiais_data, clear_all_data
    import dash_bootstrap_components as dbc
    from dash import html
    
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == 'modal-confirm-vendas':
            count = clear_vendas_data()
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {count} registros de vendas foram removidos com sucesso!"
            ], color="success", dismissable=True)
            
        elif button_id == 'modal-confirm-cotacoes':
            count = clear_cotacoes_data()
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {count} registros de cotações foram removidos com sucesso!"
            ], color="success", dismissable=True)
            
        elif button_id == 'modal-confirm-materiais':
            count = clear_materiais_data()
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {count} registros de materiais cotados foram removidos com sucesso!"
            ], color="success", dismissable=True)
            
        elif button_id == 'modal-confirm-all':
            result = clear_all_data()
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                html.Div([
                    html.P("✅ Limpeza total concluída com sucesso!", className="mb-2 fw-bold"),
                    html.Ul([
                        html.Li(f"Vendas: {result['vendas']} registros"),
                        html.Li(f"Cotações: {result['cotacoes']} registros"),
                        html.Li(f"Materiais: {result['materiais']} registros"),
                        html.Li(f"Datasets: {result['datasets']} registros"),
                    ]),
                    html.P(f"Total: {result['total']} registros removidos", className="fw-bold")
                ])
            ], color="success", dismissable=True)
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"❌ Erro ao limpar dados: {str(e)}"
        ], color="danger", dismissable=True)
    
    return ""

# Callback adicional para fechar modais após confirmação
@app.callback(
    [Output('modal-confirm-clear-vendas', 'is_open', allow_duplicate=True),
     Output('modal-confirm-clear-cotacoes', 'is_open', allow_duplicate=True),
     Output('modal-confirm-clear-materiais', 'is_open', allow_duplicate=True),
     Output('modal-confirm-clear-all', 'is_open', allow_duplicate=True)],
    [Input('modal-confirm-vendas', 'n_clicks'),
     Input('modal-confirm-cotacoes', 'n_clicks'),
     Input('modal-confirm-materiais', 'n_clicks'),
     Input('modal-confirm-all', 'n_clicks')],
    prevent_initial_call=True
)
@authenticated_callback
def close_modals_after_confirmation(confirm_vendas, confirm_cotacoes, confirm_materiais, confirm_all):
    """Fecha os modais após confirmação da limpeza"""
    ctx = callback_context
    if not ctx.triggered:
        return False, False, False, False
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Fecha o modal correspondente após confirmação
    if button_id == 'modal-confirm-vendas':
        return False, False, False, False
    elif button_id == 'modal-confirm-cotacoes':
        return False, False, False, False
    elif button_id == 'modal-confirm-materiais':
        return False, False, False, False
    elif button_id == 'modal-confirm-all':
        return False, False, False, False
    
    return False, False, False, False

# Callback para mostrar estatísticas atuais dos dados
@app.callback(
    Output('data-stats', 'children'),
    [Input('url', 'pathname'),
     Input('clear-data-status', 'children')],  # Atualiza após limpeza
    prevent_initial_call=True
)
@authenticated_callback
def update_data_statistics(pathname, clear_status):
    """Atualiza as estatísticas dos dados na tela de configurações"""
    if pathname != '/app/config':
        return ""
    
    from utils.db import get_data_statistics
    import dash_bootstrap_components as dbc
    from dash import html
    import time
    
    try:
        # Pequeno delay para evitar conflitos durante limpeza de dados
        if clear_status and clear_status != "":
            time.sleep(0.5)
            
        stats = get_data_statistics()
        
        return dbc.Card([
            dbc.CardBody([
                html.H6("📊 Dados Atuais no Sistema", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Badge([
                            html.I(className="fas fa-chart-line me-1"),
                            f"Vendas: {stats['vendas']:,}"
                        ], color="primary", className="me-2 mb-1")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Badge([
                            html.I(className="fas fa-file-contract me-1"),
                            f"Cotações: {stats['cotacoes']:,}"
                        ], color="info", className="me-2 mb-1")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Badge([
                            html.I(className="fas fa-tools me-1"),
                            f"Materiais: {stats['materiais']:,}"
                        ], color="success", className="me-2 mb-1")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Badge([
                            html.I(className="fas fa-database me-1"),
                            f"Datasets: {stats['datasets']:,}"
                        ], color="secondary", className="me-2 mb-1")
                    ], width="auto")
                ])
            ])
        ], className="border-0 bg-light")
        
    except Exception as e:
        print(f"❌ Erro em update_data_statistics: {e}")
        return dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Erro ao carregar estatísticas: {str(e)}"
        ], color="warning", dismissable=True)

# =======================================
# CALLBACKS ADICIONAIS PARA OUTRAS TELAS
# =======================================

# Callback para tabela de clientes - CORRIGIDO E COMPLETO
@app.callback(
    Output('tabela-kpis-clientes', 'data'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_clients_table(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, pathname):
    """Atualiza tabela de KPIs por cliente com TODOS os filtros"""
    print(f"🔄 UPDATE_CLIENTS_TABLE executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Filtros avançados: hierarquia={filtro_hierarquia}, canal={filtro_canal}")
    print(f"   Filtros extras: top_clientes={filtro_top_clientes}, dias_sem_compra={filtro_dias_sem_compra}")
    
    try:
        # Só processa se estiver na página de clientes
        if pathname and "/app/clients" not in pathname and "clients" not in pathname:
            print(f"❌ Não é página de clientes: {pathname}")
            return []
            
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            print("❌ Dados de vendas vazios")
            return []
        
        # Aplica TODOS os filtros usando a função centralizada
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
        
        # Cria tabela de clientes
        if 'cod_cliente' in df_filtrado.columns and 'cliente' in df_filtrado.columns:
            clients_stats = df_filtrado.groupby(['cod_cliente', 'cliente']).agg({
                'vlr_rol': 'sum',
                'data': ['min', 'max', 'count']
            }).reset_index()
            
            # Flatten column names
            clients_stats.columns = ['cod_cliente', 'cliente', 'faturamento', 'data_primeira', 'data_ultima', 'num_vendas']
            
            # Calcula dias sem compra
            from datetime import datetime
            hoje = datetime.now()
            clients_stats['data_ultima'] = pd.to_datetime(clients_stats['data_ultima'])
            clients_stats['dias_sem_compra'] = (hoje - clients_stats['data_ultima']).dt.days
            clients_stats['dias_sem_compra'] = clients_stats['dias_sem_compra'].fillna(0).clip(lower=0)
            
            # Aplica filtro Top N clientes APENAS se especificado e > 0
            # Se vazio ou 0, mostra TODOS os clientes (respeitando outros filtros)
            if filtro_top_clientes and isinstance(filtro_top_clientes, (int, float)) and filtro_top_clientes > 0:
                print(f"   Aplicando filtro top {filtro_top_clientes} clientes")
                clients_stats = clients_stats.nlargest(int(filtro_top_clientes), 'faturamento')
                # Usa todos os registros quando top_clientes está definido
                max_registros = len(clients_stats)
            else:
                print(f"   Top clientes vazio - mostrando TODOS os clientes")
                # Sem limite quando top_clientes está vazio
                max_registros = len(clients_stats)
            
            # Formata dados para a tabela - SEM limitação fixa de 50
            table_data = []
            for _, row in clients_stats.head(max_registros).iterrows():
                table_data.append({
                    'cod_cliente': str(row['cod_cliente']),
                    'cliente': str(row['cliente']),
                    'dias_sem_compra': int(row['dias_sem_compra']) if pd.notna(row['dias_sem_compra']) else 0,
                    'frequencia_media_compra': 30,  # Valor fixo temporário
                    'mix_produtos': int(row['num_vendas']) if pd.notna(row['num_vendas']) else 0,
                    'percentual_mix': 100.0,  # Valor fixo temporário
                    'unidades_negocio': "WEG",  # Valor fixo temporário
                    'produtos_cotados': 0,  # Valor fixo temporário
                    'produtos_comprados': 0,  # Valor fixo temporário
                    'perc_nao_comprado': 0.0  # Valor fixo temporário
                })
            
            print(f"✅ Tabela de clientes criada com {len(table_data)} registros")
            return table_data
        
        return []
        
    except Exception as e:
        print(f"❌ Erro em update_clients_table: {e}")
        import traceback
        traceback.print_exc()
        return []

# Callback para controlar page_size da tabela de clientes
@app.callback(
    Output('tabela-kpis-clientes', 'page_size'),
    [Input('table-page-size-clientes', 'value')],
    prevent_initial_call=False
)
def update_clients_table_page_size(page_size):
    """Atualiza o tamanho da página da tabela de clientes"""
    print(f"🔄 UPDATE_CLIENTS_TABLE_PAGE_SIZE: {page_size}")
    return page_size or 25

# Callback para gráficos de produtos - REATIVO A FILTROS
@app.callback(
    [Output('grafico-bolhas-produtos', 'figure'),
     Output('grafico-pareto-produtos', 'figure')],
    [Input('url', 'pathname'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value'),
     Input('filter-top-produtos', 'value')],
    prevent_initial_call=False
)
def update_products_charts(pathname, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, top_produtos):
    """Atualiza gráficos da página de produtos"""
    print(f"🔄 UPDATE_PRODUCTS_CHARTS executado - pathname: {pathname}")
    print(f"   Filtros recebidos: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    print(f"   Hierarquia={filtro_hierarquia}, Top Produtos={top_produtos}")
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Processa sempre, mas mostra mensagem se não for página de produtos
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            print("❌ Dados de vendas vazios")
            fig_empty = go.Figure().add_annotation(
                text="Sem dados disponíveis", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig_empty, fig_empty
        
        # Aplica filtros usando a função centralizada
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        # === LÓGICA INTELIGENTE DE HIERARQUIA ===
        # Determina qual nível de hierarquia usar baseado no filtro
        hierarchy_level, product_column = determine_hierarchy_level(df_filtrado, filtro_hierarquia)
        print(f"   🎯 Nível de hierarquia determinado: {hierarchy_level}, coluna: {product_column}")
        
        # Define número de top produtos (padrão 20 se não especificado)
        top_n_produtos = top_produtos if top_produtos and top_produtos > 0 else 20
        print(f"   📊 Top N produtos: {top_n_produtos}")
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            fig_empty = go.Figure().add_annotation(
                text="Nenhum dado encontrado com os filtros aplicados", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig_empty, fig_empty
        
        # === GRÁFICO DE BOLHAS (Matriz Clientes x Produtos) ===
        fig_bolhas = go.Figure()
        
        if 'cliente' in df_filtrado.columns and product_column in df_filtrado.columns:
            # Determina qual coluna de quantidade usar
            qty_col = None
            for col in ['qty_vendida', 'qtde', 'quantidade', 'qte']:
                if col in df_filtrado.columns:
                    qty_col = col
                    break
            
            # Agrupa dados por cliente e produto usando a coluna inteligente determinada
            agg_dict = {'vlr_rol': 'sum'}
            if qty_col:
                agg_dict[qty_col] = 'sum'
            
            matriz_data = df_filtrado.groupby(['cliente', product_column]).agg(agg_dict).reset_index()
            
            if len(matriz_data) > 0:
                # Para clientes: se não há filtro top_clientes aplicado, pega top N baseado no faturamento
                # Se já foi aplicado o filtro no apply_filters, usa todos os clientes resultantes
                if filtro_top_clientes and filtro_top_clientes > 0:
                    # Filtro já foi aplicado no apply_filters, usa todos os clientes
                    clientes_matriz = matriz_data['cliente'].unique()
                    print(f"   📊 Clientes na matriz (filtro já aplicado): {len(clientes_matriz)}")
                else:
                    # Não há filtro, pega top 10 clientes por faturamento
                    top_clientes_n = 10
                    top_clientes = matriz_data.groupby('cliente')['vlr_rol'].sum().nlargest(top_clientes_n).index
                    clientes_matriz = top_clientes
                    print(f"   📊 Top {top_clientes_n} clientes selecionados para matriz")
                
                # Para produtos: sempre pega top N produtos baseado no filtro
                top_produtos_matriz = matriz_data.groupby(product_column)['vlr_rol'].sum().nlargest(top_n_produtos).index
                print(f"   📊 Top {top_n_produtos} produtos selecionados para matriz")
                
                # Filtra a matriz final
                matriz_filtered = matriz_data[
                    (matriz_data['cliente'].isin(clientes_matriz)) & 
                    (matriz_data[product_column].isin(top_produtos_matriz))
                ]
                
                if not matriz_filtered.empty:
                    # Usa quantidade se disponível, senão usa faturamento para cor
                    color_col = qty_col if qty_col and qty_col in matriz_filtered.columns else 'vlr_rol'
                    
                    # CORREÇÃO: Valores negativos não são permitidos no size do scatter
                    # Converte valores negativos para positivos (valor absoluto)
                    size_col = 'vlr_rol_abs'
                    matriz_filtered[size_col] = matriz_filtered['vlr_rol'].abs()
                    
                    # Garante que não há valores zero que podem causar problemas
                    matriz_filtered[size_col] = matriz_filtered[size_col].replace(0, 1)
                    
                    title_suffix = f"(Nível {hierarchy_level})"
                    if hierarchy_level == 4:
                        title_suffix = "(Produtos Individuais)"
                    
                    fig_bolhas = px.scatter(
                        matriz_filtered, 
                        x='cliente', 
                        y=product_column,
                        size=size_col,  # Usa coluna com valores absolutos
                        color=color_col,
                        hover_data=['vlr_rol'] + ([qty_col] if qty_col and qty_col in matriz_filtered.columns else []),
                        title=f'Matriz Clientes × Produtos {title_suffix}'
                    )
                    fig_bolhas.update_layout(
                        height=400,
                        xaxis_title="Clientes",
                        yaxis_title="Produtos", 
                    )
                else:
                    fig_bolhas.add_annotation(
                        text="Sem dados para matriz", 
                        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                    )
            else:
                fig_bolhas.add_annotation(
                    text="Sem dados para processar", 
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
        else:
            missing_cols = []
            if 'cliente' not in df_filtrado.columns:
                missing_cols.append('cliente')
            if product_column not in df_filtrado.columns:
                missing_cols.append(product_column)
            fig_bolhas.add_annotation(
                text=f"Colunas ausentes: {', '.join(missing_cols)}", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        # === GRÁFICO DE PARETO (Produtos por Faturamento) ===
        fig_pareto = go.Figure()
        
        if product_column in df_filtrado.columns and 'vlr_rol' in df_filtrado.columns:
            # Cria dados para Pareto usando a coluna de produto inteligente
            pareto_data = df_filtrado.groupby(product_column)['vlr_rol'].sum().sort_values(ascending=False).reset_index()
            
            if len(pareto_data) > 0:
                pareto_data['faturamento_acumulado'] = pareto_data['vlr_rol'].cumsum()
                pareto_data['percentual_acumulado'] = (pareto_data['faturamento_acumulado'] / pareto_data['vlr_rol'].sum()) * 100
                
                # Usa o top_n_produtos do filtro
                pareto_data = pareto_data.head(top_n_produtos)
                
                # Cria o gráfico de Pareto
                fig_pareto = go.Figure()
                
                # Barras de faturamento
                fig_pareto.add_trace(go.Bar(
                    x=pareto_data[product_column],
                    y=pareto_data['vlr_rol'],
                    name='Faturamento',
                    yaxis='y',
                    marker_color='steelblue'
                ))
                
                # Linha de percentual acumulado
                fig_pareto.add_trace(go.Scatter(
                    x=pareto_data[product_column],
                    y=pareto_data['percentual_acumulado'],
                    mode='lines+markers',
                    name='% Acumulado',
                    yaxis='y2',
                    line=dict(color='red', width=2),
                    marker=dict(size=6)
                ))
                
                # Layout com dois eixos Y
                title_suffix = f"(Nível {hierarchy_level})"
                if hierarchy_level == 4:
                    title_suffix = "(Produtos Individuais)"
                
                fig_pareto.update_layout(
                    title=f'Análise de Pareto - Produtos {title_suffix} (Top {top_n_produtos})',
                    xaxis=dict(title='Produtos', tickangle=45),
                    yaxis=dict(title='Faturamento (R$)', side='left'),
                    yaxis2=dict(title='% Acumulado', side='right', overlaying='y', range=[0, 100]),
                    height=400,
                    legend=dict(x=0.7, y=0.9)
                )
            else:
                fig_pareto.add_annotation(
                    text="Sem produtos para análise", 
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
        else:
            missing_cols = []
            if product_column not in df_filtrado.columns:
                missing_cols.append(product_column)
            if 'vlr_rol' not in df_filtrado.columns:
                missing_cols.append('vlr_rol')
            fig_pareto.add_annotation(
                text=f"Colunas ausentes: {', '.join(missing_cols)}", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        print(f"✅ Gráficos de produtos criados - {len(df_filtrado)} registros processados")
        return fig_bolhas, fig_pareto
        
    except Exception as e:
        print(f"❌ Erro em update_products_charts: {e}")
        import traceback
        traceback.print_exc()
        import plotly.graph_objects as go
        fig_error = go.Figure().add_annotation(
            text=f"Erro: {str(e)}", 
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        return fig_error, fig_error

# =======================================
# CALLBACKS DUPLICADOS REMOVIDOS
# =======================================
# Os callbacks individuais para grafico-bolhas-produtos e grafico-pareto-produtos
# foram removidos para evitar conflito com o callback combinado na linha 1232-1233

print("✅ Callbacks principais registrados com sucesso")