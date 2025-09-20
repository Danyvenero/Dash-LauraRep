#!/usr/bin/env python3
"""
Teste da funcionalidade de geração de PDF
"""

def test_pdf_generation():
    """Testa a criação de PDF com dados de exemplo"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from datetime import datetime
        import os
        
        print("✅ Bibliotecas importadas com sucesso")
        
        # Dados de exemplo
        suggestions_data = [
            {
                'material': 'MAT001',
                'produto': 'Produto Teste 1',
                'quantidade_sugerida': 10,
                'valor_estimado': 1500.50,
                'classificacao_abc': 'A',
                'confianca': 85.5
            },
            {
                'material': 'MAT002',
                'produto': 'Produto Teste 2',
                'quantidade_sugerida': 5,
                'valor_estimado': 750.25,
                'classificacao_abc': 'B',
                'confianca': 72.3
            }
        ]
        
        print("✅ Dados de exemplo criados")
        
        # Define nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Teste_PDF_{timestamp}.pdf"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads_path, filename)
        
        print(f"📁 Caminho do arquivo: {filepath}")
        
        # Cria documento
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        print("✅ Documento criado")
        
        # Estilo customizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Título
        story.append(Paragraph("TESTE DE RELATÓRIO PDF", title_style))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        print("✅ Título adicionado")
        
        # Resumo
        story.append(Paragraph("RESUMO DO TESTE", styles['Heading2']))
        resumo_text = "• Total de Produtos: 2<br/>• Valor Total: R$ 2.250,75<br/>• Teste realizado com sucesso"
        story.append(Paragraph(resumo_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        print("✅ Resumo adicionado")
        
        # Tabela
        story.append(Paragraph("DADOS DE TESTE", styles['Heading2']))
        
        table_data = [['Material', 'Produto', 'Qtd', 'Valor', 'ABC', 'Conf.']]
        
        for item in suggestions_data:
            table_data.append([
                str(item.get('material', ''))[:12],
                str(item.get('produto', ''))[:25],
                str(int(item.get('quantidade_sugerida', 0))),
                f"R$ {item.get('valor_estimado', 0):,.2f}",
                str(item.get('classificacao_abc', '')),
                f"{item.get('confianca', 0):.1f}%"
            ])
        
        # Cria tabela
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        
        print("✅ Tabela adicionada")
        
        # Constrói PDF
        doc.build(story)
        
        print(f"✅ PDF criado com sucesso: {filepath}")
        
        # Verifica se o arquivo foi criado
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"📄 Arquivo criado: {file_size} bytes")
            return True, filepath
        else:
            print("❌ Arquivo não foi criado")
            return False, None
            
    except Exception as e:
        print(f"❌ Erro durante criação do PDF: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

if __name__ == "__main__":
    print("🔧 Testando criação de PDF...")
    success, result = test_pdf_generation()
    
    if success:
        print(f"🎉 Teste concluído com sucesso! Arquivo: {result}")
    else:
        print(f"💥 Teste falhou: {result}")