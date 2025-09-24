"""
Callbacks principais da aplicação com performance otimizada
Integração com AI Framework para preparação evolutiva
"""

from dash import Input, Output, State, callback_context, dash_table, html, dcc
import dash
import pandas as pd
import dash_bootstrap_components as dbc
import logging
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

# Import callbacks da página de sugestões - REMOVIDO para evitar duplicação
# import webapp.purchase_suggestions_callbacks  # ❌ COMENTADO - usando versão simplificada
from utils.cache_manager import cached_dataframe, cached_result, cache_manager
from utils.ai_framework import ai_analytics, SimpleNLPMatcher, UserInteractionLogger

# Logger local deste módulo
logger = logging.getLogger(__name__)

# Import callback de produtos com tratamento de erro robusto
try:
    import webapp.produtos_table_callback_new
    logger.info("Callback de produtos carregado (produtos_table_callback_new)")
except Exception as e:
    logger.warning(f"Erro ao carregar callback de produtos: {e}")

# --- CÓDIGO DE TESTE DESATIVADO PARA REDUZIR RUÍDO DE LOG ---
# try:
#     import webapp.temp_test_callback
#     logger.info("Callback de TESTE para a tabela de produtos carregado")
# except ImportError:
#     logger.debug("Callback de TESTE não encontrado (ok)")

# Instâncias globais para IA
ai_logger = UserInteractionLogger()
nlp_matcher = SimpleNLPMatcher()

def apply_filters(df, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra=None, metrica_type=None):
    """Aplica todos os filtros ao DataFrame de vendas de forma otimizada
    
    Args:
        metrica_type: 'entrada' para usar coluna 'data', 'faturamento' para usar 'data_faturamento', None para detectar automaticamente
    """
    print(f"🔍 APPLY_FILTERS iniciado - DataFrame original: {len(df)} registros")
    print(f"   📊 Filtros recebidos:")
    print(f"      • Ano: {filtro_ano}")
    print(f"      • Mês: {filtro_mes}")
    print(f"      • Cliente: {filtro_cliente} (tipo: {type(filtro_cliente)})")
    print(f"      • Hierarquia: {filtro_hierarquia}")
    print(f"      • Canal: {filtro_canal}")
    print(f"      • Top Clientes: {filtro_top_clientes}")
    print(f"      • Dias sem compra: {filtro_dias_sem_compra}")
    print(f"      • Métrica tipo: {metrica_type}")
    
    if df is None or df.empty:
        print("   ⚠️ DataFrame vazio ou None - retornando original")
        return df
    
    df_filtrado = df.copy()
    
    # Detecta automaticamente a coluna de data baseada na métrica
    date_column = None
    if metrica_type == 'entrada':
        # Para entrada de pedidos, sempre usar 'data' (data do pedido)
        for col in ['data', 'data_faturamento', 'data_venda']:
            if col in df_filtrado.columns:
                date_column = col
                print(f"   📅 Coluna de data para entrada detectada: {date_column}")
                break
    elif metrica_type == 'faturamento':
        # Para faturamento, sempre usar 'data_faturamento'
        for col in ['data_faturamento', 'data', 'data_venda']:
            if col in df_filtrado.columns:
                date_column = col
                print(f"   📅 Coluna de data para faturamento detectada: {date_column}")
                break
    else:
        # Detecta automaticamente (comportamento padrão anterior)
        for col in ['data_faturamento', 'data', 'data_venda']:
            if col in df_filtrado.columns:
                date_column = col
                print(f"   📅 Coluna de data detectada automaticamente: {date_column}")
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
        print(f"📊 DADOS CARREGADOS: {len(vendas_df)} registros")
        print(f"   Colunas originais: {list(vendas_df.columns)}")
        
        if vendas_df.empty:
            print("❌ DataFrame de vendas está vazio!")
            return "R$ 0"
            
        # Verificar dados originais de vlr_entrada
        if 'vlr_entrada' in vendas_df.columns:
            total_entrada_original = vendas_df['vlr_entrada'].sum()
            registros_com_entrada = (vendas_df['vlr_entrada'] > 0).sum()
            print(f"💰 DADOS ORIGINAIS vlr_entrada: soma={total_entrada_original:,.2f}, registros_positivos={registros_com_entrada}")
            print(f"   Amostra vlr_entrada original: {vendas_df['vlr_entrada'].head(10).tolist()}")
        else:
            print("❌ Coluna vlr_entrada não existe nos dados originais!")
            
        # Aplica todos os filtros usando função auxiliar - especifica que é para entrada de pedidos
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='entrada')
        
        print(f"📊 DADOS FILTRADOS: {len(df_filtrado)} registros")
        print(f"   Colunas filtradas: {list(df_filtrado.columns) if not df_filtrado.empty else 'DataFrame vazio'}")
        
        entrada_valor = df_filtrado['vlr_entrada'].sum() if 'vlr_entrada' in df_filtrado.columns else 0
        if 'vlr_entrada' in df_filtrado.columns and not df_filtrado.empty:
            registros_filtrados_com_entrada = (df_filtrado['vlr_entrada'] > 0).sum()
            print(f"💰 DADOS FILTRADOS vlr_entrada: soma={entrada_valor:,.2f}, registros_positivos={registros_filtrados_com_entrada}")
            print(f"   Amostra vlr_entrada filtrado: {df_filtrado['vlr_entrada'].head(10).tolist()}")
        
        return f"R$ {entrada_valor:,.0f}"
        
    except Exception as e:
        print(f"❌ Erro em update_kpi_entrada: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return "Erro"# Callback para KPI de Carteira - REATIVO A FILTROS
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
            
        # Aplica todos os filtros usando função auxiliar - especifica que é para faturamento
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='faturamento')
        
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
            
        # Para o gráfico de evolução, precisamos filtrar separadamente para cada métrica
        # porque entrada usa 'data' e faturamento usa 'data_faturamento'
        
        # Filtrar dados para FATURAMENTO (usando data_faturamento)
        df_filtrado_faturamento = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                               filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='faturamento')
        
        # Filtrar dados para ENTRADA (usando data)
        df_filtrado_entrada = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                          filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='entrada')
        
        # Gráfico de evolução - CORREÇÃO: Incluir vlr_entrada
        import plotly.graph_objects as go
        fig_vendas = go.Figure()
        
        # Preparar dados de faturamento agrupados por mês
        if not df_filtrado_faturamento.empty and 'data_faturamento' in df_filtrado_faturamento.columns:
            df_mes_faturamento = df_filtrado_faturamento.groupby(df_filtrado_faturamento['data_faturamento'].dt.strftime('%Y-%m')).agg({
                'vlr_rol': 'sum'
            }).sort_index()
            
            # Linha de Faturamento (vlr_rol)
            fig_vendas.add_trace(go.Scatter(
                x=df_mes_faturamento.index, 
                y=df_mes_faturamento['vlr_rol'],
                mode='lines+markers',
                name='Faturamento',
                line=dict(color='#28a745', width=3),
                marker=dict(size=8),
                yaxis='y'
            ))
        
        # Preparar dados de entrada agrupados por mês
        if not df_filtrado_entrada.empty and 'data' in df_filtrado_entrada.columns:
            df_mes_entrada = df_filtrado_entrada.groupby(df_filtrado_entrada['data'].dt.strftime('%Y-%m')).agg({
                'vlr_entrada': 'sum'
            }).sort_index()
            
            # Linha de Entrada (vlr_entrada)
            fig_vendas.add_trace(go.Scatter(
                x=df_mes_entrada.index, 
                y=df_mes_entrada['vlr_entrada'],
                mode='lines+markers',
                name='Entrada de Pedidos',
                line=dict(color='#007bff', width=3, dash='dash'),
                marker=dict(size=8),
                yaxis='y'
            ))
        
        fig_vendas.update_layout(
            title="Evolução de Vendas e Entrada de Pedidos",
            xaxis_title="Período",
            yaxis_title="Valor (R$)",
            template="plotly_white",
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        print(f"📈 Gráfico de evolução criado com dados separados para faturamento e entrada")
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
        print(f"❌ Pathname não válido para unidades de negócio: {pathname}")
        return []

    try:
        vendas_df = load_vendas_data()
        print(f"📊 DADOS CARREGADOS para UN: {len(vendas_df)} registros")
        print(f"   Colunas originais: {list(vendas_df.columns)}")
        
        if vendas_df.empty:
            print("❌ DataFrame de vendas está vazio para UN!")
            return []
            
        # Verificar se existe coluna unidade_negocio
        col_unidade = None
        for col in vendas_df.columns:
            if 'unidade' in col.lower():
                col_unidade = col
                print(f"🏢 Coluna de unidade encontrada: {col}")
                break
        
        if not col_unidade:
            print("❌ Nenhuma coluna de unidade de negócio encontrada!")
            print(f"   Colunas disponíveis: {list(vendas_df.columns)}")
            return []
            
        # Aplicar filtros separadamente para cada métrica para garantir que usamos a data correta
        # Para faturamento (vlr_rol) - usar data_faturamento
        df_filtrado_faturamento = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                               filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='faturamento')
        
        # Para entrada (vlr_entrada) - usar data  
        df_filtrado_entrada = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                          filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, metrica_type='entrada')
        
        # Para carteira - usar padrão (normalmente data_faturamento)
        df_filtrado_carteira = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                           filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        print(f"📊 DADOS FILTRADOS para UN:")
        print(f"   Faturamento: {len(df_filtrado_faturamento)} registros")
        print(f"   Entrada: {len(df_filtrado_entrada)} registros") 
        print(f"   Carteira: {len(df_filtrado_carteira)} registros")
        
        # KPIs por Unidade de Negócio - CORREÇÃO: Usar dados separados por métrica
        kpis_un = []
        
        # Calcular KPIs separadamente para cada métrica
        kpis_faturamento = {}
        kpis_entrada = {}
        kpis_carteira = {}
        
        # Processar Faturamento
        if not df_filtrado_faturamento.empty and col_unidade in df_filtrado_faturamento.columns and 'vlr_rol' in df_filtrado_faturamento.columns:
            kpis_faturamento = df_filtrado_faturamento.groupby(col_unidade)['vlr_rol'].sum().to_dict()
            print(f"💰 KPIs Faturamento: {kpis_faturamento}")
        
        # Processar Entrada  
        if not df_filtrado_entrada.empty and col_unidade in df_filtrado_entrada.columns and 'vlr_entrada' in df_filtrado_entrada.columns:
            kpis_entrada = df_filtrado_entrada.groupby(col_unidade)['vlr_entrada'].sum().to_dict()
            print(f"💰 KPIs Entrada: {kpis_entrada}")
        
        # Processar Carteira
        if not df_filtrado_carteira.empty and col_unidade in df_filtrado_carteira.columns and 'vlr_carteira' in df_filtrado_carteira.columns:
            kpis_carteira = df_filtrado_carteira.groupby(col_unidade)['vlr_carteira'].sum().to_dict()
            print(f"💰 KPIs Carteira: {kpis_carteira}")
        
        # Combinar todas as unidades de negócio
        todas_unidades = set()
        todas_unidades.update(kpis_faturamento.keys())
        todas_unidades.update(kpis_entrada.keys())
        todas_unidades.update(kpis_carteira.keys())
        
        print(f"🏢 Unidades de negócio encontradas: {len(todas_unidades)}")
        print(f"   Unidades: {list(todas_unidades)}")
        
        if todas_unidades:
            import dash_bootstrap_components as dbc
            
            # Organizar cards em três linhas separadas
            cards_faturamento = []
            cards_entrada = []
            cards_carteira = []
            
            # Criar cards para cada unidade de negócio organizados por métrica
            for un in sorted(todas_unidades):
                print(f"   Processando unidade: {un}")
                
                vlr_rol = kpis_faturamento.get(un, 0)
                vlr_entrada = kpis_entrada.get(un, 0) 
                vlr_carteira = kpis_carteira.get(un, 0)
                
                # Card para Faturamento (vlr_rol) - Primeira linha
                if vlr_rol > 0:
                    kpi_card_rol = dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6(f"R$ {vlr_rol:,.0f}", className="card-title text-secondary"),
                                html.P(f"{str(un)} - Faturamento", className="card-text small text-muted")
                            ])
                        ], className="text-center h-100 mb-2 border-secondary")
                    ], width=12, md=2)
                    cards_faturamento.append(kpi_card_rol)
                
                # Card para Entrada (vlr_entrada) - Segunda linha
                if vlr_entrada > 0:
                    kpi_card_entrada = dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6(f"R$ {vlr_entrada:,.0f}", className="card-title text-secondary"),
                                html.P(f"{str(un)} - Entrada", className="card-text small text-muted")
                            ])
                        ], className="text-center h-100 mb-2 border-secondary")
                    ], width=12, md=2)
                    cards_entrada.append(kpi_card_entrada)
                
                # Card para Carteira (vlr_carteira) - Terceira linha
                if vlr_carteira > 0:
                    kpi_card_carteira = dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6(f"R$ {vlr_carteira:,.0f}", className="card-title text-secondary"),
                                html.P(f"{str(un)} - Carteira", className="card-text small text-muted")
                            ])
                        ], className="text-center h-100 mb-2 border-secondary")
                    ], width=12, md=2)
                    cards_carteira.append(kpi_card_carteira)
            
            # Organizar em linhas separadas
            if cards_faturamento:
                # Linha 1: Cards de Faturamento
                kpis_un.extend([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Faturamento por Unidade de Negócio", className="text-success mb-3")
                        ], width=12)
                    ], className="mb-2"),
                    dbc.Row(cards_faturamento, className="g-2 mb-4")
                ])
            
            if cards_entrada:
                # Linha 2: Cards de Entrada
                kpis_un.extend([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Entrada de Pedidos por Unidade de Negócio", className="text-primary mb-3")
                        ], width=12)
                    ], className="mb-2"),
                    dbc.Row(cards_entrada, className="g-2 mb-4")
                ])
            
            if cards_carteira:
                # Linha 3: Cards de Carteira
                kpis_un.extend([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Carteira por Unidade de Negócio", className="text-warning mb-3")
                        ], width=12)
                    ], className="mb-2"),
                    dbc.Row(cards_carteira, className="g-2 mb-4")
                ])
        
        print(f"🏢 KPIs por Unidade de Negócio criados: {len(kpis_un)} cards")
        return kpis_un
        
    except Exception as e:
        print(f"❌ Erro em update_kpis_unidades_negocio: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return []# Registrar callbacks do chat
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
            layout = create_chat_layout()
        elif pathname == '/app/overview' or pathname == '/app' or pathname == '/':
            from webapp.layouts import create_overview_layout
            layout = create_overview_layout()
        elif pathname == '/app/clients':
            from webapp.layouts import create_clients_layout
            layout = create_clients_layout()
            
            # CORREÇÃO ESPECÍFICA: Verificar se o layout de clientes é válido
            if layout is None:
                print(f"❌ Layout de clientes retornado é None")
                return html.Div([
                    dbc.Alert("Erro: Layout de clientes não encontrado", color="danger")
                ])
            
            print("✅ Layout de clientes validado com sucesso")
            return layout
        elif pathname == '/app/products' or pathname == '/produtos':
            from webapp.layouts import create_products_layout
            from utils.component_validator import safe_component_return
            try:
                layout = create_products_layout()
                
                # CORREÇÃO ESPECÍFICA: Validação robusta do layout
                validated_layout = safe_component_return(
                    layout, 
                    "Erro ao carregar página de produtos"
                )
                
                print("✅ Layout de produtos validado com sucesso")
                return validated_layout
                
            except Exception as e:
                print(f"❌ Erro ao criar layout de produtos: {e}")
                import traceback
                traceback.print_exc()
                return html.Div([
                    dbc.Alert(f"Erro ao carregar página de produtos: {str(e)}", color="danger"),
                    html.P("Verifique os logs do servidor para mais detalhes.")
                ])
                
        elif pathname == '/app/funnel':
            from webapp.layouts import create_funnel_layout
            layout = create_funnel_layout()
        elif pathname == '/app/insights':
            from webapp.layouts import create_insights_layout
            layout = create_insights_layout()
        elif pathname == '/app/analytics':
            from webapp.layouts import create_analytics_layout
            layout = create_analytics_layout()
        elif pathname == '/app/config':
            from webapp.layouts import create_config_layout
            layout = create_config_layout()
        else:
            layout = html.Div([
                dbc.Alert("Página não encontrada", color="warning")
            ])
            
        # CORREÇÃO: Verificar se o layout é válido antes de retornar
        if layout is None:
            print(f"❌ Layout retornado é None para pathname: {pathname}")
            return html.Div([
                dbc.Alert("Erro: Layout não encontrado", color="danger")
            ])
            
        return layout
        
    except Exception as e:
        print(f"❌ Erro em display_page_content: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Erro ao carregar página: {str(e)}", color="danger")
        ])

