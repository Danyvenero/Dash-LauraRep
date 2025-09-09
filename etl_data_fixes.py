#!/usr/bin/env python3
"""
ETL para correção e ajuste de dados nas tabelas vendas e cotações
Dashboard Laura Representações
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from utils.db import get_db_connection
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =======================================
# FUNÇÕES DE PADRONIZAÇÃO DE DADOS
# =======================================

def ov_general_adjustments(df):
    """Ajustes gerais de padronização dos dados"""
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
    
    # Filtrar apenas produtos relevantes
    if 'Hier. Produto 1' in df.columns:
        df = df[df['Hier. Produto 1'].isin(values_to_filter)].copy()
    
    # Converter tipos de dados
    if 'Unidade de Negócio' in df.columns:
        df['Unidade de Negócio'] = df['Unidade de Negócio'].astype('string')
    if 'Canal Distribuição' in df.columns:
        df['Canal Distribuição'] = df['Canal Distribuição'].astype('string')
    if 'ID_Cli' in df.columns:
        df['ID_Cli'] = df['ID_Cli'].astype('string')
    if 'Cliente' in df.columns:
        df['Cliente'] = df['Cliente'].astype('string').str.lower()
    if 'Hier. Produto 1' in df.columns:
        df['Hier. Produto 1'] = df['Hier. Produto 1'].astype('string')
    if 'Hier. Produto 2' in df.columns:
        df['Hier. Produto 2'] = df['Hier. Produto 2'].astype('string')
    if 'Hier. Produto 3' in df.columns:
        df['Hier. Produto 3'] = df['Hier. Produto 3'].astype('string')
    if 'Material' in df.columns:
        df['Material'] = df['Material'].astype('string')
    if 'Produto' in df.columns:
        df['Produto'] = df['Produto'].astype('string')
    if 'Cidade do Cliente' in df.columns:
        df['Cidade do Cliente'] = df['Cidade do Cliente'].astype('string')
    if 'Doc. Vendas' in df.columns:
        df['Doc. Vendas'] = df['Doc. Vendas'].astype('string')
    
    # Converter valores numéricos
    numeric_columns = ['Vlr. Entrada', 'Qtd. Entrada', 'Vlr. Carteira', 'Qtd. Carteira', 'Vlr. ROL', 'Qtd. ROL']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Padronizar nomes de unidades de negócio
    if 'Unidade de Negócio' in df.columns:
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Automação', 'WAU')
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Digital e Sistemas', 'WDS')
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Energia', 'WEN')
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Motores Comercial e Appliance', 'WMO-C')
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Motores Industrial', 'WMO-I')
        df['Unidade de Negócio'] = df['Unidade de Negócio'].str.replace('WEG Transmissão e Distribuição', 'WTD')
        df.rename(columns={'Unidade de Negócio': 'Unidade'}, inplace=True)
    
    # Converter datas
    if 'Data Faturamento' in df.columns:
        df['Data Faturamento'] = pd.to_datetime(df['Data Faturamento'], format='%d/%m/%Y', errors='coerce')
    
    # Remover materiais configurados
    mat_configurados = ['10000008']
    if 'Material' in df.columns:
        df = df[~df['Material'].isin(mat_configurados)]
    
    return df


def ov_hierarquia_um(df):
    """Padronização da hierarquia de produto nível 1"""
    if 'Hier. Produto 1' not in df.columns:
        return df
        
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('Soluções IoT', 'DIGITAL SOLUTIONS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('SOLAR WAU', 'SOLAR', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('SOLAR E SMART METER', 'SOLAR', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('MOTORREDUTOR/REDUTOR', 'MOTORREDUTORES', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('PAINEIS ESPECIAIS BT', 'CHAVES ESPECIAIS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('CHAVE DE PARTIDA ESPECIAL', 'CHAVES ESPECIAIS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('MOTORES DE GRANDE PORTE', 'WEN-M', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('ENGENHEIRADOS WDS', 'ENGENHEIRADOS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('DRIVES BT', 'DRIVES', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('SEGURANÇA E SENSORES', 'SAFETY', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('SISTEMAS AUTOMAÇÃO E ELETRIFICAÇÃO', 'SISTEMAS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('ESTAÇÕES DE RECARGA VEÍCULOS ELÉTRICOS', 'WEMOB', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('REDUTORES INDUSTRIAIS', 'REDUTORES', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('NEGOCIOS DIGITAIS', 'DIGITAL SOLUTIONS', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('MOTORES INDUSTRIAIS', 'WMO-I', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('MOTORES COMERCIAIS', 'WMO-C', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('BARRAMENTO BLINDADO BWW', 'BWW', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('EQUIPAMENTOS DE ALTA TENSÃO', 'ALTA TENSÃO', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('TOMADAS E INTERRUPTORES', 'BUILDING', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('CONTROLS CIVIL', 'BULDING', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('SMART GRIDS & METERS', 'SMART GRID', regex=False)
    df.loc[:, 'Hier. Produto 1'] = df['Hier. Produto 1'].str.replace('MOTORES APPLIANCE', 'WMO-A', regex=False)
    return df


def ov_hierarquia_dois(df):
    """Padronização da hierarquia de produto nível 2"""
    if 'Hier. Produto 2' not in df.columns:
        return df
        
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('ACIONAMENTO INVERSOR DE FREQ. PADRÃO', 'INVERSOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSORES DE FREQUÊNCIA ENGENHEIRADOS', 'INVERSOR ENG', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSORES DE FREQÜÊNCIA ENGENHEIRADOS', 'INVERSOR ENG', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSORES DE FREQUÊNCIA SERIADOS', 'INVERSOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSOR DE FREQUÊNCIA', 'INVERSOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSOR SOLAR STRING', 'INVERSOR SOLAR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('INVERSORES DE FREQUÊNCIA SERIADOS', 'INVERSOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('BARRAMENTO BLINDADO BWW BT', 'BWW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CAPACITORES CFP', 'CAP CFP', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CAPACITORES MOTOR-RUN', 'CAP MOTOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CAPACITORES PARA ELETRONICA DE POTENCIA', 'CAP EP', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CHAVE DE PARTIDA ESPECIAL', 'CHAVES ESPECIAIS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CHAVE DE PARTIDA SERIADA', 'CHAVES SERIADAS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CHAVE FIM DE CURSO', 'FIM DE CURSO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('CHAVES SECCIONADORAS', 'SECCIONADORA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('COMANDO E SINALIZAÇÃO', 'COMANDO E SIN', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISPOSITIVO PROTETOR DE SURTO', 'SPW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISJUNTOR-MOTOR', 'MPW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISJUNTOR ABERTO', 'ABW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISJUNTOR DE MÉDIA TENSÃO', 'VBW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISJUNTORES EM CAIXA MOLDADA', 'DISJ. CAIXA MOLDADA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('DISJUNTORES SERIADOS', 'DISJUNTOR SERIADO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('ENGENHEIRADOS BT WDS', 'ENGENHEIRADOS BT', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('ESTAÇÕES DE RECARGA VEÍCULOS ELÉTRICOS', 'WEMOB', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('EDGE DEVICES', 'GATEWAYS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('GERADOR FOTOVOLTAICO', 'GER. SOLAR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('GERENCIAMENTO DE ENERGIA', 'WEM', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace("INTERRUPTOR DIFERENCIAL RESIDUAL(DR'S)", 'DR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MEDIDORES DE ENERGIA INTELIGENTES', 'SMW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MODULO FOTOVOLTAICO', 'MÓDULOS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORES COMERCIAIS', 'WCA1', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORES DE ALTA TENSÃO', 'WEN-M', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORES DE BAIXA TENSÃO', 'WEN-M', regex=False)
    
    # Tratamento especial para MOTORES INDUSTRIAIS baseado na Unidade
    if 'Unidade' in df.columns:
        df.loc[:, 'Hier. Produto 2'] = np.where(df['Unidade'].str.contains('WEN', na=False), 
                                         df['Hier. Produto 2'].str.replace('MOTORES INDUSTRIAIS', 'WEN-M', regex=False),
                                         df['Hier. Produto 2'].str.replace('MOTORES INDUSTRIAIS', 'WMO-I', regex=False)
        )
    else:
        df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORES INDUSTRIAIS', 'WMO-I', regex=False)
    
    # Continuação das substituições...
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORREDUTOR GEREMIA', 'MOTORREDUTORES', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORREDUTOR NLM', 'MOTORREDUTORES', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('MOTORREDUTOR/REDUTOR', 'MOTORREDUTORES', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PAINEIS OEMs', 'CHAVES ESPECIAIS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PAINEIS VAZIOS - PMW', 'PMW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PAINEL TTW01 - CAIXAS', 'TTW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PAINEL TTW01 - COLUNAS', 'TTW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PARA GRUPOS GERADORES', 'ALTERNADORES', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PEDAL DE SEGURANÇA', 'PEDAL', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('PLATAFORMA IOT WEGNOLOGY', 'WEGNOLOGY', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('QUADRO DE DISTRIBUIÇÃO', 'QDW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('RELÉS DE SOBRECARGA TÉRMICOS', 'RELÉS TÉRMICOS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('RETIFICADORES CUSTOMIZADOS', 'RETIFICADOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('RETIFICADORES SERIADOS', 'RETIFICADOR', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SENSORES E SISTEMAS DE VISÃO', 'SISTEMAS DE VISÃO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇO DE ASSISTÊNCIA TÉCNICA', 'ASTEC', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇOS DE ENGENHARIA', 'ENGENHARIA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇOS DIVERSOS', 'DIVERSOS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇO DE REFORMA', 'REFORMA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇO DE TREINAMENTO', 'TREINAMENTO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SERVIÇOS ESPECIALIZADOS WDI', 'WDI', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SISTEMAS BT WDS', 'SISTEMAS WDS', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SISTEMAS DE IDENTIFICAÇÃO WEG', 'IDENTIFICAÇÃO BTW', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SOFT-STARTERS SERIADAS', 'SOFT-STARTER', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SOFT-STARTERS BT', 'SOFT-STARTER', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SOFT-STARTERS ENGENHEIRADAS', 'SOFT-STARTER ENG', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('SWITCHES INDUSTRIAIS', 'SWITCHES', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADOR A ÓLEO PEDESTAL', 'PEDESTAL', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES A ÓLEO DISTRIBUIÇÃO', 'DISTRIBUIÇÃO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES A ÓLEO FORÇA', 'FORÇA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES A ÓLEO MEDIA FORÇA I', 'MEIA FORÇA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES A ÓLEO MEDIA FORÇA II', 'MEIA FORÇA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES A ÓLEO MEIA FORÇA', 'MEIA FORÇA', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('TRANSFORMADORES SECO', 'SECO', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WCG20 / WG20', 'WCG20', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEG MOTION FLEET MANAGEMENT', 'WMFM', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEG MOTOR SCAN', 'MOTOR SCAN', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEG SCAN', 'WSCAN', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEG SMART MACHINE', 'WSM', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEGNOLOGY EDGE SUITE', 'WEGNOLOGY', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEGSCAN', 'WSCAN', regex=False)
    df.loc[:, 'Hier. Produto 2'] = df['Hier. Produto 2'].str.replace('WEGSCAN 1000', 'WSCAN 1000', regex=False)
    return df

def ov_hierarquia_tres(df):
    """Padronização da hierarquia de produto nível 3"""
    if 'Hier. Produto 3' not in df.columns:
        return df
        
    df['Hier. Produto 3'] = df['Hier. Produto 3'].apply(lambda x: 'ACESSÓRIOS' if isinstance(x, str) and 'ACESS' in x else x)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CHAVE DE PARTIDA CX. TERMOPLÁSTICA', 'PDW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 RURAL TEFC', 'W22 RURAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MPW25/40', 'MPW40', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MPW12/16/18', 'MPW18', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('FUSÍVEL NH ULTRARRÁPIDO', 'aR', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONTATORES AUXILIARES', 'CAW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SERVIÇO DE REFORMA', 'REFORMA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP ODP MONO (ANTIGO)', 'ODP (ANTIGO)', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SACA FUSÍVEL - FSW', 'FSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONTATOR CAPACITOR CWMC', 'CWMC', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONJUNTOS CEW', 'CEW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('FUSÍVEL NH RETARDADO', 'gG', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONJUNTOS CSW', 'CSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HIDROGERADORES - GH20', 'GH20', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TURBOGERADORES ST41', 'ST41', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22Xdb À PROVA DE EXPLOSÃO', 'W22X-db', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SINALEIROS CEW', 'SIN CEW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO INDUSTRIAL', 'ÓLEO INDUSTRIAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WCG20 VERTIMAX / WG20 F', 'VERTIMAX', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HIDROGERADORES - SH11', 'SH11', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS AVIÁRIO', 'AVIÁRIO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES SECO INDUSTRIAL', 'SECO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HIDROGERADORES - GH11', 'GH11', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CHAVE DE PARTIDA CX. METÁLICA ESPECIAL', 'CHAVE ESPECIAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORREDUTOR/REDUTOR', 'MOTORREDUTOR', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SL - INDUTIVOS', 'INDUTIVOS', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HIDROGERADORES S', 'GH-S', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORES INDUSTRIAIS', 'WMO-I', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WMFM MANGMT MOTOR', 'WMFM', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOTÕES CSW', 'BOT CSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('PSS24 - PADRAO', 'PSS24', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RELÉS DE NÍVEL', 'RNW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('FUSÍVEL D RETARDADO', 'D', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONTATOR CAPACITOR CWBC', 'CWBC', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W21Xdb À PROVA DE EXPLOSÃO', 'W21X-DB', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TURBOGERADORES S', 'TG-S', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP ODP MONO', 'ODP MONO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 MOTOFREIO', 'MOTOFREIO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('FUSIVEL FLUSH END', 'FLUSH END', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('ASSINATURA SAAS WEG SMART MACHINE', 'WSM-SIG', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MODULO FOTOVOLTAICO', 'MÓDULO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SC - CAPACITIVOS', 'CAPACITIVOS', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22Xec SEGURANÇA AUMENTADA (NÃO ACENDÍVE', 'W22X-ec', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('CONTROLADOR AUTOMÁTICO', 'PFW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('ROTATIVA PORTA FUSIVEL - RFW', 'RFW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADOR A ÓLEO DE POTÊNCIA', 'ÓLEO POTENCIA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22Xtb DIP', 'DIP W22X-tb', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SERVIÇO DE ENGENHARIA', 'ENGENHARIA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('COMUTADORES CSW', 'COMT CSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADOR A ÓLEO INDUSTRIAL', 'ÓLEO INDUSTRIAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 MOTOR PARA REDUTOR TIPO 1', 'TIPO 1', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WEG MOTOR SCAN COM SUBSCRIÇÃO', 'MOTOR SCAN', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORES DE ALTA TENSÃO - H', 'WEN-H', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('IHM MT', 'IHM', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WCG20 COAXIAL / WG20 C', 'COAXIAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOTÕES CEW', 'BOT CEW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO DE POTÊNCIA', 'ÓLEO POTENCIA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOTÕES CSW-M', 'BOT CSW-M', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WCG20 CONIMAX / WG20 K', 'CONIMAX', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP ODP TRIF (ANTIGO)', 'ODP 3F ANTIGO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP TEFC MONO (ANTIGO)', 'MONO ANTIGO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORES DE ALTA TENSÃO - M', 'WEN-M', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO DE DISTRIBUIÇÃO', 'DISTRIBUIÇÃO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES SECO PARA RETIFICADOR', 'SECO RETF', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('GERADORES PARA GRUPOS GERADORES', 'ALTERNADOR', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22Xec WELL SEGURANÇA AUMENTADA', 'WELL EX-ec', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('JET PUMP BOMBA/FILTRO', 'JET PUMP', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W01 FHP ODP TRIF', 'W01 TRIF', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO TIPO AUTOTRAFO', 'AUTOTRAFO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('COMUTADORES CEW', 'COMT CEW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RECTIFIER', 'RETIFICADOR', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AFW11 CUSTOMIZADO', 'AFW11', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('COMUTADORES CSW-M', 'COMT CSW-M', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('GATEWAY MOTOR SCAN', 'GATEWAY', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES SECO', 'SECO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOMBA COMBUSTÍVEL FERRO', 'BB COMBUSTIVEL FF', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MINI FECHADO', 'MINI FECHADO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 BOMBA MONOBLOCO JM/JP', 'JM/JP', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WEM CLOUD SAAS', 'WEM', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WSDAL - DUPLA ABERTURA LATERAL', 'WSDAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('IDENTIFICADOR DE BORNES', 'ID BORNES', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP TEFC MONO', 'MONO FECHADO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AC RESIDENCIAL JANELA', 'AC JANELA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('PSS24W - METALICA', 'PSS24W METAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SWITCHES ETHERNET SWU', 'SWITCH SWU', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AFW11M G2 CUSTOMIZADO', 'AFW11M G2', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('Sistema Integrado de Distribuição (SID)', 'SID', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TURBINA FRANCIS SIMPLES EIXO HORIZONTAL', 'TURBINA FRANCIS', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SINALEIROS CSW', 'SIN CSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO PARA FORNO', 'ÓLEO FORNO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('QUADROS DE COMANDO - PNW', 'PNW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WEG DRIVE SCAN SEM ASSINATURA', 'DRIVE SCAN NO SIGN', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W21 MOTOFREIO AL', 'W21 AL COM FREIO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOMBA COMBUSTÍVEL CHAPA', 'BB COMBUSTIVEL CHAPA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('ON PREMISE LICENCA', 'LICENÇA WEN', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RELÉS DE MULTI-FUNÇÕES', 'ERWM', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS WJET PUMP ODP (ANTIGO)', 'JET PUMP ANTIGO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RTDW CUSTOMIZADO (NÃO UTILIZAR)', 'RTDW*', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BANCO DE BATERIAS RETIFICADORES', 'BATERIAS RETIF', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RS GERAL FHP ODP TRIF', 'ODP TRIF', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SERVIÇOS DIVERSOS', 'DIVERSOS', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SM - MAGNÉTICOS', 'MAGNÉTICOS', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORES DE ALTA TENSÃO - M MINING', 'WEN-MINING', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('QUADROS DE COMANDO - PNW WDS', 'PNW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RP- IRRIGATION (60 AND 61)', 'REDUTOR RODA PIVÔ', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WEGNOLOGY DEVELOPER PAAS', 'WEGNOLOGY', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('WEGNOLOGY GENERIC', 'WEGNOLOGY', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SMW CONCESSIONÁRIA', 'SMW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HMI ENG&RUNTIME WES', 'WES', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('HIDROGERADORES - SH1', 'SH1', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AFW11 PADRÃO', 'AFW11', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 MOTOFREIO PARA REDUTOR TIPO 1', 'W22 TIPO 1 COM FREIO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('COMUTADORAS ROTATIVA', 'MSW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AFW11C PADRÃO', 'AFW11C', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADOR A ÓLEO PEDESTAL', 'PEDESTAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('MOTORES COMERCIAIS', 'WMO-C', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('RTDW CUSTOMIZADO', 'RTDW', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('BOMBA COMBUSTÍVEL CH', 'BB COMBUSTIVEL CH', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('TRANSFORMADORES A ÓLEO MEIA FORÇA', 'ÓLEO MEIA FORÇA', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('SD - ÓPTICOS DIFUSOS', 'OPT DIFUSO', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('W22 RURAL FARM DUTY', 'W22 RURAL', regex=False)
    df.loc[:, 'Hier. Produto 3'] = df['Hier. Produto 3'].str.replace('AC RESIDENCIAL SPLIT', 'AC SPLIT', regex=False)
    return df

class DataETL:
    def __init__(self):
        self.conn = None
        
    def connect_db(self):
        """Conecta ao banco de dados"""
        try:
            self.conn = get_db_connection()
            logger.info("✅ Conexão com banco de dados estabelecida")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            return False
    
    def close_db(self):
        """Fecha conexão com banco"""
        if self.conn:
            self.conn.close()
            logger.info("🔒 Conexão com banco fechada")
    
    def analyze_current_data(self):
        """Analisa os dados atuais das tabelas"""
        logger.info("🔍 Analisando dados atuais...")
        
        try:
            # Análise da tabela vendas
            vendas_df = pd.read_sql_query("SELECT * FROM vendas LIMIT 10", self.conn)
            logger.info(f"📊 Tabela VENDAS - Amostra de {len(vendas_df)} registros:")
            logger.info(f"   Colunas: {list(vendas_df.columns)}")
            
            if not vendas_df.empty:
                logger.info(f"   Amostra de dados:")
                for idx, row in vendas_df.head(3).iterrows():
                    logger.info(f"     Row {idx}: {dict(row)}")
            
            # Contagem total vendas
            total_vendas = pd.read_sql_query("SELECT COUNT(*) as total FROM vendas", self.conn).iloc[0]['total']
            logger.info(f"   Total de registros: {total_vendas}")
            
            # Análise da tabela cotações
            cotacoes_df = pd.read_sql_query("SELECT * FROM cotacoes LIMIT 10", self.conn)
            logger.info(f"📊 Tabela COTAÇÕES - Amostra de {len(cotacoes_df)} registros:")
            logger.info(f"   Colunas: {list(cotacoes_df.columns)}")
            
            if not cotacoes_df.empty:
                logger.info(f"   Amostra de dados:")
                for idx, row in cotacoes_df.head(3).iterrows():
                    logger.info(f"     Row {idx}: {dict(row)}")
            
            # Contagem total cotações
            total_cotacoes = pd.read_sql_query("SELECT COUNT(*) as total FROM cotacoes", self.conn).iloc[0]['total']
            logger.info(f"   Total de registros: {total_cotacoes}")
            
            return vendas_df, cotacoes_df
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar dados: {e}")
            return None, None
    
    def check_data_types_and_formats(self):
        """Verifica tipos de dados e formatos problemáticos"""
        logger.info("🔍 Verificando tipos de dados e formatos...")
        
        try:
            # Verificar datas na tabela vendas
            date_analysis = pd.read_sql_query("""
                SELECT 
                    MIN(data) as min_data,
                    MAX(data) as max_data,
                    COUNT(DISTINCT data) as total_datas_unicas,
                    COUNT(*) as total_registros
                FROM vendas
            """, self.conn)
            
            logger.info("📅 Análise de datas - VENDAS:")
            logger.info(f"   Data mínima: {date_analysis.iloc[0]['min_data']}")
            logger.info(f"   Data máxima: {date_analysis.iloc[0]['max_data']}")
            logger.info(f"   Datas únicas: {date_analysis.iloc[0]['total_datas_unicas']}")
            logger.info(f"   Total registros: {date_analysis.iloc[0]['total_registros']}")
            
            # Verificar valores numéricos problemáticos
            numeric_issues = pd.read_sql_query("""
                SELECT 
                    COUNT(CASE WHEN valor_venda IS NULL THEN 1 END) as valores_nulos,
                    COUNT(CASE WHEN valor_venda = 0 THEN 1 END) as valores_zero,
                    COUNT(CASE WHEN valor_venda < 0 THEN 1 END) as valores_negativos,
                    AVG(valor_venda) as valor_medio,
                    MIN(valor_venda) as valor_min,
                    MAX(valor_venda) as valor_max
                FROM vendas
            """, self.conn)
            
            logger.info("💰 Análise de valores - VENDAS:")
            for col in numeric_issues.columns:
                logger.info(f"   {col}: {numeric_issues.iloc[0][col]}")
            
            # Verificar problemas em cotações
            cotacoes_analysis = pd.read_sql_query("""
                SELECT 
                    COUNT(CASE WHEN data IS NULL THEN 1 END) as datas_nulas,
                    COUNT(CASE WHEN cliente IS NULL OR cliente = '' THEN 1 END) as clientes_vazios,
                    COUNT(CASE WHEN numero_cotacao IS NULL OR numero_cotacao = '' THEN 1 END) as cotacoes_sem_numero,
                    COUNT(DISTINCT cliente) as clientes_unicos,
                    COUNT(DISTINCT numero_cotacao) as cotacoes_unicas
                FROM cotacoes
            """, self.conn)
            
            logger.info("📋 Análise de dados - COTAÇÕES:")
            for col in cotacoes_analysis.columns:
                logger.info(f"   {col}: {cotacoes_analysis.iloc[0][col]}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar tipos de dados: {e}")
    
    def fix_vendas_data(self):
        """Corrige problemas na tabela vendas"""
        logger.info("🔧 Iniciando correções na tabela VENDAS...")
        
        try:
            cursor = self.conn.cursor()
            
            # 1. Corrigir valores nulos ou zero para valores de venda
            cursor.execute("""
                UPDATE vendas 
                SET valor_venda = 1.0 
                WHERE valor_venda IS NULL OR valor_venda = 0
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} valores nulos/zero em valor_venda")
            
            # 2. Corrigir datas malformadas ou nulas
            cursor.execute("""
                UPDATE vendas 
                SET data = date('now') 
                WHERE data IS NULL OR data = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidas {affected_rows} datas nulas/vazias")
            
            # 3. Garantir que campos de texto não sejam nulos
            cursor.execute("""
                UPDATE vendas 
                SET cliente = 'Cliente Não Informado' 
                WHERE cliente IS NULL OR cliente = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} nomes de cliente vazios")
            
            cursor.execute("""
                UPDATE vendas 
                SET produto = 'Produto Não Informado' 
                WHERE produto IS NULL OR produto = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} nomes de produto vazios")
            
            # 4. Padronizar formato de data se necessário
            cursor.execute("""
                UPDATE vendas 
                SET data = date(data) 
                WHERE data IS NOT NULL
            """)
            
            self.conn.commit()
            logger.info("✅ Correções na tabela VENDAS finalizadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao corrigir dados de vendas: {e}")
            self.conn.rollback()
    
    def fix_cotacoes_data(self):
        """Corrige problemas na tabela cotações"""
        logger.info("🔧 Iniciando correções na tabela COTAÇÕES...")
        
        try:
            cursor = self.conn.cursor()
            
            # 1. Corrigir clientes vazios
            cursor.execute("""
                UPDATE cotacoes 
                SET cliente = 'Cliente Não Informado' 
                WHERE cliente IS NULL OR cliente = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} nomes de cliente vazios")
            
            # 2. Corrigir números de cotação vazios
            cursor.execute("""
                UPDATE cotacoes 
                SET numero_cotacao = 'COT-' || id 
                WHERE numero_cotacao IS NULL OR numero_cotacao = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} números de cotação vazios")
            
            # 3. Corrigir datas nulas
            cursor.execute("""
                UPDATE cotacoes 
                SET data = date('now') 
                WHERE data IS NULL OR data = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidas {affected_rows} datas nulas/vazias")
            
            # 4. Garantir que status não seja nulo
            cursor.execute("""
                UPDATE cotacoes 
                SET status_cotacao = 'Em Análise' 
                WHERE status_cotacao IS NULL OR status_cotacao = ''
            """)
            affected_rows = cursor.rowcount
            logger.info(f"   ✅ Corrigidos {affected_rows} status vazios")
            
            self.conn.commit()
            logger.info("✅ Correções na tabela COTAÇÕES finalizadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao corrigir dados de cotações: {e}")
            self.conn.rollback()
    
    def add_missing_indexes(self):
        """Adiciona índices para melhorar performance"""
        logger.info("🚀 Adicionando índices para melhorar performance...")
        
        try:
            cursor = self.conn.cursor()
            
            # Índices para vendas
            indexes_vendas = [
                "CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data)",
                "CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente)",
                "CREATE INDEX IF NOT EXISTS idx_vendas_produto ON vendas(produto)",
                "CREATE INDEX IF NOT EXISTS idx_vendas_ano_mes ON vendas(strftime('%Y', data), strftime('%m', data))"
            ]
            
            for idx_sql in indexes_vendas:
                cursor.execute(idx_sql)
                logger.info(f"   ✅ {idx_sql.split('ON')[1].strip()}")
            
            # Índices para cotações
            indexes_cotacoes = [
                "CREATE INDEX IF NOT EXISTS idx_cotacoes_data ON cotacoes(data)",
                "CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente ON cotacoes(cliente)",
                "CREATE INDEX IF NOT EXISTS idx_cotacoes_numero ON cotacoes(numero_cotacao)"
            ]
            
            for idx_sql in indexes_cotacoes:
                cursor.execute(idx_sql)
                logger.info(f"   ✅ {idx_sql.split('ON')[1].strip()}")
            
            self.conn.commit()
            logger.info("✅ Índices criados com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")
    
    def apply_data_standardization(self):
        """Aplica todas as padronizações nos dados das tabelas"""
        logger.info("🔧 Aplicando padronizações nos dados...")
        
        try:
            # Carregar dados de vendas
            logger.info("📊 Carregando dados da tabela vendas...")
            vendas_df = pd.read_sql_query("SELECT * FROM vendas", self.conn)
            logger.info(f"   Total de registros carregados: {len(vendas_df)}")
            
            if not vendas_df.empty:
                # Aplicar funções de padronização
                logger.info("   Aplicando ajustes gerais...")
                vendas_df = ov_general_adjustments(vendas_df)
                
                logger.info("   Aplicando padronização hierarquia nível 1...")
                vendas_df = ov_hierarquia_um(vendas_df)
                
                logger.info("   Aplicando padronização hierarquia nível 2...")
                vendas_df = ov_hierarquia_dois(vendas_df)
                
                logger.info("   Aplicando padronização hierarquia nível 3...")
                vendas_df = ov_hierarquia_tres(vendas_df)
                
                # Limpar tabela e inserir dados padronizados
                logger.info("   Atualizando tabela vendas com dados padronizados...")
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM vendas")
                
                # Inserir dados padronizados
                vendas_df.to_sql('vendas', self.conn, if_exists='append', index=False)
                
                logger.info(f"   ✅ {len(vendas_df)} registros padronizados inseridos")
            
            # Carregar e padronizar cotações se necessário
            logger.info("📊 Verificando dados da tabela cotações...")
            cotacoes_df = pd.read_sql_query("SELECT * FROM cotacoes", self.conn)
            
            if not cotacoes_df.empty:
                # Aplicar padronizações básicas em cotações
                logger.info("   Aplicando padronizações básicas em cotações...")
                
                # Padronizar cliente
                if 'cliente' in cotacoes_df.columns:
                    cotacoes_df['cliente'] = cotacoes_df['cliente'].astype('string').str.lower()
                
                # Converter datas
                if 'data' in cotacoes_df.columns:
                    cotacoes_df['data'] = pd.to_datetime(cotacoes_df['data'], errors='coerce')
                
                # Atualizar tabela cotações
                cursor.execute("DELETE FROM cotacoes")
                cotacoes_df.to_sql('cotacoes', self.conn, if_exists='append', index=False)
                
                logger.info(f"   ✅ {len(cotacoes_df)} registros de cotações padronizados")
            
            self.conn.commit()
            logger.info("✅ Padronização de dados concluída com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar padronizações: {e}")
            self.conn.rollback()
            raise
    
    def validate_fixes(self):
        """Valida se as correções foram aplicadas corretamente"""
        logger.info("✅ Validando correções aplicadas...")
        
        try:
            # Validar vendas
            validation_vendas = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(CASE WHEN valor_venda IS NULL OR valor_venda = 0 THEN 1 END) as valores_problematicos,
                    COUNT(CASE WHEN cliente IS NULL OR cliente = '' THEN 1 END) as clientes_vazios,
                    COUNT(CASE WHEN data IS NULL THEN 1 END) as datas_nulas
                FROM vendas
            """, self.conn)
            
            logger.info("📊 Validação VENDAS:")
            for col in validation_vendas.columns:
                logger.info(f"   {col}: {validation_vendas.iloc[0][col]}")
            
            # Validar cotações
            validation_cotacoes = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(CASE WHEN cliente IS NULL OR cliente = '' THEN 1 END) as clientes_vazios,
                    COUNT(CASE WHEN numero_cotacao IS NULL OR numero_cotacao = '' THEN 1 END) as cotacoes_sem_numero,
                    COUNT(CASE WHEN data IS NULL THEN 1 END) as datas_nulas
                FROM cotacoes
            """, self.conn)
            
            logger.info("📊 Validação COTAÇÕES:")
            for col in validation_cotacoes.columns:
                logger.info(f"   {col}: {validation_cotacoes.iloc[0][col]}")
                
        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
    
    def run_complete_etl(self):
        """Executa todo o processo ETL"""
        logger.info("🚀 Iniciando processo completo de ETL...")
        
        if not self.connect_db():
            return False
        
        try:
            # 1. Análise inicial
            self.analyze_current_data()
            self.check_data_types_and_formats()
            
            # 2. Aplicar correções básicas
            self.fix_vendas_data()
            self.fix_cotacoes_data()
            
            # 3. Aplicar padronizações
            self.apply_data_standardization()
            
            # 4. Otimizações
            self.add_missing_indexes()
            
            # 5. Validação final
            self.validate_fixes()
            
            logger.info("✅ Processo ETL concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no processo ETL: {e}")
            return False
        finally:
            self.close_db()

def main():
    """Função principal para executar o ETL"""
    logger.info("=" * 60)
    logger.info("🔧 ETL - Correção de Dados - Dashboard Laura Rep")
    logger.info("=" * 60)
    
    etl = DataETL()
    success = etl.run_complete_etl()
    
    if success:
        logger.info("🎉 ETL finalizado com sucesso!")
    else:
        logger.error("💥 ETL falhou! Verifique os logs acima.")
    
    return success

if __name__ == "__main__":
    main()
