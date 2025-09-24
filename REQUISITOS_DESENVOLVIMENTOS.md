# REQUISITOS E FUNCIONALIDADES IMPLEMENTADAS

Este documento descreve os requisitos funcionais e técnicos implementados recentemente na Análise Detalhada de Produtos e nos callbacks relacionados.

## Contexto
- Página: Produtos (`/app/products` ou `/produtos`).
- Componentes principais:
  - Dropdown de materiais: `filter-material-table` (value, search_value, options)
  - Tabela de produtos: `produtos-table` (dash_table)
  - Contêiner de saída: `tabela-analise-produtos-container`
  - Filtros globais: `global-filtro-ano`, `global-filtro-mes`, `global-filtro-cliente`, `global-filtro-hierarquia`, `global-filtro-canal`, `global-filtro-top-clientes`, `global-filtro-dias-sem-compra`
- Módulos impactados:
  - `webapp/produtos_table_callback_new.py` (callback ativo da página de produtos)
  - `webapp/callbacks.py` (registro do callback e padronização de logs)

## Funcionalidades novas/alteradas

### 1) Tabela de Produtos alinhada aos filtros globais
- A tabela agora utiliza a mesma função de filtragem global dos gráficos: `apply_filters(...)` com `metrica_type='faturamento'`.
- A resposta da tabela reflete exatamente as seleções de Ano, Mês, Cliente, Hierarquia, Canal, Top Clientes e Dias sem compra.

### 2) Métrica de Recorrência
- Métrica ajustada para “Recorrência/Mês” (média mensal):
  - Cálculo: `recorrencia_mensal = recorrencia_compra / meses_distintos`.
  - `meses_distintos` é inferido a partir de `data_faturamento` (ou `data` como fallback), normalizado por período mensal.
  - Apresentação: coluna “Recorrência/Mês” com 2 casas decimais; alinhamento à direita.

### 3) Dropdown de Materiais com busca avançada e destaque (typeahead)
- Opções do dropdown são dinâmicas e coerentes com os filtros globais atuais (a fonte de dados das opções é o DataFrame já filtrado por `apply_filters`).
- Limite de 200 opções após ordenação (performance).
- Manutenção de seleção: valores já selecionados são preservados nas opções mesmo quando não atendem a nova busca.
- Priorização: itens que começam com o(s) termo(s) buscado(s) aparecem primeiro.
- Destaque visual: termos buscados são realçados no label do código/descrição.
- Ajuda embutida: ao digitar, surge uma entrada (desabilitada) com um resumo dos operadores.

#### Operadores suportados no campo de busca do dropdown
- "frase exata" — exige a sequência exata no código ou na descrição.
- -termo — exclui opções contendo o termo.
- code:abc — busca apenas no código (material).
- desc:xyz — busca apenas na descrição (produto).
- ^ini — âncora de início (começa com).
- fim$ — âncora de término (termina com).
- a|b — operador OR (qualquer um dos termos do grupo deve aparecer).
- AND implícito — múltiplos termos separados por espaço são combinados por AND (todos devem aparecer), exceto quando explicitamente separados por `|` (OR).

### 4) Comportamento do filtro de materiais (consistência com a tabela)
- A tabela aplica dois tipos de filtro:
  - Seleção exata por código (valores marcados no dropdown).
  - Filtro “contains” digitado (código ou descrição) quando `search_value` possui ao menos 2 chars.
- Valores especiais internos (ex.: opção de ajuda) são ignorados pela tabela.

### 5) Melhorias de logging e estabilidade
- Redução de ruído: substituição de prints por `logging` em `produtos_table_callback_new.py`.
- Desativação do callback de teste temporário em `callbacks.py`.
- Import do callback de produtos logado em nível `INFO`.

### 6) Priorização RFM com pesos ajustáveis e normalização por quantis
- Foi adicionada a coluna “Prioridade” na tabela, calculada a partir de um score RFM (Recency, Frequency, Monetary).
- Normalização robusta por quantis (percentile ranks) para cada componente:
  - R (recency_days): invertida (quanto mais recente, maior o score)
  - F (recorrência_mensal): direta
  - M (faturamento_total): direta
- O score final é uma soma ponderada: Prioridade = 100 * (wR*R + wF*F + wM*M)
- Pesos ajustáveis via sliders no layout: `rfm-weight-r`, `rfm-weight-f`, `rfm-weight-m` (padrão 40/30/30). Os valores são normalizados para somar 1.
- A ordenação padrão da tabela considera primeiro “Prioridade” (desc), depois “Faturamento Total” (desc) como desempate.

## Critérios de Aceite (resumo)
- [x] A tabela exibe a coluna “Recorrência/Mês” com duas casas decimais.
- [x] A tabela reage a todos os filtros globais, reproduzindo o comportamento dos gráficos.
- [x] O dropdown “Filtrar por Material” mostra opções coerentes com os filtros globais e com a busca digitada.
- [x] Busca avançada com operadores funciona conforme descrito e destaca termos no label.
- [x] Até 200 opções são exibidas; itens selecionados permanecem visíveis nas opções.
- [x] A coluna “Prioridade” aparece e responde aos pesos R/F/M definidos nos sliders.
- [x] A normalização do score RFM é baseada em quantis, tornando o ranking mais robusto a outliers.

## Detalhes técnicos
- Callback da tabela: `update_produtos_table_with_filters(...)` em `webapp/produtos_table_callback_new.py`.
  - Inputs: `filter-material-table.value`, `filter-material-table.search_value`, `filter-top-produtos`, `table-page-size-produtos`, filtros globais, sliders de pesos RFM (`rfm-weight-r`, `rfm-weight-f`, `rfm-weight-m`) e `url.pathname`.
  - Saída: `tabela-analise-produtos-container.children` com um `dash_table.DataTable` configurado.
- Callback de opções do dropdown: `update_material_filter_options(...)` em `webapp/produtos_table_callback_new.py`.
  - Inputs: `url.pathname`, `filter-material-table.search_value`, filtros globais.
  - State: `filter-material-table.value`.
  - Saída: `filter-material-table.options`.
- Colunas exibidas (quando disponíveis): Material, Produto, Faturamento Total, Valor Médio, Quantidade, Recorrência/Mês e Hierarquia.

## Limitações conhecidas e próximos passos
- Limite de 200 opções no dropdown é fixo para performance; podemos priorizar por faturamento/recorrência antes de cortar se necessário.
- Busca avançada não suporta parênteses de precedência; grupos OR são por token (`a|b`).
- Sugerido: adicionar preferência de ordenação por faturamento nas opções e cache leve para buscas repetidas com os mesmos filtros globais.

## Arquivos alterados
- `webapp/produtos_table_callback_new.py`:
  - Uso de `apply_filters` para a tabela
  - Cálculo de recorrência mensal e mapeamento de colunas
  - Dropdown com busca avançada, destaque e ajuda embutida
  - Logging reduzido (menos prints)
  - Score RFM com normalização por quantis e pesos ajustáveis via sliders
- `webapp/callbacks.py`:
  - Desativação do callback de teste
  - Padronização de logs na importação do callback de produtos

## Contatos / Observações
- Qualquer ajuste fino de UX (ordenação por faturamento, mais operadores, etc.) pode ser incorporado incrementalmente.
