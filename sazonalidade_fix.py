    def analyze_seasonality_new(self, vendas_df: pd.DataFrame = None, filters: Dict = None) -> pd.DataFrame:
        """
        Análise estatística de sazonalidade das vendas com tratamento correto para vlr_entrada
        """
        # Usa DataFrame armazenado se não fornecido
        vendas_data = vendas_df if vendas_df is not None else self.vendas_df
        
        if vendas_data is None or vendas_data.empty:
            # Dados sintéticos com padrão sazonal mais realista
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            sales_base = 500000
            seasonal_pattern = [0.7, 0.8, 0.9, 1.0, 1.1, 0.9, 0.8, 0.85, 1.0, 1.2, 1.4, 1.3]
            entrada_factor = 0.85
            
            return pd.DataFrame({
                'month': months,
                'sales_amount': [sales_base * factor for factor in seasonal_pattern],
                'trend': [sales_base] * 12,
                'seasonal': [(factor - 1) * sales_base for factor in seasonal_pattern],
                'coefficient_variation': [0.25] * 12,
                'entrada_amount': [sales_base * factor * entrada_factor for factor in seasonal_pattern],
                'entrada_trend': [sales_base * entrada_factor] * 12,
                'entrada_seasonal': [(factor - 1) * sales_base * entrada_factor for factor in seasonal_pattern],
                'entrada_coefficient_variation': [0.22] * 12
            })
        
        print("📈 Analisando sazonalidade das vendas com dados reais...")
        
        try:
            # Detecta colunas de valor
            valor_cols = []
            for col in ['vlr_rol', 'vlr_entrada']:
                if col in vendas_data.columns:
                    valor_cols.append(col)
            
            if not valor_cols:
                print("⚠️ Nenhuma coluna de valor encontrada")
                return self.analyze_seasonality_new(None)
            
            print(f"🔍 Debug - Colunas encontradas: {valor_cols}")
            print(f"🔍 Debug - Total de registros: {len(vendas_data)}")
            
            # Processa cada métrica com estratégia adequada
            metrics_data = {}
            
            for valor_col in valor_cols:
                print(f"\n📊 Processando {valor_col}...")
                
                if valor_col == 'vlr_entrada':
                    # Para vlr_entrada: usar 'data' e filtrar registros com vlr_entrada > 0
                    metric_data = vendas_data[vendas_data[valor_col] > 0].copy()
                    date_col = 'data'
                    print(f"🔍 {valor_col}: {len(metric_data)} registros com valor > 0")
                else:
                    # Para vlr_rol: usar 'data_faturamento' e filtrar registros válidos
                    metric_data = vendas_data[
                        (vendas_data[valor_col] > 0) & 
                        (vendas_data['data_faturamento'].notna()) &
                        (vendas_data['data_faturamento'] != '')
                    ].copy()
                    date_col = 'data_faturamento'
                    print(f"🔍 {valor_col}: {len(metric_data)} registros com valor > 0 e data válida")
                
                if metric_data.empty:
                    print(f"⚠️ Nenhum dado válido para {valor_col}")
                    continue
                
                # Converte coluna de data
                metric_data[date_col] = pd.to_datetime(metric_data[date_col], errors='coerce')
                metric_data = metric_data.dropna(subset=[date_col])
                
                if metric_data.empty:
                    print(f"⚠️ Nenhum dado válido após conversão de data para {valor_col}")
                    continue
                
                print(f"🔍 {valor_col}: {len(metric_data)} registros finais")
                print(f"🔍 {valor_col}: período de {metric_data[date_col].min()} até {metric_data[date_col].max()}")
                
                # Agrupa por mês
                metric_data['month'] = metric_data[date_col].dt.month
                metric_data['month_name'] = metric_data[date_col].dt.strftime('%b')
                
                # Calcula totais mensais
                monthly_sales = metric_data.groupby(['month', 'month_name'])[valor_col].agg(['sum', 'count']).reset_index()
                monthly_sales.columns = ['month_num', 'month_name', 'total_sales', 'count_sales']
                
                # Converte nomes dos meses para português
                month_mapping = {
                    'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
                    'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
                    'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
                }
                monthly_sales['month_name_pt'] = monthly_sales['month_name'].map(month_mapping)
                
                # Garante todos os 12 meses
                all_months = pd.DataFrame({
                    'month_num': range(1, 13),
                    'month_name_pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                })
                
                # Merge com todos os meses
                monthly_final = all_months.merge(
                    monthly_sales[['month_num', 'month_name_pt', 'total_sales', 'count_sales']], 
                    on=['month_num', 'month_name_pt'], how='left'
                )
                monthly_final[['total_sales', 'count_sales']] = monthly_final[['total_sales', 'count_sales']].fillna(0)
                
                print(f"🔍 {valor_col} por mês:")
                for _, row in monthly_final.iterrows():
                    print(f"  {row['month_name_pt']}: R$ {row['total_sales']:,.2f}")
                
                # Calcula estatísticas
                mean_sales = monthly_final['total_sales'].mean()
                std_sales = monthly_final['total_sales'].std()
                coef_var = std_sales / mean_sales if mean_sales > 0 else 0
                
                # Componentes sazonais
                monthly_final['trend'] = mean_sales
                monthly_final['seasonal'] = monthly_final['total_sales'] - mean_sales
                monthly_final['coefficient_variation'] = coef_var
                
                # Armazena
                metrics_data[valor_col] = monthly_final
                
                # Mês de vale
                min_idx = monthly_final['total_sales'].idxmin()
                min_month = monthly_final.loc[min_idx, 'month_name_pt']
                min_value = monthly_final.loc[min_idx, 'total_sales']
                print(f"✅ {valor_col} mês de vale: {min_month} (R$ {min_value:,.2f})")
            
            # Combina resultados
            resultado = pd.DataFrame({
                'month': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            })
            
            # Adiciona vlr_rol
            if 'vlr_rol' in metrics_data:
                rol_data = metrics_data['vlr_rol']
                resultado['sales_amount'] = rol_data['total_sales'].values
                resultado['trend'] = rol_data['trend'].values
                resultado['seasonal'] = rol_data['seasonal'].values
                resultado['coefficient_variation'] = rol_data['coefficient_variation'].values
            else:
                resultado['sales_amount'] = 0
                resultado['trend'] = 0
                resultado['seasonal'] = 0
                resultado['coefficient_variation'] = 0
            
            # Adiciona vlr_entrada
            if 'vlr_entrada' in metrics_data:
                entrada_data = metrics_data['vlr_entrada']
                resultado['entrada_amount'] = entrada_data['total_sales'].values
                resultado['entrada_trend'] = entrada_data['trend'].values
                resultado['entrada_seasonal'] = entrada_data['seasonal'].values
                resultado['entrada_coefficient_variation'] = entrada_data['coefficient_variation'].values
                print("✅ Usando dados REAIS de vlr_entrada")
            else:
                # Fallback: dados sintéticos baseados em vlr_rol
                print("⚠️ Gerando dados sintéticos para vlr_entrada baseados em vlr_rol")
                entrada_factors = {
                    'Jan': 0.90, 'Fev': 0.85, 'Mar': 0.88, 'Abr': 0.82,
                    'Mai': 0.85, 'Jun': 0.87, 'Jul': 0.84, 'Ago': 0.89,
                    'Set': 0.91, 'Out': 0.93, 'Nov': 0.88, 'Dez': 0.80
                }
                
                entrada_amounts = []
                entrada_seasonals = []
                for _, row in resultado.iterrows():
                    factor = entrada_factors.get(row['month'], 0.85)
                    entrada_amounts.append(row['sales_amount'] * factor)
                    entrada_seasonals.append(row['seasonal'] * factor)
                
                resultado['entrada_amount'] = entrada_amounts
                resultado['entrada_trend'] = resultado['trend'] * 0.85
                resultado['entrada_seasonal'] = entrada_seasonals
                resultado['entrada_coefficient_variation'] = resultado['coefficient_variation'] * 0.9
            
            # Converte tipos
            for col in ['sales_amount', 'trend', 'seasonal', 'coefficient_variation',
                       'entrada_amount', 'entrada_trend', 'entrada_seasonal', 'entrada_coefficient_variation']:
                resultado[col] = resultado[col].astype(float)
            
            print(f"✅ Análise de sazonalidade concluída:")
            print(f"   📊 vlr_rol total: R$ {resultado['sales_amount'].sum():,.2f}")
            print(f"   📊 vlr_entrada total: R$ {resultado['entrada_amount'].sum():,.2f}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro na análise de sazonalidade: {e}")
            import traceback
            traceback.print_exc()
            return self.analyze_seasonality_new(None)  # Retorna dados sintéticos
