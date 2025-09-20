"""
Sistema de Ações Interativas para Recomendações B2B
Implementa botões funcionais: Cotação, Feedback, Exportação
Laura Representações - WEG
"""

import pandas as pd
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import base64
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from utils.db import get_connection as get_db_connection

class RecommendationActionHandler:
    """Gerencia todas as ações possíveis em recomendações"""
    
    def __init__(self):
        self.db_path = "instance/database.sqlite"
    
    def generate_quotation_data(self, recommendation: Dict) -> Dict:
        """
        Gera dados de cotação baseado na recomendação
        """
        try:
            # Dados base da cotação
            quotation_data = {
                'numero_cotacao': f"COT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'material': recommendation.get('material', 'N/A'),
                'descricao': recommendation.get('descricao', 'Produto WEG'),
                'quantidade_sugerida': recommendation.get('qtd_sugerida', 0),
                'motivo_sugestao': recommendation.get('motivo_da_sugestao', 'Análise automática'),
                'probabilidade': recommendation.get('probabilidade_recompra', 0),
                'valor_estimado': recommendation.get('valor_potencial', 0),
                'prazo_entrega_estimado': '15-30 dias úteis',
                'condicoes_pagamento': 'A definir conforme política comercial',
                'validade_cotacao': '30 dias',
                'observacoes': f"Cotação gerada automaticamente pelo sistema B2B Laura Representações baseada em análise de machine learning. Score de oportunidade: {recommendation.get('probabilidade_recompra', 0):.1f}%"
            }
            
            # Buscar dados históricos do material se disponível
            conn = get_db_connection()
            historic_query = """
            SELECT AVG(vlr_entrada) as preco_medio, COUNT(*) as vendas_historicas
            FROM vendas 
            WHERE material = ?
            AND vlr_entrada > 0
            """
            
            cursor = conn.execute(historic_query, (recommendation.get('material'),))
            historic_data = cursor.fetchone()
            conn.close()
            
            if historic_data and historic_data[0]:
                quotation_data['preco_referencia'] = f"R$ {historic_data[0]:,.2f}"
                quotation_data['vendas_historicas'] = historic_data[1]
            else:
                quotation_data['preco_referencia'] = "Consultar equipe comercial"
                quotation_data['vendas_historicas'] = 0
                
            return quotation_data
            
        except Exception as e:
            print(f"Erro ao gerar dados de cotação: {e}")
            return {}
    
    def save_feedback(self, recommendation_id: str, feedback_type: str, 
                     client_code: str, additional_data: Dict = None) -> bool:
        """
        Salva feedback do usuário sobre recomendação
        """
        try:
            conn = get_db_connection()
            
            # Criar tabela de feedback se não existir
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT NOT NULL,
                    client_code TEXT,
                    feedback_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    additional_data TEXT,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Inserir feedback
            conn.execute("""
                INSERT INTO recommendation_feedback 
                (recommendation_id, client_code, feedback_type, additional_data)
                VALUES (?, ?, ?, ?)
            """, (
                recommendation_id,
                client_code,
                feedback_type,
                json.dumps(additional_data) if additional_data else None
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar feedback: {e}")
            return False
    
    def export_recommendation_pdf(self, recommendation: Dict, quotation_data: Dict = None) -> bytes:
        """
        Exporta recomendação individual como PDF
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            
            story.append(Paragraph("Recomendação Inteligente de Compra", title_style))
            story.append(Paragraph("Laura Representações - Sistema B2B WEG", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Informações da recomendação
            rec_data = [
                ['Campo', 'Valor'],
                ['Material', recommendation.get('material', 'N/A')],
                ['Descrição', recommendation.get('descricao', 'N/A')],
                ['Quantidade Sugerida', f"{recommendation.get('qtd_sugerida', 0):,.0f}"],
                ['Motivo da Sugestão', recommendation.get('motivo_da_sugestao', 'N/A')],
                ['Probabilidade de Recompra', f"{recommendation.get('probabilidade_recompra', 0):.1f}%"],
                ['Nível de Confiança', recommendation.get('nivel_confianca', 'N/A')],
                ['Valor Potencial', f"R$ {recommendation.get('valor_potencial', 0):,.2f}"]
            ]
            
            rec_table = Table(rec_data)
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(rec_table)
            story.append(Spacer(1, 20))
            
            # Dados de cotação se disponível
            if quotation_data:
                story.append(Paragraph("Dados para Cotação", styles['Heading2']))
                
                cot_data = [
                    ['Número da Cotação', quotation_data.get('numero_cotacao', 'N/A')],
                    ['Data de Geração', quotation_data.get('data_geracao', 'N/A')],
                    ['Preço de Referência', quotation_data.get('preco_referencia', 'N/A')],
                    ['Prazo de Entrega', quotation_data.get('prazo_entrega_estimado', 'N/A')],
                    ['Validade', quotation_data.get('validade_cotacao', 'N/A')]
                ]
                
                cot_table = Table(cot_data)
                cot_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(cot_table)
                story.append(Spacer(1, 20))
            
            # Observações
            story.append(Paragraph("Observações", styles['Heading2']))
            story.append(Paragraph(
                "Esta recomendação foi gerada automaticamente pelo sistema de Machine Learning "
                "da Laura Representações, baseada na análise de padrões históricos de compra, "
                "gaps de mercado e benchmarking com clientes similares.",
                styles['Normal']
            ))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
                styles['Italic']
            ))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            return b""
    
    def export_recommendations_excel(self, recommendations: List[Dict]) -> bytes:
        """
        Exporta múltiplas recomendações como Excel
        """
        try:
            buffer = io.BytesIO()
            
            # Preparar dados para DataFrame
            export_data = []
            for rec in recommendations:
                export_data.append({
                    'Material': rec.get('material', 'N/A'),
                    'Descrição': rec.get('descricao', 'N/A'),
                    'Qtd_Sugerida': rec.get('qtd_sugerida', 0),
                    'Motivo_Sugestão': rec.get('motivo_da_sugestao', 'N/A'),
                    'Probabilidade_Recompra_%': rec.get('probabilidade_recompra', 0),
                    'Nível_Confiança': rec.get('nivel_confianca', 'N/A'),
                    'Valor_Potencial_R$': rec.get('valor_potencial', 0),
                    'Tipo_Gap': rec.get('tipo_gap', 'N/A')
                })
            
            df = pd.DataFrame(export_data)
            
            # Criar Excel com formatação
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Recomendações', index=False)
                
                # Obter workbook e worksheet
                workbook = writer.book
                worksheet = writer.sheets['Recomendações']
                
                # Formatação do cabeçalho
                header_fill = workbook.create_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#1f77b4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Ajustar largura das colunas
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
            
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"Erro ao gerar Excel: {e}")
            return b""
    
    def get_feedback_summary(self, client_code: str = None, days: int = 30) -> Dict:
        """
        Retorna resumo dos feedbacks para análise
        """
        try:
            conn = get_db_connection()
            
            where_clause = "WHERE timestamp >= date('now', '-30 days')"
            params = []
            
            if client_code:
                where_clause += " AND client_code = ?"
                params.append(client_code)
            
            query = f"""
                SELECT 
                    feedback_type,
                    COUNT(*) as total,
                    DATE(timestamp) as data
                FROM recommendation_feedback 
                {where_clause}
                GROUP BY feedback_type, DATE(timestamp)
                ORDER BY data DESC
            """
            
            cursor = conn.execute(query, params)
            feedback_data = cursor.fetchall()
            conn.close()
            
            # Processar dados
            summary = {
                'total_feedbacks': len(feedback_data),
                'by_type': {},
                'by_date': {}
            }
            
            for row in feedback_data:
                feedback_type, total, data = row
                if feedback_type not in summary['by_type']:
                    summary['by_type'][feedback_type] = 0
                summary['by_type'][feedback_type] += total
                
                if data not in summary['by_date']:
                    summary['by_date'][data] = {}
                summary['by_date'][data][feedback_type] = total
            
            return summary
            
        except Exception as e:
            print(f"Erro ao obter resumo de feedback: {e}")
            return {}
    
    def process_pending_feedback(self) -> Dict:
        """
        Processa feedbacks pendentes para ajustar algoritmo ML
        """
        try:
            conn = get_db_connection()
            
            # Buscar feedbacks não processados
            cursor = conn.execute("""
                SELECT id, recommendation_id, feedback_type, additional_data
                FROM recommendation_feedback 
                WHERE processed = FALSE
            """)
            
            pending_feedback = cursor.fetchall()
            
            # Contadores para análise
            adjustments = {
                'positive_feedback': 0,
                'negative_feedback': 0,
                'relevance_score_adjustments': [],
                'confidence_adjustments': []
            }
            
            for feedback in pending_feedback:
                fb_id, rec_id, fb_type, additional = feedback
                
                if fb_type == 'like':
                    adjustments['positive_feedback'] += 1
                    adjustments['confidence_adjustments'].append(0.05)  # Aumenta confiança
                elif fb_type == 'dislike':
                    adjustments['negative_feedback'] += 1
                    adjustments['confidence_adjustments'].append(-0.05)  # Diminui confiança
                elif fb_type == 'not_relevant':
                    adjustments['relevance_score_adjustments'].append(-0.1)
                
                # Marcar como processado
                conn.execute("""
                    UPDATE recommendation_feedback 
                    SET processed = TRUE 
                    WHERE id = ?
                """, (fb_id,))
            
            conn.commit()
            conn.close()
            
            return adjustments
            
        except Exception as e:
            print(f"Erro ao processar feedback pendente: {e}")
            return {}

def create_download_link(data: bytes, filename: str, mime_type: str) -> str:
    """
    Cria link de download para dados binários
    """
    try:
        b64_data = base64.b64encode(data).decode()
        return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Erro ao criar link de download: {e}")
        return ""