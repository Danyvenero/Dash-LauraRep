from app import app
from utils import db
import pandas as pd

with app.app_context():
    print("=== VERIFICAÇÃO DA COLUNA ROL ===")
    
    # Carregar dados
    df_vendas = db.get_clean_vendas_as_df()
    
    print(f"Total de registros: {len(df_vendas)}")
    print(f"\nColunas disponíveis:")
    for i, col in enumerate(df_vendas.columns, 1):
        print(f"{i:2d}. {col}")
    
    # Verificar se existe ROL
    if 'ROL' in df_vendas.columns:
        print(f"\n✅ Coluna ROL encontrada!")
        print(f"Valores na coluna ROL:")
        print(f"  - Soma total: {df_vendas['ROL'].sum():,.2f}")
        print(f"  - Valores negativos: {(df_vendas['ROL'] < 0).sum()}")
        print(f"  - Valores positivos: {(df_vendas['ROL'] > 0).sum()}")
        print(f"  - Valores zero: {(df_vendas['ROL'] == 0).sum()}")
        
        # Mostrar exemplos
        print(f"\nExemplos de valores ROL:")
        print(df_vendas[['cod_cliente', 'cliente', 'ROL']].head(10))
        
    elif 'rol' in df_vendas.columns:
        print(f"\n✅ Coluna rol (minúscula) encontrada!")
        print(f"Valores na coluna rol:")
        print(f"  - Soma total: {df_vendas['rol'].sum():,.2f}")
        print(f"  - Valores negativos: {(df_vendas['rol'] < 0).sum()}")
        
    else:
        print(f"\n❌ Coluna ROL não encontrada!")
        
        # Procurar colunas similares
        colunas_valor = [col for col in df_vendas.columns if any(term in col.lower() for term in ['valor', 'fatur', 'receita', 'rol'])]
        print(f"Colunas relacionadas a valor encontradas: {colunas_valor}")
        
        for col in colunas_valor:
            if df_vendas[col].dtype in ['int64', 'float64']:
                soma = df_vendas[col].sum()
                negativos = (df_vendas[col] < 0).sum()
                print(f"  {col}: soma={soma:,.2f}, negativos={negativos}")
    
    # Testar filtro CONTROLS
    print(f"\n=== TESTE FILTRO CONTROLS ===")
    colunas_produto = [col for col in df_vendas.columns if any(term in col.lower() for term in ['produto', 'material', 'descri'])]
    print(f"Colunas relacionadas a produto: {colunas_produto}")
    
    for col in colunas_produto:
        if col in df_vendas.columns:
            controls_matches = df_vendas[df_vendas[col].str.contains('CONTROLS', case=False, na=False)]
            print(f"  {col}: {len(controls_matches)} registros contêm 'CONTROLS'")
            if len(controls_matches) > 0:
                clientes_controls = controls_matches['cliente'].unique()
                print(f"    Clientes: {clientes_controls[:5]}")
                
    # Verificar filtros de ano e mês
    print(f"\n=== VERIFICAÇÃO DE DADOS 2024-2025 ===")
    df_vendas['data_faturamento'] = pd.to_datetime(df_vendas['data_faturamento'], errors='coerce')
    df_2024_2025 = df_vendas[df_vendas['data_faturamento'].dt.year.isin([2024, 2025])]
    print(f"Registros em 2024-2025: {len(df_2024_2025)}")
    
    if len(df_2024_2025) > 0:
        df_dez = df_2024_2025[df_2024_2025['data_faturamento'].dt.month == 12]
        print(f"Registros em dezembro 2024-2025: {len(df_dez)}")
        
        if len(df_dez) > 0:
            clientes_dez = df_dez['cliente'].unique()
            print(f"Clientes únicos em dezembro: {len(clientes_dez)}")
            print(f"Primeiros clientes: {clientes_dez[:10]}")
