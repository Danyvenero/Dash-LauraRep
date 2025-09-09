#!/usr/bin/env python3
"""
Script para testar o sistema de login
"""

from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('instance/database.sqlite')
cursor = conn.cursor()

# Buscar o usuário admin
cursor.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
row = cursor.fetchone()

if row:
    username, stored_hash = row
    print(f"✅ Usuário encontrado: {username}")
    print(f"🔑 Hash armazenado: {stored_hash[:50]}...")
    
    # Testar a senha
    test_password = 'admin123'
    is_valid = check_password_hash(stored_hash, test_password)
    
    print(f"🧪 Testando senha '{test_password}': {is_valid}")
    
    if not is_valid:
        print("❌ Senha não confere!")
        print("🔧 Gerando novo hash para comparação...")
        new_hash = generate_password_hash(test_password)
        print(f"🆕 Novo hash: {new_hash[:50]}...")
        
        # Atualizar o hash no banco
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (new_hash,))
        conn.commit()
        print("✅ Hash atualizado no banco!")
        
        # Testar novamente
        is_valid_now = check_password_hash(new_hash, test_password)
        print(f"🧪 Teste com novo hash: {is_valid_now}")
    else:
        print("✅ Senha está correta!")
        
else:
    print("❌ Usuário admin não encontrado!")

conn.close()
