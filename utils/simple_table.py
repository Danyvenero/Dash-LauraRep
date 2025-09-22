#!/usr/bin/env python3
"""
Solução Simples para Substituir dash_table
Evita problemas de carregamento assíncrono
"""

import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

def create_simple_table(data=None, columns=None, id=None, **kwargs):
    """
    Cria uma tabela simples usando Bootstrap sem dependências do dash_table
    """
    if data is None:
        data = []
    
    if columns is None:
        columns = []
    
    # Se data é um DataFrame, converte para lista de dicionários
    if isinstance(data, pd.DataFrame):
        if not columns:
            columns = [{"name": col, "id": col} for col in data.columns]
        data = data.to_dict('records')
    
    # Cria cabeçalho da tabela
    header = html.Thead([
        html.Tr([
            html.Th(col.get("name", col.get("id", ""))) 
            for col in columns
        ])
    ])
    
    # Cria linhas da tabela
    rows = []
    for row_data in data[:50]:  # Limita a 50 linhas para performance
        cells = []
        for col in columns:
            col_id = col.get("id", "")
            value = row_data.get(col_id, "")
            
            # Formata valores numéricos
            if isinstance(value, (int, float)):
                if abs(value) >= 1000:
                    value = f"{value:,.0f}"
                else:
                    value = f"{value:.2f}"
            
            cells.append(html.Td(str(value)))
        rows.append(html.Tr(cells))
    
    body = html.Tbody(rows)
    
    # Retorna tabela Bootstrap responsiva
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Table([header, body], 
                         striped=True, 
                         bordered=True, 
                         hover=True, 
                         responsive=True,
                         size="sm")
            ], style={"overflowX": "auto", "maxHeight": "400px"})
        ])
    ], id=id)

def create_products_table_safe():
    """Cria uma tabela de produtos segura sem dash_table"""
    sample_data = [
        {"produto": "Produto A", "vendas": 1250, "margem": "15%", "categoria": "Cat 1"},
        {"produto": "Produto B", "vendas": 980, "margem": "12%", "categoria": "Cat 2"},
        {"produto": "Produto C", "vendas": 750, "margem": "18%", "categoria": "Cat 1"},
        {"produto": "Produto D", "vendas": 650, "margem": "14%", "categoria": "Cat 3"},
        {"produto": "Produto E", "vendas": 540, "margem": "16%", "categoria": "Cat 2"},
    ]
    
    columns = [
        {"name": "Produto", "id": "produto"},
        {"name": "Vendas", "id": "vendas"},
        {"name": "Margem", "id": "margem"},
        {"name": "Categoria", "id": "categoria"}
    ]
    
    return create_simple_table(data=sample_data, columns=columns, id="products-table-safe")

if __name__ == "__main__":
    print("✅ Módulo simple_table carregado com sucesso!")