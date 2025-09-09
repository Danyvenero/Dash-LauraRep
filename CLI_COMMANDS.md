# 🛠️ Comandos CLI - Dashboard WEG

Este documento explica como usar os comandos de linha de comando para gerenciar o banco de dados do Dashboard WEG.

## 📋 Comandos Disponíveis

### 🔧 Inicializar Banco de Dados
```bash
# Usando o script personalizado
flask-cli.bat init-db

# Ou diretamente com Python
python -c "from utils.db import init_db; init_db()"
```
**O que faz:** Cria todas as tabelas necessárias e insere o usuário admin padrão.

### 📊 Ver Estatísticas
```bash
# Usando o script personalizado
flask-cli.bat stats

# Ou diretamente com Python
python -c "from utils.db import get_dataset_statistics; stats = get_dataset_statistics(); print(stats)"
```
**O que faz:** Mostra total de datasets, vendas, cotações e produtos cotados.

### 🔍 Verificar Banco
```bash
# Usando o script personalizado
flask-cli.bat check

# Ou diretamente com Python
python -c "import os, sqlite3; print('Banco existe:', os.path.exists('instance/database.sqlite'))"
```
**O que faz:** Verifica se o banco existe e mostra informações básicas.

### 💡 Ajuda
```bash
flask-cli.bat help
```
**O que faz:** Mostra todos os comandos disponíveis.

## 🚀 Execução Rápida

### Problema Original
Você tentou usar:
```bash
flask init-db  # ❌ Comando não existia
```

### Solução Criada
Agora você pode usar:
```bash
flask-cli.bat init-db  # ✅ Funciona perfeitamente!
```

## 🔧 Scripts Alternativos

### Para Desenvolvedores
Se preferir usar Python diretamente:

```python
# Inicializar banco
from utils.db import init_db
init_db()

# Ver estatísticas
from utils.db import get_dataset_statistics
stats = get_dataset_statistics()
print(stats)

# Verificar tabelas
import sqlite3
conn = sqlite3.connect('instance/database.sqlite')
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tabelas:", [t[0] for t in tables])
conn.close()
```

### Para Administradores
Use o script de gerenciamento completo:
```bash
python db_manager.py init    # Inicializar
python db_manager.py stats   # Estatísticas
python db_manager.py check   # Verificar
python db_manager.py reset   # ⚠️ Resetar (CUIDADO!)
```

## 📁 Arquivos Criados

- `flask-cli.bat` - Script batch para comandos rápidos
- `db_manager.py` - Script Python completo para gerenciamento
- `webapp/cli.py` - Comandos Flask personalizados (para futuro)
- `flask_app.py` - Configuração Flask CLI (para futuro)

## ✅ Teste Rápido

Execute agora mesmo:
```bash
flask-cli.bat init-db
flask-cli.bat stats
```

Resultado esperado:
```
🔧 Inicializando banco de dados...
✅ Banco de dados inicializado com sucesso

📊 Obtendo estatísticas do banco...
Datasets: 0
Vendas: 0
Cotações: 0
Produtos: 0
```

## 🎯 Próximos Passos

1. ✅ **Inicialize o banco:** `flask-cli.bat init-db`
2. ✅ **Execute a aplicação:** `python app.py`
3. ✅ **Faça upload de dados** via interface web
4. ✅ **Verifique resultados:** `flask-cli.bat stats`
