"""
Sistema de Cache para otimização de performance
"""

import pandas as pd
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from functools import wraps
import threading

class CacheManager:
    """Gerenciador de cache thread-safe para DataFrames e resultados"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Gera chave única para cache baseada nos argumentos"""
        key_parts = [func_name]
        
        # Adiciona argumentos posicionais
        for arg in args:
            if isinstance(arg, (list, tuple)):
                key_parts.append(str(sorted(arg) if arg else "empty"))
            else:
                key_parts.append(str(arg))
        
        # Adiciona argumentos nomeados
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (list, tuple)):
                key_parts.append(f"{k}={sorted(v) if v else 'empty'}")
            else:
                key_parts.append(f"{k}={v}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera item do cache se ainda válido"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self.ttl_seconds:
                    entry['hits'] += 1
                    return entry['data']
                else:
                    # Remove entrada expirada
                    del self._cache[key]
            return None
    
    def set(self, key: str, data: Any) -> None:
        """Armazena item no cache"""
        with self._lock:
            # Remove entradas antigas se cache estiver cheio
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'hits': 0
            }
    
    def _evict_oldest(self) -> None:
        """Remove a entrada mais antiga do cache"""
        if not self._cache:
            return
        
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k]['timestamp'])
        del self._cache[oldest_key]
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_hits = sum(entry['hits'] for entry in self._cache.values())
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_hits': total_hits,
                'hit_rate': total_hits / max(1, len(self._cache))
            }

# Instância global do cache
cache_manager = CacheManager(max_size=50, ttl_seconds=180)  # 3 minutos TTL

def cached_dataframe(ttl_seconds: int = 180):
    """Decorator para cache de funções que retornam DataFrames"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave do cache
            cache_key = cache_manager._generate_key(func.__name__, *args, **kwargs)
            
            # Tenta recuperar do cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                print(f"🚀 Cache HIT para {func.__name__}")
                return cached_result
            
            # Executa função e cacheia resultado
            print(f"💾 Cache MISS para {func.__name__} - executando...")
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(f"⏱️ {func.__name__} executado em {execution_time:.2f}s")
            
            # Cacheia apenas se resultado não for vazio
            if result is not None and not (isinstance(result, pd.DataFrame) and result.empty):
                cache_manager.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

def cached_result(ttl_seconds: int = 180):
    """Decorator para cache de resultados simples (não DataFrames)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_manager._generate_key(func.__name__, *args, **kwargs)
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            return result
        return wrapper
    return decorator

# Função para pré-carregar dados mais utilizados
def preload_common_data():
    """Pré-carrega dados comumente utilizados"""
    from . import load_vendas_data, load_cotacoes_data
    
    print("🔄 Pré-carregando dados no cache...")
    try:
        # Carrega dados de vendas (mais utilizados)
        load_vendas_data()
        print("✅ Dados de vendas pré-carregados")
        
        # Carrega dados de cotações
        load_cotacoes_data()
        print("✅ Dados de cotações pré-carregados")
        
    except Exception as e:
        print(f"⚠️ Erro no pré-carregamento: {e}")
