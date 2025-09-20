"""
Sistema Avançado de Exportação B2B
Templates Executivos, Relatórios Detalhados e API Endpoints
Laura Representações - WEG
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
import base64
import io
import zipfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
import plotly.io as pio
from utils.db import get_connection as get_db_connection
from utils.ml_recommendations import SmartPurchaseRecommendations

class AdvancedExportSystem:
    """Sistema avançado de exportação com múltiplos formatos e templates"""
    
    def __init__(self):
        self.db_path = "instance/database.sqlite"
        self.templates_dir = "export_templates"
        self.recommender = SmartPurchaseRecommendations()
    
    def generate_executive_summary_pdf(self, client_code: str, recommendations: List[Dict]) -> bytes:
        """Gera relatório executivo em PDF com gráficos e insights"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2.5*cm, bottomMargin=2*cm)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilo customizado para título
            title_style = ParagraphStyle(
                'ExecutiveTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4'),
                alignment=1  # Centralizado
            )
            
            # Cabeçalho executivo
            story.append(Paragraph("RELATÓRIO EXECUTIVO B2B", title_style))
            story.append(Paragraph("Sistema de Recomendações Inteligentes", styles['Heading2']))
            story.append(Paragraph("Laura Representações - WEG", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Dados do cliente e período
            story.append(Paragraph(f"<b>Cliente:</b> {client_code}", styles['Normal']))
            story.append(Paragraph(f"<b>Data do Relatório:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
            story.append(Paragraph(f"<b>Período de Análise:</b> Últimos 12 meses", styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Executive Summary
            df = pd.DataFrame(recommendations)
            if not df.empty:
                total_opportunities = len(df)
                high_confidence = len(df[df['probabilidade_recompra'] >= 70])
                total_value = df['valor_potencial'].sum()
                avg_confidence = df['probabilidade_recompra'].mean()
                
                summary_text = f"""
                <b>RESUMO EXECUTIVO</b><br/><br/>
                • <b>{total_opportunities}</b> oportunidades identificadas através de análise de Machine Learning<br/>
                • <b>{high_confidence}</b> recomendações de alta confiança (≥70%)<br/>
                • <b>R$ {total_value:,.0f}</b> em valor potencial total<br/>
                • <b>{avg_confidence:.1f}%</b> score médio de confiança<br/><br/>
                
                <b>PRINCIPAIS INSIGHTS:</b><br/>
                ✓ Gaps de mercado identificados através de benchmarking com clientes similares<br/>
                ✓ Padrões sazonais analisados com base em histórico de 12 meses<br/>
                ✓ Recomendações priorizadas por potencial de ROI e probabilidade de conversão<br/>
                ✓ Sistema de aprendizado contínuo baseado em feedback comercial
                """
                
                story.append(Paragraph(summary_text, styles['Normal']))
                story.append(Spacer(1, 30))
            
            # Top 10 Oportunidades
            if not df.empty:
                story.append(Paragraph("TOP 10 OPORTUNIDADES PRIORITÁRIAS", styles['Heading2']))
                
                top_10 = df.nlargest(10, 'probabilidade_recompra')
                top_data = [['Ranking', 'Material', 'Confiança', 'Valor Potencial', 'Justificativa']]
                
                for i, (_, row) in enumerate(top_10.iterrows(), 1):
                    top_data.append([
                        str(i),
                        str(row['material'])[:15],
                        f"{row['probabilidade_recompra']:.1f}%",
                        f"R$ {row['valor_potencial']:,.0f}",
                        str(row['motivo_da_sugestao'])[:40] + "..."
                    ])
                
                top_table = Table(top_data, colWidths=[1*cm, 3*cm, 2*cm, 2.5*cm, 5*cm])
                top_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                
                story.append(top_table)
                story.append(PageBreak())
            
            # Análise por Segmento
            story.append(Paragraph("ANÁLISE POR SEGMENTO DE CONFIANÇA", styles['Heading2']))
            
            if not df.empty:
                # Distribuição por nível de confiança
                confidence_dist = df['nivel_confianca'].value_counts()
                
                dist_data = [['Nível de Confiança', 'Quantidade', 'Participação', 'Valor Total']]
                for nivel, count in confidence_dist.items():
                    valor_segmento = df[df['nivel_confianca'] == nivel]['valor_potencial'].sum()
                    participacao = (count / len(df)) * 100
                    
                    dist_data.append([
                        nivel,
                        str(count),
                        f"{participacao:.1f}%",
                        f"R$ {valor_segmento:,.0f}"
                    ])
                
                dist_table = Table(dist_data, colWidths=[4*cm, 2*cm, 2*cm, 3*cm])
                dist_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(dist_table)
                story.append(Spacer(1, 30))
            
            # Recomendações estratégicas
            story.append(Paragraph("RECOMENDAÇÕES ESTRATÉGICAS", styles['Heading2']))
            
            estrategias = [
                "🎯 <b>FOCO IMEDIATO:</b> Priorizar contato nos materiais de alta confiança (≥80%) para maximizar taxa de conversão",
                "📊 <b>ABORDAGEM GRADUAL:</b> Materiais de confiança média (50-80%) podem ser trabalhados com informações adicionais",
                "🔄 <b>CICLO CONTÍNUO:</b> Feedback das abordagens alimenta o sistema ML para melhorar futuras recomendações",
                "📈 <b>MONITORAMENTO:</b> Acompanhar taxa de conversão por material para otimizar algoritmo",
                "🎲 <b>TESTE A/B:</b> Experimentar diferentes abordagens nos materiais de confiança média",
                "📅 <b>TIMING:</b> Considerar sazonalidade histórica do cliente para timing ideal de abordagem"
            ]
            
            for estrategia in estrategias:
                story.append(Paragraph(estrategia, styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Footer
            story.append(Spacer(1, 50))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=1
            )
            
            story.append(Paragraph(
                f"Relatório gerado automaticamente pelo Sistema B2B Laura Representações em {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
                "Este documento contém informações confidenciais e estratégicas",
                footer_style
            ))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"Erro ao gerar PDF executivo: {e}")
            return b""
    
    def generate_detailed_excel_report(self, client_code: str, full_analysis: Dict) -> bytes:
        """Gera relatório Excel detalhado com múltiplas abas"""
        try:
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Aba 1: Resumo Executivo
                if 'analises' in full_analysis and 'gaps_mercado' in full_analysis['analises']:
                    gaps_data = full_analysis['analises']['gaps_mercado']
                    
                    if 'gaps' in gaps_data:
                        # Preparar dados das recomendações
                        recommendations_data = []
                        for gap in gaps_data['gaps']:
                            recommendations_data.append({
                                'Material': gap['material'],
                                'Produto': gap.get('produto', 'Produto WEG'),
                                'Score_Oportunidade_%': gap['score_oportunidade'],
                                'Qtd_Potencial': gap.get('qtd_potencial', 0),
                                'Valor_Potencial_R$': gap.get('valor_potencial', 0),
                                'Penetracao_Base_%': gap['w_percent'],
                                'Gap_Type': gap.get('gap_type', 'OPORTUNIDADE'),
                                'Justificativa': f"Penetração de {gap['w_percent']:.1f}% na base de clientes similares"
                            })
                        
                        df_recs = pd.DataFrame(recommendations_data)
                        df_recs.to_excel(writer, sheet_name='Recomendações', index=False)
                
                # Aba 2: Análise de Sazonalidade
                if 'analises' in full_analysis and 'sazonalidade' in full_analysis['analises']:
                    sazon_data = full_analysis['analises']['sazonalidade']
                    
                    if 'padroes_mensais' in sazon_data:
                        sazon_df = pd.DataFrame([
                            {'Mes': i+1, 'Padrão': padroes} 
                            for i, padroes in enumerate(sazon_data['padroes_mensais'])
                        ])
                        sazon_df.to_excel(writer, sheet_name='Sazonalidade', index=False)
                
                # Aba 3: KPIs e Métricas
                kpis_data = []
                if 'analises' in full_analysis:
                    analises = full_analysis['analises']
                    
                    # KPIs gerais
                    kpis_data.extend([
                        {'Categoria': 'Oportunidades', 'Métrica': 'Total Identificadas', 'Valor': len(gaps_data.get('gaps', []))},
                        {'Categoria': 'Oportunidades', 'Métrica': 'Alta Confiança (≥80%)', 'Valor': len([g for g in gaps_data.get('gaps', []) if g.get('score_oportunidade', 0) >= 80])},
                        {'Categoria': 'Financeiro', 'Métrica': 'Valor Potencial Total (R$)', 'Valor': sum(g.get('valor_potencial', 0) for g in gaps_data.get('gaps', []))},
                        {'Categoria': 'Qualidade', 'Métrica': 'Score Médio (%)', 'Valor': np.mean([g.get('score_oportunidade', 0) for g in gaps_data.get('gaps', [])])}
                    ])
                    
                    # Alertas
                    if 'alertas' in analises:
                        alertas = analises['alertas']
                        kpis_data.extend([
                            {'Categoria': 'Alertas', 'Métrica': 'Críticos', 'Valor': len(alertas.get('alertas', {}).get('criticos', []))},
                            {'Categoria': 'Alertas', 'Métrica': 'Importantes', 'Valor': len(alertas.get('alertas', {}).get('importantes', []))},
                            {'Categoria': 'Alertas', 'Métrica': 'Informativos', 'Valor': len(alertas.get('alertas', {}).get('informativos', []))}
                        ])
                
                df_kpis = pd.DataFrame(kpis_data)
                df_kpis.to_excel(writer, sheet_name='KPIs', index=False)
                
                # Aba 4: Histórico do Cliente
                try:
                    conn = get_db_connection()
                    historico_query = """
                    SELECT 
                        material,
                        COUNT(*) as total_compras,
                        SUM(vlr_entrada) as valor_total,
                        AVG(vlr_entrada) as ticket_medio,
                        MIN(data_emissao) as primeira_compra,
                        MAX(data_emissao) as ultima_compra
                    FROM vendas 
                    WHERE cod_cliente = ?
                    GROUP BY material
                    ORDER BY valor_total DESC
                    LIMIT 50
                    """
                    
                    df_historico = pd.read_sql(historico_query, conn, params=[client_code])
                    df_historico.to_excel(writer, sheet_name='Histórico_Cliente', index=False)
                    conn.close()
                    
                except Exception as e:
                    print(f"Erro ao obter histórico: {e}")
                
                # Aba 5: Comparativo Benchmark
                if 'analises' in full_analysis and 'benchmark' in full_analysis['analises']:
                    benchmark_data = full_analysis['analises']['benchmark']
                    
                    if 'comparacoes' in benchmark_data:
                        bench_list = []
                        for material, dados in benchmark_data['comparacoes'].items():
                            bench_list.append({
                                'Material': material,
                                'Cliente_Compras': dados.get('cliente_compras', 0),
                                'Media_Mercado': dados.get('media_mercado', 0),
                                'Gap_Absoluto': dados.get('gap_absoluto', 0),
                                'Gap_Percentual': dados.get('gap_percentual', 0),
                                'Oportunidade': 'SIM' if dados.get('gap_absoluto', 0) > 0 else 'NÃO'
                            })
                        
                        df_benchmark = pd.DataFrame(bench_list)
                        df_benchmark.to_excel(writer, sheet_name='Benchmark', index=False)
                
                # Formatação das planilhas
                workbook = writer.book
                
                # Formato para células de cabeçalho
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#1f77b4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Aplicar formatação em todas as abas
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # Ajustar largura das colunas
                    for col_num, column in enumerate(worksheet.columns):
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"Erro ao gerar Excel detalhado: {e}")
            return b""
    
    def generate_complete_export_package(self, client_code: str) -> bytes:
        """Gera pacote completo de exportação em ZIP"""
        try:
            # Executar análise completa
            resultado = self.recommender.run_complete_b2b_analysis(
                cod_cliente=client_code,
                contexto_comercial={'tipo_analise': 'completa_export'},
                export_format='completo'
            )
            
            # Preparar recomendações
            recommendations = []
            if 'analises' in resultado and 'gaps_mercado' in resultado['analises']:
                gaps_data = resultado['analises']['gaps_mercado']
                for gap in gaps_data.get('gaps', []):
                    recommendations.append({
                        'material': gap['material'],
                        'descricao': gap.get('produto', 'Produto WEG'),
                        'qtd_sugerida': gap.get('qtd_potencial', 0),
                        'motivo_da_sugestao': f"Gap de mercado: {gap['w_percent']:.1f}% penetração",
                        'probabilidade_recompra': gap['score_oportunidade'],
                        'nivel_confianca': 'ALTA' if gap['score_oportunidade'] >= 80 else 'MÉDIA' if gap['score_oportunidade'] >= 60 else 'BAIXA',
                        'valor_potencial': gap.get('valor_potencial', 0)
                    })
            
            # Criar ZIP com múltiplos arquivos
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 1. PDF Executivo
                pdf_data = self.generate_executive_summary_pdf(client_code, recommendations)
                if pdf_data:
                    zip_file.writestr(f"01_Relatorio_Executivo_{client_code}_{datetime.now().strftime('%Y%m%d')}.pdf", pdf_data)
                
                # 2. Excel Detalhado
                excel_data = self.generate_detailed_excel_report(client_code, resultado)
                if excel_data:
                    zip_file.writestr(f"02_Analise_Detalhada_{client_code}_{datetime.now().strftime('%Y%m%d')}.xlsx", excel_data)
                
                # 3. JSON com dados completos
                json_data = json.dumps(resultado, indent=2, ensure_ascii=False, default=str)
                zip_file.writestr(f"03_Dados_Completos_{client_code}_{datetime.now().strftime('%Y%m%d')}.json", json_data)
                
                # 4. CSV das recomendações
                if recommendations:
                    df_csv = pd.DataFrame(recommendations)
                    csv_data = df_csv.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f"04_Recomendacoes_{client_code}_{datetime.now().strftime('%Y%m%d')}.csv", csv_data)
                
                # 5. Relatório de texto simples
                txt_report = self.generate_text_summary(client_code, recommendations, resultado)
                zip_file.writestr(f"05_Resumo_Textual_{client_code}_{datetime.now().strftime('%Y%m%d')}.txt", txt_report)
            
            zip_buffer.seek(0)
            return zip_buffer.read()
            
        except Exception as e:
            print(f"Erro ao gerar pacote completo: {e}")
            return b""
    
    def generate_text_summary(self, client_code: str, recommendations: List[Dict], full_analysis: Dict) -> str:
        """Gera resumo textual para integração com outros sistemas"""
        try:
            df = pd.DataFrame(recommendations)
            
            summary = f"""
RELATÓRIO B2B - SISTEMA DE RECOMENDAÇÕES INTELIGENTES
Laura Representações - WEG
=======================================================

CLIENTE: {client_code}
DATA: {datetime.now().strftime('%d/%m/%Y %H:%M')}
PERÍODO: Últimos 12 meses

RESUMO EXECUTIVO
================
Total de Oportunidades: {len(df) if not df.empty else 0}
Oportunidades Alta Confiança (≥70%): {len(df[df['probabilidade_recompra'] >= 70]) if not df.empty else 0}
Valor Potencial Total: R$ {df['valor_potencial'].sum():,.2f if not df.empty else 0}
Score Médio de Confiança: {df['probabilidade_recompra'].mean():.1f}% {'' if not df.empty else 'N/A'}

TOP 5 RECOMENDAÇÕES
===================
"""
            
            if not df.empty:
                top_5 = df.nlargest(5, 'probabilidade_recompra')
                for i, (_, row) in enumerate(top_5.iterrows(), 1):
                    summary += f"""
{i}. Material: {row['material']}
   Confiança: {row['probabilidade_recompra']:.1f}%
   Valor: R$ {row['valor_potencial']:,.2f}
   Motivo: {row['motivo_da_sugestao']}
   
"""
            
            summary += f"""
DISTRIBUIÇÃO POR CONFIANÇA
==========================
"""
            
            if not df.empty:
                confidence_dist = df['nivel_confianca'].value_counts()
                for nivel, count in confidence_dist.items():
                    pct = (count / len(df)) * 100
                    summary += f"{nivel}: {count} oportunidades ({pct:.1f}%)\n"
            
            summary += f"""

PRÓXIMOS PASSOS RECOMENDADOS
=============================
1. Focar nas oportunidades de alta confiança para maximizar conversão
2. Preparar material técnico para os produtos recomendados
3. Agendar reunião comercial considerando sazonalidade do cliente
4. Registrar feedback no sistema para aprimorar futuras recomendações
5. Monitorar taxa de conversão para otimização contínua

OBSERVAÇÕES TÉCNICAS
====================
- Análise baseada em Machine Learning com algoritmos de gap analysis
- Benchmarking realizado com clientes de perfil similar
- Sistema de aprendizado contínuo baseado em feedback comercial
- Dados históricos de 12 meses utilizados para padrões sazonais
- Confiabilidade estatística validada com base de {full_analysis.get('metadata', {}).get('total_vendas', 'N/A')} vendas

Relatório gerado automaticamente pelo Sistema B2B Laura Representações
Confidencial - Uso interno apenas
"""
            
            return summary
            
        except Exception as e:
            print(f"Erro ao gerar resumo textual: {e}")
            return f"Erro ao gerar resumo para cliente {client_code}: {str(e)}"
    
    def schedule_automated_reports(self, client_codes: List[str], frequency: str = "weekly") -> bool:
        """Agenda relatórios automáticos (placeholder para implementação futura)"""
        try:
            # Implementação futura: integração com scheduler (Celery, APScheduler, etc.)
            # Por ora, apenas salva configuração no banco
            
            conn = get_db_connection()
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_codes TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    last_generated DATETIME,
                    next_generation DATETIME,
                    active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Calcular próxima geração
            if frequency == "daily":
                next_gen = datetime.now() + timedelta(days=1)
            elif frequency == "weekly":
                next_gen = datetime.now() + timedelta(weeks=1)
            elif frequency == "monthly":
                next_gen = datetime.now() + timedelta(days=30)
            else:
                next_gen = datetime.now() + timedelta(weeks=1)
            
            conn.execute("""
                INSERT INTO scheduled_reports (client_codes, frequency, next_generation)
                VALUES (?, ?, ?)
            """, (json.dumps(client_codes), frequency, next_gen))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erro ao agendar relatórios: {e}")
            return False

def create_download_link_advanced(data: bytes, filename: str, mime_type: str) -> str:
    """Cria link de download otimizado para arquivos grandes"""
    try:
        # Para arquivos muito grandes, considerar streaming
        if len(data) > 10 * 1024 * 1024:  # 10MB
            # Implementar streaming ou salvamento temporário
            pass
        
        b64_data = base64.b64encode(data).decode()
        return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Erro ao criar link de download: {e}")
        return ""