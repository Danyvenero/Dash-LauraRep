# 📍 Como Executar os Comandos - Guia Visual

## 🖥️ Onde Digitar os Comandos?

Você precisa usar um **Terminal** (também chamado de **Prompt de Comando** ou **Console**).

---

## 🪟 Abrindo o Terminal

### Windows
1. Pressione `Windows + R`
2. Digite `cmd` e pressione Enter
   - OU
3. Pressione `Windows + X` e escolha "Terminal" ou "Prompt de Comando"
   - OU
4. No menu Iniciar, procure por "Prompt de Comando" ou "PowerShell"

### Mac
1. Pressione `Cmd + Espaço`
2. Digite "Terminal" e pressione Enter
   - OU
3. Vá em Aplicações → Utilitários → Terminal

### Linux
1. Pressione `Ctrl + Alt + T`
   - OU
2. Procure por "Terminal" no menu de aplicações

---

## 📂 Navegando até o Projeto

### Passo 1: Verificar onde você está

No terminal, digite:
```bash
pwd
```
(No Windows, use: `cd`)

Isso mostra o diretório atual.

---

### Passo 2: Navegar até o projeto

#### Se o projeto está em `/workspace`:
```bash
cd /workspace
```

#### Se o projeto está em outro lugar (exemplo: Desktop):
```bash
# Windows
cd C:\Users\SeuNome\Desktop\dash-laurarep

# Mac/Linux
cd ~/Desktop/dash-laurarep
```

#### Se você não sabe onde está o projeto:

**Opção A - Procurar pelo nome do projeto:**
```bash
# Windows
dir /s /b | findstr "dash-laurarep"

# Mac/Linux
find ~ -name "dash-laurarep" -type d 2>/dev/null
```

**Opção B - Se você clonou do GitHub:**
O projeto geralmente está em:
- Windows: `C:\Users\SeuNome\Documents\` ou `C:\Users\SeuNome\Desktop\`
- Mac: `~/Documents/` ou `~/Desktop/`
- Linux: `~/` ou `~/Documents/`

---

### Passo 3: Verificar se está no lugar certo

Depois de navegar, verifique se está no diretório correto:
```bash
# Windows
dir

# Mac/Linux
ls
```

Você deve ver pastas como:
- `backend/`
- `frontend/`
- `utils/`
- `webapp/`
- `README.md`
- etc.

---

## 🚀 Executando os Comandos

### Agora que está no diretório do projeto:

#### 1. Abrir Terminal 1 (Backend)

```bash
# Você já está em /workspace (ou onde está o projeto)
# Agora entre na pasta backend:
cd backend

# Verificar se está certo:
# Windows: dir
# Mac/Linux: ls
# Deve mostrar: requirements.txt, api/, etc.

# Instalar dependências:
pip install -r requirements.txt

# Executar backend:
python -m uvicorn backend.api.main:app --reload --port 8000
```

**✅ Deve aparecer algo como:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**⚠️ Deixe este terminal aberto!**

---

#### 2. Abrir Terminal 2 (Frontend)

**Abra um NOVO terminal** (não feche o primeiro!)

```bash
# Navegar até o projeto novamente:
cd /workspace
# (ou o caminho onde está seu projeto)

# Entrar na pasta frontend:
cd frontend

# Verificar se está certo:
# Windows: dir
# Mac/Linux: ls
# Deve mostrar: package.json, src/, etc.

# Instalar dependências:
npm install

# Executar frontend:
npm run dev
```

**✅ Deve aparecer algo como:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**⚠️ Deixe este terminal aberto também!**

---

## 📋 Resumo Visual

```
┌─────────────────────────────────────────┐
│  Terminal 1 (Backend)                   │
├─────────────────────────────────────────┤
│  $ cd /workspace                        │
│  $ cd backend                           │
│  $ pip install -r requirements.txt      │
│  $ python -m uvicorn ...                │
│  ✅ Rodando em http://localhost:8000    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Terminal 2 (Frontend)                  │
├─────────────────────────────────────────┤
│  $ cd /workspace                        │
│  $ cd frontend                          │
│  $ npm install                          │
│  $ npm run dev                          │
│  ✅ Rodando em http://localhost:3000    │
└─────────────────────────────────────────┘
```

---

## 🎯 Comandos Essenciais

### Navegação
```bash
# Ver onde estou
pwd          # Mac/Linux
cd           # Windows

# Listar arquivos
ls           # Mac/Linux
dir          # Windows

# Entrar em uma pasta
cd nome_da_pasta

# Voltar uma pasta
cd ..

# Voltar para a pasta home
cd ~         # Mac/Linux
cd %USERPROFILE%  # Windows
```

### Verificar se está no lugar certo
```bash
# Ver estrutura do projeto
# Windows:
dir /b

# Mac/Linux:
ls -la
```

Você deve ver:
- ✅ `backend/` - pasta do backend
- ✅ `frontend/` - pasta do frontend
- ✅ `utils/` - utilitários
- ✅ `README.md` - documentação

---

## 🐛 Problemas Comuns

### "cd: no such file or directory"
**Problema**: A pasta não existe ou você está no lugar errado.

**Solução**:
1. Verifique onde está: `pwd` (Mac/Linux) ou `cd` (Windows)
2. Liste os arquivos: `ls` ou `dir`
3. Navegue corretamente até a pasta

### "command not found"
**Problema**: Comando não existe ou não está instalado.

**Solução**:
- Windows: Use `python` em vez de `python3`
- Verifique se Python está instalado: `python --version`
- Verifique se Node está instalado: `node --version`

### "Permission denied"
**Problema**: Sem permissão.

**Solução**:
- Mac/Linux: Use `sudo` se necessário (cuidado!)
- Verifique permissões da pasta

---

## 📍 Exemplo Completo Passo a Passo

### Cenário: Projeto está em `C:\Users\João\Desktop\dash-laurarep`

#### Terminal 1 (Backend):
```bash
C:\Users\João> cd Desktop
C:\Users\João\Desktop> cd dash-laurarep
C:\Users\João\Desktop\dash-laurarep> cd backend
C:\Users\João\Desktop\dash-laurarep\backend> pip install -r requirements.txt
C:\Users\João\Desktop\dash-laurarep\backend> python -m uvicorn backend.api.main:app --reload --port 8000
```

#### Terminal 2 (Frontend):
```bash
C:\Users\João> cd Desktop
C:\Users\João\Desktop> cd dash-laurarep
C:\Users\João\Desktop\dash-laurarep> cd frontend
C:\Users\João\Desktop\dash-laurarep\frontend> npm install
C:\Users\João\Desktop\dash-laurarep\frontend> npm run dev
```

---

## 🎓 Dica para Iniciantes

Se você está usando **VS Code** ou **Cursor**:

1. Abra a pasta do projeto no editor
2. Pressione `` Ctrl + ` `` (backtick) para abrir o terminal integrado
3. O terminal já estará na pasta do projeto!
4. Basta digitar `cd backend` ou `cd frontend`

---

## ✅ Checklist

Antes de executar, verifique:

- [ ] Terminal aberto
- [ ] Estou no diretório do projeto (vejo as pastas `backend/` e `frontend/`)
- [ ] Python instalado (`python --version`)
- [ ] Node.js instalado (`node --version`)
- [ ] Tenho dois terminais abertos (um para backend, outro para frontend)

---

**Agora você sabe onde e como executar os comandos! 🚀**

Se ainda tiver dúvidas, me diga qual sistema operacional você usa e onde está o projeto!
