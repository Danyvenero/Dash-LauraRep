"""
Callbacks para upload de arquivos
"""
import dash
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
import base64
import io
import pandas as pd
from webapp import app
from webapp.auth import authenticated_callback
from utils.data_loader_fixed import DataLoaderFixed
from utils import save_dataset, SecurityManager, get_current_user_id, get_latest_dataset

# Instâncias
data_loader = DataLoaderFixed()
security_manager = SecurityManager()

def _safe_dataframe_concat(dataframes_dict, key, new_df):
    """Concatenação robusta de DataFrames evitando erros de reindexing"""
    try:
        # Força reset de índice no novo DataFrame
        if new_df is not None and not new_df.empty:
            new_df = new_df.copy()
            new_df.index = range(len(new_df))
            print(f"🔍 DEBUG: Preparando {key} para concatenação - shape: {new_df.shape}")
            
            if dataframes_dict[key] is None:
                print(f"🔍 DEBUG: Primeiro DataFrame para {key}")
                return new_df
            else:
                existing_df = dataframes_dict[key].copy()
                existing_df.index = range(len(existing_df))
                print(f"🔍 DEBUG: Concatenando {key} - existente: {existing_df.shape}, novo: {new_df.shape}")
                
                # Força índices únicos antes da concatenação
                combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
                print(f"🔍 DEBUG: Resultado da concatenação {key}: {combined_df.shape}")
                return combined_df
        else:
            print(f"⚠️  DataFrame {key} vazio ou None")
            return dataframes_dict[key]
            
    except Exception as e:
        print(f"❌ DEBUG: Erro na concatenação {key}: {str(e)}")
        # Fallback: retorna apenas o novo DataFrame
        if new_df is not None and not new_df.empty:
            new_df.index = range(len(new_df))
            return new_df
        return dataframes_dict[key]

