# webapp/callbacks_uploads.py

from dash import Output, Input, State, html
import dash_bootstrap_components as dbc
from flask import session
import hashlib

from webapp import app
from utils import data_loader, db

@app.callback(
    Output('upload-msgs', 'children', allow_duplicate=True),
    Input('upload-vendas', 'contents'),
    Input('upload-vendas', 'filename'),
    prevent_initial_call=True
)
def on_upload_vendas(contents_list, filenames_list):
    if not contents_list or not filenames_list:
        return dbc.Alert("Erro no upload. Por favor, tente selecionar o arquivo novamente.", color="warning")
    
    user_id = session.get('user_id')
    if not user_id: 
        return dbc.Alert("Sessão inválida.", color="danger")

    messages = []
    for contents, filename in zip(contents_list, filenames_list):
        if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
            messages.append(dbc.Alert(f"Erro em '{filename}': Apenas arquivos .xlsx ou .xls são permitidos.", color="danger"))
            continue

        try:
            file_io = data_loader.parse_upload_content(contents)
            fingerprint = data_loader.generate_fingerprint(file_io)

            if db.check_raw_fingerprint_exists(fingerprint, 'raw_vendas'):
                messages.append(dbc.Alert(f"O arquivo '{filename}' já foi carregado.", color="warning"))
                continue
            
            df = data_loader.read_raw_vendas(file_io)
            rows_inserted = db.insert_raw_df(df, 'raw_vendas', filename, fingerprint, user_id)

            if rows_inserted > 0:
                messages.append(dbc.Alert(f"Arquivo de vendas '{filename}' carregado! {rows_inserted} registros brutos salvos.", color="success"))
            else:
                messages.append(dbc.Alert(f"Erro ao salvar dados brutos do arquivo '{filename}'.", color="danger"))
        except Exception as e:
            messages.append(dbc.Alert(f"Erro ao processar o arquivo de vendas '{filename}': {e}", color="danger"))
            
    return messages


@app.callback(
    Output('upload-msgs', 'children', allow_duplicate=True),
    Input('upload-cotacoes', 'contents'),
    Input('upload-cotacoes', 'filename'),
    prevent_initial_call=True
)
def on_upload_cotacoes(contents_list, filenames_list):
    if not contents_list or not filenames_list:
        return dbc.Alert("Erro no upload. Por favor, tente selecionar os arquivos novamente.", color="warning")
    
    user_id = session.get('user_id')
    if not user_id: 
        return dbc.Alert("Sessão inválida.", color="danger")
    
    messages = []
    for contents, filename in zip(contents_list, filenames_list):
        try:
            # --- CORREÇÃO AQUI: A ordem das operações foi ajustada ---

            # 1. Processa o conteúdo do arquivo PRIMEIRO para criar o file_io
            file_io = data_loader.parse_upload_content(contents)
            
            # 2. Identifica o tipo de arquivo e chama a função de leitura correta
            table_name = None
            df = None
            if 'materiais_cotados' in filename:
                table_name = 'raw_materiais_cotados'
                df = data_loader.read_raw_materiais_cotados(file_io)
            elif any(char.isdigit() for char in filename) and ('.xls' in filename or '.xlsx' in filename):
                table_name = 'raw_propostas_anuais'
                df = data_loader.read_raw_propostas_anuais(file_io)
            else:
                messages.append(dbc.Alert(f"Arquivo '{filename}' não reconhecido e foi ignorado.", color="warning"))
                continue
            
            # 3. Agora que temos o file_io, podemos gerar o fingerprint
            fingerprint = data_loader.generate_fingerprint(file_io)

            if db.check_raw_fingerprint_exists(fingerprint, table_name):
                messages.append(dbc.Alert(f"O arquivo '{filename}' já foi carregado.", color="warning"))
                continue
            
            # 4. Insere o DataFrame (df) que já foi lido e processado
            rows_inserted = db.insert_raw_df(df, table_name, filename, fingerprint, user_id)
            
            if rows_inserted > 0:
                messages.append(dbc.Alert(f"Arquivo '{filename}' carregado! {rows_inserted} registros brutos salvos em '{table_name}'.", color="success"))
            else:
                messages.append(dbc.Alert(f"Erro ao salvar dados brutos do arquivo '{filename}'.", color="danger"))

        except Exception as e:
            messages.append(dbc.Alert(f"Erro ao processar '{filename}': {e}", color="danger"))
            
    return messages