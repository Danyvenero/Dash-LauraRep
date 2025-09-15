# 🤖 SISTEMA DE SUGESTÕES INTELIGENTES ML - DOCUMENTAÇÃO COMPLETA

## 📋 VISÃO GERAL

O Sistema de Sugestões Inteligentes é uma funcionalidade avançada do Dashboard WEG que utiliza algoritmos de Machine Learning para identificar oportunidades de venda baseadas em padrões históricos de cotações e vendas.

---

## 🧠 ALGORITMO IMPLEMENTADO

### **1. ANÁLISE DE CONVERSÃO DE COTAÇÕES**
```
Objetivo: Identificar produtos com alta demanda mas baixa conversão
Método: Análise de disparidade entre cotações e vendas efetivas

Cálculo da Taxa de Conversão:
Taxa = Total_Vendas ÷ Total_Cotações

Critérios de Oportunidade:
- Mínimo 3 cotações no período
- Taxa de conversão < 40%
- Existe diferença entre clientes que cotaram vs compraram
```

### **2. SCORING DE CONFIANÇA (0-100%)**
```
Componentes do Score:

🔹 Fator Base (até 90%): 
   min(0.9, total_cotações ÷ 10)
   
🔹 Fator Gap (até 30%):
   min(0.3, gap_clientes ÷ 5)
   
🔹 Fator Valor (até 20%):
   min(0.2, valor_histórico ÷ 100.000)

Score Final = Fator Base + Fator Gap + Fator Valor
```

### **3. IDENTIFICAÇÃO DE CLIENTE ALVO**
```
Algoritmo:
1. Listar clientes que fizeram cotações do produto
2. Remover clientes que já compraram o produto  
3. Resultado = Clientes em potencial para venda
4. Priorizar por histórico de compras similares
```

### **4. ESTIMATIVA DE RECEITA**
```
Cálculo:
Valor_Médio = Valor_Total_Histórico ÷ Total_Vendas
Receita_Estimada = Valor_Médio × Número_Clientes_Potenciais

Ajustes:
- Sazonalidade: ±15% baseado no mês atual
- Perfil Cliente: ±25% baseado no histórico do cliente
- Categoria Produto: ±10% baseado na margem típica
```

---

## 📊 FONTES DE DADOS

### **Dados de Vendas (Tabela: vendas)**
- `material`: Código do produto/material
- `vlr_rol`: Valor da venda realizada
- `cod_cliente`: Identificação do cliente
- `data_faturamento`: Data da venda
- `produto`: Descrição do produto

### **Dados de Cotações (Tabela: cotacoes)**
- `material`: Código do produto cotado
- `numero_cotacao`: Identificador da cotação
- `cod_cliente`: Cliente que solicitou cotação
- `data`: Data da cotação
- `produto`: Descrição do produto

### **Dados Derivados (Calculados pelo Sistema)**
- Taxa de conversão por produto
- Padrões sazonais de compra
- Perfil RFM dos clientes (Recência, Frequência, Valor Monetário)
- Clusters de produtos correlacionados

---

## 🔄 PROCESSAMENTO DE FEEDBACK

### **Sistema de Coleta**
```
Feedback Estruturado:
- Rating: 1-5 estrelas
- Categorias: Precisão, Timing, Relevância, Qualidade

Feedback em Texto Livre:
- Análise de sentimento (positivo/negativo/neutro)
- Extração de palavras-chave
- Categorização automática do tipo de feedback
```

### **Palavras-Chave Monitoradas**
```
Qualidade Positiva: 'preciso', 'correto', 'bom', 'útil', 'relevante'
Qualidade Negativa: 'errado', 'irrelevante', 'ruim', 'inútil'
Timing: 'tarde', 'atrasado', 'oportuno', 'momento certo'
Cliente: 'cliente errado', 'perfil diferente', 'cliente ideal'
```

### **Processamento Automatizado**
```python
def processar_feedback(rating, texto):
    # 1. Classificar sentiment
    sentiment = classificar_sentiment(rating, texto)
    
    # 2. Extrair keywords
    keywords = extrair_palavras_chave(texto)
    
    # 3. Ajustar pesos do modelo
    if sentiment == 'positivo':
        aumentar_peso_fatores_utilizados()
    elif sentiment == 'negativo':
        reduzir_peso_fatores_utilizados()
    
    # 4. Log estruturado
    salvar_feedback_log(rating, texto, keywords, timestamp)
```

---

## 🎯 TIPOS DE SUGESTÕES GERADAS

### **1. Oportunidades de Conversão**
```
Descrição: Produtos cotados mas não comprados
Justificativa: "🎯 X cotações vs Y vendas (conversão: Z%) - N clientes em potencial"
Confiança: 65-95% (baseada em volume de dados)
```

### **2. Cross-Selling Inteligente**
```
Descrição: Produtos comprados por clientes similares
Justificativa: "📈 Padrão ML: Similar a compras de X clientes equivalentes"
Confiança: 60-85% (baseada em similaridade)
```

### **3. Reativação de Clientes**
```
Descrição: Produtos para clientes inativos há X dias
Justificativa: "⏰ Cliente inativo há X dias, padrão de recompra identificado"
Confiança: 50-75% (baseada em histórico temporal)
```

---

## ⚙️ CONFIGURAÇÕES E PARÂMETROS

