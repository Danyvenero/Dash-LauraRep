# utils/security.py

from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Gera um hash seguro para a senha fornecida."""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return check_password_hash(password_hash, password)