#!/usr/bin/env python3
"""
Teste para diagnóstico dos botões de exportação
"""

import os
import pandas as pd
import sys

def test_export_dependencies():
    """Testa se as dependências necessárias estão instaladas"""
    
    print("🔍 TESTE DE DEPENDÊNCIAS PARA EXPORTAÇÃO")
    print("="*50)
    
    # Teste Excel
    try:
        import openpyxl
        print("✅ openpyxl: Instalado")
        print(f"   Versão: {openpyxl.__version__}")
    except ImportError:
        print("❌ openpyxl: NÃO INSTALADO")
        print("   Execute: pip install openpyxl")
    
    # Teste PDF
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import reportlab
        print("✅ reportlab: Instalado")
        print(f"   Versão: {reportlab.Version}")
    except ImportError:
        print("❌ reportlab: NÃO INSTALADO")
        print("   Execute: pip install reportlab")
    
    # Teste pasta Downloads
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(downloads_path):
        print(f"✅ Pasta Downloads: {downloads_path}")
        if os.access(downloads_path, os.W_OK):
            print("✅ Permissão de escrita: OK")
        else:
            print("❌ Permissão de escrita: NEGADA")
    else:
        print(f"❌ Pasta Downloads não encontrada: {downloads_path}")
    
    # Teste criação de arquivo simples
    try:
        test_file = os.path.join(downloads_path, "teste_export.txt")
        with open(test_file, 'w') as f:
            f.write("Teste")
        os.remove(test_file)
        print("✅ Criação de arquivo: OK")
    except Exception as e:
        print(f"❌ Criação de arquivo: ERRO - {e}")

def test_excel_creation():
    """Testa criação de Excel"""
    print("\n📊 TESTE DE CRIAÇÃO EXCEL")
    print("="*30)
    
    try:
        import pandas as pd
        from datetime import datetime
        
        # Dados de teste
        test_data = [
            {
                'material': '12345',
                'produto': 'Produto Teste',
                'quantidade_sugerida': 10,
                'valor_estimado': 1000.0,
                'confianca': 85.5,
                'classificacao': 'AX'
            }
        ]
        
        df = pd.DataFrame(test_data)
        
        # Tenta criar Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"teste_excel_{timestamp}.xlsx"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads_path, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Teste', index=False)
        
        print(f"✅ Excel criado: {filepath}")
        
        # Remove arquivo de teste
        if os.path.exists(filepath):
            os.remove(filepath)
            print("✅ Arquivo de teste removido")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação Excel: {e}")
        return False

def test_pdf_creation():
    """Testa criação de PDF"""
    print("\n📄 TESTE DE CRIAÇÃO PDF")
    print("="*25)
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from datetime import datetime
        
        # Tenta criar PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"teste_pdf_{timestamp}.pdf"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Conteúdo simples
        story.append(Paragraph("TESTE DE PDF", styles['Title']))
        story.append(Paragraph("Este é um teste de criação de PDF.", styles['Normal']))
        
        doc.build(story)
        
        print(f"✅ PDF criado: {filepath}")
        
        # Remove arquivo de teste
        if os.path.exists(filepath):
            os.remove(filepath)
            print("✅ Arquivo de teste removido")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação PDF: {e}")
        return False

if __name__ == "__main__":
    test_export_dependencies()
    excel_ok = test_excel_creation()
    pdf_ok = test_pdf_creation()
    
    print(f"\n📋 RESUMO:")
    print(f"   Excel: {'✅ OK' if excel_ok else '❌ ERRO'}")
    print(f"   PDF: {'✅ OK' if pdf_ok else '❌ ERRO'}")