#!/usr/bin/env python3
"""
Callback simples para testar o registro
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dash import callback, Input, Output, html
import logging

logger = logging.getLogger(__name__)

# Callback de teste mais simples
@callback(
    Output('filter-b2b-unidade-negocio', 'placeholder'),
    Input('filter-loader-interval', 'n_intervals'),
    prevent_initial_call=False
)
def test_simple_callback(n_intervals):
    """Callback simples só para testar se conseguimos registrar"""
    print(f"🧪 CALLBACK TESTE EXECUTADO! n_intervals={n_intervals}")
    logger.info(f"🧪 Callback de teste executado: {n_intervals}")
    return f"Teste executado {n_intervals} vezes"

print("✅ Callback de teste registrado")