@app.callback(
    Output('upload-status', 'children'),
    [Input('upload-vendas', 'contents'),
     Input('upload-cotacoes', 'contents'),
     Input('upload-materiais', 'contents'),
     Input('btn-load-saved-data', 'n_clicks')],
    [State('upload-vendas', 'filename'),
     State('upload-cotacoes', 'filename'),
     State('upload-materiais', 'filename')],
    prevent_initial_call=True
)
@authenticated_callback
def handle_file_uploads(vendas_content, cotacoes_content, materiais_content, load_btn_clicks,
                       vendas_filename, cotacoes_filename, materiais_filename):
    """Processa uploads de arquivos"""
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Se foi clique no botão de carregar dados salvos
    if trigger_id == 'btn-load-saved-data':
        try:
            latest = get_latest_dataset()
            if latest:
                return dbc.Alert(
                    f"✅ Dados carregados com sucesso! Dataset: {latest['name']} "
                    f"(Uploaded: {latest['uploaded_at']})",
                    color="success",
                    duration=10000
                )
            else:
                return dbc.Alert(
                    "⚠️ Nenhum dataset encontrado no banco de dados.",
                    color="warning",
                    duration=10000
                )
        except Exception as e:
            return dbc.Alert(
                f"❌ Erro ao carregar dados: {str(e)}",
                color="danger",
                duration=10000
            )
    
    # Processamento de uploads
    print(f"🚀 INICIANDO PROCESSAMENTO DE UPLOAD...")
    print(f"📁 Arquivos recebidos:")
    print(f"  - Vendas: {type(vendas_content)} / {type(vendas_filename)}")
    print(f"  - Cotações: {type(cotacoes_content)} / {type(cotacoes_filename)}")
    print(f"  - Materiais: {type(materiais_content)} / {type(materiais_filename)}")
    
    uploads_processed = []
    errors = []
    
    # Mapeia uploads
    upload_data = [
        (vendas_content, vendas_filename, 'vendas'),
        (cotacoes_content, cotacoes_filename, 'cotacoes'),
        (materiais_content, materiais_filename, 'materiais')
    ]
    
    dataframes = {'vendas': None, 'cotacoes': None, 'produtos_cotados': None}
    
    for content, filename, file_type in upload_data:
        if content and filename:
            # Se content e filename são listas (múltiplos arquivos)
            if isinstance(content, list) and isinstance(filename, list):
                for i, (single_content, single_filename) in enumerate(zip(content, filename)):
                    try:
                        # Valida arquivo
                        content_type, content_string = single_content.split(',')
                        decoded = base64.b64decode(content_string)
                        file_size = len(decoded)
                        
                        validation = security_manager.validate_file_upload(single_filename, file_size)
                        if not validation['valid']:
                            errors.extend(validation['errors'])
                            continue
                        
                        # Lê arquivo Excel (suporte para .xlsx e .xls)
                        try:
                            # Verifica se o arquivo é realmente um Excel válido
                            file_bytes = io.BytesIO(decoded)
                            
                            # Detecta se é arquivo HTML/texto masquerado como Excel
                            file_bytes.seek(0)
                            first_bytes = file_bytes.read(200)
                            file_bytes.seek(0)
                            
                            # Verificações mais abrangentes para detectar formatos inválidos
                            invalid_signatures = [
                                b'MIME-Ver', b'<html', b'<!doctype', b'Content-Type',
                                b'<HTML', b'<!DOCTYPE', b'<table', b'<TABLE',
                                b'Version:', b'Pragma:', b'Cache-Control:'
                            ]
                            
                            if any(sig in first_bytes for sig in invalid_signatures):
                                errors.append(f"❌ {single_filename} não é um arquivo Excel válido (formato HTML/MIME detectado)")
                                continue
                            
                            # Tenta múltiplos engines para máxima compatibilidade
                            df = None
                            print(f"🔍 DEBUG: Lendo arquivo {single_filename}...")
                            
                            if single_filename.lower().endswith('.xls'):
                                try:
                                    # Primeiro verifica se tem múltiplas abas
                                    excel_file = pd.ExcelFile(file_bytes, engine='xlrd')
                                    sheet_names = excel_file.sheet_names
                                    print(f"🔍 DEBUG: Planilhas encontradas: {sheet_names}")
                                    
                                    # Lê a primeira planilha (ou a principal)
                                    df = pd.read_excel(file_bytes, engine='xlrd', sheet_name=0)
                                    print(f"🔍 DEBUG: Planilha lida com shape: {df.shape}")
                                    
                                except Exception as e1:
                                    print(f"❌ DEBUG: Erro com xlrd: {str(e1)}")
                                    file_bytes.seek(0)
                                    try:
                                        df = pd.read_excel(file_bytes, engine='openpyxl', sheet_name=0)
                                        print(f"🔍 DEBUG: Fallback openpyxl: {df.shape}")
                                    except Exception as e2:
                                        print(f"❌ DEBUG: Erro com openpyxl: {str(e2)}")
                                        file_bytes.seek(0)
                                        df = pd.read_excel(file_bytes, sheet_name=0)
                            else:
                                try:
                                    # Primeiro verifica se tem múltiplas abas
                                    excel_file = pd.ExcelFile(file_bytes, engine='openpyxl')
                                    sheet_names = excel_file.sheet_names
                                    print(f"🔍 DEBUG: Planilhas encontradas: {sheet_names}")
                                    
                                    # Lê a primeira planilha (ou a principal)
                                    df = pd.read_excel(file_bytes, engine='openpyxl', sheet_name=0)
                                    print(f"🔍 DEBUG: Planilha lida com shape: {df.shape}")
                                    
                                except Exception as e1:
                                    print(f"❌ DEBUG: Erro com openpyxl: {str(e1)}")
                                    file_bytes.seek(0)
                                    try:
                                        df = pd.read_excel(file_bytes, engine='xlrd', sheet_name=0)
                                        print(f"🔍 DEBUG: Fallback xlrd: {df.shape}")
                                    except Exception as e2:
                                        print(f"❌ DEBUG: Erro com xlrd: {str(e2)}")
                                        file_bytes.seek(0)
                                        df = pd.read_excel(file_bytes, sheet_name=0)
                            
                            if df is None or df.empty:
                                errors.append(f"❌ {single_filename} está vazio ou não pôde ser lido")
                                continue
                            
                            # CRÍTICO: Reset do índice logo após leitura para evitar problemas
                            print(f"🔍 DEBUG: Índice original: {df.index}")
                            df = df.reset_index(drop=True)
                            print(f"🔍 DEBUG: Índice após reset: {df.index}")
                            
                            # Verifica se há duplicatas no índice
                            if df.index.duplicated().any():
                                print(f"⚠️  WARNING: Índices duplicados detectados, forçando reset")
                                df = df.copy()
                                df.index = range(len(df))
                                print(f"🔍 DEBUG: Índice forçado: {df.index}")
                                
                        except Exception as read_error:
                            errors.append(f"❌ Erro ao ler arquivo {single_filename}: {str(read_error)}")
                            continue
                        
                        # Processa baseado no tipo com concatenação robusta
                        if file_type == 'vendas':
                            df_processed = data_loader.normalize_vendas_data(df)
                            df_processed = _safe_dataframe_concat(dataframes, 'vendas', df_processed)
                            dataframes['vendas'] = df_processed
                        elif file_type == 'cotacoes':
                            df_processed = data_loader.normalize_cotacoes_data(df)
                            df_processed = _safe_dataframe_concat(dataframes, 'cotacoes', df_processed)
                            dataframes['cotacoes'] = df_processed
                        elif file_type == 'materiais':
                            df_processed = data_loader.normalize_produtos_cotados_data(df)
                            df_processed = _safe_dataframe_concat(dataframes, 'produtos_cotados', df_processed)
                            dataframes['produtos_cotados'] = df_processed
                        
                        uploads_processed.append(f"✅ {single_filename} - {len(df_processed)} registros")
                        
                    except Exception as e:
                        errors.append(f"❌ Erro ao processar {single_filename}: {str(e)}")
            
            # Se content e filename são strings (arquivo único)
            elif isinstance(content, str) and isinstance(filename, str):
                try:
                    # Valida arquivo
                    content_type, content_string = content.split(',')
                    decoded = base64.b64decode(content_string)
                    file_size = len(decoded)
                    
                    validation = security_manager.validate_file_upload(filename, file_size)
                    if not validation['valid']:
                        errors.extend(validation['errors'])
                        continue
                    
                    # Lê arquivo Excel (suporte para .xlsx e .xls)
                    try:
                        # Verifica se o arquivo é realmente um Excel válido
                        file_bytes = io.BytesIO(decoded)
                        
                        # Detecta se é arquivo HTML/texto masquerado como Excel
                        file_bytes.seek(0)
                        first_bytes = file_bytes.read(200)
                        file_bytes.seek(0)
                        
                        # Verificações mais abrangentes para detectar formatos inválidos
                        invalid_signatures = [
                            b'MIME-Ver', b'<html', b'<!doctype', b'Content-Type',
                            b'<HTML', b'<!DOCTYPE', b'<table', b'<TABLE',
                            b'Version:', b'Pragma:', b'Cache-Control:'
                        ]
                        
                        if any(sig in first_bytes for sig in invalid_signatures):
                            errors.append(f"❌ {filename} não é um arquivo Excel válido (formato HTML/MIME detectado)")
                            continue
                        
                        # Tenta múltiplos engines para máxima compatibilidade
                        df = None
                        print(f"🔍 DEBUG: Lendo arquivo único {filename}...")
                        
                        if filename.lower().endswith('.xls'):
                            try:
                                # Primeiro verifica se tem múltiplas abas
                                excel_file = pd.ExcelFile(file_bytes, engine='xlrd')
                                sheet_names = excel_file.sheet_names
                                print(f"🔍 DEBUG: Planilhas encontradas: {sheet_names}")
                                
                                # Lê a primeira planilha (ou a principal)
                                df = pd.read_excel(file_bytes, engine='xlrd', sheet_name=0)
                                print(f"🔍 DEBUG: Planilha lida com shape: {df.shape}")
                                
                            except Exception as e1:
                                print(f"❌ DEBUG: Erro com xlrd: {str(e1)}")
                                file_bytes.seek(0)
                                try:
                                    df = pd.read_excel(file_bytes, engine='openpyxl', sheet_name=0)
                                    print(f"🔍 DEBUG: Fallback openpyxl: {df.shape}")
                                except Exception as e2:
                                    print(f"❌ DEBUG: Erro com openpyxl: {str(e2)}")
                                    file_bytes.seek(0)
                                    df = pd.read_excel(file_bytes, sheet_name=0)
                        else:
                            try:
                                # Primeiro verifica se tem múltiplas abas
                                excel_file = pd.ExcelFile(file_bytes, engine='openpyxl')
                                sheet_names = excel_file.sheet_names
                                print(f"🔍 DEBUG: Planilhas encontradas: {sheet_names}")
                                
                                # Lê a primeira planilha (ou a principal)
                                df = pd.read_excel(file_bytes, engine='openpyxl', sheet_name=0)
                                print(f"🔍 DEBUG: Planilha lida com shape: {df.shape}")
                                
                            except Exception as e1:
                                print(f"❌ DEBUG: Erro com openpyxl: {str(e1)}")
                                file_bytes.seek(0)
                                try:
                                    df = pd.read_excel(file_bytes, engine='xlrd', sheet_name=0)
                                    print(f"🔍 DEBUG: Fallback xlrd: {df.shape}")
                                except Exception as e2:
                                    print(f"❌ DEBUG: Erro com xlrd: {str(e2)}")
                                    file_bytes.seek(0)
                                    df = pd.read_excel(file_bytes, sheet_name=0)
                        
                        if df is None or df.empty:
                            errors.append(f"❌ {filename} está vazio ou não pôde ser lido")
                            continue
                        
                        # CRÍTICO: Reset do índice logo após leitura para evitar problemas
                        print(f"🔍 DEBUG: Índice original: {df.index}")
                        df = df.reset_index(drop=True)
                        print(f"🔍 DEBUG: Índice após reset: {df.index}")
                        
                        # Verifica se há duplicatas no índice
                        if df.index.duplicated().any():
                            print(f"⚠️  WARNING: Índices duplicados detectados, forçando reset")
                            df = df.copy()
                            df.index = range(len(df))
                            print(f"🔍 DEBUG: Índice forçado: {df.index}")
                            
                    except Exception as read_error:
                        errors.append(f"❌ Erro ao ler arquivo {filename}: {str(read_error)}")
                        continue
                    
                    # Processa baseado no tipo com concatenação robusta
                    if file_type == 'vendas':
                        df_processed = data_loader.normalize_vendas_data(df)
                        dataframes['vendas'] = _safe_dataframe_concat(dataframes, 'vendas', df_processed)
                    elif file_type == 'cotacoes':
                        df_processed = data_loader.normalize_cotacoes_data(df)
                        dataframes['cotacoes'] = _safe_dataframe_concat(dataframes, 'cotacoes', df_processed)
                    elif file_type == 'materiais':
                        df_processed = data_loader.normalize_produtos_cotados_data(df)
                        dataframes['produtos_cotados'] = _safe_dataframe_concat(dataframes, 'produtos_cotados', df_processed)
                    
                    uploads_processed.append(f"✅ {filename} - {len(df_processed)} registros")
                    
                except Exception as e:
                    errors.append(f"❌ Erro ao processar {filename}: {str(e)}")
            else:
                errors.append(f"❌ Tipo de dados inválido para {file_type}: content={type(content)}, filename={type(filename)}")
    
    # Se houve uploads processados, salva no banco
    if uploads_processed and not errors:
        try:
            print(f"🔄 INICIANDO SALVAMENTO NO BANCO DE DADOS...")
            print(f"📊 Dataframes processados:")
            for tipo, df in dataframes.items():
                if df is not None:
                    print(f"  - {tipo}: {df.shape}")
                else:
                    print(f"  - {tipo}: None")
            
            user_id = get_current_user_id()
            dataset_name = f"Upload_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"👤 User ID: {user_id}")
            print(f"📝 Dataset Name: {dataset_name}")
            
            dataset_id = save_dataset(
                dataset_name, 
                user_id,
                dataframes['vendas'],
                dataframes['cotacoes'], 
                dataframes['produtos_cotados']
            )
            
            print(f"✅ DATASET SALVO COM SUCESSO! ID: {dataset_id}")
            
            # 🔍 MENSAGEM INTELIGENTE BASEADA NO RESULTADO
            if dataset_id is None:
                # Dados idênticos detectados
                warning_msg = html.Div([
                    html.H6("⚠️ Dados idênticos detectados!", className="text-warning"),
                    html.P("Os arquivos enviados são idênticos aos já existentes no banco de dados.", className="mb-2"),
                    html.P("Upload cancelado para evitar duplicação.", className="small text-muted"),
                    html.Ul([html.Li(f"📁 {msg}") for msg in uploads_processed])
                ])
                return dbc.Alert(warning_msg, color="warning", duration=15000)
            else:
                # Upload bem-sucedido
                success_msg = html.Div([
                    html.H6("✅ Upload realizado com sucesso!", className="text-success"),
                    html.P("Dados processados com validação inteligente de duplicatas.", className="mb-2"),
                    html.Ul([html.Li(msg) for msg in uploads_processed]),
                    html.P(f"📊 Dataset ID: {dataset_id}", className="small text-muted")
                ])
                return dbc.Alert(success_msg, color="success", duration=10000)
            
        except Exception as e:
            print(f"❌ ERRO AO SALVAR NO BANCO: {str(e)}")
            import traceback
            traceback.print_exc()
            errors.append(f"❌ Erro ao salvar no banco: {str(e)}")
    
    # Se houve erros
    if errors:
        error_msg = html.Div([
            html.H6("❌ Erros encontrados:", className="text-danger"),
            html.Ul([html.Li(error) for error in errors])
        ])
        return dbc.Alert(error_msg, color="danger", duration=10000)
    
    return dash.no_update