### **Thresholds do Algoritmo**
```python
# Critérios de oportunidade
MINIMO_COTACOES = 3
TAXA_CONVERSAO_LIMITE = 0.4  # 40%
MINIMO_GAP_CLIENTES = 1

# Limites de confidence
CONFIDENCE_MINIMO = 0.5   # 50%
CONFIDENCE_MAXIMO = 0.95  # 95%

# Limites de sugestões
MAX_SUGESTOES_REAIS = 15
MAX_SUGESTOES_SINTETICAS = 10
TOTAL_MAX_SUGESTOES = 20
```

### **Pesos para Scoring**
```python
PESO_VOLUME_COTACOES = 0.4    # 40%
PESO_GAP_CLIENTES = 0.3       # 30%
PESO_VALOR_HISTORICO = 0.2    # 20%
PESO_SAZONALIDADE = 0.1       # 10%
```

---

## 🔧 ARQUITETURA TÉCNICA

### **Fluxo de Execução**
```mermaid
graph TD
    A[Usuário clica "Gerar Sugestões ML"] --> B[Carregar dados vendas/cotações]
    B --> C[Análise de conversão por produto]
    C --> D[Cálculo de gap de clientes]
    D --> E[Scoring de confiança]
    E --> F[Identificação cliente alvo]
    F --> G[Estimativa de receita]
    G --> H[Ordenação por confiança]
    H --> I[Apresentação na interface]
    I --> J[Coleta de feedback]
    J --> K[Ajuste de pesos do modelo]
```

### **Tecnologias Utilizadas**
```
Backend: Python + Pandas + NumPy
Frontend: Dash + Plotly + DataTable
Database: SQLite (desenvolvimento) / PostgreSQL (produção)
ML Libraries: Scikit-learn (futuro), SciPy (estatísticas)
```

---

## 📈 MÉTRICAS DE PERFORMANCE

### **KPIs do Sistema**
```
1. Taxa de Precisão: % de sugestões que resultaram em vendas
2. Cobertura: % de oportunidades reais identificadas
3. Relevância: Média do feedback dos usuários (1-5)
4. Tempo de Resposta: < 3 segundos para gerar sugestões
5. Adoption Rate: % de usuários que utilizam regularmente
```

### **Monitoramento Contínuo**
```python
def calcular_metricas_performance():
    # Taxa de conversão das sugestões
    conversao = vendas_de_sugestoes / total_sugestoes_geradas
    
    # Feedback médio dos usuários
    feedback_medio = media(todos_ratings_feedback)
    
    # Cobertura de oportunidades
    cobertura = oportunidades_identificadas / total_oportunidades_reais
    
    return {
        'conversao': conversao,
        'feedback_medio': feedback_medio, 
        'cobertura': cobertura
    }
```

---

## 🚀 ROADMAP DE EVOLUÇÃO

### **Versão Atual (1.0)**
- ✅ Algoritmo baseado em regras heurísticas
- ✅ Análise de conversão cotação→venda
- ✅ Sistema de feedback estruturado
- ✅ Interface interativa com seleção múltipla

### **Versão 2.0 (Planejada)**
- 🔄 Machine Learning verdadeiro (Random Forest)
- 🔄 Análise de sazonalidade avançada
- 🔄 Integração com dados externos
- 🔄 API para sistemas externos

### **Versão 3.0 (Futuro)**
- 📅 Deep Learning para padrões complexos
- 📅 Análise de sentimento em tempo real
- 📅 Recomendações personalizadas por usuário
- 📅 A/B Testing automatizado

---

## 👥 INSTRUÇÕES PARA A EQUIPE

### **Para Vendedores**
```
1. Acesse Analytics Avançados → Gaps de Oportunidade
2. Clique em "Gerar Sugestões ML"
3. Analise a lista ordenada por confiança
4. Selecione sugestões relevantes para seu portfólio
5. Exporte em CSV para ação comercial
6. Forneça feedback sobre resultados
```

### **Para Gestores**
```
1. Monitore métricas de adoption rate
2. Analise feedback dos vendedores
3. Identifique padrões de sucesso/insucesso
4. Ajuste parâmetros conforme performance
5. Reporte insights para evolução do modelo
```

### **Para Analistas de Dados**
```
1. Monitore qualidade dos dados de entrada
2. Analise logs de feedback para insights
3. Identifique oportunidades de melhoria
4. Mantenha documentação atualizada
5. Planeje evoluções do algoritmo
```

---

## ❓ FAQ - PERGUNTAS FREQUENTES

**Q: O sistema realmente usa Machine Learning?**
A: A versão atual (1.0) usa algoritmos estatísticos e regras heurísticas. ML verdadeiro está planejado para v2.0.

**Q: Como o feedback melhora o modelo?**
A: Feedback positivo aumenta peso dos fatores usados; feedback negativo os reduz. Sistema de aprendizado contínuo.

**Q: Por que algumas sugestões mostram clientes genéricos?**
A: Quando dados reais são insuficientes, o sistema gera sugestões sintéticas para demonstração.

**Q: Como interpretar o score de confiança?**
A: 80-95% = Alta confiança; 60-79% = Média; 50-59% = Baixa. Baseado em volume e qualidade dos dados.

**Q: Posso personalizar os critérios do algoritmo?**
A: Sim, parâmetros são configuráveis via código. Contate o administrador do sistema.

---

## 📞 SUPORTE TÉCNICO

**Desenvolvedor:** Assistant AI
**Documentação:** Dashboard WEG v2.0
**Última Atualização:** Setembro 2025
**Versão do Sistema:** 1.0

Para sugestões de melhoria ou reportar bugs, utilize o sistema de feedback integrado na aplicação.
