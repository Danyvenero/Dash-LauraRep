# Especificação Técnica --- Projeto WEG em Dash

**Data:** 21/08/2025

## 1) Objetivo do Sistema

Aplicação web para gestão comercial de um escritório de representação
WEG, com: - Uploads de **Vendas,** **Cotações** e **Materiais**
(`.xlsx`` ou .xls`). - KPIs gerais e por cliente (incluindo **% de
materiais cotados e não comprados**). - Visualizações interativas (ex.:
gráfico de bolhas). - Funil de conversão & Ações recomendadas. - Geração
de **relatórios em PDF** por cliente. - Autenticação de usuários. -
Persistência em **SQLite**. - **Sidebar** com menu de configurações para
gestão de usuários e upload dos arquivos "Carregar Dados".

Todos os gráficos, tabelas, análises devem ter fundamentação estatística
para sugestões de compra e mapeamento de estratégias para aumento de
vendas, acompanhamento de propostas (follow-up), etc.

## 2) Arquitetura & Stack

-   **Frontend:** Dash / Plotly / Dash Bootstrap Components (dbc).
-   **Backend:** Python (Flask).
-   **Banco de Dados:** SQLite.
-   **Sessão:** Flask Session.
-   **Gerência de Estados:** `dcc.Store`.
-   **Módulos:**
    -   `utils/` → ETL, KPIs, PDF, DB, segurança.
    -   `webapp/` → layout, autenticação, callbacks.

## 3) Estrutura de Pastas

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

## 4) Banco de Dados (SQLite)

### Tabelas

-   **users**: id, username, password_hash, is_active, created_at
-   **datasets**: id, name, uploaded_by, uploaded_at,
    vendas_fingerprint, cot_fingerprint
-   **vendas**: id, dataset_id, cod_cliente, cliente, material, produto,
    unidade_negocio , data, data_faturamento, qtd_entrada, vlr_entrada,
    qtd_carteira, vlr_carteira, qtd_rol, vlr_rol (vlr_rol é o
    faturamento).
-   **cotacoes**: id, dataset_id, número da cotação, cod_cliente,
    cliente, material, data, quantidade
-   **produtos_cotados**: id, dataset_id, cotação, cod_cliente, cliente,
    centro_fornecedor, material, descrição, quantidade,
    preço_liquido_unitario, preço_liquido_total.

> Nota: Deve ser feito o merge da tabela cotações com a tabela
> produtos_cotados a partir da coluna Número da Cotação na tabela de
> cotações e Cotação na tabela de materiais cotados para que seja
> possível vincular a data da cotação com a data em que material foi
> cotado para análises estatísticas.

-   **settings**: key, value_json

### Índices

-   vendas(cod_cliente, data), vendas(material)
-   cotacoes(cod_cliente, data, número da cotação), cotacoes(material)

## 5) Autenticação

-   **/login:** usuário/senha → validação `check_password_hash`.
-   Sucesso → `session['user_id']` e redirect para `/app/overview`.
-   **/logout:** limpa sessão.
-   Guard: páginas e callbacks só rendem autenticado.

## 6) Sidebar & Navegação

-   Filtros globais (Ano compra/cotação, sentinel `__ALL__`). Campos que
    serão utilizados para filtrar as informações mostradas:
    -   Ano: Tipo RangeSlider com faixa de 2018 até o ano corrente + 1.
        Exemplo, estamos em 2025 então a faixa de opções de seleção é
        2018 à 2026.
    -   Mês: Tipo RangeSlider com faixa de 1 a 12.
    -   Cliente: Tipo caixa de seleção permitindo selecionar vários
        clientes. Os clientes devem aparecer no formato Cod -- Nome do
        Cliente, sendo possível selecionar clientes informando o código
        ou nome. Exemplo: 782080 -- Aildo Borges Cabral e Cia Ltda
    -   Hierarquia de Produto: Tipo caixa de seleção permitindo
        selecionar vários itens. Exemplo: Controls, Drives, ACW, CWM,
        etc. Este campo deve ser populado a partir das colunas Hier.
        Produto 1, Hier. Produto 2 e Hier. Produto 3 que estão
        localizados nos dados de vendas.
    -   Canal: Tipo caixa de seleção permitindo selecionar vários itens.
        Exemplo: Revenda. Este campo será populado pela coluna Canal
        Distribuição disponível nos dados de vendas.
    -   TOP Clientes: Campo de texto onde seja possível informar um
        valor numérico, exemplo TOP Clientes igual a 10, para selecionar
        as informações referentes aos clientes com maior faturamento
        (faturamento é igual a coluna Vlr. ROL dos dados de vendas).
    -   Dias sem compra: Tipo RangeSlider.
