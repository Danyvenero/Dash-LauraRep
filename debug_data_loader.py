import pandas as pd
import io
import base64

def debug_normalize_vendas_data(df: pd.DataFrame) -> pd.DataFrame:
    """Versão debug da função normalize_vendas_data"""
    print(f"🔍 DEBUG: Iniciando normalize_vendas_data")
    print(f"🔍 DEBUG: Colunas originais: {list(df.columns)}")
    print(f"🔍 DEBUG: Shape original: {df.shape}")
    
    try:
        df_norm = df.copy()
        print(f"🔍 DEBUG: Cópia criada com sucesso")
        
        # Teste simples: só tentar renomear uma coluna
        if 'ID_Cli' in df_norm.columns:
            print(f"🔍 DEBUG: Tentando renomear ID_Cli")
            df_norm = df_norm.rename(columns={'ID_Cli': 'cod_cliente'})
            print(f"🔍 DEBUG: Renomeação ID_Cli -> cod_cliente OK")
        
        # Teste: verificar se cod_cliente existe
        if 'cod_cliente' in df_norm.columns:
            print(f"🔍 DEBUG: cod_cliente encontrado, tentando normalizar")
            original_type = type(df_norm['cod_cliente'].iloc[0])
            print(f"🔍 DEBUG: Tipo original da primeira linha: {original_type}")
            
            # Tenta normalização simples
            df_norm['cod_cliente'] = df_norm['cod_cliente'].astype(str)
            print(f"🔍 DEBUG: Conversão para string OK")
            
            df_norm['cod_cliente'] = df_norm['cod_cliente'].str.strip()
            print(f"🔍 DEBUG: Strip OK")
        
        # Teste: filtrar dados faltando
        if 'cod_cliente' in df_norm.columns:
            print(f"🔍 DEBUG: Testando filtro de dados faltando")
            initial_shape = df_norm.shape
            print(f"🔍 DEBUG: Shape antes do filtro: {initial_shape}")
            
            # Testa notna()
            mask = df_norm['cod_cliente'].notna()
            print(f"🔍 DEBUG: Mask criada: {type(mask)}")
            print(f"🔍 DEBUG: Mask shape: {mask.shape}")
            print(f"🔍 DEBUG: Mask valores únicos: {mask.value_counts()}")
            
            # Aplica o filtro
            df_norm = df_norm[mask]
            final_shape = df_norm.shape
            print(f"🔍 DEBUG: Shape após filtro: {final_shape}")
        
        print(f"🔍 DEBUG: Função concluída com sucesso")
        return df_norm
        
    except Exception as e:
        print(f"❌ DEBUG: Erro capturado: {str(e)}")
        print(f"❌ DEBUG: Tipo do erro: {type(e)}")
        import traceback
        print(f"❌ DEBUG: Traceback:")
        traceback.print_exc()
        raise e

def test_with_sample_data():
    """Testa com dados de exemplo"""
    print("🧪 Testando com dados de exemplo...")
    
    # Cria dados de exemplo similares aos arquivos Excel
    sample_data = {
        'Unidade de Negócio': ['WEG Automação', 'WEG Automação'],
        'Canal Distribuição': ['Revendedor', 'Consumidor Final'],
        'ID_Cli': [123456, 789012],
        'Cliente': ['EMPRESA A', 'EMPRESA B'],
        'Hier. Produto 1': ['DRIVES', 'CONTROLS'],
        'Material': [100001, 100002],
        'Produto': ['PRODUTO A', 'PRODUTO B'],
        'Qtd. ROL': [10, 5],
        'Vlr. ROL': [1000.50, 500.25]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"📊 Dados de exemplo criados: {df.shape}")
    print(f"📊 Colunas: {list(df.columns)}")
    
    try:
        result = debug_normalize_vendas_data(df)
        print(f"✅ Teste com dados de exemplo bem-sucedido!")
        print(f"✅ Shape resultado: {result.shape}")
        print(f"✅ Colunas resultado: {list(result.columns)}")
        return True
    except Exception as e:
        print(f"❌ Teste com dados de exemplo falhou: {str(e)}")
        return False

if __name__ == "__main__":
    test_with_sample_data()
