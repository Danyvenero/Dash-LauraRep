# Encontrar onde começa a duplicação
with open('webapp/callbacks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total de linhas: {len(lines)}')

# Procurar por linhas idênticas consecutivas em grande escala
duplicate_start = None
duplicate_count = 0

for i in range(len(lines) - 100):  # Verificar em blocos
    # Verificar se as próximas 50 linhas já apareceram antes
    current_block = lines[i:i+50]
    
    for j in range(i):
        if j + 50 < len(lines):
            compare_block = lines[j:j+50]
            if current_block == compare_block:
                duplicate_start = j + 1
                duplicate_end = i + 1
                print(f'\\n🔍 DUPLICAÇÃO ENCONTRADA!')
                print(f'Bloco original: linhas {duplicate_start} a {duplicate_start + 49}')
                print(f'Bloco duplicado: linhas {duplicate_end} a {duplicate_end + 49}')
                
                # Mostrar conteúdo da duplicação
                print(f'\\nConteúdo duplicado (primeiras 5 linhas):')
                for k in range(5):
                    if j + k < len(lines):
                        print(f'  {j + k + 1:4d}: {lines[j + k].rstrip()}')
                
                break
    
    if duplicate_start:
        break

if not duplicate_start:
    print('\\nNenhuma duplicação de bloco grande encontrada')
    
    # Verificar de forma diferente - procurar por seções que se repetem
    print('\\nVerificando seções específicas...')
    
    # Procurar por início de callbacks duplicados
    callback_starts = []
    for i, line in enumerate(lines):
        if '@app.callback' in line and not line.strip().startswith('#'):
            callback_starts.append(i)
    
    print(f'Callbacks encontrados nas linhas: {callback_starts}')
    
    # Verificar se há duplicação próximo ao meio do arquivo
    mid_point = len(lines) // 2
    print(f'\\nVerificando ao redor da linha {mid_point}...')
    
    # Procurar por linhas características
    for search_text in ['# Callback para mostrar conteúdo', 'def display_page_content', '@app.callback']:
        occurrences = []
        for i, line in enumerate(lines):
            if search_text in line:
                occurrences.append(i + 1)
        if len(occurrences) > 1:
            print(f'"{search_text}" encontrado nas linhas: {occurrences}')
else:
    # Sugerir onde fazer o corte
    print(f'\\n💡 SOLUÇÃO: Remover linhas {duplicate_end} até o final do arquivo')
    print(f'O arquivo deve ter {duplicate_end - 1} linhas em vez de {len(lines)}')
