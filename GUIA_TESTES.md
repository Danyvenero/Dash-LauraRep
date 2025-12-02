# 🧪 Guia Completo de Testes - Dashboard WEG

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8+** (recomendado 3.10+)
- **Node.js 18+** e npm
- **Git** (opcional, para clonar o repositório)

### Verificar Instalações

```bash
# Verificar Python
python --version
# ou
python3 --version

# Verificar Node.js
node --version
npm --version
```

---

## 🚀 Passo a Passo para Testar

### 1. Preparar o Ambiente

#### 1.1. Navegar para o diretório do projeto
```bash
cd /workspace
# ou o caminho onde está o projeto
```

#### 1.2. Configurar o Banco de Dados
```bash
# Criar diretório instance se não existir
mkdir -p instance

# Executar setup do banco (se necessário)
python setup_database.py
```

---

### 2. Iniciar o Backend (API)

#### 2.1. Instalar Dependências do Backend
```bash
cd backend
pip install -r requirements.txt
```

**Nota**: Se usar ambiente virtual (recomendado):
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

#### 2.2. Executar o Backend
```bash
# Opção 1: Usando uvicorn diretamente
python -m uvicorn backend.api.main:app --reload --port 8000

# Opção 2: Usando o script
cd ..
./run_backend.sh
```

**✅ Backend rodando em**: http://localhost:8000  
**📚 Documentação Swagger**: http://localhost:8000/api/docs

#### 2.3. Verificar se o Backend está Funcionando
Abra no navegador: http://localhost:8000/api/health