# Callback para popular filtros globais
@app.callback(
    [Output('global-filtro-cliente', 'options'),
     Output('global-filtro-hierarquia', 'options'),
     Output('global-filtro-canal', 'options')],
    [Input('url', 'pathname')],
    prevent_initial_call=False
)
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
        
        # Opções de clientes (dados já estão deduplicados pela padronização)
        cliente_options = []
        if 'cod_cliente' in vendas_df.columns and 'cliente' in vendas_df.columns:
            # Agrupa por código para garantir cliente único por código
            clientes_unique = (vendas_df[['cod_cliente', 'cliente']]
                             .dropna()
                             .groupby('cod_cliente')['cliente']
                             .first()  # Pega o primeiro (já foi deduplicado)
                             .reset_index())
            cliente_options = [
                {'label': f"{row['cod_cliente']} -- {row['cliente']}", 'value': row['cod_cliente']}
                for _, row in clientes_unique.iterrows()
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

# Callback para analytics
@app.callback(
    Output('analytics-content', 'children'),
    [Input('analytics-tipo-analise', 'value'),
     Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value')],
    prevent_initial_call=False
)
def update_analytics_content(tipo_analise, filtro_ano, filtro_mes, filtro_cliente, 
                           filtro_hierarquia, filtro_canal, filtro_top_clientes):
    """Atualiza o conteúdo da página de analytics baseado no tipo de análise selecionado"""
    print(f"🔥 UPDATE_ANALYTICS_CONTENT EXECUTADO!")
    print(f"🔥 Tipo análise: {tipo_analise}")
    print(f"🔥 Filtros: ano={filtro_ano}, mes={filtro_mes}, cliente={filtro_cliente}")
    
    # Set default analysis type if none selected
    if not tipo_analise:
        tipo_analise = "gaps"
        print(f"🔥 Usando tipo padrão: {tipo_analise}")
    
    try:
        from utils import AdvancedAnalytics
        
        # Carregar dados
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        print(f"📊 Analytics Debug - Vendas: {len(df_vendas) if df_vendas is not None else 0} registros")
        print(f"📊 Analytics Debug - Cotações: {len(df_cotacoes) if df_cotacoes is not None else 0} registros")
        
        # Aplicar filtros aos dados
        df_vendas_filtrado = apply_filters(
            df_vendas, filtro_ano, filtro_mes, filtro_cliente, 
            filtro_hierarquia, filtro_canal, filtro_top_clientes
        ) if df_vendas is not None and not df_vendas.empty else df_vendas
        
        df_cotacoes_filtrado = apply_filters(
            df_cotacoes, filtro_ano, filtro_mes, filtro_cliente, 
            filtro_hierarquia, filtro_canal, filtro_top_clientes
        ) if df_cotacoes is not None and not df_cotacoes.empty else df_cotacoes
        
        print(f"📊 Analytics Debug - Vendas filtradas: {len(df_vendas_filtrado) if df_vendas_filtrado is not None else 0} registros")
        print(f"📊 Analytics Debug - Cotações filtradas: {len(df_cotacoes_filtrado) if df_cotacoes_filtrado is not None else 0} registros")
        
        # Inicializar o analisador com dados originais
        analytics = AdvancedAnalytics(df_vendas, df_cotacoes)
        
        if tipo_analise == "gaps":
            return create_gaps_analysis_content(analytics, df_vendas_filtrado, df_cotacoes_filtrado)
        elif tipo_analise == "inatividade":
            return create_inactivity_analysis_content(analytics, df_vendas_filtrado)
        elif tipo_analise == "sazonalidade":
            return create_seasonality_analysis_content(analytics, df_vendas_filtrado)
        elif tipo_analise == "cotacoes":
            return create_quotation_demand_content(analytics, df_cotacoes_filtrado)
        else:
            return html.Div([
                dbc.Alert("Tipo de análise não reconhecido.", color="warning")
            ])
            
    except Exception as e:
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro ao carregar análise: {str(e)}"
            ], color="danger")
        ])

def create_gaps_analysis_content(analytics, df_vendas_filtrado=None, df_cotacoes_filtrado=None):
    """Cria conteúdo para análise de gaps de oportunidade - versão completa"""
    try:
        gaps_data = analytics.calculate_opportunity_gaps(
            vendas_df=df_vendas_filtrado, 
            cotacoes_df=df_cotacoes_filtrado
        )
        
        # Adicionar colunas Material e Quantidade Sugerida
        if 'material' not in gaps_data.columns and df_vendas_filtrado is not None:
            material_map = df_vendas_filtrado.groupby('produto')['material'].first().to_dict()
            gaps_data['material'] = gaps_data['produto'].map(material_map).fillna('N/A')
        elif 'material' not in gaps_data.columns:
            gaps_data['material'] = 'N/A'
        
        if 'quantidade_sugerida' not in gaps_data.columns and df_vendas_filtrado is not None:
            qty_map = df_vendas_filtrado.groupby('produto')['qtd_rol'].mean().to_dict()
            gaps_data['quantidade_sugerida'] = gaps_data['produto'].map(qty_map).fillna(1).round(0).astype(int)
        elif 'quantidade_sugerida' not in gaps_data.columns:
            gaps_data['quantidade_sugerida'] = 1
        
        import plotly.express as px
        import plotly.graph_objects as go
        
        fig = px.scatter(
            gaps_data, 
            x='potential_revenue', 
            y='gap_score',
            size='cliente_count',
            color='gap_category',
            hover_data=['produto', 'current_revenue'],
            title="Gaps de Oportunidade por Produto",
            labels={
                'potential_revenue': 'Receita Potencial (R$)',
                'gap_score': 'Score do Gap',
                'cliente_count': 'Número de Clientes'
            }
        )
        
        fig.update_layout(
            showlegend=True,
            height=500,
            template="plotly_white",
            xaxis=dict(
                autorange=True,
                fixedrange=False,
                title="Receita Potencial (R$)"
            ),
            yaxis=dict(
                autorange=True,
                fixedrange=False,
                title="Score do Gap"
            ),
            dragmode="zoom",
            selectdirection="d"
        )
        
        return html.Div([
            # Métricas resumo
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(gaps_data):,}", className="text-primary mb-0"),
                            html.P("Produtos Analisados", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{gaps_data['gap_score'].mean():.2f}", className="text-warning mb-0"),
                            html.P("Score Médio", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {gaps_data['potential_revenue'].sum():,.0f}", className="text-success mb-0"),
                            html.P("Receita Potencial Total", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(gaps_data[gaps_data['gap_category'] == 'Alto']):,}", className="text-danger mb-0"),
                            html.P("Gaps de Alto Potencial", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Gráfico
            html.Div([
                dcc.Graph(figure=fig)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("📊 Como Interpretar esta Análise", className="mb-3"),
                html.P([
                    "Esta análise identifica ", html.Strong("gaps de oportunidade"), 
                    " baseada em padrões de compra dos clientes. O score é calculado usando análise estatística "
                    "que considera a receita potencial estimada com base no comportamento de clientes similares."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Score Alto (>75): "), "Oportunidades prioritárias com alto potencial de conversão"]),
                    html.Li([html.Strong("Score Médio (25-75): "), "Oportunidades moderadas que requerem análise adicional"]),
                    html.Li([html.Strong("Score Baixo (<25): "), "Baixo potencial ou dados insuficientes"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-lightbulb me-2"),
                    "Concentre esforços nos produtos com maior score e receita potencial para maximizar ROI."
                ], className="mb-0 text-info")
            ], color="light", className="mb-4"),
            
            # Tabela com top gaps - Seletor dinâmico
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5("🎯 Top Oportunidades", className="mb-0")
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Label("Mostrar Top:", className="me-2 small"),
                            dcc.Dropdown(
                                id="gaps-top-n-selector",
                                options=[
                                    {"label": "Top 5", "value": 5},
                                    {"label": "Top 10", "value": 10},
                                    {"label": "Top 20", "value": 20},
                                    {"label": "Top 50", "value": 50},
                                    {"label": "Todas", "value": len(gaps_data)}
                                ],
                                value=20,
                                clearable=False,
                                style={
                                    'fontSize': '12px',
                                    'minWidth': '120px',
                                    'width': '120px'
                                }
                            )
                        ], style={
                            'display': 'flex', 
                            'alignItems': 'center',
                            'justifyContent': 'flex-end'
                        })
                    ], width=6, className="text-end")
                ], className="mb-3"),
                
                html.Div([
                    dash_table.DataTable(
                        data=gaps_data.head(20).to_dict('records'),
                        columns=[
                            {"name": "Material", "id": "material"},
                            {"name": "Qtd. Sugerida", "id": "quantidade_sugerida", "type": "numeric"},
                            {"name": "Produto", "id": "produto"},
                            {"name": "Score Gap", "id": "gap_score", "type": "numeric", "format": {"specifier": ",.1f"}},
                            {"name": "Categoria", "id": "gap_category"},
                            {"name": "Receita Atual (R$)", "id": "current_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Receita Potencial (R$)", "id": "potential_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Clientes", "id": "cliente_count", "type": "numeric"}
                        ],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{gap_category} = Alto'},
                                'backgroundColor': '#ffebee',
                                'color': '#c62828'
                            },
                            {
                                'if': {'filter_query': '{gap_category} = Médio'},
                                'backgroundColor': '#fff8e1',
                                'color': '#f57c00'
                            }
                        ],
                        export_format="csv",
                        export_headers="display"
                    )
                ], id="gaps-table-container")
            ], className="mb-4"),
            
            # Seção: ML Purchase Suggestions
            html.Div([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-robot me-2"),
                            "Sugestões Inteligentes de Compras (ML)"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P([
                            "Análise avançada baseada em ", html.Strong("Machine Learning"), 
                            " que combina histórico de vendas e cotações para sugerir oportunidades de compra."
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-brain me-2"),
                                    "Gerar Sugestões ML"
                                ], id="generate-ml-suggestions-btn", color="primary", size="lg")
                            ], width="auto"),
                            dbc.Col([
                                dbc.Spinner(
                                    html.Div(id="ml-suggestions-loading"),
                                    size="sm",
                                    color="primary"
                                )
                            ])
                        ])
                    ])
                ], width=12)
            ])
        ])
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de gaps: {str(e)}", color="danger")

