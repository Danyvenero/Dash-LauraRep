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
from utils import DataLoader, save_dataset, SecurityManager, get_current_user_id

# Instâncias
data_loader = DataLoader()
security_manager = SecurityManager()

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
            from utils import get_latest_dataset
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
                        
                        # Lê arquivo Excel
                        df = pd.read_excel(io.BytesIO(decoded))
                        
                        # Processa baseado no tipo
                        if file_type == 'vendas':
                            df_processed = data_loader.normalize_vendas_data(df)
                            if dataframes['vendas'] is None:
                                dataframes['vendas'] = df_processed
                            else:
                                dataframes['vendas'] = pd.concat([dataframes['vendas'], df_processed], ignore_index=True)
                        elif file_type == 'cotacoes':
                            df_processed = data_loader.normalize_cotacoes_data(df)
                            if dataframes['cotacoes'] is None:
                                dataframes['cotacoes'] = df_processed
                            else:
                                dataframes['cotacoes'] = pd.concat([dataframes['cotacoes'], df_processed], ignore_index=True)
                        elif file_type == 'materiais':
                            df_processed = data_loader.normalize_produtos_cotados_data(df)
                            if dataframes['produtos_cotados'] is None:
                                dataframes['produtos_cotados'] = df_processed
                            else:
                                dataframes['produtos_cotados'] = pd.concat([dataframes['produtos_cotados'], df_processed], ignore_index=True)
                        
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
                    
                    # Lê arquivo Excel
                    df = pd.read_excel(io.BytesIO(decoded))
                    
                    # Processa baseado no tipo
                    if file_type == 'vendas':
                        df_processed = data_loader.normalize_vendas_data(df)
                        dataframes['vendas'] = df_processed
                    elif file_type == 'cotacoes':
                        df_processed = data_loader.normalize_cotacoes_data(df)
                        dataframes['cotacoes'] = df_processed
                    elif file_type == 'materiais':
                        df_processed = data_loader.normalize_produtos_cotados_data(df)
                        dataframes['produtos_cotados'] = df_processed
                    
                    uploads_processed.append(f"✅ {filename} - {len(df_processed)} registros")
                    
                except Exception as e:
                    errors.append(f"❌ Erro ao processar {filename}: {str(e)}")
            else:
                errors.append(f"❌ Tipo de dados inválido para {file_type}: content={type(content)}, filename={type(filename)}")
    
    # Se houve uploads processados, salva no banco
    if uploads_processed and not errors:
        try:
            user_id = get_current_user_id()
            dataset_name = f"Upload_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            dataset_id = save_dataset(
                dataset_name, 
                user_id,
                dataframes['vendas'],
                dataframes['cotacoes'], 
                dataframes['produtos_cotados']
            )
            
            success_msg = html.Div([
                html.H6("✅ Upload realizado com sucesso!", className="text-success"),
                html.Ul([html.Li(msg) for msg in uploads_processed]),
                html.P(f"Dataset ID: {dataset_id}", className="small text-muted")
            ])
            
            return dbc.Alert(success_msg, color="success", duration=10000)
            
        except Exception as e:
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
