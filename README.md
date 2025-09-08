# Dashboard WEG - Laura Representações

Sistema de gestão comercial desenvolvido em Dash para análise de vendas, cotações e KPIs.

## 🚀 Funcionalidades

- **Autenticação de usuários** com controle de sessão
- **Upload de dados** (Excel) para vendas, cotações e materiais cotados
- **KPIs em tempo real** por cliente e unidade de negócio
- **Visualizações interativas** (gráficos de evolução, bolhas, Pareto)
- **Filtros globais** por ano, mês, cliente, hierarquia de produto, canal
- **Análise de performance** com classificação de clientes
- **Configurações personalizáveis** de thresholds por UN

## 📁 Estrutura do Projeto

```
dash_laurarep/
├── app.py                      # Aplicação principal
├── requirements.txt            # Dependências
├── schema.sql                  # Schema do banco de dados
├── README.md                   # Este arquivo
├── assets/
│   └── style.css              # Estilos CSS customizados
├── utils/                     # Módulos utilitários
│   ├── __init__.py
│   ├── db.py                  # Operações de banco de dados
│   ├── data_loader.py         # Carregamento e normalização de dados
│   ├── kpis.py                # Cálculo de KPIs
│   ├── visualizations.py     # Geração de gráficos
│   └── security.py           # Segurança e autenticação
└── webapp/                    # Interface web
    ├── __init__.py
    ├── auth.py                # Sistema de login/logout
    ├── layouts.py             # Layouts das páginas
    ├── callbacks.py           # Callbacks principais
    └── callbacks_uploads.py   # Callbacks para uploads
```

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd dash_laurarep
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # ou
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a aplicação:**
   ```bash
   python app.py
   ```

5. **Acesse no navegador:**
   ```
   http://127.0.0.1:8050
   ```

## 🔐 Login Padrão

- **Usuário:** admin
- **Senha:** admin123

## 📊 Como Usar

### 1. Upload de Dados

1. Acesse **Configurações** no menu lateral
2. Na seção "Carregar Dados", faça upload dos arquivos Excel:
   - **Vendas:** arquivo com dados de faturamento
   - **Cotações:** arquivo com cotações realizadas
   - **Materiais Cotados:** arquivo com produtos cotados

### 2. Visualização de KPIs

- **Visão Geral:** KPIs principais e evolução de vendas
- **Clientes:** Tabela detalhada com métricas por cliente
- **Mix de Produtos:** Análise de produtos com gráfico de bolhas e Pareto

### 3. Filtros Globais

Use a sidebar esquerda para filtrar dados por:
- Ano (range slider)
- Mês (range slider)  
- Cliente (seleção múltipla)
- Hierarquia de Produto
- Canal de Distribuição
- TOP Clientes (número)
- Dias sem compra (range slider)

### 4. Configurações

Configure thresholds por Unidade de Negócio para classificação de performance.

## 🗃️ Formato dos Dados

### Arquivo de Vendas
Colunas obrigatórias:
- `cod_cliente` ou `ID_Cli`
- `cliente`
- `material`
- `data_faturamento` ou `data`
- `vlr_rol`, `vlr_entrada`, `vlr_carteira`
- `unidade_negocio`
- `canal_distribuicao`

### Arquivo de Cotações
Colunas obrigatórias:
- `numero_cotacao`
- `cod_cliente`
- `cliente`
- `material`
- `data`
- `quantidade`

### Arquivo de Materiais Cotados
Colunas obrigatórias:
- `cotacao`
- `cod_cliente`
- `material`
- `quantidade`
- `preco_liquido_unitario`

## 🔧 Configuração Avançada

### Banco de Dados
O sistema usa SQLite por padrão. O banco é criado automaticamente em `instance/database.sqlite`.

### Variáveis de Ambiente
```bash
# Opcional - configurar em produção
export FLASK_SECRET_KEY="sua-chave-secreta-aqui"
export DATABASE_URL="sqlite:///path/to/database.sqlite"
```

### Segurança
- Senhas são hashadas com Werkzeug
- Rate limiting para tentativas de login
- Validação de arquivos upload
- Sanitização de entradas de usuário

## 📈 Métricas Calculadas

### KPIs por Cliente
- **Dias sem compra:** Dias desde a última compra
- **Frequência média:** Intervalo médio entre compras
- **Mix de produtos:** Quantidade de produtos únicos comprados
- **% Mix:** Percentual do mix em relação ao total disponível
- **% Não comprado:** (Cotados - Comprados) / Cotados × 100

### Classificação de Clientes
- 🟢 **Ativo:** < 90 dias sem compra
- 🟡 **Em Risco:** 90-365 dias sem compra  
- 🔴 **Inativo:** > 365 dias sem compra

## 🆘 Solução de Problemas

### Erro ao fazer upload
- Verifique se o arquivo é .xlsx ou .xls
- Confirme se as colunas obrigatórias estão presentes
- Tamanho máximo: 50MB

### Dados não aparecem
- Verifique se fez upload dos arquivos
- Use "Carregar Dados Salvos" para recuperar último dataset
- Verifique filtros aplicados

### Performance lenta
- Reduza o range de datas nos filtros
- Use filtro de TOP Clientes para limitar resultados
- Considere fazer upload de dados menores para teste

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs no terminal onde a aplicação está rodando
2. Consulte a documentação das dependências (Dash, Plotly)
3. Abra uma issue no repositório do projeto

## 🔄 Versão

**v1.0.0** - Versão inicial completa
- Sistema de autenticação
- Upload e processamento de dados
- KPIs e visualizações
- Filtros interativos
- Configurações personalizáveis

---

Desenvolvido para **Laura Representações** com tecnologia **WEG**.
