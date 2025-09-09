# 📋 Padronização de Dados - Dashboard Laura Representações

## ✅ Implementação Concluída

### 🎯 **Abordagem Escolhida: Padronização ANTES do Uso dos Dados**

A melhor abordagem é aplicar padronizações **APÓS carregar os dados do banco** e **ANTES de usar nos callbacks**. Isso garante:

- ✅ **Preservação dos dados originais** no banco
- ✅ **Rastreabilidade completa** dos dados brutos
- ✅ **Flexibilidade** para ajustar padronizações sem reprocessar dados
- ✅ **Performance otimizada** (aplicada apenas quando necessário)

---

## 🔧 **Arquivos Implementados**

### 1. **`utils/data_standardization.py`** (NOVO)

**Funções para Vendas:**
- `ov_general_adjustments()` - Ajustes gerais (filtros, tipos, unidades de negócio)
- `ov_hierarquia_um()` - Padronização da hierarquia produto nível 1  
- `ov_hierarquia_dois()` - Padronização da hierarquia produto nível 2
- `ov_hierarquia_tres()` - Padronização da hierarquia produto nível 3
- `apply_vendas_standardization()` - Função principal que aplica todas as padronizações

**Funções para Cotações:**
- `centro_fornecedor_mapping()` - Mapeia centro fornecedor para unidade de negócio
- `apply_cotacoes_standardization()` - Função principal para cotações

### 2. **`utils/db.py`** (MODIFICADO)

**Funções Atualizadas:**
- `load_vendas_data()` - Agora aplica `apply_vendas_standardization()` antes de retornar
- `load_cotacoes_data()` - Agora aplica `apply_cotacoes_standardization()` antes de retornar

---

## 🔄 **Como Funciona**

### **Fluxo de Dados:**

```mermaid
graph LR
    A[Dados Brutos no Banco] --> B[load_vendas_data()]
    B --> C[Conversão de Datas]
    C --> D[apply_vendas_standardization()]
    D --> E[Dados Padronizados para Callbacks]
    
    F[Dados Brutos no Banco] --> G[load_cotacoes_data()]
    G --> H[Conversão de Datas]
    H --> I[apply_cotacoes_standardization()]
    I --> J[Dados Padronizados para Callbacks]
```

### **1. Carregamento de Vendas:**
```python
# Antes
vendas_df = load_vendas_data()  # Dados brutos

# Agora  
vendas_df = load_vendas_data()  # Dados padronizados automaticamente
```

### **2. Carregamento de Cotações:**
```python
# Antes
cotacoes_df = load_cotacoes_data()  # Dados brutos

# Agora
cotacoes_df = load_cotacoes_data()  # Dados padronizados automaticamente
```

---

## 📊 **Principais Padronizações Aplicadas**

### **Para Vendas:**

#### **Filtros de Produtos:**
- Filtra apenas produtos válidos baseado em `hier_produto_1`
- Remove materiais configurados (ex: `10000008`)

#### **Conversões de Tipo:**
- Campos texto → `string`
- Campos numéricos → `numeric` (com `errors='coerce'`)
- Cliente → `lowercase`

#### **Padronização de Unidades de Negócio:**
```python
'WEG Automação' → 'WAU'
'WEG Digital e Sistemas' → 'WDS'  
'WEG Energia' → 'WEN'
'WEG Motores Comercial e Appliance' → 'WMO-C'
'WEG Motores Industrial' → 'WMO-I'
'WEG Transmissão e Distribuição' → 'WTD'
```

#### **Hierarquia de Produtos (Exemplos):**
```python
# Nível 1
'MOTORES INDUSTRIAIS' → 'WMO-I'
'SOLAR WAU' → 'SOLAR'
'DRIVES BT' → 'DRIVES'

# Nível 2  
'INVERSORES DE FREQUÊNCIA SERIADOS' → 'INVERSOR'
'MODULO FOTOVOLTAICO' → 'MÓDULOS'
'MOTORES COMERCIAIS' → 'WCA1'

# Nível 3
'W22 RURAL TEFC' → 'W22 RURAL'
'FUSÍVEL NH ULTRARRÁPIDO' → 'aR'
'CONTATORES AUXILIARES' → 'CAW'
```

### **Para Cotações:**

#### **Mapeamento Centro Fornecedor:**
```python
1100.0 → 'WMO-I'    # WEG Motores Industrial
1106.0 → 'WMO-C'    # WEG Motores Comercial  
1200.0 → 'WEN'      # WEG Energia
1340.0 → 'SOLAR'    # Solar
9999.0 → 'OUTRO'    # Outros não mapeados
```

---

## 🚀 **Benefícios da Implementação**

### **1. Transparência:**
- Dados originais preservados no banco
- Padronizações aplicadas em tempo real
- Facilita debugging e auditoria

### **2. Performance:**
- Padronizações só ocorrem quando dados são solicitados
- Cache natural do Dash/Flask evita reprocessamento desnecessário
- Índices do banco mantêm consultas rápidas

### **3. Manutenibilidade:**
- Lógica de padronização centralizada em um módulo
- Fácil adicionar novas regras sem alterar banco
- Versionamento simples através do código

### **4. Flexibilidade:**
- Diferentes padronizações para diferentes contextos
- Possibilidade de aplicar padronizações condicionalmente
- Facilita testes A/B com diferentes regras

---

## 🔍 **Próximos Passos**

1. **✅ CONCLUÍDO:** Implementar todas as funções de padronização
2. **✅ CONCLUÍDO:** Integrar com funções de carregamento de dados
3. **⏳ PENDENTE:** Testar com dados reais no dashboard
4. **⏳ PENDENTE:** Validar se cálculos de KPIs estão corretos após padronização
5. **⏳ PENDENTE:** Ajustar filtros individuais se necessário

---

## 📝 **Como Testar**

### **Método 1: Testar Carregamento**
```python
from utils.db import load_vendas_data, load_cotacoes_data

# Carregar dados (já com padronizações aplicadas)
vendas_df = load_vendas_data()
cotacoes_df = load_cotacoes_data()

# Verificar se padronizações foram aplicadas
print(vendas_df['unidade'].unique())  # Deve mostrar WAU, WDS, WEN, etc.
print(cotacoes_df['unidade_negocio'].unique())  # Deve mostrar WMO-I, WEN, SOLAR, etc.
```

### **Método 2: Testar Dashboard**
1. Acessar o dashboard: http://127.0.0.1:8050
2. Navegar para "Visão Geral"
3. Verificar se os KPIs respondem corretamente aos filtros
4. Verificar se os valores calculados fazem sentido com os dados padronizados

---

## 🎯 **Resultado Esperado**

Com as padronizações implementadas:

- **✅ Dados consistentes** em toda a aplicação
- **✅ KPIs mais precisos** com categorias padronizadas  
- **✅ Filtros funcionando corretamente** com dados limpos
- **✅ Visualizações melhores** com labels padronizados
- **✅ Performance mantida** sem impacto significativo

---

*Implementação concluída em 09/09/2025 - Dashboard Laura Representações*
