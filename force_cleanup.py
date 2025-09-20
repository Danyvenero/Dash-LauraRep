#!/usr/bin/env python3
"""
Script de Reinicialização Forçada
Finaliza todos os processos Python e limpa recursos
"""

import os
import subprocess
import time
import sys

def force_cleanup():
    """Finaliza todos os processos Python e limpa recursos"""
    
    print("🚨 LIMPEZA FORÇADA DO SISTEMA")
    print("=" * 50)
    
    try:
        # 1. Finaliza todos os processos Python
        print("🔫 Finalizando todos os processos Python...")
        result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                              capture_output=True, text=True)
        if "ÊXITO" in result.stdout or "SUCCESS" in result.stdout:
            print("   ✅ Processos Python finalizados")
        else:
            print("   ⚠️ Nenhum processo Python encontrado ou erro ao finalizar")
        
        time.sleep(2)
        
        # 2. Verifica se ainda há processos
        print("🔍 Verificando processos restantes...")
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') if 'python.exe' in line.lower()]
        
        if python_processes:
            print(f"   ⚠️ Ainda há {len(python_processes)} processos Python:")
            for proc in python_processes[:3]:  # Mostra até 3
                print(f"      {proc.strip()}")
        else:
            print("   ✅ Nenhum processo Python encontrado")
        
        # 3. Limpa conexões de rede pendentes
        print("🌐 Verificando conexões na porta 8050...")
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        connections_8050 = [line for line in result.stdout.split('\n') if ':8050' in line]
        
        if connections_8050:
            print(f"   ⚠️ {len(connections_8050)} conexões na porta 8050")
            # Mostra apenas algumas para não poluir
            for conn in connections_8050[:5]:
                print(f"      {conn.strip()}")
        else:
            print("   ✅ Porta 8050 limpa")
        
        # 4. Backup do log atual
        print("📝 Fazendo backup do log...")
        if os.path.exists('user_interactions.log'):
            backup_name = f"user_interactions_backup_{int(time.time())}.log"
            try:
                import shutil
                shutil.copy2('user_interactions.log', backup_name)
                print(f"   ✅ Backup criado: {backup_name}")
                
                # Limpa o log atual
                with open('user_interactions.log', 'w') as f:
                    f.write(f"# Log reiniciado em {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                print("   ✅ Log principal limpo")
            except Exception as e:
                print(f"   ⚠️ Erro no backup: {e}")
        else:
            print("   ℹ️ Nenhum log encontrado")
        
        print("\n" + "=" * 50)
        print("✅ LIMPEZA CONCLUÍDA!")
        print("\n💡 Próximos passos:")
        print("   1. Aguarde 10 segundos")
        print("   2. Inicie o dashboard: python app.py")
        print("   3. Teste o treinamento otimizado")
        print("\n🎯 Com as correções aplicadas:")
        print("   • Timeout funcional no Windows")
        print("   • Proteção contra múltiplas execuções")
        print("   • Dataset limitado a 15K registros")
        print("   • Tempo esperado: 1-3 minutos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        return False

if __name__ == "__main__":
    success = force_cleanup()
    
    if success:
        print("\n⏳ Aguardando 10 segundos para estabilização...")
        for i in range(10, 0, -1):
            print(f"   {i}...", end='\r')
            time.sleep(1)
        print("\n🚀 Sistema pronto para reiniciar!")
    else:
        print("\n⚠️ Limpeza teve problemas. Tente reiniciar manualmente.")
    
    print("\n🎯 Para iniciar o dashboard:")
    print("   python app.py")
    print("   ou")
    print("   python flask_app.py")