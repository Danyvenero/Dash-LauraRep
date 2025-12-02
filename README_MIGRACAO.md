# 🚀 Dashboard WEG - Migração para React + Tailwind

## 📋 Visão Geral da Migração

Este projeto foi migrado de **Dash (Python)** para uma arquitetura moderna com:
- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI (Python) - API REST
- **Banco de Dados**: SQLite (mantido)

---

## 🏗️ Estrutura do Projeto

```
dashboard-weg/
├── backend/                    # API REST (FastAPI)
│   ├── api/
│   │   ├── main.py           # Aplicação FastAPI
│   │   ├── routes/           # Endpoints da API
│   │   │   ├── auth.py       # Autenticação JWT
│   │   │   ├── vendas.py     # Endpoints de vendas
│   │   │   ├── cotacoes.py   # Endpoints de cotações
│   │   │   ├── kpis.py       # Endpoints de KPIs
│   │   │   ├── uploads.py    # Upload de arquivos
│   │   │   ├── reports.py    # Relatórios e exports
│   │   │   └── users.py      # Gestão de usuários
│   │   └── models/           # Schemas Pydantic
│   └── requirements.txt
│
├── frontend/                  # Aplicação React
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── pages/           # Páginas da aplicação
│   │   ├── services/        # Chamadas à API
│   │   ├── store/           # Estado global (Zustand)
│   │   └── utils/           # Utilitários
│   ├── package.json
│   └── vite.config.ts
│
├── utils/                    # Lógica de negócio (mantida)
│   ├── db.py
│   ├── kpis.py
│   ├── etl.py
│   └── ...
│
└── instance/                 # Banco de dados SQLite
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8+
- Node.js 18+
- npm ou yarn

### 1. Backend (API)

```bash
# Instalar dependências
cd backend
pip install -r requirements.txt

# Executar API
python -m backend.api.main
# ou
uvicorn backend.api.main:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`
Documentação Swagger: `http://localhost:8000/api/docs`

### 2. Frontend

```bash
# Instalar dependências
cd frontend
npm install

# Executar em desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:3000`

---

## 🔑 Autenticação

A autenticação foi migrada de **Flask Session** para **JWT (JSON Web Tokens)**:

- **Login**: `POST /api/auth/login`
- **Registro**: `POST /api/auth/register`
- **Verificar Token**: `GET /api/auth/me`

O token JWT é armazenado no localStorage e enviado em todas as requisições via header `Authorization: Bearer <token>`

---

## 📡 Endpoints da API

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Cadastro
- `GET /api/auth/me` - Usuário atual

### KPIs
- `GET /api/kpis/gerais` - KPIs gerais
- `POST /api/kpis/cliente` - KPIs por cliente (com filtros)
- `GET /api/kpis/funil` - Métricas do funil
- `GET /api/kpis/produtos/matrix` - Matriz produtos vs clientes

### Vendas
- `GET /api/vendas/` - Lista vendas
- `GET /api/vendas/stats` - Estatísticas

### Cotações
- `GET /api/cotacoes/` - Lista cotações
- `GET /api/cotacoes/stats` - Estatísticas

### Uploads
- `POST /api/uploads/vendas` - Upload de vendas (Excel)
- `POST /api/uploads/cotacoes` - Upload de cotações (Excel)

### Relatórios
- `GET /api/reports/csv/kpis-cliente` - Export CSV KPIs
- `GET /api/reports/csv/funil-lista-a` - Export Lista A
- `GET /api/reports/csv/funil-lista-b` - Export Lista B

### Usuários
- `GET /api/users/` - Lista usuários
- `POST /api/users/` - Cria usuário
- `DELETE /api/users/{id}` - Deleta usuário

---

## 🎨 Frontend - Tecnologias

- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **Vite** - Build tool
- **React Router** - Roteamento
- **Zustand** - Estado global
- **Axios** - Cliente HTTP
- **Recharts** - Gráficos
- **React Hot Toast** - Notificações

---

## 🔄 Migração de Funcionalidades

### ✅ Implementado

- [x] Sistema de autenticação (JWT)
- [x] Layout principal com sidebar
- [x] Página de Login
- [x] Página Visão Geral (KPIs gerais)
- [x] Página KPIs por Cliente (parcial)
- [x] API REST completa
- [x] Integração frontend-backend

### 🚧 Em Desenvolvimento

- [ ] Página KPIs de Propostas
- [ ] Página Produtos (Bolhas) com gráficos
- [ ] Página Funil & Ações
- [ ] Página Configurações
- [ ] Upload de arquivos no frontend
- [ ] Gráficos interativos (Plotly/Recharts)
- [ ] Exportações (CSV/PDF)
- [ ] Dark mode toggle
- [ ] Filtros avançados

---

## 🎯 Melhorias Implementadas

1. **Separação Frontend/Backend**: Arquitetura mais escalável
2. **API REST**: Facilita integrações futuras
3. **JWT Authentication**: Autenticação stateless
4. **TypeScript**: Maior segurança de tipos
5. **Tailwind CSS**: Design moderno e responsivo
6. **Performance**: Vite oferece HMR muito rápido

---

## 📝 Próximos Passos

1. Completar todas as páginas do frontend
2. Implementar gráficos interativos
3. Adicionar dark mode
4. Implementar upload de arquivos
5. Adicionar testes (unitários e E2E)
6. Otimizações de performance
7. Deploy e CI/CD

---

## 🐛 Troubleshooting

### Erro de CORS
Se encontrar erros de CORS, verifique se o backend está configurado para aceitar requisições do frontend:
```python
# backend/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    ...
)
```

### Erro de Autenticação
Verifique se o token está sendo enviado corretamente. O interceptor do Axios deve adicionar o token automaticamente.

### Banco de Dados
O banco SQLite continua no mesmo local: `instance/database.sqlite`

---

## 📚 Documentação Adicional

- [Análise e Plano de Migração](./ANALISE_E_PLANO_MIGRACAO.md)
- [Documentação da API](http://localhost:8000/api/docs) (quando o backend estiver rodando)

---

**Versão**: 2.0.0  
**Data**: 2025-01-28  
**Status**: Em Desenvolvimento
