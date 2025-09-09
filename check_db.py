#!/usr/bin/env python3

import sqlite3
from pathlib import Path

DB_PATH = Path('instance/database.sqlite')
print(f"Database path: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('PRAGMA table_info(cotacoes)')
    columns = cursor.fetchall()
    
    print('\n✅ Columns in cotacoes table:')
    for row in columns:
        print(f'  {row[1]} - {row[2]}')
    
    if not columns:
        print('❌ No columns found - table may not exist')
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
