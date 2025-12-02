# ⚡ Quick Start - Dashboard WEG

## 🚀 Início Rápido (5 minutos)

### 1. Backend (Terminal 1)

```bash
# Instalar dependências
cd backend
pip install -r requirements.txt

# Executar API
python -m uvicorn backend.api.main:app --reload --port 8000
```

✅ API rodando em: http://localhost:8000  
📚 Docs: http://localhost:8000/api/docs

### 2. Frontend (Terminal 2)

```bash
# Instalar dependências
cd frontend
npm install

# Executar app
npm run dev
```

✅ App rodando em: http://localhost:3000

### 3. Acessar

1. Abra http://localhost:3000
2. Faça login (ou crie uma conta)
3. Explore o dashboard!

---

## 🔧 Troubleshooting

### Erro: "Module not found"
```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install
```

### Erro: "Port already in use"
```bash
# Matar processo na porta 8000
lsof -ti:8000 | xargs kill -9

# Matar processo na porta 3000
lsof -ti:3000 | xargs kill -9
```

### Erro: "Database not found"
```bash
# Criar banco de dados
python setup_database.py
```

---

## 📝 Credenciais Padrão

**Usuário**: admin  
**Senha**: admin123

⚠️ Altere após o primeiro login!

---

## 🎯 Próximos Passos

1. ✅ Backend e Frontend rodando
2. 📤 Fazer upload de dados (vendas/cotações)
3. 📊 Explorar as análises
4. 🎨 Personalizar conforme necessário

---

**Precisa de ajuda?** Consulte:
- `README_MIGRACAO.md` - Guia completo
- `ANALISE_E_PLANO_MIGRACAO.md` - Análise detalhada
- `MELHORIAS_E_SUGESTOES.md` - Melhorias sugeridas