Deve retornar:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "service": "Dashboard WEG API"
}
```

---

### 3. Iniciar o Frontend

#### 3.1. Instalar Dependências do Frontend
```bash
cd frontend
npm install
```

**Nota**: Se encontrar erros, tente:
```bash
# Limpar cache e reinstalar
rm -rf node_modules package-lock.json
npm install
```

#### 3.2. Executar o Frontend
```bash
npm run dev
```

**✅ Frontend rodando em**: http://localhost:3000

#### 3.3. Verificar se o Frontend está Funcionando
Abra no navegador: http://localhost:3000

Deve mostrar a tela de login.

---

## 🧪 Testando Funcionalidades

### 1. Teste de Autenticação

#### 1.1. Criar Usuário
1. Acesse: http://localhost:3000/login
2. Clique em "Não tem uma conta? Cadastre-se"
3. Preencha:
   - Usuário: `teste`
   - Senha: `teste123`
   - Confirme a senha: `teste123`
4. Clique em "Cadastrar"
5. ✅ Deve mostrar mensagem de sucesso

#### 1.2. Fazer Login
1. Na tela de login, preencha:
   - Usuário: `teste` (ou `admin` se já existir)
   - Senha: `teste123` (ou `admin123`)
2. Clique em "Entrar"
3. ✅ Deve redirecionar para a página Visão Geral

**Credenciais Padrão (se já existir no banco)**:
- Usuário: `admin`
- Senha: `admin123`

---

### 2. Teste da Página Visão Geral

1. Após login, você deve estar na página "Visão Geral"
2. ✅ Deve mostrar 3 cards com KPIs:
   - Entrada de Pedidos
   - Valor em Carteira
   - Faturamento (ROL)
3. Se não houver dados, os valores serão R$ 0,00

---

### 3. Teste de Upload de Dados

#### 3.1. Acessar Configurações
1. No menu lateral, clique em "Configurações"
2. ✅ Deve mostrar a página de configurações

#### 3.2. Fazer Upload de Vendas
1. Clique em "Mostrar Upload"
2. Na seção "Upload de Vendas (Anual)":
   - Arraste um arquivo Excel (.xlsx ou .xls) OU
   - Clique na área e selecione um arquivo
3. ✅ Deve mostrar:
   - Loading durante upload
   - Mensagem de sucesso com número de registros
   - Ou mensagem se arquivo já foi carregado

**Formato esperado do arquivo de vendas**:
- Colunas: `ID_Cli`, `Cliente`, `Material`, `Produto`, `Unidade de Negócio`, `Data Faturamento`, `Qtd. ROL`, `Vlr. ROL`, `Vlr. Entrada`, `Vlr. Carteira`, etc.

#### 3.3. Fazer Upload de Cotações
1. Na seção "Upload de Cotações":
   - Faça upload de arquivo Excel de cotações
2. ✅ Deve mostrar mensagem de sucesso

**Formato esperado do arquivo de cotações**:
- Colunas: `Cotação`, `Cod. Cliente`, `Cliente`, `Material`, `Quantidade`, etc.

#### 3.4. Executar ETL
1. Após fazer uploads, role até "Ações Perigosas"
2. Clique em "Processar Dados Brutos e Atualizar Análises"
3. ✅ Deve mostrar mensagem de sucesso
4. ✅ Os dados devem aparecer nas outras páginas

---

### 4. Teste da Página KPIs por Cliente

1. No menu, clique em "KPIs por Cliente"
2. ✅ Deve mostrar:
   - Filtros (ano, mês, top N)
   - Tabela com dados dos clientes
   - Gráfico scatter (Valor Faturado x Dias sem Compra)
   - Botão "Download CSV"

#### Testar Filtros:
1. Altere o "Top N" para 10
2. ✅ A tabela deve atualizar mostrando apenas 10 clientes
3. Altere o ano
4. ✅ Os dados devem filtrar pelo ano selecionado

#### Testar Export CSV:
1. Clique em "Download CSV"
2. ✅ Deve baixar um arquivo CSV com os dados da tabela

---

### 5. Teste da Página KPIs de Propostas

1. No menu, clique em "KPIs de Propostas"
2. ✅ Deve mostrar:
   - Filtros (ano, mês, top N)
   - Seleção de tipo de gráfico (Barra/Heatmap)
   - Cards com resumo (Total Cotado, Comprado, Taxa de Conversão)

#### Testar Gráfico de Barras:
1. Selecione "Comparativo (Barra)"
2. ✅ Deve mostrar gráfico de barras com taxa de conversão por cliente

#### Testar Heatmap:
1. Selecione "Heatmap"
2. ✅ Deve mostrar heatmap interativo cliente × produto

#### Testar Sugestão de Estoque:
1. Role até "Sugestão de Lista de Compra para Estoque"
2. Clique em "Carregar Sugestões"
3. ✅ Deve mostrar tabela com sugestões
4. Clique em "Baixar Lista (.csv)"
5. ✅ Deve baixar arquivo CSV

---

### 6. Teste da Página Produtos (Bolhas)

1. No menu, clique em "Produtos (Bolhas)"
2. ✅ Deve mostrar:
   - Filtros (Top N Produtos, Top N Clientes, Ano, Paleta)
   - Gráfico de bolhas interativo

#### Testar Interatividade:
1. Passe o mouse sobre as bolhas
2. ✅ Deve mostrar tooltip com informações detalhadas
3. Altere a paleta de cores
4. ✅ O gráfico deve atualizar com nova paleta

---

### 7. Teste da Página Funil & Ações

1. No menu, clique em "Funil & Ações"
2. ✅ Deve mostrar:
   - Filtros (Período, Thresholds)
   - Cards com resumo do funil
   - Lista A (Baixa Conversão)
   - Lista B (Risco de Inatividade)

#### Testar Filtros:
1. Altere o "Período de Análise" para 6 meses
2. ✅ As listas devem atualizar
3. Altere o "Threshold % Conversão Baixa"
4. ✅ A Lista A deve atualizar

#### Testar Exports:
1. Clique em "Download CSV" na Lista A
2. ✅ Deve baixar CSV da Lista A
3. Clique em "Download CSV" na Lista B
4. ✅ Deve baixar CSV da Lista B

---

### 8. Teste do Dashboard Executivo

1. No menu, clique em "Dashboard Executivo"
2. ✅ Deve mostrar:
   - Cards destacados com KPIs principais
   - Gráfico de tendência (se houver dados)
   - Seção de Insights
   - Seção de Ações Recomendadas

---

### 9. Teste de Dark Mode

1. Na sidebar, localize o botão de tema (ícone de sol/lua)
2. Clique no botão
3. ✅ O tema deve alternar entre claro e escuro
4. ✅ Todos os componentes devem se adaptar ao tema
5. ✅ O tema deve persistir após recarregar a página

---

### 10. Teste da API Diretamente (Swagger)

1. Acesse: http://localhost:8000/api/docs
2. ✅ Deve mostrar a documentação Swagger
3. Clique em "Authorize" (cadeado no topo)
4. Cole o token JWT (obtido após login)
5. Teste endpoints:
   - `GET /api/kpis/gerais` - Deve retornar KPIs
   - `GET /api/vendas/stats` - Deve retornar estatísticas
   - `POST /api/kpis/cliente` - Deve retornar KPIs por cliente

---

## 🐛 Troubleshooting

### Problema: Backend não inicia

**Erro**: `ModuleNotFoundError`
```bash
# Solução: Instalar dependências
cd backend
pip install -r requirements.txt
```

**Erro**: `Port 8000 already in use`
```bash
# Solução: Matar processo na porta
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Erro**: `Database not found`
```bash
# Solução: Criar banco
python setup_database.py
```

