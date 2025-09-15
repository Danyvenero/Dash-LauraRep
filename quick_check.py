import sqlite3

# Conecta ao banco
conn = sqlite3.connect('instance/database.sqlite')
cursor = conn.cursor()

# Verifica dados de vlr_entrada
cursor.execute("SELECT COUNT(*), SUM(vlr_entrada), AVG(vlr_entrada), MIN(vlr_entrada), MAX(vlr_entrada) FROM vendas WHERE vlr_entrada IS NOT NULL")
stats = cursor.fetchone()
print(f"Estatísticas vlr_entrada:")
print(f"  Count: {stats[0]}")
print(f"  Sum: {stats[1]}")
print(f"  Avg: {stats[2]}")
print(f"  Min: {stats[3]}")
print(f"  Max: {stats[4]}")

# Verifica alguns registros específicos
cursor.execute("SELECT vlr_entrada, vlr_rol FROM vendas WHERE vlr_entrada > 0 LIMIT 5")
samples = cursor.fetchall()
print(f"\nAmostras com vlr_entrada > 0:")
for i, (entrada, rol) in enumerate(samples):
    print(f"  {i+1}: entrada={entrada}, rol={rol}")

# Verifica registros zero vs não-zero
cursor.execute("SELECT COUNT(*) FROM vendas WHERE vlr_entrada = 0")
zeros = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM vendas WHERE vlr_entrada > 0")
positivos = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM vendas WHERE vlr_entrada IS NULL")
nulls = cursor.fetchone()[0]

print(f"\nDistribuição vlr_entrada:")
print(f"  Zeros: {zeros}")
print(f"  Positivos: {positivos}")
print(f"  Nulls: {nulls}")

conn.close()
