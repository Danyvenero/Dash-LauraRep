import sqlite3

conn = sqlite3.connect('instance/database.sqlite')
cursor = conn.cursor()

print('Estrutura da tabela datasets:')
cursor.execute('PRAGMA table_info(datasets)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[1]} ({col[2]})')

print('\nConteudo da tabela datasets:')
cursor.execute('SELECT * FROM datasets')
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
