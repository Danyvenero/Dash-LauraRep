# ⚡ Teste Rápido - Dashboard WEG

## 🚀 Início Rápido (5 minutos)

### 1. Executar Script de Verificação
```bash
./test_quick.sh
```

Este script verifica:
- ✅ Python instalado
- ✅ Node.js instalado
- ✅ Dependências do backend
- ✅ Dependências do frontend
- ✅ Estrutura de pastas

---

### 2. Iniciar Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000
```

**✅ Backend rodando**: http://localhost:8000  
**📚 API Docs**: http://localhost:8000/api/docs

---

### 3. Iniciar Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

**✅ Frontend rodando**: http://localhost:3000

---

### 4. Testar Login

1. Acesse: http://localhost:3000
2. **Criar conta**:
   - Usuário: `teste`
   - Senha: `teste123`
3. **Fazer login**
4. ✅ Deve redirecionar para Visão Geral

---

### 5. Testar Upload (Opcional)

1. Menu → **Configurações**
2. Clique em **"Mostrar Upload"**
3. Faça upload de arquivo Excel de vendas
4. Clique em **"Processar Dados"** (ETL)
5. ✅ Dados devem aparecer nas outras páginas

---

## ✅ Checklist Rápido

- [ ] Backend iniciou sem erros
- [ ] Frontend iniciou sem erros
- [ ] Login funciona
- [ ] Páginas carregam
- [ ] Navegação funciona

---

## 🐛 Problemas Comuns

### Porta em uso?
```bash
# Matar processo na porta 8000
lsof -ti:8000 | xargs kill -9

# Matar processo na porta 3000
lsof -ti:3000 | xargs kill -9
```

### Dependências não instaladas?
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

---

**Pronto! Agora você pode testar todas as funcionalidades! 🎉**

Para mais detalhes, consulte: `GUIA_TESTES.md`
