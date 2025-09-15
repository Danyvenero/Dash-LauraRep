#!/usr/bin/env python3
"""
Debug da análise de sazonalidade
"""

import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime

def debug_seasonality_data():
    """Debug específico para entender os dados de sazonalidade"""
    print("🔍 Debug da análise de sazonalidade...")
    
    # Conectar ao banco
    db_path = "instance/database.sqlite"
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Verificar estrutura da tabela vendas
        print("\n📋 Estrutura da tabela vendas:")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(vendas)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar dados básicos
        print("\n📊 Estatísticas básicas:")
        df_vendas = pd.read_sql_query("SELECT * FROM vendas LIMIT 10", conn)
        print(f"Total de registros (sample): {len(df_vendas)}")
        
        if not df_vendas.empty:
            print(f"Colunas disponíveis: {list(df_vendas.columns)}")
            
            # Verificar colunas de data
            date_columns = [col for col in df_vendas.columns if 'data' in col.lower()]
            print(f"Colunas de data encontradas: {date_columns}")
            
            # Verificar colunas de valor
            value_columns = [col for col in df_vendas.columns if any(x in col.lower() for x in ['vlr', 'valor', 'price', 'amount'])]
            print(f"Colunas de valor encontradas: {value_columns}")
            
            # Se temos dados, vamos analisar por mês
            if date_columns and value_columns:
                date_col = date_columns[0]
                value_col = value_columns[0]
                
                print(f"\n📅 Analisando usando {date_col} e {value_col}...")
                
                # Carregar todos os dados
                query = f"SELECT {date_col}, {value_col} FROM vendas WHERE {date_col} IS NOT NULL AND {value_col} IS NOT NULL"
                df_all = pd.read_sql_query(query, conn)
                
                print(f"Registros válidos: {len(df_all)}")
                
                if not df_all.empty:
                    # Converter data
                    df_all[date_col] = pd.to_datetime(df_all[date_col], errors='coerce')
                    df_all = df_all.dropna(subset=[date_col])
                    
                    print(f"Registros após conversão de data: {len(df_all)}")
                    
                    # Verificar range de datas
                    if not df_all.empty:
                        min_date = df_all[date_col].min()
                        max_date = df_all[date_col].max()
                        print(f"Range de datas: {min_date} até {max_date}")
                        
                        # Análise por mês
                        df_all['month'] = df_all[date_col].dt.month
                        df_all['month_name'] = df_all[date_col].dt.strftime('%b')
                        df_all['year'] = df_all[date_col].dt.year
                        
                        print(f"\n📈 Vendas por mês (total de todos os anos):")
                        monthly_sales = df_all.groupby(['month', 'month_name'])[value_col].agg(['sum', 'count', 'mean']).reset_index()
                        monthly_sales.columns = ['month_num', 'month_name', 'total_sales', 'count_transactions', 'avg_sales']
                        monthly_sales = monthly_sales.sort_values('month_num')
                        
                        for _, row in monthly_sales.iterrows():
                            print(f"  {row['month_name']}: R$ {row['total_sales']:,.2f} ({row['count_transactions']} transações, média: R$ {row['avg_sales']:,.2f})")
                        
                        # Verificar se há meses com zero
                        zero_months = monthly_sales[monthly_sales['total_sales'] == 0]
                        if not zero_months.empty:
                            print(f"\n⚠️ Meses com vendas zero:")
                            for _, row in zero_months.iterrows():
                                print(f"  {row['month_name']} (mês {row['month_num']})")
                        
                        # Encontrar mês de vale real
                        min_month = monthly_sales.loc[monthly_sales['total_sales'].idxmin()]
                        print(f"\n📉 Mês de vale real: {min_month['month_name']} com R$ {min_month['total_sales']:,.2f}")
                        
                        # Verificar anos disponíveis
                        years = df_all['year'].unique()
                        print(f"\nAnos disponíveis: {sorted(years)}")
                        
                        # Análise por ano e mês
                        print(f"\n📊 Vendas por ano e mês (primeiros 24 registros):")
                        yearly_monthly = df_all.groupby(['year', 'month', 'month_name'])[value_col].sum().reset_index()
                        yearly_monthly = yearly_monthly.sort_values(['year', 'month'])
                        
                        for _, row in yearly_monthly.head(24).iterrows():
                            print(f"  {row['year']}-{row['month_name']}: R$ {row[value_col]:,.2f}")
        
        print("\n✅ Debug concluído!")
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_seasonality_data()
