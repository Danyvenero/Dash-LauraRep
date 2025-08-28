# 🚀 Dashboard WEG - Sistema de Análise Comercial

## 📋 Visão Geral

Dashboard completo para gestão comercial de escritório de representação WEG, desenvolvido em Python/Dash com funcionalidades avançadas de análise de vendas, cotações e KPIs.

## ✨ Funcionalidades Principais

### 🔐 Sistema de Autenticação
- Login seguro com hash de senhas
- Cadastro de novos usuários
- Controle de sessão

### 📊 Páginas de Análise

#### 🏠 Visão Geral
- KPIs principais: Entrada de Pedidos, Valor em Carteira, Faturamento
- Cards com métricas essenciais do negócio

#### 👥 KPIs por Cliente
- Análise detalhada por cliente com filtros avançados
- Gráfico scatter interativo
- Evolução histórica personalizável
- Export em CSV

#### 📈 KPIs de Propostas
- Análise de gaps entre cotações e vendas
- Comparativo visual (barras/heatmap)
- Geração de lista de sugestão de estoque

#### 🎯 Produtos (Bolhas)
- Matriz visual clientes vs produtos
- Gráfico de bolhas com métricas de conversão
- Filtros por ano, unidade de negócio, paleta de cores
- Export CSV e PDF por cliente

#### 🔄 Funil & Ações
- Análise do funil de conversão
- Lista A: Baixa conversão, alto volume
- Lista B: Risco de inatividade
- Métricas configuráveis de threshold

#### ⚙️ Configurações
- Gestão de usuários
- Limpeza de dados
- Processamento ETL

### 📁 Upload de Dados
- Upload de vendas (Excel)
- Upload de cotações (Excel)
- Processamento automático com fingerprint
- Validação e normalização de dados

## 🛠️ Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- Windows/Linux/Mac

### 1. Clone o Repositório
```bash
git clone https://github.com/Danyvenero/Dash-LauraRep.git
cd dash_laurarep
```

### 2. Configuração do Ambiente Virtual
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração Inicial do Banco de Dados
```bash
# Configuração básica
python setup_database.py

# Ou com dados de exemplo
python setup_database.py --sample-data

# Reset completo (cuidado!)
python setup_database.py --reset
```

### 4. Executar o Dashboard
```bash
python app.py
```

Acesse: http://localhost:8050

## 👤 Credenciais Padrão

**Usuário:** admin  
**Senha:** admin123

⚠️ **IMPORTANTE:** Altere a senha após o primeiro login!

## 📂 Estrutura do Projeto

```
dash_laurarep/
├── app.py                      # Ponto de entrada
├── setup_database.py           # Script de configuração
├── requirements.txt            # Dependências
├── README.md                  # Este arquivo
├── .gitignore                 # Arquivos ignorados pelo Git
├── instance/                  # Banco de dados SQLite
│   └── database.sqlite
├── assets/                    # CSS e recursos estáticos
│   └── style.css
├── utils/                     # Módulos utilitários
│   ├── __init__.py
│   ├── data_loader.py         # ETL e carregamento
│   ├── data_stats.py          # Estatísticas
│   ├── db.py                  # Acesso ao banco
│   ├── kpis.py               # Cálculo de KPIs
│   ├── report.py             # Geração de PDFs
│   ├── security.py           # Funções de segurança
│   └── visualizations.py     # Gráficos e visualizações
└── webapp/                    # Aplicação Dash
    ├── __init__.py
    ├── auth.py               # Autenticação
    ├── callbacks.py          # Callbacks principais
    ├── callbacks_downloads.py # Downloads CSV/PDF
    ├── callbacks_uploads.py  # Upload de arquivos
    └── layouts.py            # Layouts das páginas
```

## 📊 Dados e Formatos

### Upload de Vendas
Arquivo Excel com colunas:
- `cod_cliente` - Código do cliente
- `cliente` - Nome do cliente
- `material` - Código do material
- `produto` - Descrição do produto
- `unidade_negocio` - Unidade de negócio
- `data_faturamento` - Data do faturamento
- `quantidade_faturada` - Quantidade faturada
- `valor_faturado` - Valor faturado
- `valor_entrada` - Valor de entrada
- `valor_carteira` - Valor em carteira

### Upload de Cotações
Arquivo Excel com colunas:
- `cod_cliente` - Código do cliente
- `cliente` - Nome do cliente
- `material` - Código do material
- `data` - Data da cotação
- `quantidade` - Quantidade cotada

## 🔧 Configurações Avançadas

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:
```
SECRET_KEY=sua-chave-secreta-super-forte
DATABASE_URL=sqlite:///instance/database.sqlite
DEBUG=True
```

### Customizações
- **Cores e Tema:** Edite `assets/style.css`
- **Layout:** Modifique `webapp/layouts.py`
- **KPIs:** Ajuste `utils/kpis.py`
- **Visualizações:** Customize `utils/visualizations.py`

## 🚀 Funcionalidades Avançadas

### Análise de Funil
- Configure thresholds personalizados
- Identifique clientes em risco
- Gere listas de ação automáticas

### Geração de Relatórios
- PDFs por cliente com gráficos
- Exports CSV personalizáveis
- Lista de sugestão de estoque

### Filtros Inteligentes
- Filtros por ano, mês, cliente
- Top N selecionável
- Faixas de valores configuráveis

## 🐛 Solução de Problemas

### Erro de Importação
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Banco de Dados Corrompido
```bash
# Reset do banco
python setup_database.py --reset
```

### Erro de Porta em Uso
```bash
# Matar processo na porta 8050
# Windows:
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8050 | xargs kill -9
```

## 📈 Performance

### Otimizações Implementadas
- ✅ Índices no banco de dados
- ✅ Cache de dados com dcc.Store
- ✅ Lazy loading de gráficos
- ✅ Paginação de tabelas
- ✅ Compressão de dados

### Monitoramento
- Logs de erro automáticos
- Métricas de performance
- Auditoria de ações de usuário

## 🔐 Segurança

### Medidas Implementadas
- ✅ Hash de senhas com salt
- ✅ Proteção contra SQL injection
- ✅ Validação de uploads
- ✅ Controle de sessão
- ✅ Sanitização de inputs

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

- **Email:** suporte@dashboard-weg.com
- **Issues:** [GitHub Issues](https://github.com/Danyvenero/Dash-LauraRep/issues)
- **Documentação:** [Wiki do Projeto](https://github.com/Danyvenero/Dash-LauraRep/wiki)

## 🏆 Changelog

### v1.0.0 (2025-01-28)
- ✅ Sistema completo de autenticação
- ✅ Dashboard multi-página
- ✅ Análise de KPIs avançada
- ✅ Funil de conversão
- ✅ Gráfico de bolhas interativo
- ✅ Geração de relatórios PDF
- ✅ Exports CSV personalizáveis
- ✅ Sistema de upload robusto

---

**Desenvolvido com ❤️ usando Python, Dash e Bootstrap**

🌟 **Se este projeto foi útil, deixe uma estrela no GitHub!**
