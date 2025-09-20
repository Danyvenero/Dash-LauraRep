"""
Teste do treinamento ML com dados sintéticos
"""

import sys
import os
import pandas as pd
import traceback
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path
sys.path.insert(0, os.getcwd())

def create_synthetic_data():
    """Cria dados sintéticos para teste"""
    
    print("🏭 Criando dados sintéticos...")
    
    # Dados de vendas sintéticas
    vendas_data = []
    base_date = datetime.now() - timedelta(days=365)
    
    materials = ['MAT001', 'MAT002', 'MAT003', 'MAT004', 'MAT005']
    clients = ['CLI01', 'CLI02', 'CLI03', 'CLI04', 'CLI05']
    
    for i in range(100):  # 100 registros de vendas
        material = materials[i % len(materials)]
        client = clients[i % len(clients)]
        date = base_date + timedelta(days=i*3)
        
        vendas_data.append({
            'material': material,
            'cod_cliente': client,
            'vlr_entrada': 1000 + (i * 50),
            'vlr_rol': 1000 + (i * 50),  # Adicionar vlr_rol para compatibilidade
            'data_faturamento': date.strftime('%Y-%m-%d')
        })
    
    vendas_df = pd.DataFrame(vendas_data)
    vendas_df['data_faturamento'] = pd.to_datetime(vendas_df['data_faturamento'])
    
    # Dados de cotações sintéticas
    cotacoes_data = []
    for i in range(50):  # 50 cotações
        material = materials[i % len(materials)]
        client = clients[i % len(clients)]
        date = base_date + timedelta(days=i*5)
        
        cotacoes_data.append({
            'material': material,
            'cod_cliente': client,
            'preco': 1200 + (i * 30),
            'data': date.strftime('%Y-%m-%d')
        })
    
    cotacoes_df = pd.DataFrame(cotacoes_data)
    cotacoes_df['data'] = pd.to_datetime(cotacoes_df['data'])
    
    print(f"✅ Vendas criadas: {len(vendas_df)} registros")
    print(f"✅ Cotações criadas: {len(cotacoes_df)} registros")
    
    return vendas_df, cotacoes_df

def test_ml_training_synthetic():
    """Testa o treinamento ML com dados sintéticos"""
    
    print("🤖 TESTE DE TREINAMENTO ML COM DADOS SINTÉTICOS")
    print("=" * 60)
    
    try:
        print("📦 Importando módulos...")
        from utils.ml_recommendations import purchase_recommender
        
        print("✅ Importação bem-sucedida")
        
        # Criar dados sintéticos
        vendas_df, cotacoes_df = create_synthetic_data()
        
        # Forçar novo treinamento
        print("\n🔄 Forçando novo treinamento...")
        purchase_recommender.is_trained = False
        
        # Tentar treinar o modelo
        print("\n🤖 Iniciando treinamento do modelo...")
        
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
            print(f"\n📊 INFORMAÇÕES DO MODELO:")
            print(f"   🔢 Versão: {model_info.get('version', 'N/A')}")
            print(f"   📈 Features: {model_info.get('features_count', 'N/A')}")
            print(f"   🎯 Acurácia: {model_info.get('accuracy', 'N/A'):.3f}" if model_info.get('accuracy') else "   🎯 Acurácia: N/A")
            print(f"   📅 Treinado em: {model_info.get('train_date', 'N/A')}")
            
            # Testar predição
            print("\n🔮 Testando predição...")
            pred_result = purchase_recommender.predict_repurchase_probability(
                vendas_df=vendas_df,
                cotacoes_df=cotacoes_df,
                produtos_cotados_df=pd.DataFrame()
            )
            
            if not pred_result.empty:
                print(f"✅ Predições geradas: {len(pred_result)} registros")
                print(f"   📊 Range probabilidades: {pred_result['prob_recompra_ml'].min():.3f} - {pred_result['prob_recompra_ml'].max():.3f}")
            else:
                print("⚠️ Nenhuma predição gerada")
            
        else:
            print("❌ FALHA NO TREINAMENTO")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"   Traceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ml_training_synthetic()
    if success:
        print("\n🎉 TESTE COMPLETO - MODELO FUNCIONANDO!")
    else:
        print("\n💔 PROBLEMAS DETECTADOS NO MODELO")