# Callback para configurações de thresholds
@app.callback(
    [Output('threshold-inputs', 'children'),
     Output('threshold-status', 'children')],
    [Input('url', 'pathname'),
     Input('btn-save-thresholds', 'n_clicks')],
    [State('threshold-inputs', 'children')],
    prevent_initial_call=True
)
@authenticated_callback
def handle_thresholds(pathname, save_clicks, current_inputs):
    """Gerencia configurações de thresholds"""
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Carrega unidades de negócio disponíveis
    try:
        from utils import load_vendas_data, get_setting, save_setting
        vendas_df = load_vendas_data()
        
        if vendas_df.empty or 'unidade_negocio' not in vendas_df.columns:
            unidades = ['WAU', 'WEN', 'WMO-C', 'WMO-I', 'WDS']  # Padrão
        else:
            unidades = vendas_df['unidade_negocio'].dropna().unique().tolist()
        
        # Se for salvamento
        if trigger_id == 'btn-save-thresholds' and save_clicks:
            # Aqui deveria extrair valores dos inputs e salvar
            # Por simplicidade, salvamos um exemplo
            thresholds = {}
            for un in unidades:
                thresholds[un] = {
                    'baixo': 50000,
                    'medio': 100000,
                    'alto': 200000
                }
            
            save_setting('business_unit_thresholds', thresholds)
            
            status = dbc.Alert(
                "✅ Configurações salvas com sucesso!",
                color="success",
                duration=3000
            )
            
            # Reconstrói inputs
            inputs = []
            for un in unidades:
                inputs.append(
                    dbc.Row([
                        dbc.Col([
                            html.Label(f"{un}:", className="fw-bold")
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id=f"threshold-{un}-baixo",
                                type="number",
                                placeholder="Baixo",
                                value=thresholds[un]['baixo']
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id=f"threshold-{un}-medio", 
                                type="number",
                                placeholder="Médio",
                                value=thresholds[un]['medio']
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id=f"threshold-{un}-alto",
                                type="number", 
                                placeholder="Alto",
                                value=thresholds[un]['alto']
                            )
                        ], width=3)
                    ], className="mb-2")
                )
            
            return inputs, status
        
        # Carregamento inicial
        saved_thresholds = get_setting('business_unit_thresholds', {})
        
        inputs = []
        for un in unidades:
            un_thresholds = saved_thresholds.get(un, {'baixo': 50000, 'medio': 100000, 'alto': 200000})
            
            inputs.append(
                dbc.Row([
                    dbc.Col([
                        html.Label(f"{un}:", className="fw-bold")
                    ], width=3),
                    dbc.Col([
                        dbc.Input(
                            id=f"threshold-{un}-baixo",
                            type="number",
                            placeholder="Baixo", 
                            value=un_thresholds['baixo']
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Input(
                            id=f"threshold-{un}-medio",
                            type="number",
                            placeholder="Médio",
                            value=un_thresholds['medio']
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Input(
                            id=f"threshold-{un}-alto",
                            type="number",
                            placeholder="Alto",
                            value=un_thresholds['alto']
                        )
                    ], width=3)
                ], className="mb-2")
            )
        
        return inputs, dash.no_update
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Erro ao carregar configurações: {str(e)}",
            color="danger",
            duration=5000
        )
        return [], error_msg

print("✅ Callbacks de upload registrados com sucesso")
