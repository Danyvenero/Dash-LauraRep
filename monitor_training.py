#!/usr/bin/env python3
"""
Monitor de Treinamento ML - Dash Laura Rep
Script para monitorar o progresso do treinamento do modelo ML
"""

import time
import psutil
import os
from datetime import datetime

def monitor_training():
    """Monitora processos Python e uso de recursos durante o treinamento"""
    
    print("🔍 Monitor de Treinamento ML - Dash Laura Rep")
    print("=" * 60)
    
    start_time = time.time()
    
    while True:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - start_time
            
            # Encontra processos Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        mem_mb = proc.info['memory_info'].rss / 1024 / 1024
                        cpu = proc.info.get('cpu_percent', 0)
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'memory_mb': mem_mb,
                            'cpu_percent': cpu
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Limpa tela
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"🔍 Monitor de Treinamento ML - {current_time}")
            print(f"⏱️  Tempo decorrido: {elapsed:.0f}s ({elapsed/60:.1f} min)")
            print("=" * 60)
            
            if python_processes:
                print(f"🐍 Processos Python ativos: {len(python_processes)}")
                print("-" * 40)
                
                total_memory = 0
                for proc in sorted(python_processes, key=lambda x: x['memory_mb'], reverse=True):
                    total_memory += proc['memory_mb']
                    print(f"  PID {proc['pid']:>6} | {proc['memory_mb']:>6.1f} MB | CPU: {proc['cpu_percent']:>4.1f}%")
                
                print("-" * 40)
                print(f"💾 Memória total Python: {total_memory:.1f} MB")
                
                # Alerta se algum processo está usando muita memória
                for proc in python_processes:
                    if proc['memory_mb'] > 1000:  # > 1GB
                        print(f"⚠️  ALERTA: PID {proc['pid']} usando {proc['memory_mb']:.1f} MB!")
                
            else:
                print("❌ Nenhum processo Python encontrado")
            
            # Uso geral do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            print("\n💻 Sistema:")
            print(f"  CPU: {cpu_percent:.1f}%")
            print(f"  RAM: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}/{memory.total/1024/1024/1024:.1f} GB)")
            
            # Verifica se log foi atualizado recentemente
            try:
                log_path = "user_interactions.log"
                if os.path.exists(log_path):
                    log_time = os.path.getmtime(log_path)
                    last_log = time.time() - log_time
                    print(f"📝 Último log: {last_log:.0f}s atrás")
                    
                    if last_log > 300:  # 5 minutos sem logs
                        print("⚠️  ALERTA: Log não atualizado há mais de 5 min!")
            except:
                pass
            
            print("\n💡 Dicas:")
            print("  • Ctrl+C para sair do monitor")
            print("  • Processo normal: 1-3 processos Python, <500MB cada")
            print("  • Timeout automático: 5 minutos na extração de features")
            
            if elapsed > 600:  # 10 minutos
                print("⚠️  ALERTA: Treinamento rodando há mais de 10 minutos!")
                print("          Considere reiniciar se travado.")
            
            time.sleep(5)  # Atualiza a cada 5 segundos
            
        except KeyboardInterrupt:
            print("\n👋 Monitor finalizado pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_training()