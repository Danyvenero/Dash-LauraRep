"""
Sistema de Feedback e Aprendizado Automático
Machine Learning Adaptativo para Recomendações B2B
Laura Representações - WEG
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pickle
from utils.db import get_connection as get_db_connection

@dataclass
class FeedbackMetrics:
    """Métricas de feedback para análise"""
    total_feedbacks: int
    positive_rate: float
    negative_rate: float
    relevance_rate: float
    avg_confidence_adjustment: float
    top_performing_materials: List[str]
    underperforming_materials: List[str]

class MLFeedbackLearningSystem:
    """Sistema de aprendizado baseado em feedback do usuário"""
    
    def __init__(self):
        self.db_path = "instance/database.sqlite"
        self.weights_file = "ml_weights.pkl"
        self.initialize_feedback_tables()
        self.load_or_initialize_weights()
    
    def initialize_feedback_tables(self):
        """Inicializa tabelas de feedback no banco"""
        try:
            conn = get_db_connection()
            
            # Tabela principal de feedback
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT NOT NULL,
                    client_code TEXT,
                    material TEXT,
                    feedback_type TEXT NOT NULL,
                    confidence_score REAL,
                    value_potential REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    additional_data TEXT,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabela de ajustes de pesos ML
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ml_weight_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    weight_type TEXT NOT NULL,
                    old_value REAL,
                    new_value REAL,
                    adjustment_reason TEXT,
                    feedback_count INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    performance_metric REAL
                )
            """)
            
            # Tabela de performance de materiais
            conn.execute("""
                CREATE TABLE IF NOT EXISTS material_performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material TEXT NOT NULL,
                    client_code TEXT,
                    recommendation_count INTEGER DEFAULT 0,
                    positive_feedback_count INTEGER DEFAULT 0,
                    negative_feedback_count INTEGER DEFAULT 0,
                    conversion_rate REAL DEFAULT 0.0,
                    avg_confidence_score REAL DEFAULT 0.0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(material, client_code)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao inicializar tabelas de feedback: {e}")
    
    def load_or_initialize_weights(self):
        """Carrega ou inicializa pesos do sistema ML"""
        try:
            with open(self.weights_file, 'rb') as f:
                self.ml_weights = pickle.load(f)
        except FileNotFoundError:
            # Pesos iniciais baseados na análise atual
            self.ml_weights = {
                'gap_analysis_weight': 0.3,
                'seasonality_weight': 0.2,
                'benchmark_weight': 0.25,
                'historical_performance_weight': 0.15,
                'client_similarity_weight': 0.1,
                'confidence_threshold': 70.0,
                'value_threshold': 1000.0,
                'recency_bonus': 1.1,
                'feedback_learning_rate': 0.05
            }
            self.save_weights()
    
    def save_weights(self):
        """Salva pesos atualizados"""
        try:
            with open(self.weights_file, 'wb') as f:
                pickle.dump(self.ml_weights, f)
        except Exception as e:
            print(f"Erro ao salvar pesos: {e}")
    
    def process_user_feedback(self, recommendation_id: str, feedback_type: str, 
                            client_code: str, material: str, 
                            confidence_score: float, value_potential: float,
                            session_id: str = None) -> bool:
        """Processa feedback individual do usuário"""
        try:
            conn = get_db_connection()
            
            # Inserir feedback
            conn.execute("""
                INSERT INTO recommendation_feedback 
                (recommendation_id, client_code, material, feedback_type, 
                 confidence_score, value_potential, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (recommendation_id, client_code, material, feedback_type,
                  confidence_score, value_potential, session_id))
            
            # Atualizar performance do material
            conn.execute("""
                INSERT OR REPLACE INTO material_performance_history 
                (material, client_code, recommendation_count, positive_feedback_count, 
                 negative_feedback_count, conversion_rate, avg_confidence_score)
                VALUES (
                    ?, ?, 
                    COALESCE((SELECT recommendation_count FROM material_performance_history 
                             WHERE material = ? AND client_code = ?), 0) + 1,
                    COALESCE((SELECT positive_feedback_count FROM material_performance_history 
                             WHERE material = ? AND client_code = ?), 0) + 
                             CASE WHEN ? = 'like' THEN 1 ELSE 0 END,
                    COALESCE((SELECT negative_feedback_count FROM material_performance_history 
                             WHERE material = ? AND client_code = ?), 0) + 
                             CASE WHEN ? IN ('dislike', 'not_relevant') THEN 1 ELSE 0 END,
                    CASE WHEN (COALESCE((SELECT recommendation_count FROM material_performance_history 
                              WHERE material = ? AND client_code = ?), 0) + 1) > 0 
                         THEN CAST((COALESCE((SELECT positive_feedback_count FROM material_performance_history 
                                           WHERE material = ? AND client_code = ?), 0) + 
                                   CASE WHEN ? = 'like' THEN 1 ELSE 0 END) AS FLOAT) / 
                              (COALESCE((SELECT recommendation_count FROM material_performance_history 
                                       WHERE material = ? AND client_code = ?), 0) + 1)
                         ELSE 0.0 END,
                    ?
                )
            """, (material, client_code, material, client_code, material, client_code, 
                  feedback_type, material, client_code, feedback_type, material, client_code,
                  material, client_code, feedback_type, material, client_code, confidence_score))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erro ao processar feedback: {e}")
            return False
    
    def analyze_feedback_patterns(self, days: int = 30) -> FeedbackMetrics:
        """Analisa padrões de feedback para ajustar algoritmo"""
        try:
            conn = get_db_connection()
            
            # Feedback dos últimos N dias
            feedback_query = """
                SELECT feedback_type, confidence_score, material, value_potential
                FROM recommendation_feedback
                WHERE timestamp >= date('now', '-{} days')
            """.format(days)
            
            feedback_df = pd.read_sql(feedback_query, conn)
            
            if feedback_df.empty:
                conn.close()
                return FeedbackMetrics(0, 0.0, 0.0, 0.0, 0.0, [], [])
            
            # Calcular métricas
            total_feedbacks = len(feedback_df)
            positive_rate = len(feedback_df[feedback_df['feedback_type'] == 'like']) / total_feedbacks
            negative_rate = len(feedback_df[feedback_df['feedback_type'].isin(['dislike', 'not_relevant'])]) / total_feedbacks
            relevance_rate = len(feedback_df[feedback_df['feedback_type'] != 'not_relevant']) / total_feedbacks
            
            # Performance por material
            material_performance = """
                SELECT material, conversion_rate, recommendation_count
                FROM material_performance_history
                WHERE last_updated >= date('now', '-{} days')
                ORDER BY conversion_rate DESC
            """.format(days)
            
            performance_df = pd.read_sql(material_performance, conn)
            conn.close()
            
            top_performers = performance_df.head(5)['material'].tolist() if not performance_df.empty else []
            underperformers = performance_df.tail(5)['material'].tolist() if not performance_df.empty else []
            
            # Ajuste médio de confiança baseado no feedback
            confidence_adjustments = []
            for _, row in feedback_df.iterrows():
                if row['feedback_type'] == 'like':
                    confidence_adjustments.append(0.05)
                elif row['feedback_type'] == 'dislike':
                    confidence_adjustments.append(-0.03)
                elif row['feedback_type'] == 'not_relevant':
                    confidence_adjustments.append(-0.10)
            
            avg_confidence_adjustment = np.mean(confidence_adjustments) if confidence_adjustments else 0.0
            
            return FeedbackMetrics(
                total_feedbacks=total_feedbacks,
                positive_rate=positive_rate,
                negative_rate=negative_rate,
                relevance_rate=relevance_rate,
                avg_confidence_adjustment=avg_confidence_adjustment,
                top_performing_materials=top_performers,
                underperforming_materials=underperformers
            )
            
        except Exception as e:
            print(f"Erro ao analisar padrões de feedback: {e}")
            return FeedbackMetrics(0, 0.0, 0.0, 0.0, 0.0, [], [])
    
    def auto_adjust_ml_weights(self, feedback_metrics: FeedbackMetrics) -> Dict[str, float]:
        """Ajusta automaticamente os pesos do ML baseado no feedback"""
        adjustments = {}
        
        try:
            # Ajuste baseado na taxa de relevância
            if feedback_metrics.relevance_rate < 0.7:  # Baixa relevância
                # Aumentar peso da análise de gaps
                old_gap_weight = self.ml_weights['gap_analysis_weight']
                self.ml_weights['gap_analysis_weight'] = min(0.5, old_gap_weight + 0.05)
                adjustments['gap_analysis_weight'] = self.ml_weights['gap_analysis_weight'] - old_gap_weight
                
                # Aumentar threshold de confiança
                old_threshold = self.ml_weights['confidence_threshold']
                self.ml_weights['confidence_threshold'] = min(85.0, old_threshold + 2.0)
                adjustments['confidence_threshold'] = self.ml_weights['confidence_threshold'] - old_threshold
            
            # Ajuste baseado na taxa positiva
            if feedback_metrics.positive_rate > 0.8:  # Muito feedback positivo
                # Reduzir threshold para capturar mais oportunidades
                old_threshold = self.ml_weights['confidence_threshold']
                self.ml_weights['confidence_threshold'] = max(60.0, old_threshold - 1.0)
                adjustments['confidence_threshold'] = self.ml_weights['confidence_threshold'] - old_threshold
            
            # Ajuste do peso de performance histórica baseado em materiais top/bottom
            if len(feedback_metrics.top_performing_materials) > 0:
                old_hist_weight = self.ml_weights['historical_performance_weight']
                self.ml_weights['historical_performance_weight'] = min(0.3, old_hist_weight + 0.02)
                adjustments['historical_performance_weight'] = self.ml_weights['historical_performance_weight'] - old_hist_weight
            
            # Salvar ajustes no banco
            if adjustments:
                self.save_weight_adjustments(adjustments, feedback_metrics)
                self.save_weights()
            
            return adjustments
            
        except Exception as e:
            print(f"Erro ao ajustar pesos ML: {e}")
            return {}
    
    def save_weight_adjustments(self, adjustments: Dict[str, float], metrics: FeedbackMetrics):
        """Salva histórico de ajustes de pesos"""
        try:
            conn = get_db_connection()
            
            for weight_type, adjustment in adjustments.items():
                conn.execute("""
                    INSERT INTO ml_weight_adjustments 
                    (weight_type, old_value, new_value, adjustment_reason, 
                     feedback_count, performance_metric)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    weight_type,
                    self.ml_weights[weight_type] - adjustment,
                    self.ml_weights[weight_type],
                    f"Auto-adjustment based on feedback analysis",
                    metrics.total_feedbacks,
                    metrics.positive_rate
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao salvar ajustes: {e}")
    
    def get_material_confidence_modifier(self, material: str, client_code: str) -> float:
        """Retorna modificador de confiança baseado no histórico do material"""
        try:
            conn = get_db_connection()
            
            cursor = conn.execute("""
                SELECT conversion_rate, recommendation_count
                FROM material_performance_history
                WHERE material = ? AND client_code = ?
            """, (material, client_code))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1] >= 3:  # Mínimo 3 recomendações para ser significativo
                conversion_rate = result[0]
                if conversion_rate > 0.7:
                    return 1.1  # Boost de 10%
                elif conversion_rate < 0.3:
                    return 0.9  # Penalidade de 10%
            
            return 1.0  # Sem modificação
            
        except Exception as e:
            print(f"Erro ao obter modificador de confiança: {e}")
            return 1.0
    
    def generate_feedback_report(self, days: int = 30) -> Dict:
        """Gera relatório completo de feedback e aprendizado"""
        try:
            metrics = self.analyze_feedback_patterns(days)
            
            report = {
                'period_days': days,
                'total_feedbacks': metrics.total_feedbacks,
                'feedback_rates': {
                    'positive': f"{metrics.positive_rate:.1%}",
                    'negative': f"{metrics.negative_rate:.1%}",
                    'relevance': f"{metrics.relevance_rate:.1%}"
                },
                'top_materials': metrics.top_performing_materials,
                'underperforming_materials': metrics.underperforming_materials,
                'current_weights': self.ml_weights.copy(),
                'recommendations': []
            }
            
            # Gerar recomendações de melhoria
            if metrics.relevance_rate < 0.7:
                report['recommendations'].append("⚠️ Taxa de relevância baixa - considerar ajuste nos filtros de confiança")
            
            if metrics.positive_rate > 0.8:
                report['recommendations'].append("✅ Alta satisfação - considerar reduzir threshold para capturar mais oportunidades")
            
            if len(metrics.underperforming_materials) > 3:
                report['recommendations'].append("📉 Múltiplos materiais com baixa performance - revisar critérios de gap analysis")
            
            return report
            
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")
            return {}
    
    def run_daily_learning_cycle(self):
        """Executa ciclo diário de aprendizado automático"""
        try:
            print("🤖 Iniciando ciclo de aprendizado automático...")
            
            # Analisar feedback dos últimos 7 dias
            metrics = self.analyze_feedback_patterns(7)
            
            result = {
                'success': False,
                'feedbacks_processed': metrics.total_feedbacks,
                'model_updated': False,
                'improvements': 'Nenhuma',
                'message': ''
            }
            
            if metrics.total_feedbacks >= 5:  # Mínimo de feedbacks para ajustar
                # Executar ajustes
                adjustments = self.auto_adjust_ml_weights(metrics)
                
                if adjustments:
                    print(f"✅ Pesos ajustados: {adjustments}")
                    result.update({
                        'success': True,
                        'model_updated': True,
                        'improvements': f"Pesos ajustados: {adjustments}",
                        'message': 'Modelo atualizado com sucesso'
                    })
                else:
                    print("ℹ️ Nenhum ajuste necessário")
                    result.update({
                        'success': True,
                        'message': 'Nenhum ajuste necessário - modelo já otimizado'
                    })
            else:
                print(f"ℹ️ Feedbacks insuficientes ({metrics.total_feedbacks}/5) - aguardando mais dados")
                result.update({
                    'success': True,
                    'message': f'Feedbacks insuficientes ({metrics.total_feedbacks}/5) - aguardando mais dados'
                })
            
            return result
            
        except Exception as e:
            print(f"Erro no ciclo de aprendizado: {e}")
            return {
                'success': False,
                'feedbacks_processed': 0,
                'model_updated': False,
                'improvements': 'Erro',
                'message': f'Erro no ciclo de aprendizado: {str(e)}'
            }

def create_feedback_dashboard_component():
    """Cria componente de dashboard para visualizar feedback"""
    return {
        'feedback_summary_card': True,
        'learning_metrics_chart': True,
        'weight_adjustment_history': True,
        'material_performance_ranking': True
    }