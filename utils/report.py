# utils/report.py

import io
import base64
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("⚠️  ReportLab não disponível. Funcionalidade de PDF desabilitada.")
    REPORTLAB_AVAILABLE = False

def generate_client_pdf(client_data, client_name, charts_data=None):
    """
    Gera relatório PDF para um cliente específico
    
    Args:
        client_data: DataFrame com dados do cliente
        client_name: Nome do cliente
        charts_data: Dados dos gráficos (opcional)
    
    Returns:
        bytes: PDF em bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.Color(0.2, 0.4, 0.8)  # Azul WEG
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        textColor=colors.Color(0.2, 0.4, 0.8)
    )
    
    # Cabeçalho
    story.append(Paragraph("RELATÓRIO DE CLIENTE", title_style))
    story.append(Paragraph(f"Cliente: {client_name}", subtitle_style))
    story.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Resumo Executivo
    story.append(Paragraph("RESUMO EXECUTIVO", subtitle_style))
    
    if not client_data.empty:
        # KPIs principais
        total_vendas = client_data['valor'].sum() if 'valor' in client_data.columns else 0
        qtd_pedidos = len(client_data) if not client_data.empty else 0
        
        # Dados da última compra
        if 'data_faturamento' in client_data.columns:
            last_purchase = client_data['data_faturamento'].max()
            days_since_last = (datetime.now() - pd.to_datetime(last_purchase)).days
        else:
            days_since_last = "N/A"
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Vendas (R$)', f"{total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")],
            ['Quantidade de Pedidos', str(qtd_pedidos)],
            ['Dias desde Última Compra', str(days_since_last)],
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.8)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Produtos mais comprados
        if 'produto' in client_data.columns:
            story.append(Paragraph("PRODUTOS MAIS COMPRADOS", subtitle_style))
            
            produtos_top = client_data.groupby('produto').agg({
                'valor': 'sum',
                'quantidade': 'sum'
            }).sort_values('valor', ascending=False).head(5)
            
            produtos_data = [['Produto', 'Valor Total (R$)', 'Quantidade']]
            for produto, row in produtos_top.iterrows():
                produtos_data.append([
                    produto,
                    f"{row['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    f"{row['quantidade']:,.0f}".replace(",", ".")
                ])
            
            produtos_table = Table(produtos_data)
            produtos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.8)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(produtos_table)
            story.append(Spacer(1, 20))
    
    # Recomendações
    story.append(Paragraph("RECOMENDAÇÕES E AÇÕES", subtitle_style))
    
    recommendations = [
        "• Manter contato regular para identificar novas oportunidades",
        "• Apresentar produtos complementares baseados no histórico de compras",
        "• Agendar visita técnica para avaliar necessidades futuras",
        "• Oferecer condições especiais para aumentar o volume de pedidos"
    ]
    
    for rec in recommendations:
        story.append(Paragraph(rec, styles['Normal']))
        story.append(Spacer(1, 5))
    
    # Adicionar gráfico se fornecido
    if charts_data and 'image_base64' in charts_data:
        story.append(Spacer(1, 20))
        story.append(Paragraph("ANÁLISE VISUAL", subtitle_style))
        
        # Decodificar imagem base64
        image_data = base64.b64decode(charts_data['image_base64'])
        image_buffer = io.BytesIO(image_data)
        
        # Adicionar imagem ao PDF
        img = Image(image_buffer, width=4*inch, height=3*inch)
        story.append(img)
    
    # Rodapé
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph("Relatório gerado automaticamente pelo Dashboard WEG", footer_style))
    story.append(Paragraph(f"© {datetime.now().year} Laura Representações", footer_style))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()

def create_chart_for_pdf(data, chart_type='bar'):
    """
    Cria gráfico otimizado para PDF
    
    Args:
        data: DataFrame com dados
        chart_type: Tipo do gráfico ('bar', 'line', 'pie')
    
    Returns:
        str: Imagem em base64
    """
    if data.empty:
        return None
    
    fig = go.Figure()
    
    if chart_type == 'bar':
        fig.add_trace(go.Bar(
            x=data.index,
            y=data.values,
            marker_color='rgba(51, 102, 204, 0.8)'
        ))
        fig.update_layout(
            title="Evolução de Vendas",
            xaxis_title="Período",
            yaxis_title="Valor (R$)"
        )
    
    elif chart_type == 'pie':
        fig.add_trace(go.Pie(
            labels=data.index,
            values=data.values,
            hole=0.3
        ))
        fig.update_layout(title="Distribuição por Categoria")
    
    # Configurações para PDF
    fig.update_layout(
        width=600,
        height=400,
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Converter para base64
    img_bytes = pio.to_image(fig, format='png', engine='kaleido')
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64
