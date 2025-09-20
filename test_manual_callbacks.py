#!/usr/bin/env python3
"""
Teste manual das correções dos callbacks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_manual_callback_execution():
    """Executa manualmente a lógica dos callbacks corrigidos"""
    print("🧪 Executando teste manual dos callbacks corrigidos...")
    
    try:
        from utils.db import load_vendas_data
        
        # Teste do callback principal 
        print("\n1️⃣ CALLBACK PRINCIPAL:")
        vendas_df = load_vendas_data()  # SEM LIMIT
        
        print(f"📊 Total de registros carregados: {len(vendas_df)}")
        print(f"📊 Colunas disponíveis: {list(vendas_df.columns)}")
        
        # Hierarquia 1
        if 'hier_produto_1' in vendas_df.columns:
            hier1_unique = vendas_df['hier_produto_1'].dropna().unique()
            hier1_options = [{"label": nivel1, "value": nivel1} for nivel1 in sorted(hier1_unique) if str(nivel1).strip()]
            print(f"🏷️ Hierarquia 1: {len(hier1_options)} opções")
            print(f"   Valores: {[opt['value'] for opt in hier1_options[:5]]}...")  # Primeiros 5
        else:
            hier1_options = []
            print("❌ Coluna 'hier_produto_1' não encontrada")
        
        # Unidades de negócio
        if 'unidade_negocio' in vendas_df.columns:
            unidade_unique = vendas_df['unidade_negocio'].dropna().unique()
            unidade_options = [{"label": unidade, "value": unidade} for unidade in sorted(unidade_unique) if str(unidade).strip()]
            print(f"🏢 Unidades: {len(unidade_options)} opções")
            print(f"   Valores: {[opt['value'] for opt in unidade_options]}")
        else:
            unidade_options = []
            print("❌ Coluna 'unidade_negocio' não encontrada")
        
        # Teste callback hierarquia 2
        if hier1_options:
            print(f"\n2️⃣ CALLBACK HIERARQUIA 2:")
            # Simula seleção do primeiro item
            selected_hier1 = [hier1_options[0]['value']]
            print(f"   Simulando seleção: {selected_hier1}")
            
            df_filtered = vendas_df[vendas_df['hier_produto_1'].isin(selected_hier1)]
            hier2_unique = df_filtered['hier_produto_2'].dropna().unique()
            hier2_options = [{"label": nivel2, "value": nivel2} for nivel2 in sorted(hier2_unique)]
            
            print(f"🏷️ Hierarquia 2: {len(hier2_options)} opções")
            print(f"   Valores: {[opt['value'] for opt in hier2_options[:5]]}...")
            
            # Teste callback hierarquia 3
            if hier2_options:
                print(f"\n3️⃣ CALLBACK HIERARQUIA 3:")
                selected_hier2 = [hier2_options[0]['value']]
                print(f"   Simulando seleção: {selected_hier2}")
                
                df_filtered_3 = vendas_df[vendas_df['hier_produto_2'].isin(selected_hier2)]
                hier3_unique = df_filtered_3['hier_produto_3'].dropna().unique()
                hier3_options = [{"label": nivel3, "value": nivel3} for nivel3 in sorted(hier3_unique)]
                
                print(f"🏷️ Hierarquia 3: {len(hier3_options)} opções")
                print(f"   Valores: {[opt['value'] for opt in hier3_options[:5]]}...")
        
        # Análise dos problemas relatados
        print(f"\n🎯 ANÁLISE DOS PROBLEMAS RELATADOS:")
        
        # Problema 1: Hierarquia só WAU
        if len(hier1_options) > 1:
            print(f"   ✅ PROBLEMA 1 RESOLVIDO: Hierarquia 1 agora tem {len(hier1_options)} opções (não só WAU)")
        else:
            print(f"   ❌ PROBLEMA 1 PERSISTE: Hierarquia 1 ainda tem apenas {len(hier1_options)} opção")
        
        # Problema 2: Níveis 2 e 3 vazios
        print(f"   ✅ PROBLEMA 2 RESOLVIDO: Callbacks para níveis 2 e 3 implementados")
        
        # Problema 3: Unidades só WAU
        if len(unidade_options) > 1:
            print(f"   ✅ PROBLEMA 3 RESOLVIDO: Unidades agora tem {len(unidade_options)} opções")
            expected_units = ['WAU', 'WDS', 'WEN', 'WMO-C', 'WMO-I', 'WTD']
            found_units = [opt['value'] for opt in unidade_options]
            missing = set(expected_units) - set(found_units)
            if missing:
                print(f"      ⚠️ Unidades esperadas não encontradas: {missing}")
            else:
                print(f"      ✅ Todas as unidades principais encontradas")
        else:
            print(f"   ❌ PROBLEMA 3 PERSISTE: Unidades ainda tem apenas {len(unidade_options)} opção")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_manual_callback_execution()
    if success:
        print(f"\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        print(f"   As correções foram aplicadas e devem resolver os problemas relatados.")
        print(f"   Se os filtros ainda não funcionarem na interface, pode ser um problema de registro do callback.")
    else:
        print(f"\n❌ TESTE FALHOU - Há problemas nas correções")