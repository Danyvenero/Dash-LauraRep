#!/usr/bin/env python3
"""
Simple script to initialize database and check structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import init_db, get_connection

print("🔧 Initializing database...")
init_db()

print("\n🔍 Checking cotacoes table structure...")
conn = get_connection()
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(cotacoes)')
columns = cursor.fetchall()

print("📋 Columns found:")
for row in columns:
    print(f"  - {row[1]} ({row[2]})")

# Check specifically for numero_revisao
has_numero_revisao = any(col[1] == 'numero_revisao' for col in columns)
print(f"\n✅ numero_revisao column exists: {has_numero_revisao}")

conn.close()