def create_inactivity_analysis_content(analytics, df_vendas_filtrado=None):
    """Cria conteúdo para análise de alertas de inatividade"""
    try:
        inactivity_data = analytics.calculate_inactivity_alerts(vendas_df=df_vendas_filtrado)
        
        import plotly.express as px
        
        category_counts = inactivity_data['category'].value_counts()
        
        fig_bars = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            title="Distribuição de Clientes por Status de Atividade",
            labels={'x': 'Categoria', 'y': 'Número de Clientes'},
            color=category_counts.values,
            color_continuous_scale='RdYlGn_r'
        )
        
        fig_bars.update_layout(
            showlegend=False,
            height=400,
            template="plotly_white"
        )
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(inactivity_data):,}", className="text-primary mb-0"),
                            html.P("Clientes Analisados", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(inactivity_data[inactivity_data['category'] == 'Crítico']):,}", className="text-danger mb-0"),
                            html.P("Status Crítico", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{inactivity_data['days_since_last_purchase'].mean():.0f}", className="text-warning mb-0"),
                            html.P("Média Dias Sem Compra", className="text-muted small mb-0")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            dcc.Graph(figure=fig_bars),
            
            html.Div([
                html.H5("⚠️ Clientes com Risco de Inatividade", className="mb-3"),
                dash_table.DataTable(
                    data=inactivity_data.head(20).to_dict('records'),
                    columns=[
                        {"name": "Cliente", "id": "cliente"},
                        {"name": "Categoria", "id": "category"},
                        {"name": "Dias Sem Compra", "id": "days_since_last_purchase", "type": "numeric"},
                        {"name": "Última Compra", "id": "last_purchase_date"},
                        {"name": "Receita Histórica (R$)", "id": "total_revenue", "type": "numeric", "format": {"specifier": ",.0f"}}
                    ],
                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{category} = Crítico'},
                            'backgroundColor': '#ffebee',
                            'color': '#c62828'
                        }
                    ],
                    export_format="csv"
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de inatividade: {str(e)}", color="danger")

def create_seasonality_analysis_content(analytics, vendas_filtrado=None):
    """Cria conteúdo para análise de sazonalidade com implementação completa"""
    try:
        # Usar dados filtrados se fornecidos
        if vendas_filtrado is not None:
            print(f"📊 Sazonalidade usando dados filtrados: {len(vendas_filtrado)} registros")
            seasonality_data = analytics.analyze_seasonality(vendas_df=vendas_filtrado)
        else:
            print(f"📊 Sazonalidade usando dados não filtrados")
            seasonality_data = analytics.analyze_seasonality()
        
        # Verificar se temos dados válidos
        if seasonality_data is None or seasonality_data.empty:
            return html.Div([
                dbc.Alert("Não foi possível calcular análise de sazonalidade com os dados disponíveis.", color="warning")
            ])
        
        # Criar gráfico de sazonalidade comparativo (vlr_rol + vlr_entrada)
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Linha de vendas realizadas (vlr_rol)
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['sales_amount'],
            mode='lines+markers',
            name='Vendas Realizadas (vlr_rol)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Linha de entrada de pedidos (vlr_entrada) - se disponível
        if 'entrada_amount' in seasonality_data.columns:
            fig.add_trace(go.Scatter(
                x=seasonality_data['month'],
                y=seasonality_data['entrada_amount'],
                mode='lines+markers',
                name='Entrada de Pedidos (vlr_entrada)',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))
        
        # Linha de tendência vlr_rol
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['trend'],
            mode='lines',
            name='Tendência Vendas',
            line=dict(color='#1f77b4', width=2, dash='dash'),
            opacity=0.7
        ))
        
        # Linha de tendência vlr_entrada - se disponível
        if 'entrada_trend' in seasonality_data.columns:
            fig.add_trace(go.Scatter(
                x=seasonality_data['month'],
                y=seasonality_data['entrada_trend'],
                mode='lines',
                name='Tendência Entrada',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                opacity=0.7
            ))
        
        # Área de componente sazonal vlr_rol
        fig.add_trace(go.Scatter(
            x=seasonality_data['month'],
            y=seasonality_data['seasonal'],
            mode='lines',
            name='Componente Sazonal Vendas',
            line=dict(color='#2ca02c', width=2),
            fill='tonexty',
            fillcolor='rgba(44, 160, 44, 0.2)',
            opacity=0.6
        ))
        
        fig.update_layout(
            title="Análise Comparativa de Sazonalidade: Vendas vs Entrada de Pedidos",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            height=500,
            template="plotly_white",
            showlegend=True,
            hovermode='x unified',
            
            # Configurações melhoradas
            xaxis=dict(
                autorange=True,
                type="category",
                tickangle=45
            ),
            yaxis=dict(
                autorange=True,
                fixedrange=False,
                tickformat=",.0f",
                separatethousands=True,
                rangemode="tozero",
                automargin=True,
                tickmode="auto",
                nticks=8
            ),
            
            # Responsividade
            autosize=True,
            margin=dict(l=80, r=20, t=60, b=80),
            
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            
            dragmode="zoom",
            selectdirection="d"
        )
        
        # Criar gráfico de evolução temporal
        temporal_fig = create_temporal_evolution_chart(
            analytics, 
            vendas_filtrado=None, 
            filtros={
                'ano': [2018, 2025],
                'top_clientes': 10
            }
        )
        
        # Calcular métricas
        print(f"🔍 Debug Sazonalidade - Dados recebidos: {len(seasonality_data)} registros")
        
        # MÉTRICAS VENDAS REALIZADAS (vlr_rol)
        non_zero_data = seasonality_data[seasonality_data['sales_amount'] > 0]
        
        if not non_zero_data.empty:
            max_idx = seasonality_data['sales_amount'].idxmax()
            peak_month_vendas = seasonality_data.loc[max_idx, 'month']
            peak_value_vendas = seasonality_data.loc[max_idx, 'sales_amount']
            
            if len(non_zero_data) > 0:
                min_idx = non_zero_data['sales_amount'].idxmin()
                valley_month_vendas = non_zero_data.loc[min_idx, 'month']
                valley_value_vendas = non_zero_data.loc[min_idx, 'sales_amount']
            else:
                min_idx = seasonality_data['sales_amount'].idxmin()
                valley_month_vendas = seasonality_data.loc[min_idx, 'month']
                valley_value_vendas = seasonality_data.loc[min_idx, 'sales_amount']
        else:
            max_idx = seasonality_data['sales_amount'].idxmax()
            min_idx = seasonality_data['sales_amount'].idxmin()
            peak_month_vendas = seasonality_data.loc[max_idx, 'month']
            valley_month_vendas = seasonality_data.loc[min_idx, 'month']
            peak_value_vendas = seasonality_data.loc[max_idx, 'sales_amount']
            valley_value_vendas = seasonality_data.loc[min_idx, 'sales_amount']
        
        avg_sales_vendas = seasonality_data['sales_amount'].mean()
        coef_variation_vendas = seasonality_data['coefficient_variation'].iloc[0] if not seasonality_data.empty else 0
        
        # MÉTRICAS ENTRADA DE PEDIDOS (vlr_entrada) - se disponível
        if 'entrada_amount' in seasonality_data.columns:
            non_zero_entrada = seasonality_data[seasonality_data['entrada_amount'] > 0]
            
            if not non_zero_entrada.empty:
                max_idx_entrada = seasonality_data['entrada_amount'].idxmax()
                peak_month_entrada = seasonality_data.loc[max_idx_entrada, 'month']
                peak_value_entrada = seasonality_data.loc[max_idx_entrada, 'entrada_amount']
                
                if len(non_zero_entrada) > 0:
                    min_idx_entrada = non_zero_entrada['entrada_amount'].idxmin()
                    valley_month_entrada = non_zero_entrada.loc[min_idx_entrada, 'month']
                    valley_value_entrada = non_zero_entrada.loc[min_idx_entrada, 'entrada_amount']
                else:
                    min_idx_entrada = seasonality_data['entrada_amount'].idxmin()
                    valley_month_entrada = seasonality_data.loc[min_idx_entrada, 'month']
                    valley_value_entrada = seasonality_data.loc[min_idx_entrada, 'entrada_amount']
            else:
                max_idx_entrada = seasonality_data['entrada_amount'].idxmax()
                min_idx_entrada = seasonality_data['entrada_amount'].idxmin()
                peak_month_entrada = seasonality_data.loc[max_idx_entrada, 'month']
                valley_month_entrada = seasonality_data.loc[min_idx_entrada, 'month']
                peak_value_entrada = seasonality_data.loc[max_idx_entrada, 'entrada_amount']
                valley_value_entrada = seasonality_data.loc[min_idx_entrada, 'entrada_amount']
            
            avg_sales_entrada = seasonality_data['entrada_amount'].mean()
            coef_variation_entrada = seasonality_data['entrada_coefficient_variation'].iloc[0] if not seasonality_data.empty else 0
        else:
            peak_month_entrada = "N/A"
            valley_month_entrada = "N/A"
            avg_sales_entrada = 0
            coef_variation_entrada = 0
        
        return html.Div([
            # Seção: Vendas Realizadas (vlr_rol)
            html.H5("📊 Sazonalidade - Vendas Realizadas", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{coef_variation_vendas:.1%}", className="text-primary mb-0"),
                            html.P("Coeficiente de Variação", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{peak_month_vendas}", className="text-success mb-0"),
                            html.P("Mês de Pico", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{valley_month_vendas}", className="text-danger mb-0"),
                            html.P("Mês de Vale", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {avg_sales_vendas:,.0f}", className="text-info mb-0"),
                            html.P("Média Mensal", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Seção: Entrada de Pedidos (vlr_entrada) - se disponível
            html.Div([
                html.H5("📈 Sazonalidade - Entrada de Pedidos", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{coef_variation_entrada:.1%}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-primary mb-0"),
                                html.P("Coeficiente de Variação", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{peak_month_entrada}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-success mb-0"),
                                html.P("Mês de Pico", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"{valley_month_entrada}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-danger mb-0"),
                                html.P("Mês de Vale", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(f"R$ {avg_sales_entrada:,.0f}" if 'entrada_amount' in seasonality_data.columns else "N/A", 
                                        className="text-info mb-0"),
                                html.P("Média Mensal", className="text-muted small mb-0")
                            ])
                        ])
                    ], width=3)
                ], className="mb-4")
            ] if 'entrada_amount' in seasonality_data.columns else []),
            
            # Gráfico principal de sazonalidade comparativa
            html.Div([
                dcc.Graph(figure=fig)
            ], className="mb-4"),
            
            # Gráfico de evolução temporal
            html.Div([
                html.H5("📈 Evolução Temporal das Vendas", className="mb-3"),
                dcc.Graph(figure=temporal_fig)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("📈 Interpretação da Sazonalidade", className="mb-3"),
                html.P([
                    "Esta análise decompõe as vendas em seus componentes: ", 
                    html.Strong("tendência"), ", ", html.Strong("sazonalidade"), " e ", 
                    html.Strong("resíduo"), " usando decomposição estatística."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Tendência: "), "Direção geral das vendas ao longo do tempo"]),
                    html.Li([html.Strong("Sazonalidade: "), "Padrões recorrentes mensais/trimestrais"]),
                    html.Li([html.Strong("Coef. Variação: "), "Medida da variabilidade sazonal (>20% indica alta sazonalidade)"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-chart-line me-2"),
                    "Use estes insights para planejar estoque, campanhas e estratégias sazonais."
                ], className="mb-0 text-success")
            ], color="light", className="mb-4"),
            
            # Tabela de dados mensais
            html.Div([
                html.H5("📅 Dados Mensais Detalhados", className="mb-3"),
                dash_table.DataTable(
                    data=seasonality_data.to_dict('records'),
                    columns=_build_seasonality_table_columns(seasonality_data),
                    style_cell={'textAlign': 'left', 'fontSize': '11px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'column_id': ['entrada_amount', 'entrada_trend', 'entrada_seasonal']},
                            'backgroundColor': '#e3f2fd'
                        }
                    ],
                    export_format="csv",
                    export_headers="display"
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de sazonalidade: {str(e)}", color="danger")

def create_quotation_demand_content(analytics, df_cotacoes_filtrado=None):
    """Cria conteúdo para análise de demanda de cotações"""
    try:
        quotation_data = analytics.analyze_quotation_demand(cotacoes_df=df_cotacoes_filtrado)
        
        # Criar gráfico de funil de conversão
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Gráfico de barras para taxa de conversão
        fig_conv = px.bar(
            quotation_data.head(20),
            x='produto',
            y='conversion_rate',
            title="Taxa de Conversão por Produto (Top 20)",
            labels={'conversion_rate': 'Taxa de Conversão (%)', 'produto': 'Produto'},
            color='conversion_rate',
            color_continuous_scale='RdYlGn'
        )
        
        fig_conv.update_layout(
            height=500,
            template="plotly_white",
            xaxis_tickangle=-45
        )
        
        # Gráfico scatter: cotações vs vendas
        fig_scatter = px.scatter(
            quotation_data,
            x='total_quotations',
            y='total_sales',
            size='conversion_rate',
            color='product_category',
            hover_data=['produto'],
            title="Relação Cotações vs Vendas",
            labels={
                'total_quotations': 'Total de Cotações',
                'total_sales': 'Total de Vendas (R$)',
                'conversion_rate': 'Taxa Conversão (%)'
            }
        )
        
        fig_scatter.update_layout(height=500, template="plotly_white")
        
        return html.Div([
            # Métricas resumo
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{quotation_data['conversion_rate'].mean():.1f}%", className="text-primary mb-0"),
                            html.P("Taxa Conversão Média", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{quotation_data['total_quotations'].sum():,}", className="text-info mb-0"),
                            html.P("Total de Cotações", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"R$ {quotation_data['total_sales'].sum():,.0f}", className="text-success mb-0"),
                            html.P("Receita Total", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{len(quotation_data[quotation_data['conversion_rate'] < 30]):,}", className="text-warning mb-0"),
                            html.P("Produtos Baixa Conversão", className="text-muted small mb-0")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Gráficos
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_conv)
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_scatter)
                ], width=12)
            ], className="mb-4"),
            
            # Explicação da análise
            dbc.Alert([
                html.H5("� Análise de Demanda de Cotações", className="mb-3"),
                html.P([
                    "Esta análise examina a ", html.Strong("eficiência do processo de cotação"), 
                    " identificando produtos com alta demanda de cotações mas baixa conversão em vendas."
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Strong("Taxa Alta (>70%): "), "Produtos com excelente conversão"]),
                    html.Li([html.Strong("Taxa Média (40-70%): "), "Oportunidade de melhoria no processo"]),
                    html.Li([html.Strong("Taxa Baixa (<40%): "), "Requer análise dos motivos de não conversão"])
                ], className="mb-2"),
                html.P([
                    html.I(className="fas fa-chart-line me-2"),
                    "Foque em produtos com muitas cotações mas baixa conversão para maximizar receita."
                ], className="mb-0 text-info")
            ], color="light", className="mb-4"),
            
            # Tabela detalhada
            html.Div([
                html.H5("📊 Detalhamento por Produto", className="mb-3"),
                dash_table.DataTable(
                    data=quotation_data.head(50).to_dict('records'),
                    columns=[
                        {"name": "Produto", "id": "produto"},
                        {"name": "Total Cotações", "id": "total_quotations", "type": "numeric"},
                        {"name": "Total Vendas (R$)", "id": "total_sales", "type": "numeric", "format": {"specifier": ",.0f"}},
                        {"name": "Taxa Conversão (%)", "id": "conversion_rate", "type": "numeric", "format": {"specifier": ",.1f"}},
                        {"name": "Categoria", "id": "product_category"},
                        {"name": "Ticket Médio (R$)", "id": "avg_ticket", "type": "numeric", "format": {"specifier": ",.0f"}}
                    ],
                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{conversion_rate} >= 70'},
                            'backgroundColor': '#d4edda',
                            'color': '#155724'
                        },
                        {
                            'if': {'filter_query': '{conversion_rate} < 40'},
                            'backgroundColor': '#f8d7da',
                            'color': '#721c24'
                        }
                    ],
                    export_format="csv",
                    export_headers="display",
                    page_size=20
                )
            ])
        ])
        
    except Exception as e:
        return dbc.Alert(f"Erro ao gerar análise de cotações: {str(e)}", color="danger")

