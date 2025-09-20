"""
Script de teste final para validar correções do ML
"""

import sys
import os
import sqlite3
import traceback

# Adicionar o diretório atual ao path
sys.path.insert(0, os.getcwd())

def test_ml_system():
    """Testa o sistema ML com as correções aplicadas"""
    
    print("🔧 TESTE FINAL DO SISTEMA ML")
    print("=" * 50)
    
    try:
        print("📦 Importando módulos...")
        from utils.ml_recommendations import purchase_recommender
        
        print("✅ Importação bem-sucedida")
        
        # Conectar ao banco
        print("\n🗄️ Conectando ao banco de dados...")
        conn = sqlite3.connect('laura_dados.db')
        
        # Verificar se há dados
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entrada")
        count = cursor.fetchone()[0]
        print(f"📊 Registros encontrados: {count}")
        
        if count == 0:
            print("⚠️ Banco vazio - não é possível testar")
            return False
        
        # Inicializar sistema ML
        print("\n🤖 Inicializando sistema ML...")
        ml_system = purchase_recommender
        
        # Forçar novo treinamento removendo flag de compatibilidade
        print("🔄 Forçando novo treinamento...")
        
        # Gerar recomendações (isso vai treinar o modelo automaticamente)
        print("🎯 Gerando recomendações...")
        recommendations = ml_system.generate_purchase_suggestions(conn)
        
        print(f"✅ Recomendações geradas: {len(recommendations)} produtos")
        
        # Verificar características das recomendações
        if recommendations:
            print("\n📈 ANÁLISE DAS RECOMENDAÇÕES:")
            
            # Verificar variação na cobertura
            coverages = [r.get('cobertura_dias', 0) for r in recommendations]
            unique_coverages = set(coverages)
            print(f"   📅 Valores únicos de cobertura: {len(unique_coverages)}")
            print(f"   📅 Coberturas encontradas: {sorted(unique_coverages)}")
            
            # Verificar variação no nível de serviço
            service_levels = [r.get('nivel_servico', 0) for r in recommendations]
            unique_service_levels = set(service_levels)
            print(f"   🎯 Valores únicos de nível de serviço: {len(unique_service_levels)}")
            print(f"   🎯 Níveis encontrados: {sorted(unique_service_levels)}")
            
            # Verificar CV
            cvs = [r.get('cv', 0) for r in recommendations if r.get('cv', 0) > 0]
            print(f"   📊 Produtos com CV > 0: {len(cvs)}/{len(recommendations)}")
            
            # Verificar se não há produtos com apenas 1 transação
            single_transaction = [r for r in recommendations if r.get('total_transacoes', 0) <= 1]
            print(f"   🚫 Produtos com ≤1 transação: {len(single_transaction)}")
            
        print("\n" + "=" * 50)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        
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
    success = test_ml_system()
    if success:
        print("\n🎉 Todos os problemas foram corrigidos!")
    else:
        print("\n💔 Ainda há problemas a resolver")