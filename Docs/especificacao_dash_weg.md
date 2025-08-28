# Especificação Técnica — Projeto WEG em Dash

**Data:** 21/08/2025

---

## 1) Objetivo do Sistema
Aplicação web para gestão comercial de um escritório de representação WEG, com:
- Uploads de **Vendas** e **Cotações** (`.xlsx`).
- KPIs gerais e por cliente (incluindo **% cotados e não comprados**).
- Visualizações interativas (ex.: gráfico de bolhas).
- Funil de conversão & Ações recomendadas.
- Geração de **relatórios em PDF** por cliente.
- Autenticação de usuários.
- Persistência em **SQLite**.
- **Sidebar** com botão “Carregar Dados”.

---

## 2) Arquitetura & Stack
- **Frontend:** Dash / Plotly / Dash Bootstrap Components (dbc).
- **Backend:** Python (Flask).
- **Banco de Dados:** SQLite.
- **Sessão:** Flask Session.
- **Gerência de Estados:** `dcc.Store`.
- **Módulos:**
  - `utils/` → ETL, KPIs, PDF, DB, segurança.
  - `webapp/` → layout, autenticação, callbacks.

---

## 3) Estrutura de Pastas
```
weg_dash_app/
│ app.py
│ requirements.txt
│ assets/style.css
│
├── utils/
│   ├── db.py
│   ├── data_loader.py
│   ├── kpis.py
│   ├── visualizations.py
│   ├── report.py
│   └── security.py
│
└── webapp/
    ├── __init__.py
    ├── auth.py
    ├── layouts.py
    ├── callbacks.py
    ├── callbacks_uploads.py
    └── callbacks_downloads.py
```

---

## 4) Banco de Dados (SQLite)
### Tabelas
- **users**: id, username, password_hash, is_active, created_at  
- **datasets**: id, name, uploaded_by, uploaded_at, vendas_fingerprint, cot_fingerprint  
- **vendas**: id, dataset_id, cod_cliente, cliente, material, produto, unidade_negocio, data, data_faturamento, quantidade, valor  
- **cotacoes**: id, dataset_id, cod_cliente, cliente, material, data, quantidade  
- **settings**: key, value_json  

### Índices
- vendas(cod_cliente, data), vendas(material)  
- cotacoes(cod_cliente, data), cotacoes(material)  

---

## 5) Autenticação
- **/login:** usuário/senha → validação `check_password_hash`.  
- Sucesso → `session['user_id']` e redirect para `/app/overview`.  
- **/logout:** limpa sessão.  
- Guard: páginas e callbacks só rendem autenticado.  

---

## 6) Sidebar & Navegação
- Uploads (vendas/cotações).  
- Botão “Carregar Dados”.  
- Filtros globais (Ano compra/cotação, sentinel `__ALL__`).  
- Menu:
  - **Visão Geral**
  - **KPIs por Cliente**
  - **Produtos (bolhas)**
  - **Funil & Ações**
  - **Configurações**  
- Roteamento com `dcc.Location`.  

---

## 7) Persistência & Estado
- Upload → fingerprint MD5.  
- Se novo dataset → UPSERT vendas/cotações → popula `stores`.  
- Botão “Carregar Dados” → lê último dataset do DB sem re-upload.  
- Refresh → recarrega do DB caso stores estejam vazios.  

---

## 8) Mensagens de Sucesso
- `html.Div(id="upload-msgs")`.  
- Mensagem exibida apenas quando fingerprint muda.  
- Caso contrário → `dash.no_update`.  

---

## 9) Filtros por Ano
- `Dropdown.options`: `{'label':'Todos','value':'__ALL__'}`.  
- Helper `_norm_year` normaliza valores.  

---

## 10) Páginas
- **Visão Geral:** Cards com KPIs.  
- **KPIs por Cliente:** Tabela (dias sem compra, frequência média, mix, UN, cotados, comprados, % não comprado) + scatter. Download CSV.  
- **Produtos (bolhas):** Matriz clientes × materiais (`size=qt_cot`, `color=% não comprado`), filtros (ano/UN/TopN/faixa/paleta). PDF por cliente, mensagem sugerida, download CSV.  
- **Funil & Ações:**  
  - Lista A → baixa conversão, alto volume.  
  - Lista B → risco de inatividade.  
  - Download CSV.  
- **Configurações:** thresholds por UN (salvos no settings).  

---

## 11) Callbacks
- **callbacks_uploads.py:** on_upload_vendas, on_upload_cotados, on_load_data.  
- **callbacks.py:** KPIs, Produtos, Funil, Config.  
- **callbacks_downloads.py:** CSV/PDF por cliente.  
- **auth.py:** login/logout/guards.  

---

## 12) ETL & Normalização
- Reconhecimento por hints (`'ovs','VENDAS 2025','materiais'`).  
- Normalização:  
  - Cod Cliente (`ID_Cli`).  
  - Material numérico.  
  - Data (ou Data Faturamento).  
  - Produto e Unidade de Negócio.  