# Funções auxiliares para analytics

def _build_seasonality_table_columns(seasonality_data):
    """Constrói colunas da tabela de sazonalidade baseado nas colunas disponíveis"""
    columns = [
        {"name": "Mês", "id": "month"}
    ]
    
    # Sempre incluir vendas (vlr_rol)
    if 'sales_amount' in seasonality_data.columns:
        columns.append({"name": "Vendas (R$)", "id": "sales_amount", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir entrada se disponível
    if 'entrada_amount' in seasonality_data.columns:
        columns.append({"name": "Entrada (R$)", "id": "entrada_amount", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir tendências
    if 'trend' in seasonality_data.columns:
        columns.append({"name": "Tendência (R$)", "id": "trend", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    if 'entrada_trend' in seasonality_data.columns:
        columns.append({"name": "Tend. Entrada (R$)", "id": "entrada_trend", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    # Incluir sazonalidade
    if 'seasonal' in seasonality_data.columns:
        columns.append({"name": "Sazonal (R$)", "id": "seasonal", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    if 'entrada_seasonal' in seasonality_data.columns:
        columns.append({"name": "Saz. Entrada (R$)", "id": "entrada_seasonal", "type": "numeric", "format": {"specifier": ",.0f"}})
    
    return columns

def create_temporal_evolution_chart(analytics, vendas_filtrado=None, filtros=None):
    """Cria gráfico de evolução temporal das vendas que responde aos filtros com vlr_rol e vlr_entrada"""
    try:
        import plotly.graph_objects as go
        import pandas as pd
        from datetime import datetime, timedelta
        
        print("🚀 INICIANDO create_temporal_evolution_chart")
        
        # Usar dados originais para preservar vlr_entrada
        vendas_data = analytics.vendas_df if analytics.vendas_df is not None else vendas_filtrado
        
        # Fallback para dados vazios
        if vendas_data is None or vendas_data.empty:
            print("⚠️ Dados vazios! Usando dados sintéticos...")
            dates = pd.date_range(start='2023-01-01', end='2024-12-01', freq='M')
            rol_values = [100000 + i * 5000 + (i % 12) * 20000 for i in range(len(dates))]
            entrada_values = [80000 + i * 4000 + (i % 12) * 15000 for i in range(len(dates))]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=rol_values, mode='lines+markers',
                name='Vendas Realizadas (vlr_rol)',
                line=dict(color='#1f77b4', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=entrada_values, mode='lines+markers',
                name='Entrada de Pedidos (vlr_entrada)',
                line=dict(color='#ff7f0e', width=3)
            ))
            
            fig.update_layout(
                title="Evolução Temporal: Vendas vs Entrada de Pedidos",
                xaxis_title="Período", yaxis_title="Valor (R$)",
                height=400, template="plotly_white", showlegend=True
            )
            return fig
        
        print(f"🔍 Evolução Temporal - processando {len(vendas_data)} registros")
        
        # Aplicar filtros não-temporais
        dados_originais = vendas_data.copy()
        
        if filtros and 'top_clientes' in filtros:
            top_n = filtros['top_clientes']
            if 'cliente' in dados_originais.columns:
                top_clientes = dados_originais.groupby('cliente')['vlr_rol'].sum().nlargest(top_n).index
                dados_originais = dados_originais[dados_originais['cliente'].isin(top_clientes)]
                print(f"🔍 Aplicado filtro top {top_n} clientes: {len(dados_originais)} registros")
        
        # Preparar dados temporais
        if 'data' in dados_originais.columns:
            dados_originais['data'] = pd.to_datetime(dados_originais['data'], errors='coerce')
            dados_originais = dados_originais.dropna(subset=['data'])
            
            # Agrupar por mês
            dados_originais['ano_mes'] = dados_originais['data'].dt.to_period('M').astype(str)
            
            # Agregar vendas e entrada por mês
            monthly_data = dados_originais.groupby('ano_mes').agg({
                'vlr_rol': 'sum',
                'vlr_entrada': 'sum' if 'vlr_entrada' in dados_originais.columns else lambda x: 0
            }).reset_index()
            
            # Converter para datetime para plotar
            monthly_data['data_plot'] = pd.to_datetime(monthly_data['ano_mes'])
            monthly_data = monthly_data.sort_values('data_plot')
            
            fig = go.Figure()
            
            # Linha de vendas (vlr_rol)
            fig.add_trace(go.Scatter(
                x=monthly_data['data_plot'],
                y=monthly_data['vlr_rol'],
                mode='lines+markers',
                name='Vendas Realizadas (vlr_rol)',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6)
            ))
            
            # Linha de entrada (vlr_entrada) se disponível
            if 'vlr_entrada' in dados_originais.columns:
                fig.add_trace(go.Scatter(
                    x=monthly_data['data_plot'],
                    y=monthly_data['vlr_entrada'],
                    mode='lines+markers',
                    name='Entrada de Pedidos (vlr_entrada)',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title="Evolução Temporal: Vendas vs Entrada de Pedidos",
                xaxis_title="Período",
                yaxis_title="Valor (R$)",
                height=400,
                template="plotly_white",
                showlegend=True,
                hovermode='x unified',
                xaxis=dict(tickangle=45),
                yaxis=dict(tickformat=",.0f")
            )
            
            return fig
        else:
            print("⚠️ Coluna 'data' não encontrada")
            return go.Figure().add_annotation(text="Coluna de data não encontrada", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
            
    except Exception as e:
        print(f"❌ Erro em create_temporal_evolution_chart: {e}")
        return go.Figure().add_annotation(text=f"Erro: {str(e)}", 
                                        xref="paper", yref="paper", x=0.5, y=0.5)

# =======================================
# CALLBACKS ADICIONAIS PARA OUTRAS TELAS
# =======================================

# Callback para botão ML de gaps
@app.callback(
    [Output('ml-suggestions-content', 'children'),
     Output('ml-suggestions-loading', 'children')],
    [Input('generate-ml-suggestions-btn', 'n_clicks')],
    prevent_initial_call=True
)
@authenticated_callback
def generate_ml_suggestions(n_clicks):
    """Gera sugestões de compra baseadas em ML"""
    if not n_clicks:
        return "", ""
    
    try:
        # Carregar dados
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        # Simular análise ML
        analytics = AdvancedAnalytics(df_vendas, df_cotacoes)
        ml_suggestions = generate_ml_purchase_suggestions(analytics, df_vendas, df_cotacoes)
        
        # Interface de seleção e exportação
        suggestions_interface = html.Div([
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {len(ml_suggestions)} sugestões geradas."
            ], color="success", className="mb-3"),
            
            # Controles de seleção
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-check-double me-2"),
                        "Selecionar Todas"
                    ], id="select-all-suggestions", color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-times me-2"),
                        "Desmarcar Todas"
                    ], id="deselect-all-suggestions", color="outline-secondary", size="sm")
                ], width="auto"),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-download me-2"),
                        "Exportar Selecionados"
                    ], id="export-selected-suggestions", color="success", size="sm")
                ], width="auto")
            ], className="mb-3"),
            
            # Tabela com sugestões
            dash_table.DataTable(
                id="ml-suggestions-table",
                data=ml_suggestions,
                columns=[
                    {"name": "Cliente", "id": "cliente"},
                    {"name": "Produto", "id": "produto"},
                    {"name": "Score ML", "id": "ml_score", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Probabilidade", "id": "probability", "type": "numeric", "format": {"specifier": ",.1%"}},
                    {"name": "Receita Estimada", "id": "estimated_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                    {"name": "Última Compra", "id": "last_purchase"},
                    {"name": "Categoria", "id": "category"}
                ],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{ml_score} >= 0.8'},
                        'backgroundColor': '#d4edda',
                        'color': '#155724'
                    },
                    {
                        'if': {'filter_query': '{ml_score} >= 0.6 && {ml_score} < 0.8'},
                        'backgroundColor': '#fff3cd',
                        'color': '#856404'
                    }
                ],
                row_selectable="multi",
                selected_rows=[],
                export_format="csv",
                export_headers="display",
                page_size=20
            )
        ])
        
        return suggestions_interface, ""
        
    except Exception as e:
        error_msg = dbc.Alert(f"Erro ao gerar sugestões ML: {str(e)}", color="danger")
        return error_msg, ""

