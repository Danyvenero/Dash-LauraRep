"""
Script para Popular Dados de Teste - Sistema de Feedback ML
Cria dados de exemplo para testar as funcionalidades de recomendações e aprendizado
"""

import sqlite3
import random
from datetime import datetime, timedelta

def populate_test_feedback_data():
    """Popula dados de teste para feedback e aprendizado ML"""
    print("🧪 === POPULANDO DADOS DE TESTE PARA ML ===")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        # 1. Dados de feedback de recomendações
        print("1️⃣ INSERINDO FEEDBACKS DE TESTE")
        
        materials = ['CFW700', 'CFW11', 'CVW1000', 'DWB01', 'DWB02', 'SCANNER-WEG']
        clients = ['CLIENTE-A', 'CLIENTE-B', 'CLIENTE-C', 'CLIENTE-D']
        feedback_types = ['like', 'dislike', 'not_relevant', 'converted']
        
        feedbacks_inserted = 0
        for i in range(50):  # 50 feedbacks de teste
            recommendation_id = f"rec_{i:03d}"
            client = random.choice(clients)
            material = random.choice(materials)
            feedback_type = random.choice(feedback_types)
            confidence_score = random.uniform(60, 95)
            value_potential = random.uniform(500, 5000)
            
            # Data aleatória nos últimos 30 dias
            days_ago = random.randint(0, 30)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute("""
                INSERT INTO recommendation_feedback 
                (recommendation_id, client_code, material, feedback_type, 
                 confidence_score, value_potential, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (recommendation_id, client, material, feedback_type,
                  confidence_score, value_potential, timestamp.isoformat(), f"session_{i}"))
            
            feedbacks_inserted += 1
        
        print(f"   ✅ {feedbacks_inserted} feedbacks inseridos")
        
        # 2. Dados de performance de materiais
        print("\n2️⃣ INSERINDO PERFORMANCE DE MATERIAIS")
        
        performance_inserted = 0
        for material in materials:
            for client in clients:
                recommendation_count = random.randint(5, 25)
                positive_feedback = random.randint(0, recommendation_count)
                negative_feedback = random.randint(0, recommendation_count - positive_feedback)
                conversion_rate = positive_feedback / recommendation_count if recommendation_count > 0 else 0
                avg_confidence = random.uniform(70, 90)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO material_performance_history 
                    (material, client_code, recommendation_count, positive_feedback_count, 
                     negative_feedback_count, conversion_rate, avg_confidence_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (material, client, recommendation_count, positive_feedback, 
                      negative_feedback, conversion_rate, avg_confidence, datetime.now().isoformat()))
                
                performance_inserted += 1
        
        print(f"   ✅ {performance_inserted} registros de performance inseridos")
        
        # 3. Histórico de ajustes de pesos
        print("\n3️⃣ INSERINDO HISTÓRICO DE AJUSTES")
        
        weight_types = ['gap_analysis_weight', 'seasonality_weight', 'benchmark_weight', 
                       'historical_performance_weight', 'confidence_threshold']
        
        adjustments_inserted = 0
        for i in range(10):  # 10 ajustes históricos
            weight_type = random.choice(weight_types)
            old_value = random.uniform(0.1, 0.8)
            new_value = old_value + random.uniform(-0.1, 0.1)
            new_value = max(0.05, min(0.95, new_value))  # Manter entre 0.05 e 0.95
            
            days_ago = random.randint(1, 60)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute("""
                INSERT INTO ml_weight_adjustments 
                (weight_type, old_value, new_value, adjustment_reason, 
                 feedback_count, timestamp, performance_metric)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (weight_type, old_value, new_value, 
                  f"Ajuste automático baseado em feedback", 
                  random.randint(10, 50), timestamp.isoformat(), 
                  random.uniform(0.6, 0.9)))
            
            adjustments_inserted += 1
        
        print(f"   ✅ {adjustments_inserted} ajustes de pesos inseridos")
        
        conn.commit()
        conn.close()
        
        # 4. Verificar dados inseridos
        print("\n4️⃣ VERIFICANDO DADOS INSERIDOS")
        
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM recommendation_feedback")
        feedback_count = cursor.fetchone()[0]
        print(f"   📊 Total feedbacks: {feedback_count}")
        
        cursor.execute("SELECT COUNT(*) FROM material_performance_history")
        performance_count = cursor.fetchone()[0]
        print(f"   📊 Total performance records: {performance_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ml_weight_adjustments")
        adjustments_count = cursor.fetchone()[0]
        print(f"   📊 Total weight adjustments: {adjustments_count}")
        
        # Estatísticas de feedback por tipo
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM recommendation_feedback 
            GROUP BY feedback_type
        """)
        feedback_stats = cursor.fetchall()
        
        print(f"\n   📈 Distribuição de Feedbacks:")
        for feedback_type, count in feedback_stats:
            print(f"      {feedback_type}: {count}")
        
        conn.close()
        
        print(f"\n🎉 === DADOS DE TESTE INSERIDOS COM SUCESSO ===")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados de teste: {e}")
        return False

def test_ml_system():
    """Testa o sistema ML com os dados populados"""
    print("\n🤖 === TESTANDO SISTEMA ML ===")
    
    try:
        from utils.ml_feedback_learning import MLFeedbackLearningSystem
        
        learning_system = MLFeedbackLearningSystem()
        
        # Testar análise de padrões
        print("1️⃣ TESTANDO ANÁLISE DE PADRÕES")
        metrics = learning_system.analyze_feedback_patterns(30)
        
        print(f"   📊 Total feedbacks: {metrics.total_feedbacks}")
        print(f"   📈 Taxa positiva: {metrics.positive_rate:.2%}")
        print(f"   📉 Taxa negativa: {metrics.negative_rate:.2%}")
        print(f"   🎯 Taxa relevância: {metrics.relevance_rate:.2%}")
        
        # Testar ciclo de aprendizado
        print("\n2️⃣ TESTANDO CICLO DE APRENDIZADO")
        result = learning_system.run_daily_learning_cycle()
        
        print(f"   ✅ Sucesso: {result.get('success', False)}")
        print(f"   📊 Feedbacks processados: {result.get('feedbacks_processed', 0)}")
        print(f"   🔄 Modelo atualizado: {result.get('model_updated', False)}")
        print(f"   💡 Melhorias: {result.get('improvements', 'Nenhuma')}")
        print(f"   📝 Mensagem: {result.get('message', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar sistema ML: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando população de dados de teste...")
    
    success = populate_test_feedback_data()
    
    if success:
        test_ml_system()
    
    print(f"\n⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Dados de teste prontos para validar funcionalidades ML!")