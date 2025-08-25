# utils/data_loader.py

import pandas as pd
import io
import base64
import hashlib

def parse_upload_content(contents):
    """Decodifica o conteúdo de um arquivo carregado pelo dcc.Upload."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return io.BytesIO(decoded)

def generate_fingerprint(file_bytes_io):
    """Gera uma assinatura MD5 para o conteúdo do arquivo."""
    file_bytes_io.seek(0)
    file_bytes = file_bytes_io.read()
    file_bytes_io.seek(0)
    return hashlib.md5(file_bytes).hexdigest()

def read_raw_vendas(file_bytes_io):
    """Lê um arquivo de vendas e retorna um DataFrame com todas as colunas da planilha."""
    df = pd.read_excel(file_bytes_io)
    return df

def read_raw_materiais_cotados(file_bytes_io):
    """Lê um arquivo de materiais cotados e retorna um DataFrame com as colunas relevantes."""
    df = pd.read_excel(file_bytes_io)
    # Lista definitiva de colunas para materiais cotados
    expected_cols = [
        "Cotação",
        "Cod. Cliente",
        "Cliente",
        "Material",
        "Descrição",
        "Quantidade",
        "Preço Líquido Total"
    ]
    # Filtra o DataFrame, mantendo apenas as colunas da lista que existem na planilha
    return df[[col for col in expected_cols if col in df.columns]]

def read_raw_propostas_anuais(file_bytes_io):
    """Lê um arquivo de propostas anuais e retorna um DataFrame com as colunas relevantes."""
    df = pd.read_excel(file_bytes_io)
    # Lista definitiva de colunas para propostas anuais
    expected_cols = [
        "Número da Cotação",
        "Número da Revisão",
        "Código do Cliente",
        "Nome do Cliente",
        "Data de Criação",
        "Status da Cotação",
        "Valor Total"
    ]
    # Filtra o DataFrame, mantendo apenas as colunas da lista que existem na planilha
    return df[[col for col in expected_cols if col in df.columns]]