-   Menu:
    -   **Visão Geral**
    -   **Clientes**
    -   **Mix de Produtos**
    -   **Funil & Ações**
    -   **Insights IA**
    -   **Configurações**
-   Roteamento com `dcc.Location`.

## 7) Persistência & Estado

-   Upload → fingerprint MD5.
-   Se novo dataset → UPSERT vendas/cotações → popula `stores`.
-   Botão "Carregar Dados" → lê último dataset do DB sem re-upload.
-   Refresh → recarrega do DB caso stores estejam vazios.

## 8) Mensagens de Sucesso

-   `html.Div(id="upload-msgs")`.
-   Mensagem exibida apenas quando fingerprint muda.
-   Caso contrário → `dash.no_update`.

## 9) Filtros por Ano

-   `RangeSlider``.options`: `{'label':'Todos','value':'__ALL__'}`.
-   Helper `_norm_year` normaliza valores.

## 10) Páginas

-   **Visão Geral:** Cards com KPIs de Entrada de Pedidos, Carteira e
    Faturamento. Incluir mais 5 cards sendo um para cada unidade, WAU
    (Weg Automação), WEN (Weg Energia), WMO-C (Weg Motores Comercial e
    Appliance), WMO-I (Weg Motores Industrial), WDS (Weg Digital e
    Sistemas). Nos cards para as unidades, considerar o valor do
    faturamento do ano corrente e uma identificação para mostrar a
    comparação com o realizado no ano anterior (exemplo -15%). Abaixo
    dos cards incluir gráfico de linhas com a evolução da Entrada de
    Pedidos, Carteira e Faturamento.
-   **KPIs por Cliente:** Tabela (dias sem compra, frequência média de
    compra (dias), mix (quantidade de produtos comprados em relação a
    tudo que foi comprado e cotado por todos os demais clientes),
    Percentual de Mix, UN, Produtos cotados, Produtos comprados, % não
    comprado) + gráfico de bolhas e Download CSV, Selecionar Todos,
    Desmarcar Todos, Limpar Filtros e Tamanho da Paginação. Utilizar
    Dash_table para mais interatividade. Utilizar critérios estatísticos
    para classificar os produtos no gráfico de bolhas e os clientes. Por
    exemplo, clientes que não compra a mais de 1 ano, a linha fica
    destacada em vermelho, clientes com maior faturamento destacados em
    verde, clientes entre 90 dias e 1 ano sem comprar destacados em
    amarelo,
-   **Produtos (bolhas):** Matriz clientes × materiais (`size=qt_cot`,
    `color=% não comprado`), filtros (ano/UN/TopN/faixa/paleta). PDF por
    cliente, mensagem sugerida, download CSV, Selecionar Todos,
    Desmarcar Todos, Limpar Filtros e Tamanho da Paginação. Gráfico de
    Pareto a partir da seleção dos campos de filtro (Produto x
    Quantidade Comprada). Utilizar IA para gerar uma lista de sugestões
    com os produtos com maior frequência de compra, maior frequência de
    cotação, de acordo com as opções selecionadas no filtro.
-   **Funil & Ações:**
    -   Lista A → baixa conversão, alto volume.
    -   Lista B → risco de inatividade.
    -   Download CSV.
-   **Configurações:** thresholds por UN (salvos no settings). Campos
    para upload dos arquivos de vendas, cotações e materiais cotados
    (permitir selecionar mais de um arquivo por vez).

## 11) Callbacks

