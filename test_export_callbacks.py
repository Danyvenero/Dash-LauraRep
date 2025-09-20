#!/usr/bin/env python3
"""
Teste específico para verificar se os callbacks de exportação estão funcionando
"""

import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_export_callbacks():
    """Testa se os callbacks de exportação estão registrados"""
    
    print("🔍 TESTE DOS CALLBACKS DE EXPORTAÇÃO")
    print("="*50)
    
    try:
        # Simula dados de teste
        test_suggestions_data = [
            {
                'material': '12345',
                'produto': 'Produto Teste A',
                'quantidade_sugerida': 10,
                'valor_estimado': 1000.0,
                'confianca': 85.5,
                'classificacao': 'AX',
                'prob_recompra': 0.75
            },
            {
                'material': '67890',
                'produto': 'Produto Teste B',
                'quantidade_sugerida': 5,
                'valor_estimado': 500.0,
                'confianca': 72.3,
                'classificacao': 'BY',
                'prob_recompra': 0.65
            }
        ]
        
        print(f"✅ Dados de teste criados: {len(test_suggestions_data)} registros")
        
        # Testa função de Excel
        print("\n📊 Testando função _create_excel_export...")
        from webapp.purchase_suggestions_callbacks import _create_excel_export
        
        excel_path = _create_excel_export(test_suggestions_data)
        
        if excel_path and os.path.exists(excel_path):
            print(f"✅ Excel criado com sucesso: {excel_path}")
            os.remove(excel_path)  # Remove arquivo de teste
            print("✅ Arquivo de teste removido")
        else:
            print("❌ Erro ao criar Excel")
        
        # Testa função de PDF
        print("\n📄 Testando função _create_pdf_report...")
        from webapp.purchase_suggestions_callbacks import _create_pdf_report
        
        pdf_path = _create_pdf_report(test_suggestions_data)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ PDF criado com sucesso: {pdf_path}")
            os.remove(pdf_path)  # Remove arquivo de teste
            print("✅ Arquivo de teste removido")
        else:
            print("❌ Erro ao criar PDF")
        
        # Testa callbacks de exportação
        print("\n🔧 Testando callbacks de exportação...")
        from webapp.purchase_suggestions_callbacks import export_excel, export_pdf
        
        # Teste callback Excel
        try:
            disabled, children, alert, is_open = export_excel(1, test_suggestions_data)
            print(f"✅ Callback export_excel executado")
            print(f"   Disabled: {disabled}")
            print(f"   Alert open: {is_open}")
        except Exception as e:
            print(f"❌ Erro no callback export_excel: {e}")
        
        # Teste callback PDF
        try:
            disabled, children, alert, is_open = export_pdf(1, test_suggestions_data)
            print(f"✅ Callback export_pdf executado")
            print(f"   Disabled: {disabled}")
            print(f"   Alert open: {is_open}")
        except Exception as e:
            print(f"❌ Erro no callback export_pdf: {e}")
        
    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_export_callbacks()