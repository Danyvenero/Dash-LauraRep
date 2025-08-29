from utils import db
import pandas as pd
from app import app

# Usar contexto da aplicação
with app.app_context():
    # Carregar dados
    df = db.get_clean_vendas_as_df()

    # Carregar dados
    df = db.get_clean_vendas_as_df()

    print("Colunas disponíveis:")
    print(df.columns.tolist())

    print("\nColunas relacionadas a hierarquia ou produto:")
    hier_cols = [col for col in df.columns if 'hier' in col.lower() or 'produto' in col.lower()]
    print("Colunas encontradas:", hier_cols)

    if hier_cols:
        print("\nPrimeiras linhas com colunas de hierarquia/produto:")
        print(df[hier_cols + ['cod_cliente', 'cliente']].head())
        
        print("\nValores únicos por coluna de hierarquia:")
        for col in hier_cols:
            print(f"\n{col}: {df[col].unique()[:10]}")  # Primeiros 10 valores únicos

    # Verificar filtros aplicados como no cenário da imagem
    print("\n=== TESTANDO FILTROS DO CENÁRIO ===")
    print("Filtros aplicados:")
    print("- Ano: 2023")
    print("- Mês: 1 (Janeiro)")  
    print("- Hierarquia: CONTROLS")
    print("- Top N: 5")

    # Aplicar filtros
    df_filtered = df.copy()

    # Filtro por ano (2023)
    if 'data_faturamento' in df.columns and pd.api.types.is_datetime64_any_dtype(df['data_faturamento']):
        df_filtered = df_filtered[df_filtered['data_faturamento'].dt.year == 2023]
        print(f"Após filtro de ano 2023: {len(df_filtered)} registros")

    # Filtro por mês (Janeiro = 1)
    if 'data_faturamento' in df.columns and pd.api.types.is_datetime64_any_dtype(df['data_faturamento']):
        df_filtered = df_filtered[df_filtered['data_faturamento'].dt.month == 1]
        print(f"Após filtro de mês Janeiro: {len(df_filtered)} registros")

    # Filtro por hierarquia CONTROLS
    hier_cols_found = [col for col in df.columns if col.lower().startswith('hier_produto')]
    if hier_cols_found:
        print(f"Colunas de hierarquia encontradas: {hier_cols_found}")
        mask = pd.Series(False, index=df_filtered.index)
        for col in hier_cols_found:
            mask |= df_filtered[col].str.contains('CONTROLS', case=False, na=False)
        df_filtered = df_filtered[mask]
        print(f"Após filtro de hierarquia CONTROLS: {len(df_filtered)} registros")
    else:
        print("ERRO: Nenhuma coluna de hierarquia encontrada!")

    print(f"\nRegistros finais após todos os filtros: {len(df_filtered)}")

    if len(df_filtered) > 0:
        print("\nClientes encontrados após filtros:")
        clientes_filtrados = df_filtered[['cod_cliente', 'cliente']].drop_duplicates()
        print(clientes_filtrados)
        
        print("\nValores totais por cliente:")
        resumo = df_filtered.groupby(['cod_cliente', 'cliente']).agg({
            'valor_liquido': 'sum',
            'qtd': 'sum'
        }).round(2)
        print(resumo)
