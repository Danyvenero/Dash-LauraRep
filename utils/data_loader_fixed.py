import pandas as pd
from typing import Tuple, Optional
import sqlite3
import os


class DataLoaderFixed:
    """Loader de dados com debug melhorado para identificar o problema da Series ambiguity"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.sqlite')
    
    def detect_file_type(self, df: pd.DataFrame) -> str:
        """Detecta o tipo de arquivo baseado nas colunas"""
        columns_lower = [col.lower() for col in df.columns]
        
        if any(col in columns_lower for col in ['vlr_rol', 'vlr_entrada', 'vlr_carteira']):
            return 'vendas'
        elif 'numero_cotacao' in columns_lower or 'número da cotação' in columns_lower:
            return 'cotacoes'
        elif any(col in columns_lower for col in ['preco_liquido', 'preço_liquido', 'centro_fornecedor']):
            return 'produtos_cotados'
        else:
            return 'vendas'  # Default
    
    def normalize_vendas_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de vendas com debug melhorado e validação robusta"""
        print(f"🔍 DEBUG normalize_vendas_data - Colunas: {list(df.columns)}")
        print(f"🔍 DEBUG normalize_vendas_data - Shape: {df.shape}")
        print(f"🔍 DEBUG normalize_vendas_data - Primeiras 2 linhas:")
        print(df.head(2))
        
        try:
            # Validação inicial do DataFrame
            if df.empty:
                print("⚠️  DataFrame vazio recebido")
                return pd.DataFrame()
            
            # Reset index para evitar problemas de concatenação
            df = df.reset_index(drop=True)
            df_norm = df.copy()
            
            # Mapeamento expandido de colunas
            column_mapping = {
                'unidade de negócio': 'unidade_negocio',
                'unidade_negocio': 'unidade_negocio',
                'canal distribuição': 'canal_distribuicao',
                'canal_distribuicao': 'canal_distribuicao',
                'id_cli': 'cod_cliente',
                'código cliente': 'cod_cliente',
                'codigo_cliente': 'cod_cliente',
                'cod cliente': 'cod_cliente',
                'cod. cliente': 'cod_cliente',
                'Cod. Cliente': 'cod_cliente',
                'cliente': 'cliente',
                'hier. produto 1': 'hier_produto_1',
                'hier_produto_1': 'hier_produto_1',
                'hier. produto 2': 'hier_produto_2',
                'hier_produto_2': 'hier_produto_2',
                'hier. produto 3': 'hier_produto_3',
                'hier_produto_3': 'hier_produto_3',
                'doc. vendas': 'doc_vendas',
                'doc_vendas': 'doc_vendas',
                'material': 'material',
                'produto': 'produto',
                'data faturamento': 'data_faturamento',
                'data_faturamento': 'data_faturamento',
                'data': 'data',
                'cidade do cliente': 'cidade_cliente',
                'cidade_cliente': 'cidade_cliente',
                'qtd. entrada': 'qtd_entrada',
                'qtd_entrada': 'qtd_entrada',
                'vlr. entrada': 'vlr_entrada',
                'vlr_entrada': 'vlr_entrada',
                'qtd. carteira': 'qtd_carteira',
                'qtd_carteira': 'qtd_carteira',
                'vlr. carteira': 'vlr_carteira',
                'vlr_carteira': 'vlr_carteira',
                'qtd. rol': 'qtd_rol',
                'qtd_rol': 'qtd_rol',
                'vlr. rol': 'vlr_rol',
                'vlr_rol': 'vlr_rol'
            }
            
            # Aplica mapeamento de forma mais segura
            try:
                columns_to_rename = {}
                for old_col, new_col in column_mapping.items():
                    for actual_col in df_norm.columns:
                        if actual_col.lower() == old_col.lower():
                            columns_to_rename[actual_col] = new_col
                            break
                
                if columns_to_rename:
                    df_norm = df_norm.rename(columns=columns_to_rename)
                    print(f"🔍 DEBUG: Renomeação aplicada: {columns_to_rename}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro no mapeamento: {str(e)}")
            
            # Normaliza códigos de cliente
            try:
                if 'cod_cliente' in df_norm.columns:
                    print(f"🔍 DEBUG: Normalizando cod_cliente...")
                    df_norm = df_norm.copy()  # Força uma nova cópia
                    df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str).str.strip()
                    print(f"🔍 DEBUG: cod_cliente normalizado")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar cod_cliente: {str(e)}")
            
            # Normaliza materiais
            try:
                if 'material' in df_norm.columns:
                    print(f"🔍 DEBUG: Normalizando material...")
                    df_norm['material'] = pd.to_numeric(df_norm['material'], errors='coerce').fillna(0).astype(int).astype(str)
                    print(f"🔍 DEBUG: material normalizado")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar material: {str(e)}")
            
            # Normaliza datas e converte para string compatível com SQLite
            for date_col in ['data', 'data_faturamento']:
                try:
                    if date_col in df_norm.columns:
                        print(f"🔍 DEBUG: Normalizando {date_col}...")
                        # Converte para datetime primeiro
                        df_norm[date_col] = pd.to_datetime(df_norm[date_col], errors='coerce')
                        # Converte para string para compatibilidade com SQLite
                        df_norm[date_col] = df_norm[date_col].dt.strftime('%Y-%m-%d').fillna('')
                        print(f"🔍 DEBUG: {date_col} normalizado e convertido para string")
                except Exception as e:
                    print(f"❌ DEBUG: Erro ao normalizar {date_col}: {str(e)}")
            
            # Normaliza valores numéricos
            numeric_cols = ['qtd_entrada', 'vlr_entrada', 'qtd_carteira', 'vlr_carteira', 'qtd_rol', 'vlr_rol']
            for col in numeric_cols:
                try:
                    if col in df_norm.columns:
                        print(f"🔍 DEBUG: Normalizando {col}...")
                        df_norm[col] = pd.to_numeric(df_norm[col], errors='coerce').fillna(0)
                        print(f"🔍 DEBUG: {col} normalizado")
                except Exception as e:
                    print(f"❌ DEBUG: Erro ao normalizar {col}: {str(e)}")
            
            # Remove linhas com dados críticos faltando - MÉTODO MAIS SEGURO
            try:
                print(f"🔍 DEBUG: Removendo linhas com dados faltando...")
                initial_shape = df_norm.shape
                
                # Usa dropna que é mais seguro
                required_cols = []
                if 'cod_cliente' in df_norm.columns:
                    required_cols.append('cod_cliente')
                if 'material' in df_norm.columns:
                    required_cols.append('material')
                
                if required_cols:
                    df_norm = df_norm.dropna(subset=required_cols)
                    print(f"🔍 DEBUG: Filtro aplicado: {initial_shape} -> {df_norm.shape}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro ao filtrar dados faltando: {str(e)}")
            
            # Filtra colunas válidas
            try:
                valid_columns = [
                    'cod_cliente', 'cliente', 'material', 'produto', 'unidade_negocio',
                    'canal_distribuicao', 'hier_produto_1', 'hier_produto_2', 'hier_produto_3',
                    'data', 'data_faturamento', 'qtd_entrada', 'vlr_entrada', 'qtd_carteira',
                    'vlr_carteira', 'qtd_rol', 'vlr_rol'
                ]
                
                columns_to_keep = [col for col in valid_columns if col in df_norm.columns]
                df_norm = df_norm[columns_to_keep]
                print(f"🔍 DEBUG: Colunas mantidas: {columns_to_keep}")
                print(f"🔍 DEBUG: Shape final: {df_norm.shape}")
                
            except Exception as e:
                print(f"❌ DEBUG: Erro ao filtrar colunas: {str(e)}")
            
            print(f"✅ DEBUG: normalize_vendas_data concluído")
            return df_norm
            
        except Exception as e:
            print(f"❌ DEBUG: Erro crítico: {str(e)}")
            import traceback
            traceback.print_exc()
            return df  # Retorna original se falhar
    
    def normalize_cotacoes_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de cotações com correções de Series ambiguity e validação robusta"""
        print(f"🔍 DEBUG normalize_cotacoes_data - Colunas: {list(df.columns)}")
        print(f"🔍 DEBUG normalize_cotacoes_data - Shape: {df.shape}")
        
        try:
            # Validação inicial do DataFrame
            if df.empty:
                print("⚠️  DataFrame vazio recebido")
                return pd.DataFrame()
            
            # Reset index para evitar problemas de concatenação
            df = df.reset_index(drop=True)
            df_norm = df.copy()
            
            # Mapeamento de colunas para cotações (estrutura otimizada)
            column_mapping = {
                'número da cotação': 'numero_cotacao',
                'numero da cotacao': 'numero_cotacao',
                'numero_cotacao': 'numero_cotacao',
                'cotação': 'numero_cotacao',
                'cotacao': 'numero_cotacao',
                'número da revisão': 'numero_revisao',
                'numero da revisao': 'numero_revisao',
                'numero_revisao': 'numero_revisao',
                'revisão': 'numero_revisao',
                'revisao': 'numero_revisao',
                'linhas de cotação': 'linhas_cotacao',
                'linhas da cotacao': 'linhas_cotacao',
                'linhas_cotacao': 'linhas_cotacao',
                'linhas cotacao': 'linhas_cotacao',
                'status da cotação': 'status_cotacao',
                'status da cotacao': 'status_cotacao',
                'status_cotacao': 'status_cotacao',
                'status cotacao': 'status_cotacao',
                'status': 'status_cotacao',
                'id_cli': 'cod_cliente',
                'código cliente': 'cod_cliente',
                'codigo_cliente': 'cod_cliente',
                'cod cliente': 'cod_cliente',
                'cod. cliente': 'cod_cliente',
                'Cod. Cliente': 'cod_cliente',
                'código do cliente': 'cod_cliente',
                'codigo do cliente': 'cod_cliente',
                'cod_cli': 'cod_cliente',
                'codcli': 'cod_cliente',
                'cliente código': 'cod_cliente',
                'cliente codigo': 'cod_cliente',
                'Código do Cliente': 'cod_cliente',
                'cliente': 'cliente',
                'razão social': 'cliente',
                'razao social': 'cliente',
                'nome cliente': 'cliente',
                'nome do cliente': 'cliente',
                'data': 'data',
                'data cotação': 'data',
                'data cotacao': 'data',
                'data da cotação': 'data',
                'data da cotacao': 'data',
                'Data de Criação': 'data'
            }
            
            # Aplica mapeamento de forma segura
            try:
                columns_to_rename = {}
                for old_col, new_col in column_mapping.items():
                    for actual_col in df_norm.columns:
                        if actual_col.lower() == old_col.lower():
                            columns_to_rename[actual_col] = new_col
                            break
                
                if columns_to_rename:
                    df_norm = df_norm.rename(columns=columns_to_rename)
                    print(f"🔍 DEBUG: Cotações renomeação aplicada: {columns_to_rename}")
                    
                    # Debug adicional - mostra valores únicos das colunas problemáticas
                    for old_col, new_col in columns_to_rename.items():
                        if new_col in ['cod_cliente', 'cliente'] and new_col in df_norm.columns:
                            try:
                                unique_values = df_norm[new_col].dropna().unique()[:5]  # Primeiros 5 valores únicos
                                print(f"🔍 DEBUG: Coluna '{old_col}' -> '{new_col}' - Valores exemplo: {list(unique_values)}")
                            except Exception as debug_e:
                                print(f"❌ DEBUG: Erro ao mostrar valores de {new_col}: {str(debug_e)}")
                    
                else:
                    print(f"🔍 DEBUG: Nenhuma renomeação aplicada para cotações")
                    print(f"🔍 DEBUG: Colunas disponíveis: {list(df_norm.columns)}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro no mapeamento cotações: {str(e)}")
            
            # Normaliza dados específicos de cotações
            try:
                if 'cod_cliente' in df_norm.columns:
                    # Garante que é uma Series antes de aplicar .str
                    col_data = df_norm['cod_cliente']
                    if hasattr(col_data, 'astype'):  # Verifica se é Series/DataFrame válido
                        df_norm['cod_cliente'] = col_data.astype(str).str.strip()
                        print(f"🔍 DEBUG: cod_cliente cotações normalizado")
                    else:
                        print(f"❌ DEBUG: cod_cliente não é Series/DataFrame válido: {type(col_data)}")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar cod_cliente cotações: {str(e)}")
            
            try:
                if 'data' in df_norm.columns:
                    # Converte para datetime primeiro
                    df_norm['data'] = pd.to_datetime(df_norm['data'], errors='coerce')
                    # Converte para string para compatibilidade com SQLite
                    df_norm['data'] = df_norm['data'].dt.strftime('%Y-%m-%d').fillna('')
                    print(f"🔍 DEBUG: data cotações normalizada e convertida para string")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar data cotações: {str(e)}")
            
            try:
                if 'linhas_cotacao' in df_norm.columns:
                    df_norm['linhas_cotacao'] = df_norm['linhas_cotacao'].astype(str).str.strip()
                    print(f"🔍 DEBUG: linhas_cotacao normalizada")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar linhas_cotacao: {str(e)}")
            
            try:
                if 'status_cotacao' in df_norm.columns:
                    df_norm['status_cotacao'] = df_norm['status_cotacao'].astype(str).str.strip()
                    print(f"🔍 DEBUG: status_cotacao normalizado")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar status_cotacao: {str(e)}")
            
            # Remove linhas críticas faltando (apenas cotação e cliente são essenciais)
            try:
                print(f"🔍 DEBUG: Removendo linhas com dados faltando em cotações...")
                initial_shape = df_norm.shape
                
                required_cols = []
                if 'numero_cotacao' in df_norm.columns:
                    required_cols.append('numero_cotacao')
                if 'cod_cliente' in df_norm.columns:
                    required_cols.append('cod_cliente')
                
                if required_cols:
                    df_norm = df_norm.dropna(subset=required_cols)
                    print(f"🔍 DEBUG: Filtro cotações aplicado: {initial_shape} -> {df_norm.shape}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro ao filtrar dados faltando cotações: {str(e)}")
            
            print(f"✅ DEBUG: normalize_cotacoes_data concluído")
            return df_norm
            
        except Exception as e:
            print(f"❌ DEBUG: Erro crítico em cotações: {str(e)}")
            import traceback
            traceback.print_exc()
            return df
    
    def normalize_produtos_cotados_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados de produtos cotados com correções de Series ambiguity e validação robusta"""
        print(f"🔍 DEBUG normalize_produtos_cotados_data - Colunas: {list(df.columns)}")
        print(f"🔍 DEBUG normalize_produtos_cotados_data - Shape: {df.shape}")
        
        try:
            # Validação inicial do DataFrame
            if df.empty:
                print("⚠️  DataFrame vazio recebido")
                return pd.DataFrame()
            
            # Reset index para evitar problemas de concatenação
            df = df.reset_index(drop=True)
            df_norm = df.copy()
            
            # Mapeamento de colunas
            column_mapping = {
                'cotação': 'cotacao',
                'cotacao': 'cotacao',
                'número da cotação': 'cotacao',
                'numero da cotacao': 'cotacao',
                'numero_cotacao': 'cotacao',
                'id_cli': 'cod_cliente',
                'código cliente': 'cod_cliente',
                'codigo_cliente': 'cod_cliente',
                'cod cliente': 'cod_cliente',
                'cod. cliente': 'cod_cliente',
                'Cod. Cliente': 'cod_cliente',
                'código do cliente': 'cod_cliente',
                'codigo do cliente': 'cod_cliente',
                'cod_cli': 'cod_cliente',
                'codcli': 'cod_cliente',
                'cliente código': 'cod_cliente',
                'cliente codigo': 'cod_cliente',
                'cliente': 'cliente',
                'razão social': 'cliente',
                'razao social': 'cliente',
                'nome cliente': 'cliente',
                'nome do cliente': 'cliente',
                'centro fornecedor': 'centro_fornecedor',
                'centro_fornecedor': 'centro_fornecedor',
                'centro de fornecedor': 'centro_fornecedor',
                'material': 'material',
                'código material': 'material',
                'codigo_material': 'material',
                'cod_material': 'material',
                'descrição': 'descricao',
                'descricao': 'descricao',
                'descrição do material': 'descricao',
                'descricao do material': 'descricao',
                'desc_material': 'descricao',
                'quantidade': 'quantidade',
                'qtd': 'quantidade',
                'qty': 'quantidade',
                'preço líquido unitário': 'preco_liquido_unitario',
                'preco liquido unitario': 'preco_liquido_unitario',
                'preço_liquido_unitario': 'preco_liquido_unitario',
                'preco_unit': 'preco_liquido_unitario',
                'valor unitário': 'preco_liquido_unitario',
                'valor_unitario': 'preco_liquido_unitario',
                'preço líquido total': 'preco_liquido_total',
                'preco liquido total': 'preco_liquido_total',
                'preço_liquido_total': 'preco_liquido_total',
                'valor total': 'preco_liquido_total',
                'valor_total': 'preco_liquido_total',
                'total': 'preco_liquido_total'
            }
            
            # Aplica mapeamento de forma segura
            try:
                columns_to_rename = {}
                for old_col, new_col in column_mapping.items():
                    for actual_col in df_norm.columns:
                        if actual_col.lower() == old_col.lower():
                            columns_to_rename[actual_col] = new_col
                            break
                
                if columns_to_rename:
                    df_norm = df_norm.rename(columns=columns_to_rename)
                    print(f"🔍 DEBUG: Produtos cotados renomeação aplicada: {columns_to_rename}")
                    
                    # Debug adicional - mostra valores únicos das colunas problemáticas
                    for old_col, new_col in columns_to_rename.items():
                        if new_col in ['cod_cliente', 'cliente', 'cotacao']:
                            unique_values = df_norm[new_col].dropna().unique()[:5]  # Primeiros 5 valores únicos
                            print(f"🔍 DEBUG: Coluna '{old_col}' -> '{new_col}' - Valores exemplo: {list(unique_values)}")
                    
                else:
                    print(f"🔍 DEBUG: Nenhuma renomeação aplicada para produtos cotados")
                    print(f"🔍 DEBUG: Colunas disponíveis: {list(df_norm.columns)}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro no mapeamento produtos cotados: {str(e)}")
            
            # Normaliza dados
            try:
                if 'cod_cliente' in df_norm.columns:
                    # Trata valores None, NaN, vazios antes de converter para string
                    df_norm['cod_cliente'] = df_norm['cod_cliente'].replace(['', 'None', 'none', 'NONE'], pd.NA)
                    df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str).str.strip()
                    # Reconverte 'nan' para None
                    df_norm['cod_cliente'] = df_norm['cod_cliente'].replace(['nan', 'NaN', 'NAN'], None)
                    print(f"🔍 DEBUG: cod_cliente produtos cotados normalizado")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar cod_cliente produtos cotados: {str(e)}")
            
            try:
                if 'material' in df_norm.columns:
                    # Trata valores None/vazios antes de converter
                    df_norm['material'] = df_norm['material'].replace(['', 'None', 'none', 'NONE'], pd.NA)
                    df_norm['material'] = pd.to_numeric(df_norm['material'], errors='coerce').fillna(0).astype(int).astype(str)
                    print(f"🔍 DEBUG: material produtos cotados normalizado")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao normalizar material produtos cotados: {str(e)}")
            
            # Normaliza valores numéricos
            numeric_cols = ['quantidade', 'preco_liquido_unitario', 'preco_liquido_total']
            for col in numeric_cols:
                try:
                    if col in df_norm.columns:
                        df_norm[col] = pd.to_numeric(df_norm[col], errors='coerce').fillna(0)
                        print(f"🔍 DEBUG: {col} produtos cotados normalizado")
                except Exception as e:
                    print(f"❌ DEBUG: Erro ao normalizar {col} produtos cotados: {str(e)}")
            
            # Normaliza campos de texto
            text_cols = ['cotacao', 'centro_fornecedor', 'descricao', 'cliente']
            for col in text_cols:
                try:
                    if col in df_norm.columns:
                        # Trata valores None/vazios antes de converter
                        df_norm[col] = df_norm[col].replace(['', 'None', 'none', 'NONE'], pd.NA)
                        df_norm[col] = df_norm[col].astype(str).str.strip()
                        # Reconverte 'nan' para None para campos não obrigatórios
                        if col not in ['cotacao']:  # cotacao é obrigatório
                            df_norm[col] = df_norm[col].replace(['nan', 'NaN', 'NAN'], None)
                        print(f"🔍 DEBUG: {col} produtos cotados normalizado")
                except Exception as e:
                    print(f"❌ DEBUG: Erro ao normalizar {col} produtos cotados: {str(e)}")
            
            # Remove linhas críticas faltando - MÉTODO SEGURO
            try:
                print(f"🔍 DEBUG: Removendo linhas com dados faltando em produtos cotados...")
                initial_shape = df_norm.shape
                
                required_cols = []
                if 'cotacao' in df_norm.columns:
                    required_cols.append('cotacao')
                if 'cod_cliente' in df_norm.columns:
                    required_cols.append('cod_cliente')
                if 'material' in df_norm.columns:
                    required_cols.append('material')
                
                if required_cols:
                    df_norm = df_norm.dropna(subset=required_cols)
                    print(f"🔍 DEBUG: Filtro produtos cotados aplicado: {initial_shape} -> {df_norm.shape}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Erro ao filtrar dados faltando produtos cotados: {str(e)}")
            
            print(f"✅ DEBUG: normalize_produtos_cotados_data concluído")
            return df_norm
            
        except Exception as e:
            print(f"❌ DEBUG: Erro crítico em produtos cotados: {str(e)}")
            import traceback
            traceback.print_exc()
            return df