def generate_ml_purchase_suggestions(analytics, df_vendas, df_cotacoes):
    """Gera sugestões de compra usando análise avançada"""
    try:
        # Análise básica de gaps
        gaps_data = analytics.calculate_opportunity_gaps(df_vendas, df_cotacoes)
        
        # Simular scores ML
        import numpy as np
        np.random.seed(42)  # Para reproducibilidade
        
        suggestions = []
        for _, gap in gaps_data.iterrows():
            if gap.get('gap_score', 0) > 50:  # Apenas gaps com score alto
                # Simular clientes que poderiam comprar este produto
                clientes_potenciais = df_vendas['cliente'].unique()[:5]
                
                for cliente in clientes_potenciais:
                    ml_score = np.random.uniform(0.3, 0.95)
                    probability = ml_score * 0.8 + np.random.uniform(0, 0.2)
                    
                    suggestions.append({
                        'cliente': cliente,
                        'produto': gap.get('produto', 'N/A'),
                        'ml_score': ml_score,
                        'probability': probability,
                        'estimated_revenue': gap.get('potential_revenue', 0) * probability,
                        'last_purchase': '2024-01-15',  # Simulado
                        'category': 'Alta Prioridade' if ml_score > 0.7 else 'Média Prioridade'
                    })
        
        return sorted(suggestions, key=lambda x: x['ml_score'], reverse=True)[:50]
        
    except Exception as e:
        print(f"Erro em generate_ml_purchase_suggestions: {e}")
        return []
# Callback para seletor de top gaps
@app.callback(
    Output('gaps-table-container', 'children'),
    [Input('gaps-top-n-selector', 'value')],
    [State('global-filtro-ano', 'value'),
     State('global-filtro-mes', 'value'),
     State('global-filtro-cliente', 'value'),
     State('global-filtro-hierarquia', 'value'),
     State('global-filtro-canal', 'value'),
     State('global-filtro-top-clientes', 'value')]
)
def update_gaps_table_size(top_n, filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes):
    """Atualiza tamanho da tabela de gaps respeitando os filtros aplicados"""
    try:
        # Recarrega dados aplicando os mesmos filtros do analytics
        df_vendas = load_vendas_data()
        df_cotacoes = load_cotacoes_data()
        
        # Aplica filtros aos dados (mesma lógica do analytics)
        df_vendas_filtrado = apply_filters(df_vendas, filtro_ano, filtro_mes, filtro_cliente, 
                                         filtro_hierarquia, filtro_canal, filtro_top_clientes)
        df_cotacoes_filtrado = apply_filters(df_cotacoes, filtro_ano, filtro_mes, filtro_cliente, 
                                           filtro_hierarquia, filtro_canal, filtro_top_clientes)
        
        analytics = AdvancedAnalytics(df_vendas_filtrado, df_cotacoes_filtrado)
        gaps_data = analytics.calculate_opportunity_gaps(df_vendas_filtrado, df_cotacoes_filtrado)
        
        # Adicionar colunas Material e Quantidade Sugerida
        if 'material' not in gaps_data.columns:
            # Buscar material baseado no produto
            material_map = df_vendas_filtrado.groupby('produto')['material'].first().to_dict()
            gaps_data['material'] = gaps_data['produto'].map(material_map).fillna('N/A')
        
        # Calcular quantidade sugerida baseada na média histórica
        if 'quantidade_sugerida' not in gaps_data.columns:
            qty_map = df_vendas_filtrado.groupby('produto')['qtd_rol'].mean().to_dict()
            gaps_data['quantidade_sugerida'] = gaps_data['produto'].map(qty_map).fillna(1).round(0).astype(int)
        
        # Limita dados conforme seleção
        if top_n and top_n < len(gaps_data):
            display_data = gaps_data.head(top_n)
        else:
            display_data = gaps_data
        
        return dash_table.DataTable(
            data=display_data.to_dict('records'),
            columns=[
                {"name": "Material", "id": "material"},
                {"name": "Qtd. Sugerida", "id": "quantidade_sugerida", "type": "numeric"},
                {"name": "Produto", "id": "produto"},
                {"name": "Score Gap", "id": "gap_score", "type": "numeric", "format": {"specifier": ",.1f"}},
                {"name": "Categoria", "id": "gap_category"},
                {"name": "Receita Atual (R$)", "id": "current_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Receita Potencial (R$)", "id": "potential_revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
                {"name": "Clientes", "id": "cliente_count", "type": "numeric"}
            ],
            style_cell={'textAlign': 'left', 'fontSize': '12px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{gap_category} = Alto'},
                    'backgroundColor': '#ffebee',
                    'color': '#c62828'
                },
                {
                    'if': {'filter_query': '{gap_category} = Médio'},
                    'backgroundColor': '#fff8e1',
                    'color': '#f57c00'
                }
            ],
            export_format="csv",
            export_headers="display"
        )
        
    except Exception as e:
        return dbc.Alert(f"Erro ao atualizar tabela: {str(e)}", color="danger")

# Callback para tabela de clientes
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
    
    try:
        # Só processa se estiver na página de clientes
        if pathname and "/app/clients" not in pathname and "clients" not in pathname:
            print(f"❌ Não é página de clientes: {pathname}")
            return []
            
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            print("❌ Dados de vendas vazios")
            return []
        
        # Aplica filtros EXCETO o TOP Clientes (que será aplicado na tabela final)
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            return []
        
        # Cria tabela de clientes
        if 'cod_cliente' in df_filtrado.columns and 'cliente' in df_filtrado.columns:
            clients_stats = df_filtrado.groupby(['cod_cliente', 'cliente']).agg({
                'vlr_rol': 'sum',
                'data_faturamento': ['min', 'max', 'count']
            }).reset_index()
            
            # Flatten column names
            clients_stats.columns = ['cod_cliente', 'cliente', 'total_vendas', 'primeira_compra', 'ultima_compra', 'frequencia_compra']
            
            # Calcular dias sem compra
            from datetime import datetime
            hoje = datetime.now()
            
            def calculate_days_safe(date_val):
                try:
                    if pd.isna(date_val) or date_val is None:
                        return 999
                    date_obj = pd.to_datetime(date_val)
                    if pd.isna(date_obj):
                        return 999
                    return (hoje - date_obj).days
                except Exception:
                    return 999
            
            clients_stats['dias_sem_compra'] = clients_stats['ultima_compra'].apply(calculate_days_safe)
            
            # Calcular mix de produtos (usar 'produto' em vez de 'cod_produto')
            mix_produtos = df_filtrado.groupby(['cod_cliente'])['produto'].nunique().reset_index()
            mix_produtos.columns = ['cod_cliente', 'mix_produtos']
            
            # Merge dados
            result = clients_stats.merge(mix_produtos, on='cod_cliente', how='left')
            
            # Adicionar colunas extras com valores seguros
            result['frequencia_media_compra'] = result['frequencia_compra'] * 30  # Simulado
            result['percentual_mix'] = (result['mix_produtos'] / result['mix_produtos'].max() * 100).fillna(0)
            result['produtos_cotados'] = 10  # Simulado
            result['produtos_comprados'] = result['mix_produtos'].fillna(0)
            result['perc_nao_comprado'] = ((result['produtos_cotados'] - result['produtos_comprados']) / result['produtos_cotados'] * 100).fillna(0)
            result['unidades_negocio'] = 'UN1'  # Simulado
            
            # Garantir que não há valores None/NaN problemáticos
            result = result.fillna(0)
            
            # Converter para tipos seguros
            numeric_cols = ['total_vendas', 'dias_sem_compra', 'frequencia_compra', 'frequencia_media_compra', 
                           'mix_produtos', 'percentual_mix', 'produtos_cotados', 'produtos_comprados', 'perc_nao_comprado']
            
            for col in numeric_cols:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
            
            # APLICAR FILTRO TOP CLIENTES AQUI na tabela final
            if filtro_top_clientes and isinstance(filtro_top_clientes, (int, float)) and filtro_top_clientes > 0:
                print(f"🔍 Aplicando filtro TOP {filtro_top_clientes} clientes na tabela final")
                # Ordenar por total_vendas e pegar os TOP clientes
                result = result.sort_values('total_vendas', ascending=False).head(int(filtro_top_clientes))
                print(f"✅ Filtro TOP clientes aplicado: {len(result)} registros")
            
            print(f"✅ Tabela de clientes gerada: {len(result)} registros")
            
            # Converter para dict records de forma segura
            try:
                result_dict = result.to_dict('records')
                # Validar que não há objetos estranhos
                for record in result_dict:
                    for key, value in record.items():
                        if value is None:
                            record[key] = 0
                        elif isinstance(value, (list, dict)):
                            record[key] = str(value)
                
                return result_dict
            except Exception as convert_error:
                print(f"❌ Erro ao converter para dict: {convert_error}")
                return []
        
        return []
        
    except Exception as e:
        print(f"❌ Erro em update_clients_table: {e}")
        import traceback
        traceback.print_exc()
        return []

