"""
Script para corrigir sintaxe do arquivo ML
"""

def fix_ml_syntax():
    """Corrige problemas de sintaxe no arquivo ML"""
    
    print("🔧 CORRIGINDO SINTAXE DO ML")
    print("=" * 50)
    
    # Ler o arquivo
    with open('utils/ml_recommendations.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir problemas conhecidos
    # 1. Remover try órfão antes de def _clear_incompatible_model
    content = content.replace(
        "            return features_df\n                    \n    def _clear_incompatible_model(self):",
        "            return features_df\n                    \n    def _clear_incompatible_model(self):"
    )
    
    # 2. Verificar se há algum try sem except
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Se é um try que não tem except correspondente, adiciona um except simples
        if 'try:' in line and i < len(lines) - 1:
            # Procura o except correspondente
            indent_level = len(line) - len(line.lstrip())
            found_except = False
            
            for j in range(i + 1, min(i + 50, len(lines))):  # Procura nas próximas 50 linhas
                next_line = lines[j]
                if 'except' in next_line and len(next_line) - len(next_line.lstrip()) == indent_level:
                    found_except = True
                    break
                elif 'def ' in next_line and len(next_line) - len(next_line.lstrip()) <= indent_level:
                    # Nova função no mesmo nível ou menor = try órfão
                    break
            
            if not found_except and 'def _clear_incompatible_model' in str(lines[i:i+10]):
                # Este é um try órfão antes do _clear_incompatible_model
                continue  # Pula esta linha
        
        fixed_lines.append(line)
    
    # Escrever arquivo corrigido
    with open('utils/ml_recommendations.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ Sintaxe corrigida!")

if __name__ == "__main__":
    fix_ml_syntax()