import sys
sys.path.append('.')

print("Testando imports...")
try:
    from utils.db import get_dataset_statistics
    print("✅ Import utils.db OK")
    
    stats = get_dataset_statistics()
    print("✅ get_dataset_statistics OK")
    print(stats)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
