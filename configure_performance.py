"""
Configurador de Performance - Dashboard Laura Representações
Script para ajustar configurações de performance conforme necessidade
"""

import json
import os
from pathlib import Path

class PerformanceConfigurator:
    """Configurador de performance da aplicação"""
    
    def __init__(self):
        self.config_file = Path("performance_config.json")
        self.default_config = {
            "startup": {
                "enable_preload": False,
                "db_migration_skip_when_current": True,
                "lazy_ml_loading": True,
                "data_loading_limit": 1000
            },
            "cache": {
                "ttl_seconds": 180,
                "max_size": 50,
                "enable_data_cache": True
            },
            "ml": {
                "lazy_initialization": True,
                "auto_cleanup": True
            },
            "database": {
                "wal_mode": True,
                "busy_timeout": 30000,
                "temp_store_memory": True
            }
        }
        
    def load_config(self):
        """Carrega configuração atual"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.default_config.copy()
    
    def save_config(self, config):
        """Salva configuração"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuração salva em {self.config_file}")
    
    def configure_for_fast_startup(self):
        """Configuração otimizada para startup rápido"""
        config = self.default_config.copy()
        config["startup"]["enable_preload"] = False
        config["startup"]["data_loading_limit"] = 500  # Ainda menor
        config["cache"]["ttl_seconds"] = 300  # Cache mais longo
        
        self.save_config(config)
        print("🚀 Configuração para STARTUP RÁPIDO aplicada:")
        print("  • Preload desabilitado")
        print("  • Limite de dados: 500 registros")
        print("  • Cache otimizado")
        
    def configure_for_performance(self):
        """Configuração balanceada para performance"""
        config = self.default_config.copy()
        config["startup"]["enable_preload"] = True
        config["startup"]["data_loading_limit"] = 2000
        config["cache"]["ttl_seconds"] = 600  # 10 minutos
        config["cache"]["max_size"] = 100
        
        self.save_config(config)
        print("⚡ Configuração para PERFORMANCE aplicada:")
        print("  • Preload habilitado")
        print("  • Limite de dados: 2000 registros")
        print("  • Cache expandido")
        
    def configure_for_development(self):
        """Configuração para desenvolvimento"""
        config = self.default_config.copy()
        config["startup"]["enable_preload"] = False
        config["startup"]["data_loading_limit"] = 100  # Muito pequeno
        config["cache"]["ttl_seconds"] = 60  # Cache curto
        config["ml"]["auto_cleanup"] = True
        
        self.save_config(config)
        print("🛠️ Configuração para DESENVOLVIMENTO aplicada:")
        print("  • Preload desabilitado")
        print("  • Limite de dados: 100 registros")
        print("  • Cache curto (desenvolvimento)")
        
    def show_current_config(self):
        """Mostra configuração atual"""
        config = self.load_config()
        print("📋 CONFIGURAÇÃO ATUAL:")
        print("-" * 40)
        print(f"Startup:")
        print(f"  • Preload: {'✅ Habilitado' if config['startup']['enable_preload'] else '❌ Desabilitado'}")
        print(f"  • Lazy ML: {'✅ Habilitado' if config['startup']['lazy_ml_loading'] else '❌ Desabilitado'}")
        print(f"  • Limite dados: {config['startup']['data_loading_limit']} registros")
        print(f"")
        print(f"Cache:")
        print(f"  • TTL: {config['cache']['ttl_seconds']}s")
        print(f"  • Tamanho máximo: {config['cache']['max_size']}")
        print(f"")
        print(f"ML:")
        print(f"  • Lazy loading: {'✅ Habilitado' if config['ml']['lazy_initialization'] else '❌ Desabilitado'}")
        
    def benchmark_current_config(self):
        """Executa benchmark com configuração atual"""
        print("🔍 Executando benchmark com configuração atual...")
        os.system("python benchmark_startup.py")

def main():
    configurator = PerformanceConfigurator()
    
    print("🚀 CONFIGURADOR DE PERFORMANCE")
    print("Dashboard Laura Representações")
    print("=" * 50)
    
    while True:
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("1. 🚀 Configurar para STARTUP RÁPIDO")
        print("2. ⚡ Configurar para PERFORMANCE")  
        print("3. 🛠️ Configurar para DESENVOLVIMENTO")
        print("4. 📊 Ver configuração atual")
        print("5. 🔍 Executar benchmark")
        print("6. ❌ Sair")
        
        choice = input("\n👉 Escolha uma opção (1-6): ").strip()
        
        if choice == "1":
            configurator.configure_for_fast_startup()
        elif choice == "2":
            configurator.configure_for_performance()
        elif choice == "3":
            configurator.configure_for_development()
        elif choice == "4":
            configurator.show_current_config()
        elif choice == "5":
            configurator.benchmark_current_config()
        elif choice == "6":
            print("👋 Saindo do configurador...")
            break
        else:
            print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()