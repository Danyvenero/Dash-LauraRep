"""
Módulo para carregamento e normalização de dados
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import re
from datetime import datetime

class DataLoader:
    """Classe para carregamento e normalização de dados"""
    
    def __init__(self):
        self.vendas_hints = ['ovs', 'vendas', 'venda', 'faturamento']
        self.cotacoes_hints = ['cotação', 'cotacao', 'cotações', 'cotacoes', 'quote']
        self.materiais_hints = ['materiais', 'material', 'produtos', 'produto', 'items']
    
    def detect_file_type(self, filename: str, df: pd.DataFrame) -> str:
        """Detecta o tipo de arquivo baseado no nome e conteúdo"""
        filename_lower = filename.lower()
        columns_lower = [col.lower() for col in df.columns]
        
        # Verifica hints no nome do arquivo
        if any(hint in filename_lower for hint in self.vendas_hints):
            return 'vendas'
        elif any(hint in filename_lower for hint in self.cotacoes_hints):
            return 'cotacoes'
        elif any(hint in filename_lower for hint in self.materiais_hints):
            return 'produtos_cotados'
        
        # Verifica colunas características
        if any(col in columns_lower for col in ['vlr_rol', 'vlr_entrada', 'vlr_carteira']):
            return 'vendas'
        elif 'numero_cotacao' in columns_lower or 'número da cotação' in columns_lower:
            return 'cotacoes'
        elif any(col in columns_lower for col in ['preco_liquido', 'preço_liquido', 'centro_fornecedor']):
            return 'produtos_cotados'
        
        return 'unknown'
    
    def normalize_vendas_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de vendas"""
        df_norm = df.copy()
        
        # Mapeamento de colunas conhecidas
        column_mapping = {
            'id_cli': 'cod_cliente',
            'código cliente': 'cod_cliente',
            'codigo_cliente': 'cod_cliente',
            'cod cliente': 'cod_cliente',
            'doc. vendas': 'cod_cliente',  # Adicionado mapeamento para Doc. Vendas
            'doc vendas': 'cod_cliente',
            'documento vendas': 'cod_cliente',
            'cliente': 'cliente',
            'material': 'material',
            'produto': 'produto',
            'unidade de negócio': 'unidade_negocio',
            'unidade_negocio': 'unidade_negocio',
            'canal distribuição': 'canal_distribuicao',
            'canal_distribuicao': 'canal_distribuicao',
            'hier. produto 1': 'hier_produto_1',
            'hier produto 1': 'hier_produto_1',
            'hier_produto_1': 'hier_produto_1',
            'hier. produto 2': 'hier_produto_2',
            'hier produto 2': 'hier_produto_2',
            'hier_produto_2': 'hier_produto_2',
            'hier. produto 3': 'hier_produto_3',
            'hier produto 3': 'hier_produto_3',
            'hier_produto_3': 'hier_produto_3',
            'data': 'data',
            'data faturamento': 'data_faturamento',
            'data_faturamento': 'data_faturamento',
            'qtd entrada': 'qtd_entrada',
            'qtd_entrada': 'qtd_entrada',
            'vlr entrada': 'vlr_entrada',
            'vlr_entrada': 'vlr_entrada',
            'qtd carteira': 'qtd_carteira',
            'qtd_carteira': 'qtd_carteira',
            'vlr carteira': 'vlr_carteira',
            'vlr_carteira': 'vlr_carteira',
            'qtd rol': 'qtd_rol',
            'qtd_rol': 'qtd_rol',
            'vlr rol': 'vlr_rol',
            'vlr_rol': 'vlr_rol'
        }
        
        # Aplica mapeamento de colunas
        for old_col, new_col in column_mapping.items():
            if old_col in df_norm.columns:
                df_norm = df_norm.rename(columns={old_col: new_col})
            elif old_col.lower() in [col.lower() for col in df_norm.columns]:
                # Busca case-insensitive
                for col in df_norm.columns:
                    if col.lower() == old_col.lower():
                        df_norm = df_norm.rename(columns={col: new_col})
                        break
        
        # Normaliza códigos de cliente
        if 'cod_cliente' in df_norm.columns:
            df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str).str.strip()
        
        # Normaliza materiais
        if 'material' in df_norm.columns:
            df_norm['material'] = pd.to_numeric(df_norm['material'], errors='coerce').fillna(0).astype(int).astype(str)
        
        # Normaliza datas
        for date_col in ['data', 'data_faturamento']:
            if date_col in df_norm.columns:
                df_norm[date_col] = pd.to_datetime(df_norm[date_col], errors='coerce')
        
        # Normaliza valores numéricos
        numeric_cols = ['qtd_entrada', 'vlr_entrada', 'qtd_carteira', 'vlr_carteira', 'qtd_rol', 'vlr_rol']
        for col in numeric_cols:
            if col in df_norm.columns:
                df_norm[col] = pd.to_numeric(df_norm[col], errors='coerce').fillna(0)
        
        # Remove linhas com dados críticos faltando
        required_cols = ['cod_cliente', 'material']
        for col in required_cols:
            if col in df_norm.columns:
                df_norm = df_norm.dropna(subset=[col])
        
        # Mantém apenas colunas válidas do schema
        valid_columns = [
            'cod_cliente', 'cliente', 'material', 'produto', 'unidade_negocio',
            'canal_distribuicao', 'hier_produto_1', 'hier_produto_2', 'hier_produto_3',
            'data', 'data_faturamento', 'qtd_entrada', 'vlr_entrada', 'qtd_carteira',
            'vlr_carteira', 'qtd_rol', 'vlr_rol'
        ]
        
        # Filtra apenas colunas que existem tanto no DataFrame quanto no schema
        columns_to_keep = [col for col in valid_columns if col in df_norm.columns]
        df_norm = df_norm[columns_to_keep]
        
        return df_norm
    
    def normalize_cotacoes_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de cotações"""
        df_norm = df.copy()
        
        # Mapeamento de colunas
        column_mapping = {
            'número da cotação': 'numero_cotacao',
            'numero da cotacao': 'numero_cotacao',
            'numero_cotacao': 'numero_cotacao',
            'cotação': 'numero_cotacao',
            'cotacao': 'numero_cotacao',
            'id_cli': 'cod_cliente',
            'código cliente': 'cod_cliente',
            'codigo_cliente': 'cod_cliente',
            'cod cliente': 'cod_cliente',
            'cliente': 'cliente',
            'material': 'material',
            'data': 'data',
            'quantidade': 'quantidade',
            'qtd': 'quantidade'
        }
        
        # Aplica mapeamento
        for old_col, new_col in column_mapping.items():
            for col in df_norm.columns:
                if col.lower() == old_col.lower():
                    df_norm = df_norm.rename(columns={col: new_col})
                    break
        
        # Normaliza dados
        if 'cod_cliente' in df_norm.columns:
            df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str).str.strip()
        
        if 'material' in df_norm.columns:
            df_norm['material'] = pd.to_numeric(df_norm['material'], errors='coerce').fillna(0).astype(int).astype(str)
        
        if 'data' in df_norm.columns:
            df_norm['data'] = pd.to_datetime(df_norm['data'], errors='coerce')
        
        if 'quantidade' in df_norm.columns:
            df_norm['quantidade'] = pd.to_numeric(df_norm['quantidade'], errors='coerce').fillna(0)
        
        # Remove linhas críticas faltando
        required_cols = ['numero_cotacao', 'cod_cliente', 'material']
        for col in required_cols:
            if col in df_norm.columns:
                df_norm = df_norm.dropna(subset=[col])
        
        return df_norm
    
    def normalize_produtos_cotados_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de produtos cotados"""
        df_norm = df.copy()
        
        # Mapeamento de colunas
        column_mapping = {
            'cotação': 'cotacao',
            'cotacao': 'cotacao',
            'id_cli': 'cod_cliente',
            'código cliente': 'cod_cliente',
            'codigo_cliente': 'cod_cliente',
            'cod cliente': 'cod_cliente',
            'cliente': 'cliente',
            'centro fornecedor': 'centro_fornecedor',
            'centro_fornecedor': 'centro_fornecedor',
            'material': 'material',
            'descrição': 'descricao',
            'descricao': 'descricao',
            'quantidade': 'quantidade',
            'qtd': 'quantidade',
            'preço líquido unitário': 'preco_liquido_unitario',
            'preco liquido unitario': 'preco_liquido_unitario',
            'preço_liquido_unitario': 'preco_liquido_unitario',
            'preço líquido total': 'preco_liquido_total',
            'preco liquido total': 'preco_liquido_total',
            'preço_liquido_total': 'preco_liquido_total'
        }
        
        # Aplica mapeamento
        for old_col, new_col in column_mapping.items():
            for col in df_norm.columns:
                if col.lower() == old_col.lower():
                    df_norm = df_norm.rename(columns={col: new_col})
                    break
        
        # Normaliza dados
        if 'cod_cliente' in df_norm.columns:
            df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str).str.strip()
        
        if 'material' in df_norm.columns:
            df_norm['material'] = pd.to_numeric(df_norm['material'], errors='coerce').fillna(0).astype(int).astype(str)
        
        numeric_cols = ['quantidade', 'preco_liquido_unitario', 'preco_liquido_total']
        for col in numeric_cols:
            if col in df_norm.columns:
                df_norm[col] = pd.to_numeric(df_norm[col], errors='coerce').fillna(0)
        
        # Remove linhas críticas faltando
        required_cols = ['cotacao', 'cod_cliente', 'material']
        for col in required_cols:
            if col in df_norm.columns:
                df_norm = df_norm.dropna(subset=[col])
        
        return df_norm
    
    def load_excel_file(self, file_path: str) -> Tuple[pd.DataFrame, str]:
        """Carrega arquivo Excel e detecta tipo"""
        try:
            # Tenta ler como .xlsx primeiro
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            try:
                # Fallback para .xls
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception as e:
                raise ValueError(f"Erro ao ler arquivo Excel: {str(e)}")
        
        if df.empty:
            raise ValueError("Arquivo está vazio")
        
        # Detecta tipo do arquivo
        file_type = self.detect_file_type(Path(file_path).name, df)
        
        return df, file_type
    
    def process_file(self, file_path: str) -> Tuple[pd.DataFrame, str]:
        """Processa um arquivo e retorna dados normalizados"""
        df, file_type = self.load_excel_file(file_path)
        
        if file_type == 'vendas':
            df_normalized = self.normalize_vendas_data(df)
        elif file_type == 'cotacoes':
            df_normalized = self.normalize_cotacoes_data(df)
        elif file_type == 'produtos_cotados':
            df_normalized = self.normalize_produtos_cotados_data(df)
        else:
            raise ValueError(f"Tipo de arquivo não reconhecido: {file_type}")
        
        return df_normalized, file_type
    
    def validate_data_integrity(self, vendas_df: pd.DataFrame, 
                              cotacoes_df: pd.DataFrame, 
                              produtos_cotados_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Valida integridade dos dados"""
        issues = {
            'warnings': [],
            'errors': []
        }
        
        # Verifica se há dados
        if vendas_df.empty:
            issues['warnings'].append("Dados de vendas estão vazios")
        if cotacoes_df.empty:
            issues['warnings'].append("Dados de cotações estão vazios")
        if produtos_cotados_df.empty:
            issues['warnings'].append("Dados de produtos cotados estão vazios")
        
        # Verifica integridade referencial entre cotações e produtos cotados
        if not cotacoes_df.empty and not produtos_cotados_df.empty:
            cotacoes_nums = set(cotacoes_df['numero_cotacao'].astype(str))
            produtos_nums = set(produtos_cotados_df['cotacao'].astype(str))
            
            missing_cotacoes = produtos_nums - cotacoes_nums
            if missing_cotacoes:
                issues['warnings'].append(f"Produtos cotados sem cotação correspondente: {len(missing_cotacoes)} itens")
        
        # Verifica consistência de clientes
        if not vendas_df.empty and not cotacoes_df.empty:
            vendas_clientes = set(vendas_df['cod_cliente'].astype(str))
            cotacoes_clientes = set(cotacoes_df['cod_cliente'].astype(str))
            
            only_vendas = vendas_clientes - cotacoes_clientes
            only_cotacoes = cotacoes_clientes - vendas_clientes
            
            if only_vendas:
                issues['warnings'].append(f"Clientes apenas em vendas: {len(only_vendas)} clientes")
            if only_cotacoes:
                issues['warnings'].append(f"Clientes apenas em cotações: {len(only_cotacoes)} clientes")
        
        return issues
