#!/usr/bin/env python3
"""
Teste do sistema de exportação PDF com dados reais
"""

import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pdf_with_real_data():
    """Testa a criação de PDF com dados similares aos reais"""
    try:
        # Simula dados como vêm do sistema
        suggestions_data = [
            {
                'material': 'MAT001',
                'produto': 'Motor Elétrico WEG 1CV',
                'quantidade_sugerida': 5.0,
                'valor_estimado': 1250.75,
                'classificacao_abc': 'A',
                'classificacao_xyz': '1',
                'confianca': 87.5,
                'score_final': 0.92
            },
            {
                'material': 'MAT002',
                'produto': 'Controlador de Velocidade',
                'quantidade_sugerida': 3.0,
                'valor_estimado': 2100.50,
                'classificacao_abc': 'A',
                'classificacao_xyz': '2',
                'confianca': 79.2,
                'score_final': 0.85
            },
            {
                'material': 'MAT003',
                'produto': 'Sensor de Proximidade',
                'quantidade_sugerida': 10.0,
                'valor_estimado': 450.25,
                'classificacao_abc': 'B',
                'classificacao_xyz': '1',
                'confianca': 65.8,
                'score_final': 0.71
            },
            {
                'material': 'MAT004',
                'produto': 'Cabo de Força 3x2.5mm',
                'quantidade_sugerida': 25.0,
                'valor_estimado': 125.00,
                'classificacao_abc': 'C',
                'classificacao_xyz': '3',
                'confianca': 45.3,
                'score_final': 0.42
            }
        ]
        
        print("📊 Dados de teste criados")
        print(f"   Registros: {len(suggestions_data)}")
        
        # Importa as funções do sistema
        from webapp.purchase_suggestions_callbacks import _create_pdf_report
        
        print("✅ Funções importadas")
        
        # Testa a criação do PDF
        print("🔧 Testando criação do PDF...")
        filepath = _create_pdf_report(suggestions_data)
        
        if filepath:
            print(f"✅ PDF criado com sucesso!")
            print(f"📁 Localização: {filepath}")
            
            # Verifica se o arquivo existe
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"📄 Tamanho do arquivo: {size} bytes")
                return True
            else:
                print("❌ Arquivo não encontrado")
                return False
        else:
            print("❌ Falha na criação do PDF")
            return False
            
    except Exception as e:
        print(f"💥 Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_with_missing_data():
    """Testa com dados incompletos"""
    try:
        print("\n🔧 Testando com dados incompletos...")
        
        # Dados com campos faltando
        incomplete_data = [
            {
                'material': 'MAT005',
                'produto': 'Produto Sem Dados Completos',
                # quantidade_sugerida ausente
                # valor_estimado ausente
                'classificacao_abc': 'B',
                # confianca ausente
            },
            {
                'material': None,  # material nulo
                'produto': '',     # produto vazio
                'quantidade_sugerida': 'invalid',  # tipo inválido
                'valor_estimado': None,
                'classificacao_abc': '',
                'confianca': 'abc'  # valor não numérico
            }
        ]
        
        from webapp.purchase_suggestions_callbacks import _create_pdf_report
        
        filepath = _create_pdf_report(incomplete_data)
        
        if filepath:
            print("✅ PDF criado mesmo com dados incompletos!")
            return True
        else:
            print("⚠️ PDF não foi criado com dados incompletos")
            return False
            
    except Exception as e:
        print(f"⚠️ Erro esperado com dados incompletos: {e}")
        return True  # Erro é esperado

def test_pdf_with_empty_data():
    """Testa com dados vazios"""
    try:
        print("\n🔧 Testando com dados vazios...")
        
        from webapp.purchase_suggestions_callbacks import _create_pdf_report
        
        # Teste com lista vazia
        filepath = _create_pdf_report([])
        
        if not filepath:
            print("✅ Corretamente rejeitou dados vazios")
            return True
        else:
            print("⚠️ Deveria ter rejeitado dados vazios")
            return False
            
    except Exception as e:
        print(f"⚠️ Erro ao testar dados vazios: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Executando testes do sistema de PDF...")
    
    # Teste 1: Dados completos
    test1 = test_pdf_with_real_data()
    
    # Teste 2: Dados incompletos
    test2 = test_pdf_with_missing_data()
    
    # Teste 3: Dados vazios
    test3 = test_pdf_with_empty_data()
    
    print(f"\n📊 Resultados dos testes:")
    print(f"   Dados completos: {'✅ PASSOU' if test1 else '❌ FALHOU'}")
    print(f"   Dados incompletos: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
    print(f"   Dados vazios: {'✅ PASSOU' if test3 else '❌ FALHOU'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")