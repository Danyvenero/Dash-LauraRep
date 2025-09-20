"""
Fix rápido para ML - versão simplificada do predict_repurchase_probability
"""

def apply_quick_fix():
    """Aplica correção rápida removendo problemas de sintaxe"""
    
    print("🚨 APLICANDO CORREÇÃO RÁPIDA")
    print("=" * 50)
    
    # Ler arquivo
    with open('utils/ml_recommendations.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir problema específico: adicionar um except simples antes de _clear_incompatible_model
    
    # Encontrar onde está o problema
    old_text = """            return features_df

    def _clear_incompatible_model(self):"""
    
    new_text = """            return features_df
        except Exception as e:
            logger.warning(f"Erro ML geral: {e}")
            features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)
            return features_df

    def _clear_incompatible_model(self):"""
    
    # Aplicar correção
    if old_text in content:
        content = content.replace(old_text, new_text)
        print("✅ Problema específico corrigido")
    else:
        print("⚠️ Texto específico não encontrado, tentando alternativa...")
        
        # Se não encontrou, procura pela definição da função
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def _clear_incompatible_model(self):' in line:
                # Adiciona except antes
                lines.insert(i, "        except Exception as e:")
                lines.insert(i+1, "            logger.warning(f'Erro ML geral: {e}')")
                lines.insert(i+2, "            features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)")
                lines.insert(i+3, "            return features_df")
                lines.insert(i+4, "")
                break
        content = '\n'.join(lines)
        print("✅ Correção alternativa aplicada")
    
    # Salvar arquivo
    with open('utils/ml_recommendations.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Arquivo salvo!")

if __name__ == "__main__":
    apply_quick_fix()