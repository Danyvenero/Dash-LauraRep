#!/usr/bin/env python3
import pandas as pd
print("Pandas carregado")

# Teste simples de None handling
data = {'col1': [None, 'test', ''], 'col2': [1, 2, 3]}
df = pd.DataFrame(data)
print("DataFrame criado:")
print(df)

# Testa replace
df['col1'] = df['col1'].replace(['', 'None', 'none'], pd.NA)
print("Após replace:")
print(df)

df['col1'] = df['col1'].astype(str).str.strip()
print("Após astype str:")
print(df)

df['col1'] = df['col1'].replace(['nan', 'NaN'], None)
print("Após replace nan:")
print(df)

print("Teste concluído")
