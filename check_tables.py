import sqlite3

conn = sqlite3.connect('instance/database.sqlite')
tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tabelas existentes:', tables)

for table in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} registros")

conn.close()