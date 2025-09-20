"""
Correção específica para erro de sintaxe
"""

import re

def fix_syntax_specific():
    """Corrige erro específico de try sem except"""
    
    print("🔧 CORREÇÃO ESPECÍFICA DE SINTAXE")
    print("=" * 50)
    
    # Ler arquivo
    with open('utils/ml_recommendations.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Dividir em linhas
    lines = content.split('\n')
    
    # Encontrar a função predict_repurchase_probability
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'def predict_repurchase_probability(' in line:
            start_idx = i
        elif start_idx is not None and line.strip().startswith('def ') and not 'predict_repurchase_probability' in line:
            end_idx = i
            break
    
    if start_idx is None:
        print("❌ Função não encontrada")
        return
    
    print(f"📍 Função encontrada: linhas {start_idx} - {end_idx}")
    
    # Verificar try/except balanceamento
    function_lines = lines[start_idx:end_idx]
    try_count = 0
    except_count = 0
    
    for line in function_lines:
        if 'try:' in line:
            try_count += 1
        if 'except' in line:
            except_count += 1
    
    print(f"📊 Try: {try_count}, Except: {except_count}")
    
    if try_count > except_count:
        print("⚠️ Try órfão detectado - adicionando except")
        
        # Encontrar a linha antes de _clear_incompatible_model
        for i in range(len(lines)):
            if 'def _clear_incompatible_model(self):' in lines[i]:
                # Adicionar except antes
                lines.insert(i, "                except Exception as e:")
                lines.insert(i+1, "                    logger.warning(f'Erro ML: {e}')")
                lines.insert(i+2, "                    features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)")
                break
    
    # Salvar arquivo corrigido
    with open('utils/ml_recommendations.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Correção aplicada!")

if __name__ == "__main__":
    fix_syntax_specific()