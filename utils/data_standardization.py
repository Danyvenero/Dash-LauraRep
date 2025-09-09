#!/usr/bin/env python3
"""
Módulo de padronização de dados
Dashboard Laura Representações

Este módulo contém todas as funções de padronização que devem ser aplicadas
aos dados APÓS carregamento do banco e ANTES do uso nos callbacks.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# =======================================
# FUNÇÕES DE PADRONIZAÇÃO DE VENDAS
# =======================================

def ov_general_adjustments(df):
    """Ajustes gerais de padronização dos dados de vendas"""
    values_to_filter = ['CONTROLS', 'MOTORES INDUSTRIAIS',
       'DRIVES', 'MOTORES COMERCIAIS', 'SOLAR WAU',
       'DRIVES BT', 'CONTROLS CIVIL', 'SOLAR E SMART METER', 'GERADORES',
       'MOTORREDUTOR/REDUTOR', 'SEGURANÇA E SENSORES', 'SERVIÇOS', 'TRANSFORMADORES',
       'SOLAR', 'PAINEIS ESPECIAIS BT', 'NEGOCIOS DIGITAIS', 'CRITICAL POWER',
       'CHAVE DE PARTIDA ESPECIAL', 'MOTORES DE GRANDE PORTE', 
       'EDGE DEVICES E CONECTIVIDADE', 'ENGENHEIRADOS',
       'TOMADAS E INTERRUPTORES', 'REDUTORES INDUSTRIAIS',
       'SISTEMAS AUTOMAÇÃO E ELETRIFICAÇÃO', 'MOTORES APPLIANCE',
       'ESTAÇÕES DE RECARGA VEÍCULOS ELÉTRICOS',
       'ENGENHEIRADOS WDS', 'EQUIPAMENTOS DE ALTA TENSÃO',
       'SMART GRIDS & METERS', 'TURBINA', 'BARRAMENTO BLINDADO BWW', 'Soluções IoT', 
       'DRIVES MT']
    
    # Filtrar apenas produtos válidos
    if 'hier_produto_1' in df.columns:
        df = df[df['hier_produto_1'].isin(values_to_filter)].copy()
    
    # Conversões de tipo
    string_columns = ['unidade_negocio', 'canal_distribuicao', 'cod_cliente', 'cliente', 
                     'hier_produto_1', 'hier_produto_2', 'hier_produto_3', 'material', 
                     'produto', 'cidade_cliente', 'doc_vendas']
    
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype('string')
    
    # Conversão cliente para lowercase
    if 'cliente' in df.columns:
        df['cliente'] = df['cliente'].astype('string').str.lower()
    
    # Conversões numéricas
    numeric_columns = ['vlr_entrada', 'qtd_entrada', 'vlr_carteira', 'qtd_carteira', 'vlr_rol', 'qtd_rol']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Padronizar unidades de negócio
    if 'unidade_negocio' in df.columns:
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Automação', 'WAU')
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Digital e Sistemas', 'WDS')
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Energia', 'WEN')
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Motores Comercial e Appliance', 'WMO-C')
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Motores Industrial', 'WMO-I')
        df['unidade_negocio'] = df['unidade_negocio'].str.replace('WEG Transmissão e Distribuição', 'WTD')
        
        # Renomear coluna
        df.rename(columns={'unidade_negocio': 'unidade'}, inplace=True)
    
    # Conversão de data
    if 'data_faturamento' in df.columns:
        df['data_faturamento'] = pd.to_datetime(df['data_faturamento'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrar materiais configurados
    mat_configurados = ['10000008']
    if 'material' in df.columns:
        df = df[~df['material'].isin(mat_configurados)]
    
    return df


def ov_hierarquia_um(df):
    """Padronização da hierarquia de produto nível 1"""
    if 'hier_produto_1' not in df.columns:
        return df
        
    df = df.copy()
    
    # Aplicar todas as substituições
    replacements = {
        'Soluções IoT': 'DIGITAL SOLUTIONS',
        'SOLAR WAU': 'SOLAR',
        'SOLAR E SMART METER': 'SOLAR',
        'MOTORREDUTOR/REDUTOR': 'MOTORREDUTORES',
        'PAINEIS ESPECIAIS BT': 'CHAVES ESPECIAIS',
        'CHAVE DE PARTIDA ESPECIAL': 'CHAVES ESPECIAIS',
        'MOTORES DE GRANDE PORTE': 'WEN-M',
        'ENGENHEIRADOS WDS': 'ENGENHEIRADOS',
        'DRIVES BT': 'DRIVES',
        'SEGURANÇA E SENSORES': 'SAFETY',
        'SISTEMAS AUTOMAÇÃO E ELETRIFICAÇÃO': 'SISTEMAS',
        'ESTAÇÕES DE RECARGA VEÍCULOS ELÉTRICOS': 'WEMOB',
        'REDUTORES INDUSTRIAIS': 'REDUTORES',
        'NEGOCIOS DIGITAIS': 'DIGITAL SOLUTIONS',
        'MOTORES INDUSTRIAIS': 'WMO-I',
        'MOTORES COMERCIAIS': 'WMO-C',
        'BARRAMENTO BLINDADO BWW': 'BWW',
        'EQUIPAMENTOS DE ALTA TENSÃO': 'ALTA TENSÃO',
        'TOMADAS E INTERRUPTORES': 'BUILDING',
        'CONTROLS CIVIL': 'BULDING',
        'SMART GRIDS & METERS': 'SMART GRID',
        'MOTORES APPLIANCE': 'WMO-A'
    }
    
    for old_value, new_value in replacements.items():
        df.loc[:, 'hier_produto_1'] = df['hier_produto_1'].str.replace(old_value, new_value, regex=False)
    
    return df


def ov_hierarquia_dois(df):
    """Padronização da hierarquia de produto nível 2"""
    if 'hier_produto_2' not in df.columns:
        return df
        
    df = df.copy()
    
    # Aplicar todas as substituições
    replacements = {
        'ACIONAMENTO INVERSOR DE FREQ. PADRÃO': 'INVERSOR',
        'INVERSORES DE FREQUÊNCIA ENGENHEIRADOS': 'INVERSOR ENG',
        'INVERSORES DE FREQÜÊNCIA ENGENHEIRADOS': 'INVERSOR ENG',
        'INVERSORES DE FREQUÊNCIA SERIADOS': 'INVERSOR',
        'INVERSOR DE FREQUÊNCIA': 'INVERSOR',
        'INVERSOR SOLAR STRING': 'INVERSOR SOLAR',
        'BARRAMENTO BLINDADO BWW BT': 'BWW',
        'CAPACITORES CFP': 'CAP CFP',
        'CAPACITORES MOTOR-RUN': 'CAP MOTOR',
        'CAPACITORES PARA ELETRONICA DE POTENCIA': 'CAP EP',
        'CHAVE DE PARTIDA ESPECIAL': 'CHAVES ESPECIAIS',
        'CHAVE DE PARTIDA SERIADA': 'CHAVES SERIADAS',
        'CHAVE FIM DE CURSO': 'FIM DE CURSO',
        'CHAVES SECCIONADORAS': 'SECCIONADORA',
        'COMANDO E SINALIZAÇÃO': 'COMANDO E SIN',
        'DISPOSITIVO PROTETOR DE SURTO': 'SPW',
        'DISJUNTOR-MOTOR': 'MPW',
        'DISJUNTOR ABERTO': 'ABW',
        'DISJUNTOR DE MÉDIA TENSÃO': 'VBW',
        'DISJUNTORES EM CAIXA MOLDADA': 'DISJ. CAIXA MOLDADA',
        'DISJUNTORES SERIADOS': 'DISJUNTOR SERIADO',
        'ENGENHEIRADOS BT WDS': 'ENGENHEIRADOS BT',
        'ESTAÇÕES DE RECARGA VEÍCULOS ELÉTRICOS': 'WEMOB',
        'EDGE DEVICES': 'GATEWAYS',
        'GERADOR FOTOVOLTAICO': 'GER. SOLAR',
        'GERENCIAMENTO DE ENERGIA': 'WEM',
        "INTERRUPTOR DIFERENCIAL RESIDUAL(DR'S)": 'DR',
        'MEDIDORES DE ENERGIA INTELIGENTES': 'SMW',
        'MODULO FOTOVOLTAICO': 'MÓDULOS',
        'MOTORES COMERCIAIS': 'WCA1',
        'MOTORES DE ALTA TENSÃO': 'WEN-M',
        'MOTORES DE BAIXA TENSÃO': 'WEN-M',
        'MOTORREDUTOR GEREMIA': 'MOTORREDUTORES',
        'MOTORREDUTOR NLM': 'MOTORREDUTORES',
        'MOTORREDUTOR/REDUTOR': 'MOTORREDUTORES',
        'PAINEIS OEMs': 'CHAVES ESPECIAIS',
        'PAINEIS VAZIOS - PMW': 'PMW',
        'PAINEL TTW01 - CAIXAS': 'TTW',
        'PAINEL TTW01 - COLUNAS': 'TTW',
        'PARA GRUPOS GERADORES': 'ALTERNADORES',
        'PEDAL DE SEGURANÇA': 'PEDAL',
        'PLATAFORMA IOT WEGNOLOGY': 'WEGNOLOGY',
        'QUADRO DE DISTRIBUIÇÃO': 'QDW',
        'RELÉS DE SOBRECARGA TÉRMICOS': 'RELÉS TÉRMICOS',
        'RETIFICADORES CUSTOMIZADOS': 'RETIFICADOR',
        'RETIFICADORES SERIADOS': 'RETIFICADOR',
        'SENSORES E SISTEMAS DE VISÃO': 'SISTEMAS DE VISÃO',
        'SERVIÇO DE ASSISTÊNCIA TÉCNICA': 'ASTEC',
        'SERVIÇOS DE ENGENHARIA': 'ENGENHARIA',
        'SERVIÇOS DIVERSOS': 'DIVERSOS',
        'SERVIÇO DE REFORMA': 'REFORMA',
        'SERVIÇO DE TREINAMENTO': 'TREINAMENTO',
        'SERVIÇOS ESPECIALIZADOS WDI': 'WDI',
        'SISTEMAS BT WDS': 'SISTEMAS WDS',
        'SISTEMAS DE IDENTIFICAÇÃO WEG': 'IDENTIFICAÇÃO BTW',
        'SOFT-STARTERS SERIADAS': 'SOFT-STARTER',
        'SOFT-STARTERS BT': 'SOFT-STARTER',
        'SOFT-STARTERS ENGENHEIRADAS': 'SOFT-STARTER ENG',
        'SWITCHES INDUSTRIAIS': 'SWITCHES',
        'TRANSFORMADOR A ÓLEO PEDESTAL': 'PEDESTAL',
        'TRANSFORMADORES A ÓLEO DISTRIBUIÇÃO': 'DISTRIBUIÇÃO',
        'TRANSFORMADORES A ÓLEO FORÇA': 'FORÇA',
        'TRANSFORMADORES A ÓLEO MEDIA FORÇA I': 'MEIA FORÇA',
        'TRANSFORMADORES A ÓLEO MEDIA FORÇA II': 'MEIA FORÇA',
        'TRANSFORMADORES A ÓLEO MEIA FORÇA': 'MEIA FORÇA',
        'TRANSFORMADORES SECO': 'SECO',
        'WCG20 / WG20': 'WCG20',
        'WEG MOTION FLEET MANAGEMENT': 'WMFM',
        'WEG MOTOR SCAN': 'MOTOR SCAN',
        'WEG SCAN': 'WSCAN',
        'WEG SMART MACHINE': 'WSM',
        'WEGNOLOGY EDGE SUITE': 'WEGNOLOGY',
        'WEGSCAN': 'WSCAN',
        'WEGSCAN 1000': 'WSCAN 1000'
    }
    
    for old_value, new_value in replacements.items():
        df.loc[:, 'hier_produto_2'] = df['hier_produto_2'].str.replace(old_value, new_value, regex=False)
    
    # Tratamento especial baseado na unidade
    if 'unidade' in df.columns:
        df.loc[:, 'hier_produto_2'] = np.where(
            df['unidade'].str.contains('WEN', na=False), 
            df['hier_produto_2'].str.replace('MOTORES INDUSTRIAIS', 'WEN-M', regex=False),
            df['hier_produto_2'].str.replace('MOTORES INDUSTRIAIS', 'WMO-I', regex=False)
        )
    
    return df


def ov_hierarquia_tres(df):
    """Padronização da hierarquia de produto nível 3"""
    if 'hier_produto_3' not in df.columns:
        return df
        
    df = df.copy()
    
    # Tratamento especial para ACESSÓRIOS
    df['hier_produto_3'] = df['hier_produto_3'].apply(
        lambda x: 'ACESSÓRIOS' if isinstance(x, str) and 'ACESS' in x else x
    )
    
    # Aplicar todas as substituições
    replacements = {
        'CHAVE DE PARTIDA CX. TERMOPLÁSTICA': 'PDW',
        'W22 RURAL TEFC': 'W22 RURAL',
        'MPW25/40': 'MPW40',
        'MPW12/16/18': 'MPW18',
        'FUSÍVEL NH ULTRARRÁPIDO': 'aR',
        'CONTATORES AUXILIARES': 'CAW',
        'SERVIÇO DE REFORMA': 'REFORMA',
        'RS GERAL FHP ODP MONO (ANTIGO)': 'ODP (ANTIGO)',
        'SACA FUSÍVEL - FSW': 'FSW',
        'CONTATOR CAPACITOR CWMC': 'CWMC',
        'CONJUNTOS CEW': 'CEW',
        'FUSÍVEL NH RETARDADO': 'gG',
        'CONJUNTOS CSW': 'CSW',
        'HIDROGERADORES - GH20': 'GH20',
        'TURBOGERADORES ST41': 'ST41',
        'W22Xdb À PROVA DE EXPLOSÃO': 'W22X-db',
        'SINALEIROS CEW': 'SIN CEW',
        'TRANSFORMADORES A ÓLEO INDUSTRIAL': 'ÓLEO INDUSTRIAL',
        'WCG20 VERTIMAX / WG20 F': 'VERTIMAX',
        'HIDROGERADORES - SH11': 'SH11',
        'RS AVIÁRIO': 'AVIÁRIO',
        'TRANSFORMADORES SECO INDUSTRIAL': 'SECO',
        'HIDROGERADORES - GH11': 'GH11',
        'CHAVE DE PARTIDA CX. METÁLICA ESPECIAL': 'CHAVE ESPECIAL',
        'MOTORREDUTOR/REDUTOR': 'MOTORREDUTOR',
        'SL - INDUTIVOS': 'INDUTIVOS',
        'HIDROGERADORES S': 'GH-S',
        'MOTORES INDUSTRIAIS': 'WMO-I',
        'WMFM MANGMT MOTOR': 'WMFM',
        'BOTÕES CSW': 'BOT CSW',
        'PSS24 - PADRAO': 'PSS24',
        'RELÉS DE NÍVEL': 'RNW',
        'FUSÍVEL D RETARDADO': 'D',
        'CONTATOR CAPACITOR CWBC': 'CWBC',
        'W21Xdb À PROVA DE EXPLOSÃO': 'W21X-DB',
        'TURBOGERADORES S': 'TG-S',
        'RS GERAL FHP ODP MONO': 'ODP MONO',
        'W22 MOTOFREIO': 'MOTOFREIO',
        'FUSIVEL FLUSH END': 'FLUSH END',
        'ASSINATURA SAAS WEG SMART MACHINE': 'WSM-SIG',
        'MODULO FOTOVOLTAICO': 'MÓDULO',
        'SC - CAPACITIVOS': 'CAPACITIVOS',
        'W22Xec SEGURANÇA AUMENTADA (NÃO ACENDÍVE': 'W22X-ec',
        'CONTROLADOR AUTOMÁTICO': 'PFW',
        'ROTATIVA PORTA FUSIVEL - RFW': 'RFW',
        'TRANSFORMADOR A ÓLEO DE POTÊNCIA': 'ÓLEO POTENCIA',
        'W22Xtb DIP': 'DIP W22X-tb',
        'SERVIÇO DE ENGENHARIA': 'ENGENHARIA',
        'COMUTADORES CSW': 'COMT CSW',
        'TRANSFORMADOR A ÓLEO INDUSTRIAL': 'ÓLEO INDUSTRIAL',
        'W22 MOTOR PARA REDUTOR TIPO 1': 'TIPO 1',
        'WEG MOTOR SCAN COM SUBSCRIÇÃO': 'MOTOR SCAN',
        'MOTORES DE ALTA TENSÃO - H': 'WEN-H',
        'IHM MT': 'IHM',
        'WCG20 COAXIAL / WG20 C': 'COAXIAL',
        'BOTÕES CEW': 'BOT CEW',
        'TRANSFORMADORES A ÓLEO DE POTÊNCIA': 'ÓLEO POTENCIA',
        'BOTÕES CSW-M': 'BOT CSW-M',
        'WCG20 CONIMAX / WG20 K': 'CONIMAX',
        'RS GERAL FHP ODP TRIF (ANTIGO)': 'ODP 3F ANTIGO',
        'RS GERAL FHP TEFC MONO (ANTIGO)': 'MONO ANTIGO',
        'MOTORES DE ALTA TENSÃO - M': 'WEN-M',
        'TRANSFORMADORES A ÓLEO DE DISTRIBUIÇÃO': 'DISTRIBUIÇÃO',
        'TRANSFORMADORES SECO PARA RETIFICADOR': 'SECO RETF',
        'GERADORES PARA GRUPOS GERADORES': 'ALTERNADOR',
        'W22Xec WELL SEGURANÇA AUMENTADA': 'WELL EX-ec',
        'JET PUMP BOMBA/FILTRO': 'JET PUMP',
        'W01 FHP ODP TRIF': 'W01 TRIF',
        'TRANSFORMADORES A ÓLEO TIPO AUTOTRAFO': 'AUTOTRAFO',
        'COMUTADORES CEW': 'COMT CEW',
        'RECTIFIER': 'RETIFICADOR',
        'AFW11 CUSTOMIZADO': 'AFW11',
        'COMUTADORES CSW-M': 'COMT CSW-M',
        'GATEWAY MOTOR SCAN': 'GATEWAY',
        'TRANSFORMADORES SECO': 'SECO',
        'BOMBA COMBUSTÍVEL FERRO': 'BB COMBUSTIVEL FF',
        'MINI FECHADO': 'MINI FECHADO',
        'W22 BOMBA MONOBLOCO JM/JP': 'JM/JP',
        'WEM CLOUD SAAS': 'WEM',
        'WSDAL - DUPLA ABERTURA LATERAL': 'WSDAL',
        'IDENTIFICADOR DE BORNES': 'ID BORNES',
        'RS GERAL FHP TEFC MONO': 'MONO FECHADO',
        'AC RESIDENCIAL JANELA': 'AC JANELA',
        'PSS24W - METALICA': 'PSS24W METAL',
        'SWITCHES ETHERNET SWU': 'SWITCH SWU',
        'AFW11M G2 CUSTOMIZADO': 'AFW11M G2',
        'Sistema Integrado de Distribuição (SID)': 'SID',
        'TURBINA FRANCIS SIMPLES EIXO HORIZONTAL': 'TURBINA FRANCIS',
        'SINALEIROS CSW': 'SIN CSW',
        'TRANSFORMADORES A ÓLEO PARA FORNO': 'ÓLEO FORNO',
        'QUADROS DE COMANDO - PNW': 'PNW',
        'WEG DRIVE SCAN SEM ASSINATURA': 'DRIVE SCAN NO SIGN',
        'W21 MOTOFREIO AL': 'W21 AL COM FREIO',
        'BOMBA COMBUSTÍVEL CHAPA': 'BB COMBUSTIVEL CHAPA',
        'ON PREMISE LICENCA': 'LICENÇA WEN',
        'RELÉS DE MULTI-FUNÇÕES': 'ERWM',
        'RS WJET PUMP ODP (ANTIGO)': 'JET PUMP ANTIGO',
        'RTDW CUSTOMIZADO (NÃO UTILIZAR)': 'RTDW*',
        'BANCO DE BATERIAS RETIFICADORES': 'BATERIAS RETIF',
        'RS GERAL FHP ODP TRIF': 'ODP TRIF',
        'SERVIÇOS DIVERSOS': 'DIVERSOS',
        'SM - MAGNÉTICOS': 'MAGNÉTICOS',
        'MOTORES DE ALTA TENSÃO - M MINING': 'WEN-MINING',
        'QUADROS DE COMANDO - PNW WDS': 'PNW',
        'RP- IRRIGATION (60 AND 61)': 'REDUTOR RODA PIVÔ',
        'WEGNOLOGY DEVELOPER PAAS': 'WEGNOLOGY',
        'WEGNOLOGY GENERIC': 'WEGNOLOGY',
        'SMW CONCESSIONÁRIA': 'SMW',
        'HMI ENG&RUNTIME WES': 'WES',
        'HIDROGERADORES - SH1': 'SH1',
        'AFW11 PADRÃO': 'AFW11',
        'W22 MOTOFREIO PARA REDUTOR TIPO 1': 'W22 TIPO 1 COM FREIO',
        'COMUTADORAS ROTATIVA': 'MSW',
        'AFW11C PADRÃO': 'AFW11C',
        'TRANSFORMADOR A ÓLEO PEDESTAL': 'PEDESTAL',
        'MOTORES COMERCIAIS': 'WMO-C',
        'RTDW CUSTOMIZADO': 'RTDW',
        'BOMBA COMBUSTÍVEL CH': 'BB COMBUSTIVEL CH',
        'TRANSFORMADORES A ÓLEO MEIA FORÇA': 'ÓLEO MEIA FORÇA',
        'SD - ÓPTICOS DIFUSOS': 'OPT DIFUSO',
        'W22 RURAL FARM DUTY': 'W22 RURAL',
        'AC RESIDENCIAL SPLIT': 'AC SPLIT'
    }
    
    for old_value, new_value in replacements.items():
        df.loc[:, 'hier_produto_3'] = df['hier_produto_3'].str.replace(old_value, new_value, regex=False)
    
    return df


# =======================================
# FUNÇÕES DE PADRONIZAÇÃO DE COTAÇÕES
# =======================================

def centro_fornecedor_mapping(df):
    """Padronização de centro fornecedor para cotações"""
    if 'centro_fornecedor' not in df.columns:
        return df
    
    df = df.copy()
    
    # Mapeamento de centro fornecedor
    def map_centro_fornecedor(valor):
        mapping = {
            1100.0: 'WMO-I',
            1106.0: 'WMO-C',
            1108.0: 'WCES',
            1109.0: 'WCES',
            1200.0: 'WEN',
            1201.0: 'WEN',
            1202.0: 'WTD',
            1203.0: 'WTD',
            1304.0: 'WDS',
            1305.0: 'WDC',
            1306.0: 'WDC',
            1312.0: 'WDC',
            1320.0: 'WDC',
            1321.0: 'WDC',
            1323.0: 'WDS',
            1340.0: 'SOLAR',
            1341.0: 'SOLAR',
            1505.0: 'WTD'
        }
        return mapping.get(valor, 'OUTRO')
    
    df['unidade_negocio'] = df['centro_fornecedor'].apply(map_centro_fornecedor)
    
    return df


# =======================================
# FUNÇÃO PRINCIPAL DE PADRONIZAÇÃO
# =======================================

def apply_vendas_standardization(df):
    """Aplica todas as padronizações para dados de vendas"""
    if df.empty:
        return df
    
    logger.info("🔧 Aplicando padronizações de vendas...")
    
    try:
        # Aplicar padronizações em sequência
        df = ov_general_adjustments(df)
        df = ov_hierarquia_um(df)
        df = ov_hierarquia_dois(df)
        df = ov_hierarquia_tres(df)
        
        logger.info(f"✅ Padronizações aplicadas. Shape final: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"❌ Erro na padronização de vendas: {e}")
        return df


def apply_cotacoes_standardization(df):
    """Aplica todas as padronizações para dados de cotações"""
    if df.empty:
        return df
    
    logger.info("🔧 Aplicando padronizações de cotações...")
    
    try:
        # Aplicar padronização de centro fornecedor
        df = centro_fornecedor_mapping(df)
        
        logger.info(f"✅ Padronizações aplicadas. Shape final: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"❌ Erro na padronização de cotações: {e}")
        return df