-   **callbacks_uploads.py:** on_upload_vendas, on_upload_cotados,
    on_load_data.
-   **callbacks.py:** KPIs, Produtos, Funil, Config.
-   **callbacks_downloads.py:** CSV/PDF por cliente.
-   **auth.py:** login/logout/guards.

## 12) ETL & Normalização

-   Reconhecimento por hints (`'ovs','VENDAS 2025','materiais'`).
-   Normalização:
    -   Cod Cliente (`ID_Cli`).
    -   Material numérico.
    -   Data (ou Data Faturamento).
    -   Produto e Unidade de Negócio.
-   Coerção de tipos.

## 13) KPIs

-   **Gerais:** total clientes/produtos, frequência média global, dias
    sem compra médios, mix médio, UN médias.
-   **Por Cliente:** métricas individuais + % não comprado = (cotados -
    comprados)/cotados.

## 14) Visualizações

-   `bubble_cotados_nao_comprados(df_matrix, top_produtos, top_clientes, color_scale, status_col)`.
-   Status por UN via thresholds (■/■/■/■).

## 15) Downloads & PDF

-   Listas A/B e bases CSV.
-   PDF por cliente (ReportLab + imagem de gráfico via Kaleido).

## 16) Segurança

-   Hash de senha (Werkzeug).
-   Limitar uploads.
-   Validar extensão `.xlsx`.
-   Sanitização de tipos.
-   Callbacks protegidos.

## 17) Critérios de Aceite

-   Login obrigatório.
-   Upload persiste dataset versionado.
-   Botão "Carregar Dados" funcional.
-   Refresh mantém dados.
-   Mensagens exibidas apenas quando necessário.
-   Filtros por ano robustos.
-   KPIs/bolhas/funil/downloads operando corretamente.
-   PDF por cliente gerado.

## 18) Helpers

    SENTINEL_ALL="__ALL__"

    def _norm_year(v):
        if v in (None,SENTINEL_ALL,"","Todos"): return None
        try: return int(v)
        except: return None

# 🔥 Novas Funcionalidades Sugeridas

Para tornar a ferramenta ainda mais poderosa, propomos os seguintes
incrementos:

### A) Inteligência Artificial

-   Classificação automática de clientes em **clusters de
    comportamento** (ativos, inativos, potenciais).
-   Modelo de ML para prever **probabilidade de fechamento** de
    cotações.
-   Geração de **insights automáticos**: recomendações de follow-up e
    alerta de risco de churn.

### B) Dashboard Avançado

-   Heatmap de **clientes × produtos**.
-   Comparativo de **concorrentes vs WEG** (quando houver dados).
-   **Indicador de performance por Unidade de Negócio**.

### C) Integrações

-   Exportação direta para **Excel e Google Sheets**.
-   Integração com **Outlook/WhatsApp** para follow-up.
-   API REST para integração com CRM externo.

### D) Funcionalidades Offline / Mobile

-   PWA (Progressive Web App) para acesso offline.
-   Geolocalização de clientes em **mapa interativo**.
-   Filtro por **última visita ou compra** no mapa.

### E) Colaboração

-   Perfis de usuários (Admin / Analista).
-   Log de auditoria (quem fez upload, criou relatórios, etc.).
-   Notificações por e-mail quando thresholds forem ultrapassados.

# 📐 Apêndice --- Guia de Layout das Telas

Este apêndice detalha como cada tela do sistema deve ser visualmente
organizada, servindo como referência adicional ao mockup em imagem.

## 1. Tela de Login

-   Fundo azul WEG, logo no topo centralizado.
-   Caixa central com campos: Usuário e Senha.
-   Botão "Entrar" azul WEG, texto branco.
-   Rodapé discreto com copyright.

## 2. Visão Geral

-   **Sidebar** azul à esquerda, com menu de navegação.
-   Parte superior: **cards de KPIs** (Clientes, Produtos, Conversão,
    Dias sem Compra).
-   Abaixo:
    -   Gráfico de evolução (ROL, Carteira, Entrada de Pedidos).
    -   Gráfico comparativo anual vs mensal.

