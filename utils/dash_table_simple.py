#!/usr/bin/env python3
"""
Correção Simples para Erro de Carregamento do dash_table
Versão simplificada para evitar timeout durante import
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import logging

logger = logging.getLogger(__name__)

def create_safe_data_table(table_id, columns, data=None, **kwargs):
    """
    Cria um DataTable com fallback em caso de erro de carregamento
    Versão simplificada para evitar timeout
    """
    try:
        # Import localizado para evitar problemas de carregamento
        from dash import dash_table
        
        # Configurações mínimas para evitar problemas
        config = {
            "id": table_id,
            "columns": columns,
            "data": data or [],
            "page_size": 10,  # Reduzido para melhor performance
            "page_action": "native",
            **kwargs
        }
        
        return dash_table.DataTable(**config)
        
    except Exception as e:
        logger.warning(f"Fallback para tabela HTML: {e}")
        return create_simple_table_fallback(table_id, columns, data)

def create_simple_table_fallback(table_id, columns, data):
    """
    Tabela HTML simples como fallback
    """
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th(col.get('name', col.get('id', 'Coluna'))) 
                for col in columns
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td("Carregando dados...") 
                for _ in columns
            ]) if not data else
            html.Tr([
                html.Td(str(row.get(col.get('id', ''), '-')))
                for col in columns
            ]) for row in (data or [])[:10]  # Limite para performance
        ])
    ], id=table_id, striped=True, bordered=True, hover=True, responsive=True)

def create_products_error_message():
    """
    Mensagem de erro amigável para problemas com Mix de Produtos
    """
    return dbc.Alert([
        html.H4([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Problema de Carregamento Detectado"
        ], className="alert-heading"),
        html.P([
            "Houve um problema ao carregar os componentes da página Mix de Produtos. ",
            "Isso geralmente acontece devido a problemas de rede ou cache do navegador."
        ]),
        html.Hr(),
        html.H6("Soluções rápidas:"),
        html.Ul([
            html.Li("Recarregue a página (F5 ou Ctrl+R)"),
            html.Li("Limpe o cache do navegador (Ctrl+Shift+Delete)"),
            html.Li("Tente em modo privado/incógnito")
        ]),
        dbc.Button(
            [html.I(className="fas fa-home me-1"), "Voltar ao Dashboard Principal"],
            href="/",
            color="primary"
        )
    ], color="warning", className="mt-3")

if __name__ == "__main__":
    print("✅ Módulo dash_table_fix simplificado carregado!")