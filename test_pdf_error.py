"""
Script para testar específicamente o erro do botão PDF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from webapp.purchase_suggestions_callbacks_simple import export_pdf, _create_pdf_report
import pandas as pd

# Dados de teste simulando uma sugestão
test_data = [
    {
        'material': '7505591',
        'produto': 'MOTOR 60HP 4P 225S/M WFF2',
        'cod_cliente': '929433',
        'cliente': 'mackllen industria e comercio de ma',
        'quantidade_sugerida': 8,
        'safety_stock': 0,
        'cobertura_dias': 60,
        'nivel_servico': 0.95,
        'demanda_media_mensal': 4.0,
        'classificacao_abc': 'A',
        'classificacao_xyz': 'X',
        'classificacao': 'AX',
        'coef_variacao': 0.0,
        'valor_medio_mensal': 86494,
        'valor_estimado': 0,
        'priority_score': 75.2,
        'prob_recompra': 0.85
    }
]

df_test = pd.DataFrame(test_data)

print("🔍 Testando função de criação de PDF...")

try:
    # Testa a função _create_pdf_report diretamente
    pdf_buffer = _create_pdf_report(df_test)
    print(f"✅ PDF criado com sucesso! Tamanho: {len(pdf_buffer.getvalue())} bytes")
    
    # Salva o arquivo para teste
    with open("teste_relatorio.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())
    print("✅ Arquivo teste_relatorio.pdf salvo com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao criar PDF: {e}")
    import traceback
    traceback.print_exc()