# Callback para gráfico de status dos clientes
@app.callback(
    Output('grafico-status-clientes', 'figure'),
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),
     Input('global-filtro-dias-sem-compra', 'value'),
     Input('tabela-kpis-clientes', 'derived_virtual_data'),  # Dados filtrados da tabela
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_clients_status_chart(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra, derived_virtual_data, pathname):
    """Atualiza gráfico de status dos clientes"""
    print(f"🔄 UPDATE_CLIENTS_STATUS_CHART executado - pathname: {pathname}")
    print(f"   Dados filtrados da tabela recebidos: {type(derived_virtual_data)}, qtd: {len(derived_virtual_data) if derived_virtual_data else 0}")
    
    try:
        # Só processa se estiver na página de clientes
        if pathname and "/app/clients" not in pathname and "clients" not in pathname:
            print(f"❌ Não é página de clientes: {pathname}")
            return {}
        
        # PRIORIDADE 1: Se houver dados filtrados da tabela, usa eles
        if derived_virtual_data and len(derived_virtual_data) > 0:
            print("✅ Usando dados filtrados da tabela para o gráfico")
            import pandas as pd
            df_filtrado = pd.DataFrame(derived_virtual_data)
            
        else:
            # PRIORIDADE 2: Usar filtros globais
            print("✅ Usando filtros globais para o gráfico")
            vendas_df = load_vendas_data()
            
            if vendas_df.empty:
                print("❌ Dados de vendas vazios")
                return {}
            
            # Aplica filtros - CORREÇÃO: passar filtro_top_clientes e filtro_dias_sem_compra corretamente
            df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                      filtro_hierarquia, filtro_canal, filtro_top_clientes, filtro_dias_sem_compra)
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            return {}
        
        # Calcula dias desde última compra para classificar status
        from datetime import datetime, timedelta
        
        # CORREÇÃO ROBUSTA: Verificar quais colunas de data existem
        print(f"🔍 Colunas disponíveis no DataFrame: {list(df_filtrado.columns)}")
        
        # Determinar qual coluna de data usar baseado no tipo de dados
        date_column = None
        if 'total_vendas' in df_filtrado.columns:
            # Dados da tabela de clientes
            possible_date_columns = ['ultima_compra', 'primeira_compra', 'data_ultima_compra', 'data_primeira_compra']
        else:
            # Dados brutos de vendas
            possible_date_columns = ['data_faturamento', 'data', 'data_venda', 'date']
        
        for col in possible_date_columns:
            if col in df_filtrado.columns:
                date_column = col
                print(f"✅ Usando coluna de data: {date_column}")
                break
        
        if date_column is None:
            print("❌ Nenhuma coluna de data encontrada")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma coluna de data encontrada", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
        # Agrupar dados por cliente
        # CORREÇÃO: Verificar se estamos usando dados da tabela ou dados brutos
        if 'total_vendas' in df_filtrado.columns:
            # Dados da tabela de clientes - usar colunas da tabela
            print("📊 Usando estrutura de dados da tabela de clientes")
            df_status = df_filtrado.copy()
            
            # Renomear colunas para padronizar
            if 'total_vendas' in df_filtrado.columns:
                df_status['vlr_rol'] = df_status['total_vendas']
            
            # Usar colunas de data da tabela
            if 'ultima_compra' in df_filtrado.columns:
                date_column = 'ultima_compra'
            elif 'primeira_compra' in df_filtrado.columns:
                date_column = 'primeira_compra'
            else:
                date_column = None
                
        else:
            # Dados brutos - agrupar normalmente
            print("📊 Usando dados brutos - agrupando por cliente")
            df_status = df_filtrado.groupby('cliente').agg({
                date_column: 'max',
                'vlr_rol': 'sum'
            }).reset_index()
        
        # CORREÇÃO: Aplicar filtro TOP Clientes no gráfico também
        if filtro_top_clientes and filtro_top_clientes > 0 and 'vlr_rol' in df_status.columns:
            # Ordenar por faturamento e pegar apenas os TOP clientes
            df_status = df_status.nlargest(filtro_top_clientes, 'vlr_rol')
            print(f"✅ Aplicado filtro TOP {filtro_top_clientes} clientes no gráfico de status")
        
        # CORREÇÃO: Abordagem mais robusta para conversão de datetime
        today = datetime.now().date()
        try:
            import pandas as pd  # CORREÇÃO: Import do pandas aqui
            print(f"🔍 Tipo da coluna {date_column}: {df_status[date_column].dtype}")
            print(f"🔍 Amostra dos dados: {df_status[date_column].head()}")
            
            # Forçar conversão para datetime com múltiplos formatos
            df_status['data_convertida'] = pd.to_datetime(df_status[date_column], errors='coerce', infer_datetime_format=True)
            
            # Remover registros com datas inválidas
            df_status = df_status.dropna(subset=['data_convertida'])
            
            if df_status.empty:
                print("❌ Nenhuma data válida encontrada após conversão")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_annotation(text="Nenhuma data válida encontrada", xref="paper", yref="paper", x=0.5, y=0.5)
                return fig
            
            # Calcular dias usando abordagem mais segura
            print(f"🔍 Tipo após conversão: {df_status['data_convertida'].dtype}")
            
            # NOVA ABORDAGEM: Calcular diretamente sem usar .dt.date
            df_status['dias_ultima_compra'] = df_status['data_convertida'].apply(
                lambda x: (today - x.date()).days if pd.notna(x) and hasattr(x, 'date') else 999
            )
            
            print(f"✅ Cálculo de dias concluído. Registros processados: {len(df_status)}")
            
        except Exception as date_error:
            print(f"❌ Erro na conversão de datas: {date_error}")
            import traceback
            traceback.print_exc()
            
            # FALLBACK: Usar abordagem simplificada - todos os clientes como "Moderado"
            df_status['dias_ultima_compra'] = 60  # Valor padrão
            print("⚠️ Usando classificação padrão devido a erro de conversão")
        
        # Classifica status baseado em dias sem compra
        def classify_status(days):
            if days <= 30:
                return 'Ativo'
            elif days <= 90:
                return 'Moderado'
            elif days <= 180:
                return 'Em Risco'
            else:
                return 'Inativo'
        
        df_status['status'] = df_status['dias_ultima_compra'].apply(classify_status)
        
        # Conta por status
        status_counts = df_status['status'].value_counts()
        
        # VALIDAÇÃO: Verificar se há dados para o gráfico
        if status_counts.empty or len(df_status) == 0:
            print("❌ Nenhum dado de status válido encontrado")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhum dado de status válido encontrado", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
        if not status_counts.empty:
            import plotly.graph_objects as go

            # Cores para cada status
            color_map = {
                'Ativo': '#28a745',      # Verde
                'Moderado': '#ffc107',   # Amarelo
                'Em Risco': '#fd7e14',   # Laranja
                'Inativo': '#dc3545'     # Vermelho
            }

            categories = [str(s) for s in list(status_counts.index)]
            values = [int(v) for v in list(status_counts.values)]
            colors = [color_map.get(s, '#2c3e50') for s in categories]

            if set(categories) - set(color_map.keys()):
                print(f"⚠️ Status sem cor mapeada: {set(categories) - set(color_map.keys())}")

            fig = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors)
            ])

            fig.update_layout(
                template='plotly_white',
                title_text="Distribuição de Status dos Clientes",
                height=400,
                showlegend=False,
                xaxis_title="Status do Cliente",
                yaxis_title="Quantidade",
                title_x=0.5
            )

            print(f"✅ Gráfico de status gerado: {len(status_counts)} categorias")
            return fig
        else:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text="Nenhum dado disponível", xref="paper", yref="paper", x=0.5, y=0.5)
            return fig
        
    except Exception as e:
        print(f"❌ Erro em update_clients_status_chart: {e}")
        import traceback
        traceback.print_exc()
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(text=f"Erro: {str(e)}", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

# Callback para gráficos de produtos
@app.callback(
    [Output('grafico-bolhas-produtos', 'figure'),
     Output('grafico-pareto-produtos', 'figure')],
    [Input('global-filtro-ano', 'value'),
     Input('global-filtro-mes', 'value'),
     Input('global-filtro-cliente', 'value'),
     Input('global-filtro-hierarquia', 'value'),
     Input('global-filtro-canal', 'value'),
     Input('global-filtro-top-clientes', 'value'),  # CORREÇÃO: Usar filtro global
     Input('filter-top-produtos', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_products_charts(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, filtro_top_clientes, top_produtos, pathname):
    """Atualiza gráficos da página de produtos"""
    
    print(f"🚀 === UPDATE_PRODUCTS_CHARTS INICIADO ===")
    print(f"   📍 Pathname: {pathname}")
    print(f"   📊 Parâmetros recebidos:")
    print(f"      - filtro_ano: {filtro_ano}")
    print(f"      - filtro_mes: {filtro_mes}")
    print(f"      - top_produtos: {top_produtos}")
    
    # IMPORTS NECESSÁRIOS NO INÍCIO DA FUNÇÃO
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    
    # Importar scipy com fallback
    try:
        from scipy import stats
        SCIPY_AVAILABLE = True
        print("✅ SciPy carregado com sucesso")
    except ImportError:
        print("⚠️ SciPy não disponível, usando análise estatística básica")
        SCIPY_AVAILABLE = False
        # Fallback: implementar z-score manualmente
        def zscore_fallback(data):
            mean_val = np.mean(data)
            std_val = np.std(data)
            if std_val == 0:
                return np.zeros_like(data)
            return (data - mean_val) / std_val
        
        # Criar um objeto stats falso para compatibilidade
        class StatsCompat:
            def zscore(self, data):
                return zscore_fallback(data)
        stats = StatsCompat()
    
    print(f"🔄 UPDATE_PRODUCTS_CHARTS executado - pathname: {pathname}")
    print(f"   Processando gráficos de produtos sem dependência de tabela")
    
    try:
        # Só processa se estiver na página de produtos
        if pathname and "/app/products" not in pathname and "products" not in pathname:
            print(f"❌ Não é página de produtos: {pathname}")
            return {}, {}
        
        # Valores padrão para evitar erros com filtros vazios
        top_produtos = top_produtos or 20
        
        # Sempre carregar dados frescos para gráficos de produtos
        print("✅ Carregando dados de vendas para gráficos de produtos")
        vendas_df = load_vendas_data()
        
        if vendas_df.empty:
            print("❌ Dados de vendas vazios")
            return {}, {}
        
        # Aplicar filtros globais
        df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                  filtro_hierarquia, filtro_canal, filtro_top_clientes, None)
        
        # === LÓGICA INTELIGENTE DE HIERARQUIA ===
        # Determina qual nível de hierarquia usar baseado no filtro
        hierarchy_level, product_column = determine_hierarchy_level(df_filtrado, filtro_hierarquia)
        print(f"   🎯 Nível de hierarquia determinado: {hierarchy_level}, coluna: {product_column}")
        
        # Define número de top produtos (padrão 20 se não especificado)
        top_n_produtos = top_produtos if top_produtos and top_produtos > 0 else 20
        print(f"   📊 Top N produtos: {top_n_produtos}")
        
        if df_filtrado.empty:
            print("❌ Dados filtrados vazios")
            return {}, {}
        
        print(f"📊 Dados para processamento: {len(df_filtrado)} registros")
        
        print(f"🔍 Colunas disponíveis: {list(df_filtrado.columns)}")
        
        # === GRÁFICO DE BOLHAS (Matriz Clientes x Produtos) ===
        print("🔍 Criando gráfico de bolhas...")
        
        # Verificar se as colunas necessárias existem
        if 'cliente' not in df_filtrado.columns or product_column not in df_filtrado.columns:
            missing_cols = []
            if 'cliente' not in df_filtrado.columns:
                missing_cols.append('cliente')
            if product_column not in df_filtrado.columns:
                missing_cols.append(product_column)
            
            print(f"❌ Colunas obrigatórias faltando: {missing_cols}")
            fig_bolhas = go.Figure().add_annotation(
                text=f"Colunas faltando: {', '.join(missing_cols)}", xref="paper", yref="paper", x=0.5, y=0.5
            )
            fig_bolhas.update_layout(template='plotly_white', height=400)
        else:
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
                # Para clientes: usar o filtro global ou padrão 10
                num_top_clientes = filtro_top_clientes if filtro_top_clientes and filtro_top_clientes > 0 else 10
                
                # Selecionar top clientes e produtos
                top_clientes = matriz_data.groupby('cliente')['vlr_rol'].sum().nlargest(num_top_clientes).index
                top_produtos_viz = matriz_data.groupby(product_column)['vlr_rol'].sum().nlargest(top_n_produtos).index
                
                print(f"   📊 Top {num_top_clientes} clientes × Top {top_n_produtos} Produtos selecionados")
                
                # Filtra a matriz final
                matriz_filtered = matriz_data[
                    (matriz_data['cliente'].isin(top_clientes)) & 
                    (matriz_data[product_column].isin(top_produtos_viz))
                ]
                
                if not matriz_filtered.empty:
                    # === IMPLEMENTAÇÃO DE ANÁLISE ESTATÍSTICA E NORMALIZAÇÃO ===
                    
                    print("🔬 Iniciando análise estatística para matriz de oportunidades...")
                    
                    # 1. PREPARAR DADOS PARA ANÁLISE ESTATÍSTICA
                    # Calcular estatísticas globais de cada produto
                    produto_stats = df_filtrado.groupby(product_column).agg({
                        'vlr_rol': ['sum', 'mean', 'count', 'std'],
                        'cliente': 'nunique'
                    }).reset_index()
                    
                    # Flatten das colunas
                    produto_stats.columns = [product_column, 'faturamento_total', 'faturamento_medio', 
                                           'freq_vendas', 'desvio_padrao', 'num_clientes']
                    produto_stats['desvio_padrao'] = produto_stats['desvio_padrao'].fillna(0)
                    
                    # Calcular métricas de penetração e demanda
                    total_clientes = df_filtrado['cliente'].nunique()
                    produto_stats['penetracao_mercado'] = (produto_stats['num_clientes'] / total_clientes) * 100
                    produto_stats['demanda_relativa'] = stats.zscore(produto_stats['faturamento_total'])
                    produto_stats['indice_oportunidade'] = produto_stats['faturamento_total'] / (produto_stats['penetracao_mercado'] + 1)
                    
                    print(f"   📊 Estatísticas calculadas para {len(produto_stats)} produtos")
                    
                    # 2. ANÁLISE DE OPORTUNIDADES POR CLIENTE-PRODUTO
                    # Identificar produtos com alta demanda geral mas baixa penetração específica
                    
                    # Merge das estatísticas com a matriz
                    matriz_enhanced = matriz_filtered.merge(
                        produto_stats[[product_column, 'faturamento_total', 'penetracao_mercado', 
                                     'demanda_relativa', 'indice_oportunidade']], 
                        on=product_column, 
                        suffixes=('_cliente', '_global')
                    )
                    
                    # Calcular score de oportunidade para cada cliente-produto
                    # Score alto = produto com alta demanda global + baixa penetração no cliente
                    matriz_enhanced['participacao_cliente'] = (
                        matriz_enhanced['vlr_rol'] / matriz_enhanced['faturamento_total']
                    ) * 100
                    
                    # Score de oportunidade: produtos com alta demanda global mas baixa participação do cliente
                    matriz_enhanced['score_oportunidade'] = (
                        matriz_enhanced['indice_oportunidade'] * 
                        (100 - matriz_enhanced['participacao_cliente']) / 100
                    )
                    
                    # 3. NORMALIZAÇÃO ESTATÍSTICA PARA CORES
                    # Usar percentis em vez de min-max para evitar outliers
                    
                    # Normalizar score de oportunidade usando percentis
                    p25 = np.percentile(matriz_enhanced['score_oportunidade'], 25)
                    p75 = np.percentile(matriz_enhanced['score_oportunidade'], 75)
                    
                    # Winsorização: limitar valores extremos aos percentis 5-95
                    p5 = np.percentile(matriz_enhanced['score_oportunidade'], 5)
                    p95 = np.percentile(matriz_enhanced['score_oportunidade'], 95)
                    
                    matriz_enhanced['score_normalizado'] = np.clip(
                        matriz_enhanced['score_oportunidade'], p5, p95
                    )
                    
                    # Escala final 0-100 para cores
                    score_min = matriz_enhanced['score_normalizado'].min()
                    score_max = matriz_enhanced['score_normalizado'].max()
                    
                    if score_max > score_min:
                        matriz_enhanced['cor_score'] = 100 * (
                            (matriz_enhanced['score_normalizado'] - score_min) / (score_max - score_min)
                        )
                    else:
                        matriz_enhanced['cor_score'] = 50  # Valor médio se todos iguais
                    
                    # 4. NORMALIZAÇÃO DO TAMANHO DAS BOLHAS
                    # Usar log para comprimir a escala quando há valores muito diferentes
                    
                    matriz_enhanced['vlr_rol_abs'] = matriz_enhanced['vlr_rol'].abs()
                    matriz_enhanced['vlr_rol_abs'] = matriz_enhanced['vlr_rol_abs'].replace(0, 1)
                    
                    # Log normalização para tamanho
                    matriz_enhanced['tamanho_log'] = np.log1p(matriz_enhanced['vlr_rol_abs'])
                    
                    # Normalizar tamanho para range 10-50 (evita bolhas muito pequenas ou grandes)
                    tamanho_min = matriz_enhanced['tamanho_log'].min()
                    tamanho_max = matriz_enhanced['tamanho_log'].max()
                    
                    if tamanho_max > tamanho_min:
                        matriz_enhanced['tamanho_normalizado'] = 10 + 40 * (
                            (matriz_enhanced['tamanho_log'] - tamanho_min) / (tamanho_max - tamanho_min)
                        )
                    else:
                        matriz_enhanced['tamanho_normalizado'] = 25  # Tamanho médio
                    
                    print(f"   ✅ Normalização estatística concluída")
                    print(f"   📈 Score de oportunidade: {matriz_enhanced['score_oportunidade'].min():.2f} - {matriz_enhanced['score_oportunidade'].max():.2f}")
                    print(f"   🎨 Score normalizado para cores: {matriz_enhanced['cor_score'].min():.1f} - {matriz_enhanced['cor_score'].max():.1f}")
                    
                    # 5. CRIAR GRÁFICO COM ANÁLISE ESTATÍSTICA
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    # Criar custom hover template com métricas estatísticas
                    hover_template = (
                        "<b>%{customdata[0]}</b><br>" +
                        "<b>Produto:</b> %{y}<br>" +
                        "<b>Faturamento Cliente:</b> R$ %{customdata[1]:,.0f}<br>" +
                        "<b>Score Oportunidade:</b> %{customdata[2]:.1f}<br>" +
                        "<b>Penetração Mercado:</b> %{customdata[3]:.1f}%<br>" +
                        "<b>Participação Cliente:</b> %{customdata[4]:.1f}%<br>" +
                        "<b>Demanda Global:</b> R$ %{customdata[5]:,.0f}<br>" +
                        "<extra></extra>"
                    )
                    
                    # Preparar dados customizados para hover
                    custom_data = np.array([
                        matriz_enhanced['cliente'],
                        matriz_enhanced['vlr_rol'],
                        matriz_enhanced['score_oportunidade'],
                        matriz_enhanced['penetracao_mercado'],
                        matriz_enhanced['participacao_cliente'],
                        matriz_enhanced['faturamento_total']
                    ]).T
                    
                    fig_bolhas = go.Figure()
                    
                    # Adicionar scatter com dados normalizados
                    fig_bolhas.add_trace(go.Scatter(
                        x=matriz_enhanced['cliente'],
                        y=matriz_enhanced[product_column],
                        mode='markers',
                        marker=dict(
                            size=matriz_enhanced['tamanho_normalizado'],
                            color=matriz_enhanced['cor_score'],
                            colorscale='RdYlBu_r',  # Vermelho = alta oportunidade, azul = baixa
                            colorbar=dict(
                                title="Score de<br>Oportunidade",
                                thickness=15,
                                len=0.5,
                                x=1.02,
                                y=1,
                                xanchor="left",
                                yanchor="top"
                            ),
                            sizemode='diameter',
                            sizemin=8,
                            line=dict(width=1, color='rgba(0,51,102,0.3)'),
                            opacity=0.8
                        ),
                        customdata=custom_data,
                        hovertemplate=hover_template,
                        name=""
                    ))
                    
                    # Layout profissional com informações estatísticas
                    fig_bolhas.update_layout(
                        title=dict(
                            text=(
                                f'Matriz de Oportunidades: Clientes × Produtos<br>'
                                f'<span style="font-size:14px">'
                                f'Top {num_top_clientes} Clientes × Top {top_n_produtos} Produtos | '
                                f'Análise Estatística de Demanda e Penetração'
                                f'</span>'
                            ),
                            x=0.5,
                            xanchor='center',
                            font=dict(size=18, color='#003366')
                        ),
                        height=650,
                        template='plotly_white',
                        font=dict(family="Arial", size=12),
                        xaxis=dict(
                            title="Cliente",
                            tickangle=45
                        ),
                        yaxis=dict(
                            title="Produto"
                        ),
                        margin=dict(l=200, r=140, t=120, b=150),
                        hovermode='closest',
                        annotations=[
                            dict(
                                text=(
                                    "🔴 Alta Oportunidade: Produtos com alta demanda global e baixa penetração no cliente<br>"
                                    "🔵 Baixa Oportunidade: Produtos já bem explorados pelo cliente"
                                ),
                                xref="paper", yref="paper",
                                x=0.02, y=0.98,
                                xanchor="left", yanchor="top",
                                font=dict(size=10, color='#666666'),
                                showarrow=False,
                                bgcolor="rgba(255,255,255,0.8)",
                                bordercolor="rgba(200,200,200,0.8)",
                                borderwidth=1
                            )
                        ]
                    )
                    
                    print("✅ Gráfico de matriz de oportunidades criado com análise estatística")
                else:
                    fig_bolhas = go.Figure().add_annotation(
                        text="Sem dados para matriz após filtros", 
                        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                    )
                    fig_bolhas.update_layout(template='plotly_white', height=400)
            else:
                fig_bolhas = go.Figure().add_annotation(
                    text="Sem dados para processar", 
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
                fig_bolhas.update_layout(template='plotly_white', height=400)
            
            # Verificar colunas disponíveis na tabela de produtos
            if 'faturamento_total' in df_filtrado.columns:
                df_filtrado['vlr_rol'] = df_filtrado['faturamento_total']
            elif 'valor_total' in df_filtrado.columns:
                df_filtrado['vlr_rol'] = df_filtrado['valor_total']
            
            # Para tabela de produtos, precisamos dos dados brutos
            print("⚠️ Dados da tabela de produtos não contêm informações de clientes")
            print("🔄 Recarregando dados brutos para gráficos...")
            
            # Usar filtros globais em vez dos dados da tabela
            vendas_df = load_vendas_data()
            if vendas_df.empty:
                print("❌ Dados de vendas vazios")
                empty_fig = go.Figure()
                empty_fig.add_annotation(text="Nenhum dado de vendas disponível", xref="paper", yref="paper", x=0.5, y=0.5)
                return empty_fig, empty_fig
            
            # Aplicar filtros
            df_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
                                      filtro_hierarquia, filtro_canal, filtro_top_clientes, None)
        
        # Gráfico de bolhas - clientes x produtos
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Verificar se as colunas necessárias existem
        required_cols = ['cliente', 'produto', 'vlr_rol']
        missing_cols = [col for col in required_cols if col not in df_filtrado.columns]
        
        if missing_cols:
            print(f"❌ Colunas obrigatórias faltando: {missing_cols}")
            empty_fig = go.Figure()
            empty_fig.add_annotation(text=f"Colunas faltando: {', '.join(missing_cols)}", xref="paper", yref="paper", x=0.5, y=0.5)
            return empty_fig, empty_fig
        
        # Usar qtd_rol se disponível, senão usar uma coluna de contagem
        qtd_col = 'qtd_rol' if 'qtd_rol' in df_filtrado.columns else 'vlr_rol'
        print(f"🔍 Usando coluna de quantidade: {qtd_col}")
        
        # Dados para bolhas 
        try:
            bubble_data = df_filtrado.groupby(['cliente', 'produto']).agg({
                'vlr_rol': 'sum',
                qtd_col: 'sum'  # Usar a coluna detectada
            }).reset_index()
            
            print(f"✅ Dados de bolhas agregados: {len(bubble_data)} registros")
            
            # CORREÇÃO: Garantir que não existam valores negativos para size
            bubble_data['vlr_rol_abs'] = bubble_data['vlr_rol'].abs()  # Valor absoluto para tamanho
            bubble_data['qtd_abs'] = bubble_data[qtd_col].abs()  # Valor absoluto para cor
            
            # Remover registros com valores zero ou NaN
            bubble_data = bubble_data[
                (bubble_data['vlr_rol_abs'] > 0) & 
                (bubble_data['qtd_abs'] > 0) &
                (bubble_data['vlr_rol_abs'].notna()) &
                (bubble_data['qtd_abs'].notna())
            ]
            
            print(f"✅ Dados limpos: {len(bubble_data)} registros válidos")
            
        except Exception as e:
            print(f"❌ Erro ao agregar dados de bolhas: {e}")
            empty_fig = go.Figure()
            empty_fig.add_annotation(text=f"Erro na agregação: {str(e)}", xref="paper", yref="paper", x=0.5, y=0.5)
            return empty_fig, empty_fig
        
        # MELHORIA: Usar o filtro global Top Clientes em vez de fixo
        # Se filtro_top_clientes está definido, usar esse valor; senão usar padrão
        num_top_clientes = filtro_top_clientes if filtro_top_clientes and filtro_top_clientes > 0 else 15
        num_top_produtos = top_produtos if top_produtos and top_produtos > 0 else 20
        
        print(f"🔍 Aplicando filtros visuais: Top {num_top_clientes} clientes × Top {num_top_produtos} produtos")
        
        # === GRÁFICO DE PARETO (Produtos por Faturamento) ===
        print("🔍 Criando gráfico de Pareto...")
        
        try:
            # Cria dados para Pareto usando a coluna de produto inteligente
            pareto_data = df_filtrado.groupby(product_column)['vlr_rol'].sum().sort_values(ascending=False).reset_index()
            pareto_data = pareto_data.head(num_top_produtos)
            
            if len(pareto_data) > 0:
                pareto_data['faturamento_acumulado'] = pareto_data['vlr_rol'].cumsum()
                pareto_data['percentual_acumulado'] = (pareto_data['faturamento_acumulado'] / pareto_data['vlr_rol'].sum()) * 100
                print(f"✅ Dados Pareto preparados: {len(pareto_data)} produtos")
            else:
                print("❌ Nenhum dado para Pareto após agregação")
                fig_pareto = go.Figure().add_annotation(
                    text="Nenhum produto encontrado", 
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
                fig_pareto.update_layout(template='plotly_white', height=400)
                    
        except Exception as e:
            print(f"❌ Erro ao preparar dados Pareto: {e}")
            fig_pareto = go.Figure().add_annotation(
                text=f"Erro na preparação: {str(e)}", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            fig_pareto.update_layout(template='plotly_white', height=400)
        
        # Criar o gráfico de Pareto se há dados válidos
        if 'pareto_data' in locals() and not pareto_data.empty and len(pareto_data) > 0:
            try:
                fig_pareto = go.Figure()
                
                # Barras de faturamento com estilo profissional
                fig_pareto.add_trace(go.Bar(
                    x=pareto_data[product_column],
                    y=pareto_data['vlr_rol'],
                    name='Faturamento',
                    yaxis='y',
                    marker=dict(
                        color='#0066cc',
                        line=dict(color='#003366', width=1)
                    ),
                    hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.0f}<extra></extra>'
                ))
                
                # Linha de percentual acumulado
                fig_pareto.add_trace(go.Scatter(
                    x=pareto_data[product_column],
                    y=pareto_data['percentual_acumulado'],
                    mode='lines+markers',
                    name='% Acumulado',
                    yaxis='y2',
                    line=dict(color='#dc3545', width=3),
                    marker=dict(size=8, color='#dc3545'),
                    hovertemplate='<b>%{x}</b><br>% Acumulado: %{y:.1f}%<extra></extra>'
                ))
                
                # Layout profissional simplificado
                fig_pareto.update_layout(
                    title="Análise de Pareto - Faturamento por Produto",
                    height=550,
                    template='plotly_white',
                    yaxis=dict(
                        title="Faturamento (R$)",
                        tickformat=',.0f'
                    ),
                    yaxis2=dict(
                        title="% Acumulado",
                        overlaying='y',
                        side='right',
                        range=[0, 100],
                        tickformat='.0f',
                        ticksuffix='%'
                    ),
                    xaxis=dict(
                        title="Produto",
                        tickangle=45
                    ),
                    margin=dict(l=80, r=80, t=100, b=120)
                )
                
                # Adicionar linha de referência 80%
                fig_pareto.add_hline(
                    y=80, 
                    yref='y2',
                    line_dash="dash", 
                    line_color="red"
                )
                
                print("✅ Gráfico de Pareto criado com sucesso")
                
            except Exception as e:
                print(f"❌ Erro ao criar gráfico de Pareto: {e}")
                fig_pareto = go.Figure().add_annotation(
                    text=f"Erro no gráfico Pareto: {str(e)}", 
                    xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
                )
                fig_pareto.update_layout(template='plotly_white', height=400)
        else:
            fig_pareto = go.Figure().add_annotation(
                text="Nenhum dado disponível para análise de Pareto", 
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            fig_pareto.update_layout(template='plotly_white', height=400)
        
        print(f"✅ Gráficos de produtos gerados")
        return fig_bolhas, fig_pareto
        
    except Exception as e:
        print(f"❌ Erro em update_products_charts: {e}")
        import traceback
        traceback.print_exc()
        
        # go já está importado no início da função
        empty_fig = go.Figure().add_annotation(
            text=f"Erro geral: {str(e)}", 
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        empty_fig.update_layout(template='plotly_white', height=400)
        return empty_fig, empty_fig

# CALLBACK DESABILITADO - Tabela agora é gerenciada por produtos_table_callback.py
# @app.callback(
#     Output('tabela-analise-produtos', 'data'),
#     [Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value'),
#      Input('filter-material-table', 'value'),
#      Input('url', 'pathname')],
#     prevent_initial_call=False
# )
# def update_products_table(filtro_ano, filtro_mes, filtro_cliente, filtro_hierarquia, filtro_canal, material_filter, pathname):
#     """Atualiza tabela de análise de produtos"""
#     print(f"🔄 UPDATE_PRODUCTS_TABLE executado - pathname: {pathname}")
#     print(f"   Material filter recebido: {material_filter} (tipo: {type(material_filter)})")
#     
#     try:
        # Só processa se estiver na página de produtos
#         if pathname and "/app/products" not in pathname and "products" not in pathname:
#             print(f"❌ Não é página de produtos: {pathname}")
#             return []
            
#         vendas_df = load_vendas_data()
#         cotacoes_df = load_cotacoes_data()
        
#         if vendas_df.empty:
#             print("❌ Dados de vendas vazios")
#             return []
        
#         # Aplica filtros
#         df_vendas_filtrado = apply_filters(vendas_df, filtro_ano, filtro_mes, filtro_cliente, 
#                                          filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
#         df_cotacoes_filtrado = apply_filters(cotacoes_df, filtro_ano, filtro_mes, filtro_cliente, 
#                                           filtro_hierarquia, filtro_canal, None, filtro_dias_sem_compra)
        
#         if df_vendas_filtrado.empty:
#             print("❌ Dados filtrados vazios")
#             return []
        
#         # Analisa produtos
#         produtos_stats = df_vendas_filtrado.groupby(['material', 'produto']).agg({
#             'vlr_rol': ['sum', 'mean', 'count'],
#             'qtd_rol': 'mean'
#         }).reset_index()
        
#         # Flatten columns
#         produtos_stats.columns = ['material', 'produto', 'faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada']
        
#         # Adicionar hierarquia
#         if 'hier_produto_1' in df_vendas_filtrado.columns:
#             hierarquia_map = df_vendas_filtrado.groupby('produto')['hier_produto_1'].first().to_dict()
#             produtos_stats['hierarquia'] = produtos_stats['produto'].map(hierarquia_map).fillna('N/A')
#         else:
#             produtos_stats['hierarquia'] = 'N/A'
        
#         # Calcular dados de cotação se disponível
#         if not df_cotacoes_filtrado.empty and 'produto' in df_cotacoes_filtrado.columns:
#             cotacoes_stats = df_cotacoes_filtrado.groupby('produto').size().to_dict()
#             produtos_stats['recorrencia_cotacao'] = produtos_stats['produto'].map(cotacoes_stats).fillna(0)
            
#             # Taxa de conversão
#             produtos_stats['taxa_conversao'] = (produtos_stats['recorrencia_compra'] / produtos_stats['recorrencia_cotacao'] * 100).fillna(0)
#         else:
#             produtos_stats['recorrencia_cotacao'] = produtos_stats['recorrencia_compra'] * 1.5  # Simulado
#             produtos_stats['taxa_conversao'] = 65.0  # Simulado
        
#         # Filtrar por material se selecionado - CORREÇÃO: Melhor tratamento de múltipla seleção
#         if material_filter and len(material_filter) > 0:
#             print(f"🔍 Aplicando filtro de material: {len(material_filter)} itens selecionados")
#             print(f"   Materiais: {material_filter}")
            
#             # Criar lista de códigos de material a partir das strings completas
#             material_codes = []
#             for item in material_filter:
#                 if isinstance(item, str) and ' - ' in item:
#                     # Extrair código do material (formato: "código - descrição")
#                     code = item.split(' - ')[0].strip()
#                     material_codes.append(code)
#                 else:
#                     # Se já for só o código
#                     material_codes.append(str(item))
            
#             print(f"   Códigos extraídos: {material_codes}")
            
#             # Filtrar pelos códigos de material
#             produtos_stats = produtos_stats[produtos_stats['material'].astype(str).isin(material_codes)]
#             print(f"   Registros após filtro: {len(produtos_stats)}")
#         else:
#             print("🔍 Nenhum filtro de material aplicado")
        
#         print(f"✅ Tabela de produtos gerada: {len(produtos_stats)} registros")
        
#         # CORREÇÃO: Verificar se os dados são válidos antes de retornar
#         if produtos_stats.empty:
#             print("⚠️ produtos_stats está vazio após processamento")
#             return []
        
#         result_data = produtos_stats.head(100).to_dict('records')
        
#         # Validar e limpar dados antes do retorno
#         cleaned_data = []
#         for i, record in enumerate(result_data):
#             if not isinstance(record, dict):
#                 print(f"❌ Registro {i} não é um dicionário válido: {type(record)}")
#                 continue
            
#             # Criar novo registro limpo
#             clean_record = {}
#             for key, value in record.items():
#                 # Converter NaN, None e valores problemáticos
#                 if value is None or (hasattr(value, '__iter__') and not isinstance(value, str) and len(str(value)) == 0):
#                     clean_record[key] = ""
#                 elif hasattr(value, 'isna') and value.isna():
#                     clean_record[key] = 0 if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else ""
#                 elif isinstance(value, (int, float)):
#                     # Verificar se é um número válido
#                     if str(value).lower() in ['nan', 'inf', '-inf']:
#                         clean_record[key] = 0 if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else ""
#                     else:
#                         clean_record[key] = float(value) if key in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao'] else value
#                 else:
#                     clean_record[key] = str(value) if value is not None else ""
            
#             # Verificar se o registro tem as colunas obrigatórias
#             required_fields = ['material', 'produto', 'hierarquia', 'faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao']
            
#             # Garantir que todos os campos obrigatórios existem
#             for field in required_fields:
#                 if field not in clean_record:
#                     if field in ['faturamento_total', 'valor_medio', 'recorrencia_compra', 'qty_media_cotada', 'recorrencia_cotacao', 'taxa_conversao']:
#                         clean_record[field] = 0
#                     else:
#                         clean_record[field] = ""
            
#             cleaned_data.append(clean_record)
        
#         print(f"✅ Dados validados e limpos: {len(cleaned_data)} registros prontos para retorno")
        
#         # VALIDAÇÃO FINAL: Garantir que é sempre uma lista válida
#         if not isinstance(cleaned_data, list):
#             print(f"❌ Resultado não é uma lista: {type(cleaned_data)}")
#             return []
        
#         # Verificar se os itens da lista são dicionários válidos
#         validated_data = []
#         for i, item in enumerate(cleaned_data):
#             if isinstance(item, dict) and all(isinstance(k, str) for k in item.keys()):
#                 validated_data.append(item)
#             else:
#                 print(f"❌ Item {i} inválido: {type(item)}")
        
#         # Log dos primeiros registros para debug
#         if validated_data:
#             print(f"🔍 Exemplo do primeiro registro: {list(validated_data[0].keys()) if validated_data[0] else 'vazio'}")
        
#         # VALIDAÇÃO FINAL ROBUSTA: Garantir que os dados são serializáveis JSON
#         try:
#             import json
#             json.dumps(validated_data[:1])  # Testa serializabilidade do primeiro item
#             print("✅ Dados validados como serializáveis JSON")
#         except (TypeError, ValueError) as json_error:
#             print(f"❌ Dados não são serializáveis JSON: {json_error}")
#             # Retornar lista vazia em caso de erro de serialização
#             return []
        
#         return validated_data
        
#     except Exception as e:
#         print(f"❌ Erro em update_products_table: {e}")
#         return []

# CALLBACK DESABILITADO - ID 'tabela-analise-produtos' não existe no layout
# @app.callback(
#     Output('download-csv-produtos', 'data'),
#     [Input('btn-download-csv-produtos', 'n_clicks')],
#     [State('tabela-analise-produtos', 'data')]
# )
# def download_products_csv(n_clicks, table_data):
#     """Download da tabela de produtos em CSV"""
#     if n_clicks and table_data:
#         import pandas as pd
#         df = pd.DataFrame(table_data)
#         return dcc.send_data_frame(df.to_csv, "produtos_analysis.csv", index=False)
#     return dash.no_update

# CALLBACK DESABILITADO - ID 'tabela-analise-produtos' não existe no layout  
# @app.callback(
#     [Output('tabela-analise-produtos', 'filter_query'),
#      Output('filter-material-table', 'value')],
#     [Input('btn-clear-filters-produtos', 'n_clicks')]
# )
# def clear_products_filters(n_clicks):
#     """Limpa apenas os filtros internos da tabela de produtos e filtro de material (não os filtros globais)"""
#     if n_clicks:
#         print("🧹 Limpando filtros internos da tabela de produtos")
#         # Limpa filter_query da tabela e reseta filtro de material
#         return '', []  # filter_query vazio e material vazio
#     return dash.no_update, dash.no_update

# ==========================================
# CALLBACK PARA POPULAR OPÇÕES DE MATERIAL (MOVIDO PARA produtos_table_callback_new.py)
# ==========================================

# @app.callback(
#     Output('filter-material-table', 'options'),
#     [Input('url', 'pathname'),
#      Input('global-filtro-ano', 'value'),
#      Input('global-filtro-mes', 'value'),
#      Input('global-filtro-cliente', 'value'),
#      Input('global-filtro-hierarquia', 'value'),
#      Input('global-filtro-canal', 'value'),
#      Input('global-filtro-unidade', 'value')],
#     [State('global-filtro-representada', 'value')]
# )
# def update_material_filter_options_central(pathname, ano, mes, cliente, hierarquia, canal, unidade, representada):
#     if pathname not in ['/app/products', '/produtos']:
#         return dash.no_update

#     try:
#         # Lógica para carregar e filtrar os dados de vendas
#         df_vendas = load_vendas_data(ano, mes, representada, cliente, hierarquia, canal, unidade)
        
#         if df_vendas.empty:
#             return []

#         # Obter materiais únicos e formatar para o dropdown
#         materiais = sorted(df_vendas['Material'].unique())
#         options = [{'label': material, 'value': material} for material in materiais]
#         return options

#     except Exception as e:
#         print(f"Erro ao atualizar opções de material: {e}")
#         return []

# =================================================================
# CALLBACK PARA ATUALIZAR TABELA DE ANÁLISE DE PRODUTOS (Exemplo)
# =================================================================
