"""
Teste específico para o treinamento do modelo ML
"""

import sys
import os
import sqlite3
import pandas as pd
import traceback

# Adicionar o diretório atual ao path
sys.path.insert(0, os.getcwd())

def test_ml_training():
    """Testa especificamente o treinamento do modelo ML"""
    
    print("🤖 TESTE DE TREINAMENTO DO MODELO ML")
    print("=" * 50)
    
    try:
        print("📦 Importando módulos...")
        from utils.ml_recommendations import purchase_recommender
        
        print("✅ Importação bem-sucedida")
        
        # Conectar ao banco
        print("\n🗄️ Conectando ao banco de dados...")
        conn = sqlite3.connect('laura_dados.db')
        
        # Verificar se há dados de entrada
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entrada WHERE data_faturamento >= date('now', '-365 days')")
        vendas_count = cursor.fetchone()[0]
        print(f"📊 Vendas nos últimos 12 meses: {vendas_count}")
        
        if vendas_count < 10:
            print("⚠️ Poucos dados para treinamento - criando dados de teste...")
            
            # Criar alguns dados de teste
            test_data = []
            for i in range(20):
                test_data.append({
                    'material': f'MAT{i:03d}',
                    'cod_cliente': f'CLI{i%5:02d}',
                    'vlr_entrada': 1000 + (i * 100),
                    'data_faturamento': f'2024-{(i%12)+1:02d}-15'
                })
            
            df_test = pd.DataFrame(test_data)
            df_test.to_sql('entrada', conn, if_exists='append', index=False)
            print(f"✅ Criados {len(df_test)} registros de teste")
        
        # Carregar dados de vendas
        print("\n📥 Carregando dados de vendas...")
        vendas_df = pd.read_sql_query("""
            SELECT material, cod_cliente, vlr_entrada, data_faturamento 
            FROM entrada 
            WHERE data_faturamento >= date('now', '-365 days')
            ORDER BY data_faturamento
        """, conn)
        
        print(f"📊 Dados carregados: {len(vendas_df)} registros")
        
        # Carregar dados de cotações (pode estar vazio)
        print("📥 Carregando dados de cotações...")
        try:
            cotacoes_df = pd.read_sql_query("""
                SELECT material, cod_cliente, preco, data 
                FROM cotacoes 
                WHERE data >= date('now', '-365 days')
            """, conn)
            print(f"📊 Cotações carregadas: {len(cotacoes_df)} registros")
        except:
            cotacoes_df = pd.DataFrame()
            print("📊 Nenhuma cotação encontrada - criando DataFrame vazio")
        
        # Tentar treinar o modelo
        print("\n🤖 Iniciando treinamento do modelo...")
        
        # Forçar retreinamento
        purchase_recommender.is_trained = False
        
        success = purchase_recommender.train_repurchase_model(
            vendas_df=vendas_df,
            cotacoes_df=cotacoes_df,
            produtos_cotados_df=pd.DataFrame(),
            retrain=True
        )
        
        if success:
            print("✅ TREINAMENTO BEM-SUCEDIDO!")
            
            # Verificar informações do modelo
            model_info = purchase_recommender.get_model_info()
            print(f"📈 Versão do modelo: {model_info.get('version', 'N/A')}")
            print(f"📊 Features usadas: {model_info.get('features_count', 'N/A')}")
            print(f"🎯 Acurácia: {model_info.get('accuracy', 'N/A')}")
            
        else:
            print("❌ FALHA NO TREINAMENTO")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"   Traceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ml_training()
    if success:
        print("\n🎉 Modelo treinado com sucesso!")
    else:
        print("\n💔 Problemas no treinamento do modelo")