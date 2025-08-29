from app import app
from utils import db, kpis
import pandas as pd

# Simular filtros da imagem
ano_filtro = 2023  # Ano selecionado na imagem
mes_filtro = 1     # Mês de Janeiro selecionado na imagem  
hierarquias = ['CONTROLS']  # Hierarquia selecionada na imagem
top_n = 5          # Top 5 clientes selecionado na imagem

with app.app_context():
    print("=== TESTE DE FILTROS SIMULANDO CENÁRIO DA IMAGEM ===")
    
    # Carregar dados
    df_vendas = db.get_clean_vendas_as_df()
    df_cotacoes = db.get_clean_cotacoes_as_df()
    
    print(f"Registros iniciais: {len(df_vendas)}")
    print(f"Filtros aplicados: ano={ano_filtro}, mes={mes_filtro}, hierarquias={hierarquias}, top_n={top_n}")
    
    # Aplicar filtros na mesma ordem do callback
    
    # 1. Filtro de ano
    if ano_filtro:
        if 'data_faturamento' in df_vendas.columns and pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.year == ano_filtro]
            print(f"Após filtro de ano {ano_filtro}: {len(df_vendas)} registros")
        else:
            print("ERRO: Coluna data_faturamento não encontrada ou não é datetime")
    
    # 2. Filtro de mês  
    if mes_filtro:
        if 'data_faturamento' in df_vendas.columns and pd.api.types.is_datetime64_any_dtype(df_vendas['data_faturamento']):
            df_vendas = df_vendas[df_vendas['data_faturamento'].dt.month == mes_filtro]
            print(f"Após filtro de mês {mes_filtro}: {len(df_vendas)} registros")
    
    # 3. Filtro de hierarquia
    if hierarquias:
        print(f"Colunas disponíveis: {[col for col in df_vendas.columns if 'hier' in col.lower() or 'produto' in col.lower()]}")
        hier_cols = [col for col in df_vendas.columns if col.lower().startswith('hier_produto')]
        print(f"Colunas de hierarquia encontradas: {hier_cols}")
        
        if hier_cols:
            # Verificar valores únicos antes do filtro
            for col in hier_cols:
                valores_unicos = df_vendas[col].unique()
                print(f"Valores únicos em {col}: {valores_unicos[:10]}")
                
            mask = pd.Series(False, index=df_vendas.index)
            for col in hier_cols:
                for hierarquia in hierarquias:
                    mask_temp = df_vendas[col].str.contains(str(hierarquia), case=False, na=False)
                    print(f"Registros que contêm '{hierarquia}' em {col}: {mask_temp.sum()}")
                    mask |= mask_temp
            
            df_vendas = df_vendas[mask]
            print(f"Após filtro de hierarquia {hierarquias}: {len(df_vendas)} registros")
        else:
            print("ERRO: Nenhuma coluna de hierarquia encontrada!")
    
    # 4. Calcular KPIs
    print(f"\nCalculando KPIs com {len(df_vendas)} registros...")
    df_kpis = kpis.calculate_kpis_por_cliente(df_vendas, df_cotacoes)
    print(f"KPIs calculados para {len(df_kpis)} clientes")
    
    # 5. Aplicar Top N
    if top_n and len(df_kpis) > 0:
        try:
            top_n = int(top_n)
            if top_n > 0:
                df_kpis = df_kpis.head(top_n)
                print(f"Após filtro Top {top_n}: {len(df_kpis)} clientes")
        except (ValueError, TypeError):
            print(f"ERRO: Top N inválido: {top_n}")
    
    # 6. Mostrar resultados finais
    if not df_kpis.empty:
        print(f"\n=== RESULTADOS FINAIS ===")
        print("Clientes encontrados:")
        resultado = df_kpis[['cod_cliente', 'cliente', 'total_comprado_valor', 'total_comprado_qtd', 'mix_produtos', 'dias_sem_compra']].copy()
        resultado['total_comprado_valor'] = resultado['total_comprado_valor'].round(2)
        print(resultado)
        
        print(f"\nTotal geral valor: R$ {df_kpis['total_comprado_valor'].sum():,.2f}")
        print(f"Total geral quantidade: {df_kpis['total_comprado_qtd'].sum():,.0f}")
    else:
        print("\n=== NENHUM RESULTADO ENCONTRADO ===")
        print("Possíveis problemas:")
        print("1. Filtros muito restritivos")
        print("2. Dados não disponíveis para o período/hierarquia")
        print("3. Problema na lógica de filtros")
