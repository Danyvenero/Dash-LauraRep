#!/usr/bin/env python3
"""Script para limpar datasets problemáticos da tabela produtos_cotados"""

import sqlite3

def clean_problematic_datasets():
    """Remove datasets com valores None/NULL problemáticos"""
    
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        # Remove datasets 5 e 9 que têm problemas
        print("Removendo datasets problemáticos...")
        
        # Dataset 5: totalmente NULL
        cursor.execute("DELETE FROM produtos_cotados WHERE dataset_id = 5")
        deleted_5 = cursor.rowcount
        print(f"Dataset 5: {deleted_5} registros removidos (totalmente NULL)")
        
        # Dataset 9: cod_cliente = 'None'
        cursor.execute("DELETE FROM produtos_cotados WHERE dataset_id = 9")
        deleted_9 = cursor.rowcount
        print(f"Dataset 9: {deleted_9} registros removidos (cod_cliente='None')")
        
        # Remove também os registros dos datasets
        cursor.execute("DELETE FROM datasets WHERE id IN (5, 9)")
        
        # Confirma as mudanças
        conn.commit()
        
        # Verifica o estado final
        cursor.execute("SELECT COUNT(*) FROM produtos_cotados")
        remaining = cursor.fetchone()[0]
        print(f"Registros restantes na tabela: {remaining}")
        
        # Mostra datasets restantes
        cursor.execute("""
            SELECT d.id, d.name, COUNT(p.id) as produtos_count
            FROM datasets d
            LEFT JOIN produtos_cotados p ON d.id = p.dataset_id
            GROUP BY d.id, d.name
            ORDER BY d.id DESC
        """)
        
        datasets = cursor.fetchall()
        print("\nDatasets restantes:")
        for dataset_id, name, count in datasets:
            print(f"  Dataset {dataset_id}: '{name}' - {count} produtos")
        
        conn.close()
        print("\n✅ Limpeza concluída!")
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")

if __name__ == "__main__":
    clean_problematic_datasets()
