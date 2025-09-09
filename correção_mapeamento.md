📋 CORREÇÃO DE MAPEAMENTO - cod_cliente
=============================================

✅ PROBLEMA IDENTIFICADO:
- A coluna cod_cliente estava sendo mapeada incorretamente
- Estava capturando dados da coluna "Referência do Cliente" 
- Deveria capturar dados da coluna "Código do Cliente"

✅ CORREÇÕES APLICADAS:

1. utils/data_loader.py:
   ❌ REMOVIDO mapeamento incorreto:
   - 'referência do cliente': 'cod_cliente'
   - 'referencia do cliente': 'cod_cliente' 
   - 'ref cliente': 'cod_cliente'
   
   ✅ MANTIDO mapeamento correto:
   - 'código do cliente': 'cod_cliente'
   - 'codigo do cliente': 'cod_cliente'
   - 'código cliente': 'cod_cliente'
   - 'codigo_cliente': 'cod_cliente'
   - 'cod cliente': 'cod_cliente'
   - 'id_cli': 'cod_cliente'

2. utils/data_loader_fixed.py:
   ❌ REMOVIDO mapeamento incorreto:
   - 'referência do cliente': 'cod_cliente'
   - 'referencia do cliente': 'cod_cliente'
   - 'ref cliente': 'cod_cliente'
   
   ✅ MANTIDO mapeamento correto:
   - 'código do cliente': 'cod_cliente'
   - 'codigo do cliente': 'cod_cliente'
   - 'Código do Cliente': 'cod_cliente'
   - 'código cliente': 'cod_cliente'
   - 'codigo_cliente': 'cod_cliente'
   - 'cod cliente': 'cod_cliente'
   - 'id_cli': 'cod_cliente'

✅ RESULTADO ESPERADO:
- Agora a coluna cod_cliente vai capturar corretamente os dados da coluna "Código do Cliente"
- A coluna "Referência do Cliente" será ignorada ou tratada separadamente
- Os uploads de cotações terão o código correto do cliente

⚠️ PRÓXIMO PASSO:
- Reiniciar aplicação para aplicar as correções
- Testar upload de cotações para verificar se cod_cliente está correto
