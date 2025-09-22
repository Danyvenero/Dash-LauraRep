#!/usr/bin/env python3
"""
Teste direto da função process_produtos_analytics
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.produtos_table_callback import process_produtos_analytics
from db_manager import Database
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_produtos_analytics():
    """Testa a função process_produtos_analytics diretamente"""
    try:
        # Inicializar banco de dados
        db = Database()
        
        # Testar a função
        logger.info("Testando process_produtos_analytics...")
        result = process_produtos_analytics(top_n=10)
        
        logger.info(f"Resultado: {len(result)} produtos retornados")
        if not result.empty:
            logger.info(f"Colunas: {list(result.columns)}")
            logger.info(f"Primeiros produtos:\n{result.head()}")
        else:
            logger.warning("DataFrame vazio retornado")
            
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_produtos_analytics()