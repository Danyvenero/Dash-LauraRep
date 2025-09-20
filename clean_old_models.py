"""
Script para limpar modelos antigos incompatíveis
"""

import os
import shutil
from pathlib import Path

def clean_old_models():
    """Remove modelos antigos que causam incompatibilidade"""
    
    print("🧹 LIMPANDO MODELOS ANTIGOS INCOMPATÍVEIS")
    print("=" * 50)
    
    # Diretório dos modelos
    model_dir = Path("models")
    
    if model_dir.exists():
        try:
            # Remove todo o diretório de modelos
            shutil.rmtree(model_dir)
            print("✅ Diretório 'models' removido com sucesso")
            
            # Recria o diretório vazio
            model_dir.mkdir(exist_ok=True)
            print("✅ Diretório 'models' recriado")
            
        except Exception as e:
            print(f"❌ Erro ao limpar modelos: {e}")
    else:
        print("📝 Diretório 'models' não existe")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. O sistema irá treinar um novo modelo na próxima execução")
    print("2. O novo modelo será compatível com as features otimizadas")
    print("3. Não haverá mais erro de features inexistentes")
    
    print("\n" + "=" * 50)
    print("✅ LIMPEZA CONCLUÍDA!")

if __name__ == "__main__":
    clean_old_models()