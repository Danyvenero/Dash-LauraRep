#!/usr/bin/env python3
"""Script para recriar o banco e verificar estrutura"""

import sqlite3
import os

def recreate_database():
    """Recria o banco de dados e verifica a estrutura"""
    
    try:
        # Remove o banco antigo
        if os.path.exists('instance/database.sqlite'):
            os.remove('instance/database.sqlite')
            print('✅ Banco antigo removido')
        
        # Cria diretório instance se não existir
        os.makedirs('instance', exist_ok=True)
        
        # Lê e executa o schema
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
        
        conn = sqlite3.connect('instance/database.sqlite')
        conn.executescript(schema)
        conn.close()
        
        print('✅ Banco recriado com sucesso')
        
        # Verifica a estrutura da tabela cotacoes
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        print('\n=== ESTRUTURA DA TABELA COTACOES ===')
        cursor.execute('PRAGMA table_info(cotacoes)')
        columns = cursor.fetchall()
        
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        print(f'\nTotal de colunas: {len(columns)}')
        
        # Verifica se numero_revisao existe
        column_names = [col[1] for col in columns]
        if 'numero_revisao' in column_names:
            print('✅ Coluna numero_revisao está presente')
        else:
            print('❌ Coluna numero_revisao está AUSENTE!')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_database()
