try:
    from webapp import app
    print('✅ App importado com sucesso')
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
