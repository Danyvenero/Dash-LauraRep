@echo off
REM Comandos simplificados para gerenciamento do Dashboard WEG

if "%1"=="init-db" (
    echo 🔧 Inicializando banco de dados...
    python -c "from utils.db import init_db; init_db(); print('✅ Banco de dados inicializado!')"
    goto :end
)

if "%1"=="stats" (
    echo 📊 Obtendo estatísticas do banco...
    python -c "from utils.db import get_dataset_statistics; stats = get_dataset_statistics(); print(f'Datasets: {stats[\"total_datasets\"]}'); print(f'Vendas: {stats[\"total_vendas\"]}'); print(f'Cotações: {stats[\"total_cotacoes\"]}'); print(f'Produtos: {stats[\"total_produtos_cotados\"]}')"
    goto :end
)

if "%1"=="check" (
    echo 🔍 Verificando banco de dados...
    python -c "import os; print('✅ Banco existe:', os.path.exists('instance/database.sqlite')); import sqlite3; conn = sqlite3.connect('instance/database.sqlite'); cursor = conn.cursor(); tables = cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall(); print(f'📋 Tabelas: {len(tables)}'); conn.close()"
    goto :end
)

if "%1"=="help" (
    echo 💡 COMANDOS DISPONÍVEIS:
    echo   flask-cli init-db    - Inicializa banco de dados
    echo   flask-cli stats      - Mostra estatísticas
    echo   flask-cli check      - Verifica integridade
    echo   flask-cli help       - Esta ajuda
    goto :end
)

echo ❌ Comando desconhecido: %1
echo 💡 Use: flask-cli help

:end
