"""
Módulo de segurança e autenticação
"""

from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, request, redirect, url_for
import re
from pathlib import Path
from typing import Optional, Dict, List

class SecurityManager:
    """Classe para gerenciamento de segurança"""
    
    def __init__(self):
        self.allowed_extensions = {'xlsx', 'xls'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.password_min_length = 6
    
    def hash_password(self, password: str) -> str:
        """Gera hash da senha"""
        return generate_password_hash(password)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica senha contra hash"""
        return check_password_hash(password_hash, password)
    
    def validate_password_strength(self, password: str) -> Dict[str, bool]:
        """Valida força da senha"""
        validations = {
            'length': len(password) >= self.password_min_length,
            'has_letter': bool(re.search(r'[a-zA-Z]', password)),
            'has_number': bool(re.search(r'\d', password)),
            'has_special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        }
        
        validations['is_strong'] = all([
            validations['length'],
            validations['has_letter'],
            validations['has_number']
        ])
        
        return validations
    
    def validate_file_upload(self, filename: str, file_size: int) -> Dict[str, any]:
        """Valida upload de arquivo"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Verifica se arquivo foi fornecido
        if not filename:
            result['valid'] = False
            result['errors'].append("Nenhum arquivo foi selecionado")
            return result
        
        # Verifica extensão
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            result['valid'] = False
            result['errors'].append(f"Extensão '{file_ext}' não permitida. Use: {', '.join(self.allowed_extensions)}")
        
        # Verifica tamanho
        if file_size > self.max_file_size:
            result['valid'] = False
            result['errors'].append(f"Arquivo muito grande ({file_size / 1024 / 1024:.1f}MB). Máximo: {self.max_file_size / 1024 / 1024:.0f}MB")
        
        # Verifica caracteres especiais no nome
        if re.search(r'[<>:"/\\|?*]', filename):
            result['warnings'].append("Nome do arquivo contém caracteres especiais que podem causar problemas")
        
        return result
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitiza nome do arquivo"""
        # Remove caracteres perigosos
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove espaços múltiplos
        filename = re.sub(r'\s+', ' ', filename)
        
        # Remove espaços do início e fim
        filename = filename.strip()
        
        return filename
    
    def validate_user_input(self, input_data: Dict) -> Dict[str, any]:
        """Valida entrada de dados do usuário"""
        result = {
            'valid': True,
            'errors': [],
            'sanitized_data': {}
        }
        
        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove caracteres perigosos
                sanitized_value = self._sanitize_string(value)
                result['sanitized_data'][key] = sanitized_value
                
                # Verifica se houve modificação
                if sanitized_value != value:
                    result['warnings'] = result.get('warnings', [])
                    result['warnings'].append(f"Campo '{key}' foi sanitizado")
            else:
                result['sanitized_data'][key] = value
        
        return result
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitiza string removendo caracteres perigosos"""
        if not isinstance(text, str):
            return text
        
        # Remove tags HTML/XML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

def require_auth(f):
    """Decorator para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def is_authenticated() -> bool:
    """Verifica se usuário está autenticado"""
    return 'user_id' in session

def get_current_user_id() -> Optional[int]:
    """Retorna ID do usuário atual"""
    return session.get('user_id')

def get_current_username() -> Optional[str]:
    """Retorna username do usuário atual"""
    return session.get('username')

def login_user(user_data: Dict):
    """Faz login do usuário"""
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session.permanent = True

def logout_user():
    """Faz logout do usuário"""
    session.clear()

def validate_csrf_token(token: str) -> bool:
    """Valida token CSRF (implementação básica)"""
    stored_token = session.get('csrf_token')
    return stored_token and stored_token == token

def generate_csrf_token() -> str:
    """Gera token CSRF"""
    import secrets
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

class RateLimiter:
    """Classe para controle de rate limiting"""
    
    def __init__(self):
        self.attempts = {}
        self.max_attempts = 5
        self.lockout_time = 300  # 5 minutos
    
    def is_rate_limited(self, identifier: str) -> bool:
        """Verifica se identificador está limitado"""
        import time
        
        if identifier not in self.attempts:
            return False
        
        attempt_data = self.attempts[identifier]
        
        # Verifica se ainda está no período de lockout
        if time.time() - attempt_data['last_attempt'] < self.lockout_time:
            return attempt_data['count'] >= self.max_attempts
        
        # Reset se passou do tempo de lockout
        del self.attempts[identifier]
        return False
    
    def record_attempt(self, identifier: str):
        """Registra tentativa"""
        import time
        
        current_time = time.time()
        
        if identifier in self.attempts:
            attempt_data = self.attempts[identifier]
            
            # Reset se passou muito tempo
            if current_time - attempt_data['last_attempt'] > self.lockout_time:
                self.attempts[identifier] = {'count': 1, 'last_attempt': current_time}
            else:
                self.attempts[identifier]['count'] += 1
                self.attempts[identifier]['last_attempt'] = current_time
        else:
            self.attempts[identifier] = {'count': 1, 'last_attempt': current_time}
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """Retorna tentativas restantes"""
        if identifier not in self.attempts:
            return self.max_attempts
        
        return max(0, self.max_attempts - self.attempts[identifier]['count'])

# Instância global do rate limiter
rate_limiter = RateLimiter()

def check_file_security(file_path: str) -> Dict[str, any]:
    """Verifica segurança de arquivo"""
    result = {
        'safe': True,
        'issues': []
    }
    
    try:
        file_size = Path(file_path).stat().st_size
        
        # Verifica tamanho
        if file_size > 100 * 1024 * 1024:  # 100MB
            result['safe'] = False
            result['issues'].append("Arquivo muito grande")
        
        # Verifica se é realmente Excel
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
        # Assinaturas de arquivos Excel
        excel_signatures = [
            b'\x50\x4b\x03\x04',  # XLSX (ZIP)
            b'\xd0\xcf\x11\xe0',  # XLS (OLE)
        ]
        
        if not any(header.startswith(sig) for sig in excel_signatures):
            result['safe'] = False
            result['issues'].append("Arquivo não parece ser um Excel válido")
    
    except Exception as e:
        result['safe'] = False
        result['issues'].append(f"Erro ao verificar arquivo: {str(e)}")
    
    return result
