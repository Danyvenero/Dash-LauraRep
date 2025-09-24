import pandas as pd
from typing import Tuple, Optional
import sqlite3
import os
import re


class DataLoaderFixed:
    """Loader de dados com debug melhorado para identificar o problema da Series ambiguity"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.sqlite')
    
    def detect_file_type(self, filename: str, df: pd.DataFrame) -> str:
        """Detecta o tipo de arquivo baseado no nome e colunas"""
        filename_lower = filename.lower()
        columns_lower = [col.lower() for col in df.columns]
        
        print(f"🔍 DEBUG detect_file_type - Arquivo: {filename}", flush=True)
        print(f"🔍 DEBUG detect_file_type - Colunas disponíveis: {columns_lower}", flush=True)
        
        # Verifica hints no nome do arquivo primeiro
        if any(hint in filename_lower for hint in ['materiais', 'material', 'produtos', 'produto', 'items']):
            print(f"🔍 DEBUG: Arquivo detectado como PRODUTOS_COTADOS (por nome)", flush=True)
            return 'produtos_cotados'
        elif any(hint in filename_lower for hint in ['cotação', 'cotacao', 'cotações', 'cotacoes', 'quote']):
            print(f"🔍 DEBUG: Arquivo detectado como COTAÇÕES (por nome)", flush=True)
            return 'cotacoes'
        elif any(hint in filename_lower for hint in ['ovs', 'vendas', 'venda', 'faturamento']):
            print(f"🔍 DEBUG: Arquivo detectado como VENDAS (por nome)", flush=True)
            return 'vendas'
        
        # Se não detectou pelo nome, verifica pelas colunas
        print(f"🔍 DEBUG: Verificando colunas para detecção...", flush=True)
        
        if any(col in columns_lower for col in ['vlr_rol', 'vlr_entrada', 'vlr_carteira']):
            print(f"🔍 DEBUG: Arquivo detectado como VENDAS (por colunas: vlr_rol/vlr_entrada/vlr_carteira)", flush=True)
            return 'vendas'
        elif any(col in columns_lower for col in ['numero_cotacao', 'número da cotação', 'numero da cotacao']):
            print(f"🔍 DEBUG: Arquivo detectado como COTAÇÕES (por colunas: numero_cotacao)", flush=True)
            return 'cotacoes'
        elif any(col in columns_lower for col in ['preco_liquido', 'preço_liquido', 'preço líquido', 'preço líquido unitário', 'centro_fornecedor', 'centro fornecedor']):
            print(f"🔍 DEBUG: Arquivo detectado como PRODUTOS_COTADOS (por colunas: preço_liquido)", flush=True)
            return 'produtos_cotados'
        else:
            print(f"🔍 DEBUG: Arquivo não reconhecido, usando VENDAS como padrão", flush=True)
            print(f"🔍 DEBUG: Colunas analisadas: {columns_lower}", flush=True)
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
            
            # Normaliza materiais (preserva zeros à esquerda e formatos mistos)
            try:
                if 'material' in df_norm.columns:
                    print(f"🔍 DEBUG: Normalizando material (safe string)...")
                    def _normalize_material_value(v):
                        if pd.isna(v):
                            return None
                        s = str(v).strip()
                        if s == '' or s.lower() in {'none', 'nan', 'n/a', 'null'}:
                            return None
                        if isinstance(v, (int,)):
                            return str(v)
                        if isinstance(v, float):
                            s_float = f"{v:.15g}"
                            s_float = re.sub(r"\.0+$", "", s_float)
                            return s_float
                        t = s.replace(' ', '')
                        if re.fullmatch(r"\d+[\.,]0+", t):
                            return re.split(r"[\.,]", t)[0]
                        if re.fullmatch(r"\d+", t):
                            return t
                        return s.upper()
                    df_norm['material'] = df_norm['material'].apply(_normalize_material_value)
                    print(f"🔍 DEBUG: material normalizado (string safe)")
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
                'codigo material': 'material',
                'cod material': 'material',
                'cód material': 'material',
                'código do material': 'material',
                'codigo do material': 'material',
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
                    # Fallback: tenta encontrar coluna de 'material' por regex quando não mapeada
                    if 'material' not in df_norm.columns:
                        for c in df_norm.columns:
                            cname = c.strip().lower()
                            # padrões comuns: 'cod material', 'codigo material', 'código material', 'cod. material'
                            if re.search(r"^(cod(\.|igo)?|cód(\.)?|código)\s+do?\s*material$", cname) or \
                               re.search(r"^cod\s*material$", cname) or \
                               re.search(r"^codigo\s*material$", cname) or \
                               re.search(r"^código\s*material$", cname):
                                df_norm = df_norm.rename(columns={c: 'material'})
                                print(f"🔍 DEBUG: Fallback regex renomeou '{c}' -> 'material'")
                                break
                    
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
                    # Normaliza o código do material preservando formatos não numéricos e zeros à esquerda
                    def _normalize_material_value(v):
                        if pd.isna(v):
                            return None
                        # Converte para string e limpa espaços
                        s = str(v).strip()
                        if s == '' or s.lower() in {'none', 'nan', 'n/a', 'null'}:
                            return None
                        # Se for inteiro/float do Excel (ex.: 12345.0), remove casas decimais
                        if isinstance(v, (int,)):
                            return str(v)
                        if isinstance(v, float):
                            # Formata sem notação científica e remove .0 finais
                            s_float = f"{v:.15g}"
                            s_float = re.sub(r"\.0+$", "", s_float)
                            return s_float
                        # Trata strings numéricas com .0 ou ,0
                        t = s.replace(' ', '')
                        if re.fullmatch(r"\d+[\.,]0+", t):
                            return re.split(r"[\.,]", t)[0]
                        # Mantém inteiros com zeros à esquerda
                        if re.fullmatch(r"\d+", t):
                            return t
                        # Caso geral: mantém texto original, padronizando caixa alta
                        return s.upper()

                    df_norm['material'] = df_norm['material'].apply(_normalize_material_value)
                    print(f"🔍 DEBUG: material produtos cotados normalizado (string safe)")
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
                # material é desejável, mas se coluna existir exigimos valor
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