---

### Problema: Frontend não inicia

**Erro**: `Cannot find module`
```bash
# Solução: Reinstalar dependências
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Erro**: `Port 3000 already in use`
```bash
# Solução: Matar processo
# Linux/Mac:
lsof -ti:3000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

### Problema: Erro de CORS

**Sintoma**: Erro no console do navegador sobre CORS

**Solução**: Verificar se o backend está rodando e se o CORS está configurado:
```python
# backend/api/main.py deve ter:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    ...
)
```

---

### Problema: Login não funciona

**Sintoma**: Erro "Usuário ou senha inválidos"

**Solução**:
1. Verificar se o banco tem usuários:
```bash
python -c "from utils.db import get_all_users; print(get_all_users())"
```

2. Criar usuário manualmente:
```bash
python setup_database.py
# ou criar via API Swagger: POST /api/auth/register
```

---

### Problema: Dados não aparecem

**Sintoma**: Páginas mostram "Nenhum dado disponível"

**Solução**:
1. Verificar se fez upload de dados
2. Verificar se executou o ETL
3. Verificar se o banco tem dados:
```bash
python -c "from utils.db import get_clean_vendas_as_df; print(len(get_clean_vendas_as_df()))"
```

---

## 📊 Checklist de Testes

Use este checklist para garantir que tudo está funcionando:

### Backend
- [ ] Backend inicia sem erros
- [ ] API health check responde
- [ ] Swagger está acessível
- [ ] Endpoints de autenticação funcionam
- [ ] Endpoints de KPIs funcionam
- [ ] Upload de arquivos funciona
- [ ] ETL executa sem erros

### Frontend
- [ ] Frontend inicia sem erros
- [ ] Tela de login carrega
- [ ] Cadastro de usuário funciona
- [ ] Login funciona
- [ ] Todas as páginas carregam
- [ ] Navegação funciona
- [ ] Dark mode funciona
- [ ] Gráficos renderizam
- [ ] Upload de arquivos funciona
- [ ] Exports CSV funcionam

### Funcionalidades
- [ ] Upload de vendas funciona
- [ ] Upload de cotações funciona
- [ ] ETL processa dados
- [ ] KPIs são calculados corretamente
- [ ] Gráficos mostram dados
- [ ] Filtros funcionam
- [ ] Exports funcionam
- [ ] Dark mode persiste

---

## 🎯 Testes Recomendados por Prioridade

### Alta Prioridade (Testar Primeiro)
1. ✅ Login/Cadastro
2. ✅ Upload de dados
3. ✅ ETL
4. ✅ Visualização de KPIs
5. ✅ Export CSV

### Média Prioridade
1. ✅ Filtros avançados
2. ✅ Gráficos interativos
3. ✅ Dark mode
4. ✅ Navegação entre páginas

### Baixa Prioridade
1. ✅ Sugestão de estoque
2. ✅ Dashboard executivo
3. ✅ Análise de sazonalidade

---

## 📝 Dados de Teste

Se precisar de dados de exemplo para testar, você pode:

1. **Criar arquivos Excel de exemplo** com as colunas esperadas
2. **Usar dados reais** (se disponíveis)
3. **Gerar dados sintéticos** usando Python:

```python
import pandas as pd
import random
from datetime import datetime, timedelta

# Exemplo de dados de vendas
vendas_data = {
    'ID_Cli': [f'CLI{i:03d}' for i in range(1, 21)],
    'Cliente': [f'Cliente {i}' for i in range(1, 21)],
    'Material': [f'MAT{i:05d}' for i in range(1, 51)],
    'Produto': [f'Produto {i}' for i in range(1, 51)],
    'Data Faturamento': [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%d/%m/%Y') for _ in range(100)],
    'Vlr. ROL': [random.uniform(1000, 50000) for _ in range(100)],
    'Qtd. ROL': [random.randint(1, 100) for _ in range(100)],
}

df = pd.DataFrame(vendas_data)
df.to_excel('vendas_teste.xlsx', index=False)
```

---

## 🆘 Precisa de Ajuda?

1. **Verificar logs**: Console do navegador (F12) e terminal do backend
2. **Verificar documentação**: http://localhost:8000/api/docs
3. **Verificar status**: http://localhost:8000/api/health
4. **Revisar documentação**: Ver arquivos README e guias no projeto

---

**Boa sorte com os testes! 🚀**
