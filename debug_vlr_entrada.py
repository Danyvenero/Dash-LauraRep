#!/usr/bin/env python3
"""
Script para debugar os valores de vlr_entrada na base de dados
"""

import sys
import os
import pandas as pd
import sqlite3

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import DatabaseManager

def debug_vlr_entrada():
    """Debug dos valores vlr_entrada"""
    print("🔍 DEBUGGING VLR_ENTRADA")
    print("=" * 50)
    
    try:
        # Conecta ao banco
        db = DatabaseManager()
        
        # Verifica tabelas disponíveis
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tabelas disponíveis: {[t[0] for t in tables]}")
        
        # Verifica estrutura da tabela vendas
        cursor.execute("PRAGMA table_info(vendas)")
        columns = cursor.fetchall()
        print(f"\n📊 Colunas da tabela vendas:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verifica se vlr_entrada existe e tem dados
        query = "SELECT vlr_entrada FROM vendas WHERE vlr_entrada IS NOT NULL LIMIT 10"
        cursor.execute(query)
        vlr_entrada_samples = cursor.fetchall()
        print(f"\n💰 Amostras de vlr_entrada (não nulos): {len(vlr_entrada_samples)}")
        for i, sample in enumerate(vlr_entrada_samples[:5]):
            print(f"  {i+1}: {sample[0]}")
        
        # Estatísticas gerais de vlr_entrada
        stats_query = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(vlr_entrada) as non_null_entrada,
            SUM(vlr_entrada) as sum_entrada,
            AVG(vlr_entrada) as avg_entrada,
            MIN(vlr_entrada) as min_entrada,
            MAX(vlr_entrada) as max_entrada
        FROM vendas
        """
        cursor.execute(stats_query)
        stats = cursor.fetchone()
        print(f"\n📈 Estatísticas vlr_entrada:")
        print(f"  Total linhas: {stats[0]}")
        print(f"  Valores não nulos: {stats[1]}")
        print(f"  Soma: R$ {stats[2]:,.2f}" if stats[2] else "  Soma: 0")
        print(f"  Média: R$ {stats[3]:,.2f}" if stats[3] else "  Média: 0")
        print(f"  Min: R$ {stats[4]:,.2f}" if stats[4] else "  Min: 0")
        print(f"  Max: R$ {stats[5]:,.2f}" if stats[5] else "  Max: 0")
        
        # Verifica dados por mês
        monthly_query = """
        SELECT 
            strftime('%Y-%m', data_faturamento) as mes,
            COUNT(*) as registros,
            SUM(vlr_entrada) as total_entrada,
            SUM(vlr_rol) as total_rol
        FROM vendas 
        WHERE data_faturamento IS NOT NULL
        GROUP BY strftime('%Y-%m', data_faturamento)
        ORDER BY mes
        LIMIT 12
        """
        cursor.execute(monthly_query)
        monthly_data = cursor.fetchall()
        print(f"\n📅 Dados mensais (últimos 12 meses):")
        print(f"{'Mês':<10} {'Registros':<10} {'vlr_entrada':<15} {'vlr_rol':<15}")
        print("-" * 60)
        for row in monthly_data:
            entrada = f"R$ {row[2]:,.0f}" if row[2] else "R$ 0"
            rol = f"R$ {row[3]:,.0f}" if row[3] else "R$ 0"
            print(f"{row[0]:<10} {row[1]:<10} {entrada:<15} {rol:<15}")
        
        # Verifica se há dados zerados
        zero_check_query = """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN vlr_entrada = 0 THEN 1 END) as zeros,
            COUNT(CASE WHEN vlr_entrada IS NULL THEN 1 END) as nulls,
            COUNT(CASE WHEN vlr_entrada > 0 THEN 1 END) as positivos
        FROM vendas
        """
        cursor.execute(zero_check_query)
        zero_stats = cursor.fetchone()
        print(f"\n🔢 Distribuição de valores vlr_entrada:")
        print(f"  Total: {zero_stats[0]}")
        print(f"  Zeros: {zero_stats[1]}")
        print(f"  Nulos: {zero_stats[2]}")
        print(f"  Positivos: {zero_stats[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro durante debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vlr_entrada()
