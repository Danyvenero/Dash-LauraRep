import sqlite3

conn = sqlite3.connect('instance/database.sqlite')
cursor = conn.cursor()

# Verificar dados básicos
cursor.execute("SELECT COUNT(*) as total, SUM(vlr_entrada) as soma FROM vendas WHERE vlr_entrada > 0")
result = cursor.fetchone()
print(f"Registros com vlr_entrada > 0: {result[0]}")
print(f"Soma vlr_entrada: R$ {result[1]:,.2f}" if result[1] else "Soma vlr_entrada: 0")

# Verificar colunas de data
cursor.execute("SELECT COUNT(*) as data_count FROM vendas WHERE data IS NOT NULL")
data_count = cursor.fetchone()[0]
print(f"Registros com coluna 'data' preenchida: {data_count}")

cursor.execute("SELECT COUNT(*) as data_fat_count FROM vendas WHERE data_faturamento IS NOT NULL")
data_fat_count = cursor.fetchone()[0]
print(f"Registros com coluna 'data_faturamento' preenchida: {data_fat_count}")

conn.close()
print("Teste concluído!")
