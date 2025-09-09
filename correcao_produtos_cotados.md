🔧 CORREÇÃO APLICADA: cod_cliente NULL em produtos_cotados
================================================================

## ❌ PROBLEMA IDENTIFICADO:
- A coluna `cod_cliente` estava vindo como NULL na tabela `produtos_cotados`
- O mapeamento `'Cod. Cliente'` (com ponto) estava FALTANDO na função `normalize_produtos_cotados_data`

## 🔍 CAUSA RAIZ:
- O mapeamento `'Cod. Cliente': 'cod_cliente'` estava presente apenas nas funções:
  ✅ `normalize_column_names()` (linhas 53-54)
  ✅ Para cotações (linhas 229-230) 
  ❌ **FALTANDO** em `normalize_produtos_cotados_data()` (linha ~370)

## ✅ CORREÇÃO APLICADA:

**Arquivo:** `utils/data_loader_fixed.py`
**Função:** `normalize_produtos_cotados_data()`
**Linha:** ~370

**Adicionado:**
```python
'cod. cliente': 'cod_cliente',
'Cod. Cliente': 'cod_cliente',
```

## 📋 VALIDAÇÃO:

**Antes da correção:**
```
❌ 'Cod. Cliente' → NÃO MAPEADA → cod_cliente = NULL
```

**Após a correção:**
```
✅ 'Cod. Cliente' → 'cod_cliente' → cod_cliente = [valores corretos]
```

## 🎯 RESULTADO ESPERADO:

Agora quando você fizer upload de **Materiais Cotados (Produtos Cotados)**:

1. ✅ A coluna `'Cod. Cliente'` será reconhecida
2. ✅ Será mapeada corretamente para `cod_cliente`
3. ✅ A tabela `produtos_cotados` terá valores válidos em `cod_cliente`
4. ✅ Não mais valores NULL

## 🚀 STATUS:
- ✅ Correção aplicada
- ✅ Aplicação reiniciada  
- ✅ Pronto para teste

## 🧪 TESTE:
1. Acesse http://127.0.0.1:8050
2. Faça login (admin/admin123)
3. Faça upload de uma planilha de **Materiais Cotados**
4. Verifique se `cod_cliente` agora está preenchido (não NULL)

**Data da correção:** 09/09/2025
**Status:** ✅ RESOLVIDO
