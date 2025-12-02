# ⚡ Início Rápido - Dashboard WEG

## 🎯 Para Iniciantes

### 1️⃣ Abrir o Terminal

**Windows:**
- Pressione `Windows + R`
- Digite `cmd` e Enter

**Mac:**
- Pressione `Cmd + Espaço`
- Digite "Terminal" e Enter

**Linux:**
- Pressione `Ctrl + Alt + T`

---

### 2️⃣ Ir até o Projeto

No terminal, digite:

```bash
cd /workspace
```

**Se o projeto está em outro lugar**, use o caminho completo:
```bash
# Exemplo Windows:
cd C:\Users\SeuNome\Desktop\dash-laurarep

# Exemplo Mac/Linux:
cd ~/Desktop/dash-laurarep
```

**Verificar se está certo:**
```bash
# Windows:
dir

# Mac/Linux:
ls
```

Você deve ver as pastas `backend/` e `frontend/`.

---

### 3️⃣ Iniciar Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000
```

**✅ Deve aparecer:** `Uvicorn running on http://127.0.0.1:8000`

**⚠️ NÃO FECHE ESTE TERMINAL!**

---

### 4️⃣ Iniciar Frontend (Terminal 2)

**Abra um NOVO terminal** e digite:

```bash
cd /workspace
cd frontend
npm install
npm run dev
```

**✅ Deve aparecer:** `Local: http://localhost:3000/`

**⚠️ NÃO FECHE ESTE TERMINAL!**

---

### 5️⃣ Acessar no Navegador

Abra seu navegador e acesse:

**Frontend:** http://localhost:3000

Você verá a tela de login! 🎉

---

## 🆘 Precisa de Ajuda?

Consulte: `COMO_EXECUTAR.md` para guia detalhado!