## 3. KPIs por Cliente

-   Filtros no topo (Ano, Unidade de Negócio).
-   **Tabela central** com métricas: dias sem compra, mix, cotados,
    comprados, % não comprado.
-   À direita: scatterplot com comparativo visual.
-   Botão "Download CSV".

## 4. Produtos (Bolhas)

-   Filtros no topo (Ano, UN, Top N, Paleta).
-   **Gráfico de bolhas** clientes × produtos:
    -   Tamanho = quantidade cotada.
    -   Cor = % não comprado.
-   Abaixo: painel de **insights automáticos** gerados por IA.
-   Botões: Download CSV e PDF por cliente.

## 5. Funil & Ações

-   Duas listas centrais:
    -   Lista A → baixa conversão, alto volume.
    -   Lista B → risco de inatividade.
-   Cada cliente listado com ícones coloridos de status.
-   Rodapé: botão "Exportar CSV".

## 6. Configurações

-   Painel com inputs para thresholds por Unidade de Negócio.
-   Botão "Salvar Configurações".
-   Área de auditoria com **log de ações** de usuários.

📎 Arquivo complementar:
[layout_dashboard_weg.png](layout_dashboard_weg.png)\
Este arquivo contém a visualização consolidada de todas as telas.


---

# 🚀 Complementos Estratégicos para Evolução do Dashboard

## PWA (Progressive Web App)
- Permitir instalação no desktop e mobile como aplicativo.  
- Funcionalidade **offline-first**: sincroniza dados locais com o servidor quando houver internet.  
- Suporte a **notificações push** para alertar sobre metas, clientes em risco ou novas oportunidades.  

## Lazy Load e Performance
- Carregar gráficos e tabelas sob demanda para otimizar desempenho.  
- Implementar **paginadores inteligentes** nas tabelas grandes.  
- Utilizar cache de consultas recentes para reduzir tempo de resposta.  

## Responsividade
- Design adaptado para desktop, tablet e smartphone.  
- Sidebar recolhível automaticamente em telas menores.  
- Gráficos interativos que se reorganizam em grid responsivo.  

## Funcionamento Offline
- Base em IndexedDB/LocalStorage para manter filtros e datasets recentes.  
- Operação parcial offline (visualização dos últimos dados carregados).  
- Sincronização de logs e uploads assim que conexão for restabelecida.  

## Inteligência Artificial — Potencial Expandido
1. **Análise Preditiva Avançada**  
   - Modelos para prever faturamento futuro por cliente/produto.  
   - Identificação de clientes com maior potencial de recompra.  

2. **Assistente Virtual de Vendas**  
   - Chatbot interno para responder perguntas sobre KPIs, produtos e clientes.  
   - Sugestões de follow-up automáticas baseadas em comportamento histórico.  

3. **Conversão de Concorrentes**  
   - IA treinada para sugerir códigos equivalentes da WEG para produtos concorrentes.  
   - Geração automática de mensagens comerciais comparativas.  

4. **Otimização de Propostas**  
   - Recomendações de preço e desconto com base em histórico e margem.  
   - Análise de elasticidade da demanda.  

5. **Insights Automáticos**  
   - Alertas de clientes com risco de churn.  
   - Oportunidades de cross-sell e upsell detectadas automaticamente.  

## Tela de Cadastro e Acompanhamento de Metas
- **Cadastro de Metas por Usuário ou Unidade de Negócio**:  
  - Faturamento mensal, trimestral e anual.  
  - Quantidade de clientes ativos.  
  - Mix de produtos.  
- **Dashboard de Acompanhamento**:  
  - Gráfico de progresso (%) em relação à meta.  
  - Alertas quando metas não estiverem no ritmo esperado.  
  - Exportação de relatórios de metas em PDF e Excel.  

## Roadmap de Evolução
1. **MVP**: Uploads, KPIs, Funil e Relatórios PDF.  
2. **Versão 2.0**: IA básica (clusterização, previsões simples), integração Outlook/WhatsApp.  
3. **Versão 3.0**: PWA com offline completo, metas, IA avançada e dashboards comparativos.  

---

