"""
Teste direto para debugar o erro do PDF
"""

import pandas as pd
from io import BytesIO
from datetime import datetime

# Testa se reportlab está funcionando
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    print("✅ reportlab importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar reportlab: {e}")
    exit()

def test_create_pdf_report(df_sugestoes):
    """Teste da função de criação de PDF"""
    try:
        buffer = BytesIO()
        
        # Configuração do documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container para elementos
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        
        # Título
        title = Paragraph("Relatório de Sugestões de Compra", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Data do relatório
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1
        )
        date_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(date_text, date_style))
        elements.append(Spacer(1, 20))
        
        # Resumo executivo
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        elements.append(Paragraph("Resumo Executivo", summary_style))
        
        # Estatísticas resumo
        total_produtos = len(df_sugestoes)
        valor_total = df_sugestoes['valor_estimado'].sum() if 'valor_estimado' in df_sugestoes.columns else 0
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Produtos Sugeridos', str(total_produtos)],
            ['Valor Estimado Total', f"R$ {valor_total:,.2f}"],
            ['Média Priority Score', f"{df_sugestoes['priority_score'].mean():.1f}" if 'priority_score' in df_sugestoes.columns else "N/A"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Tabela principal de sugestões
        elements.append(Paragraph("Detalhamento das Sugestões", summary_style))
        
        # Prepara dados da tabela principal (limitados para caber na página)
        table_data = [['Material', 'Produto', 'Qtd.', 'Classif.', 'Score']]
        
        for _, row in df_sugestoes.iterrows():
            produto_short = row['produto'][:30] + "..." if len(row['produto']) > 30 else row['produto']
            table_data.append([
                str(row['material']),
                produto_short,
                str(row['quantidade_sugerida']),
                row.get('classificacao', 'N/A'),
                f"{row.get('priority_score', 0):.1f}"
            ])
        
        # Cria tabela principal
        main_table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        main_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elements.append(main_table)
        
        # Constrói o PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"❌ Erro na criação do PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

# Dados de teste
test_data = [
    {
        'material': '7505591',
        'produto': 'MOTOR 60HP 4P 225S/M WFF2',
        'quantidade_sugerida': 8,
        'classificacao': 'AX',
        'priority_score': 75.2,
        'valor_estimado': 86494
    },
    {
        'material': '8602115',
        'produto': 'MOTOR 20CV 4P 160L WFF2',
        'quantidade_sugerida': 6,
        'classificacao': 'AX',
        'priority_score': 68.5,
        'valor_estimado': 30200
    }
]

df_test = pd.DataFrame(test_data)

print("🔍 Testando criação de PDF...")
pdf_buffer = test_create_pdf_report(df_test)

if pdf_buffer:
    print(f"✅ PDF criado com sucesso! Tamanho: {len(pdf_buffer.getvalue())} bytes")
    
    # Salva arquivo
    with open("teste_pdf_debug.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())
    print("✅ Arquivo teste_pdf_debug.pdf salvo!")
else:
    print("❌ Falha na criação do PDF")