- Coerção de tipos.  

---

## 13) KPIs
- **Gerais:** total clientes/produtos, frequência média global, dias sem compra médios, mix médio, UN médias.  
- **Por Cliente:** métricas individuais + % não comprado = (cotados - comprados)/cotados.  

---

## 14) Visualizações
- `bubble_cotados_nao_comprados(df_matrix, top_produtos, top_clientes, color_scale, status_col)`.  
- Status por UN via thresholds (■/■/■/■).  

---

## 15) Downloads & PDF
- Listas A/B e bases CSV.  
- PDF por cliente (ReportLab + imagem de gráfico via Kaleido).  

---

## 16) Segurança
- Hash de senha (Werkzeug).  
- Limitar uploads.  
- Validar extensão `.xlsx`.  
- Sanitização de tipos.  
- Callbacks protegidos.  

---

## 17) Critérios de Aceite
- Login obrigatório.  
- Upload persiste dataset versionado.  
- Botão “Carregar Dados” funcional.  
- Refresh mantém dados.  
- Mensagens exibidas apenas quando necessário.  
- Filtros por ano robustos.  
- KPIs/bolhas/funil/downloads operando corretamente.  
- PDF por cliente gerado.  

---

## 18) Helpers
```python
SENTINEL_ALL="__ALL__"

def _norm_year(v):
    if v in (None,SENTINEL_ALL,"","Todos"): return None
    try: return int(v)
    except: return None
```

---

# 🔥 Novas Funcionalidades Sugeridas
Para tornar a ferramenta ainda mais poderosa, propomos os seguintes incrementos:

### A) **Inteligência Artificial**
- Classificação automática de clientes em **clusters de comportamento** (ativos, inativos, potenciais).  
- Modelo de ML para prever **probabilidade de fechamento** de cotações.  
- Geração de **insights automáticos**: recomendações de follow-up e alerta de risco de churn.  

### B) **Dashboard Avançado**
- Heatmap de **clientes × produtos**.  
- Comparativo de **concorrentes vs WEG** (quando houver dados).  
- **Indicador de performance por Unidade de Negócio**.  

### C) **Integrações**
- Exportação direta para **Excel e Google Sheets**.  
- Integração com **Outlook/WhatsApp** para follow-up.  
- API REST para integração com CRM externo.  

### D) **Funcionalidades Offline / Mobile**
- PWA (Progressive Web App) para acesso offline.  
- Geolocalização de clientes em **mapa interativo**.  
- Filtro por **última visita ou compra** no mapa.  

### E) **Colaboração**
- Perfis de usuários (Admin / Analista).  
- Log de auditoria (quem fez upload, criou relatórios, etc.).  
- Notificações por e-mail quando thresholds forem ultrapassados.  


---

# 📐 Apêndice — Guia de Layout das Telas

Este apêndice detalha como cada tela do sistema deve ser visualmente organizada, servindo como referência adicional ao mockup em imagem.

## 1. Tela de Login
- Fundo azul WEG, logo no topo centralizado.  
- Caixa central com campos: Usuário e Senha.  
- Botão "Entrar" azul WEG, texto branco.  
- Rodapé discreto com copyright.  

## 2. Visão Geral
- **Sidebar** azul à esquerda, com menu de navegação.  
- Parte superior: **cards de KPIs** (Clientes, Produtos, Conversão, Dias sem Compra).  
- Abaixo:  
  - Gráfico de evolução (ROL, Carteira, Entrada de Pedidos).  
  - Gráfico comparativo anual vs mensal.  

## 3. KPIs por Cliente
- Filtros no topo (Ano, Unidade de Negócio).  
- **Tabela central** com métricas: dias sem compra, mix, cotados, comprados, % não comprado.  
- À direita: scatterplot com comparativo visual.  
- Botão "Download CSV".  

## 4. Produtos (Bolhas)
- Filtros no topo (Ano, UN, Top N, Paleta).  
- **Gráfico de bolhas** clientes × produtos:  
  - Tamanho = quantidade cotada.  
  - Cor = % não comprado.  
- Abaixo: painel de **insights automáticos** gerados por IA.  
- Botões: Download CSV e PDF por cliente.  

## 5. Funil & Ações
- Duas listas centrais:  
  - Lista A → baixa conversão, alto volume.  
  - Lista B → risco de inatividade.  
- Cada cliente listado com ícones coloridos de status.  
- Rodapé: botão "Exportar CSV".  

## 6. Configurações
- Painel com inputs para thresholds por Unidade de Negócio.  
- Botão "Salvar Configurações".  
- Área de auditoria com **log de ações** de usuários.  

---

📎 Arquivo complementar: [layout_dashboard_weg.png](layout_dashboard_weg.png)  
Este arquivo contém a visualização consolidada de todas as telas.
