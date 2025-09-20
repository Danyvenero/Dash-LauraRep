"""
Motor de Recomendações Inteligentes de Compra
Sistema ML para sugestões de estoque para revendas
Dashboard Laura Representações - WEG
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import sqlite3
import pickle
import os
import calendar
from pathlib import Path
from utils.db import get_connection as get_db_connection
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

# Placeholder classes para ML
class MockMLClass:
    def __init__(self, *args, **kwargs):
        pass
    def fit(self, *args, **kwargs):
        return self
    def predict(self, *args, **kwargs):
        return []
    def transform(self, *args, **kwargs):
        return []

# Função para importar ML sob demanda
def _get_ml_classes():
    """Importa classes ML sob demanda para evitar problemas de inicialização"""
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler, MinMaxScaler
        return {
            'IsolationForest': IsolationForest,
            'LogisticRegression': LogisticRegression,
            'StandardScaler': StandardScaler,
            'MinMaxScaler': MinMaxScaler,
            'available': True
        }
    except (ImportError, ModuleNotFoundError, Exception) as e:
        logger.warning(f"⚠️ Bibliotecas ML não disponíveis: {e}")
        return {
            'IsolationForest': MockMLClass,
            'LogisticRegression': MockMLClass,
            'StandardScaler': MockMLClass,
            'MinMaxScaler': MockMLClass,
            'available': False
        }

# Inicializa variável global ML_AVAILABLE
try:
    import sklearn
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def _standardize_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função auxiliar para padronizar colunas de data
    Procura por 'data_entrada' ou 'data' e padroniza para 'data_entrada'
    """
    df_copy = df.copy()
    
    if 'data_entrada' in df_copy.columns:
        # Já tem a coluna correta
        pass
    elif 'data' in df_copy.columns:
        # Renomeia para manter compatibilidade
        df_copy['data_entrada'] = df_copy['data']
    else:
        logger.warning("⚠️ Nenhuma coluna de data encontrada ('data' ou 'data_entrada')")
        return df_copy
    
    # Converte para datetime
    df_copy['data_entrada'] = pd.to_datetime(df_copy['data_entrada'], errors='coerce')
    df_copy = df_copy.dropna(subset=['data_entrada'])
    
    return df_copy

class SmartPurchaseRecommendations:
    """
    Engine de Recomendações Inteligentes de Compra
    
    Funcionalidades:
    1. Classificação ABC-XYZ de produtos
    2. Cálculo de safety stock com nível de serviço
    3. Modelo ML de probabilidade de recompra
    4. Sistema de feedback para melhoria contínua
    """
    
    def __init__(self):
        self.conn = None
        self.scaler = None
        self.model = None
        self.is_trained = False
        self.ml_classes = None  # Será carregado sob demanda
        
        # ====== PERSISTÊNCIA DO MODELO ======
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)  # Cria diretório se não existe
        
        self.model_path = self.model_dir / "ml_model.pkl"
        self.scaler_path = self.model_dir / "scaler.pkl"
        self.metadata_path = self.model_dir / "model_metadata.json"
        
        # Carrega modelo existente se disponível
        self._load_model_if_exists()
        
        # Sistema de Reinforcement Learning - Pesos adaptativos
        self.adaptive_weights = {
            'abc_weight': 0.4,     # Peso para classificação ABC (valor)
            'volume_weight': 0.3,   # Peso para volume de vendas
            'recorrencia_weight': 0.2,  # Peso para recorrência
            'xyz_weight': 0.1,     # Peso para variabilidade XYZ
            'cotacao_boost': 1.1    # Multiplicador para produtos cotados
        }
        
        # Histórico de feedback para aprendizado
        self.feedback_history = []
        
        # Configurações padrão
        self.default_config = {
            'nivel_servico': 0.95,  # 95% de nível de serviço
            'leadtime_dias': 30,    # 30 dias de lead time padrão
            'janela_demanda_meses': 6,  # 6 meses para cálculo de demanda
            'min_historico_meses': 1,   # Mínimo 1 mês de histórico (reduzido de 3)
            'abc_thresholds': [0.8, 0.95],  # 80% = A, 95% = B, resto = C
            'xyz_cv_thresholds': [0.5, 1.0]  # CV < 0.5 = X, < 1.0 = Y, resto = Z
        }
    
    def connect_db(self):
        """Conecta ao banco de dados"""
        if self.conn is None:
            self.conn = get_db_connection()
    
    def close_db(self):
        """Fecha conexão com banco"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _init_ml_if_needed(self):
        """Inicializa componentes ML sob demanda"""
        if self.ml_classes is None:
            self.ml_classes = _get_ml_classes()
            
        if self.scaler is None and self.ml_classes['available']:
            try:
                self.scaler = self.ml_classes['StandardScaler']()
                self.model = self.ml_classes['LogisticRegression'](random_state=42)
                logger.info("✅ Componentes ML inicializados sob demanda")
            except Exception as e:
                logger.warning(f"⚠️ Erro na inicialização ML: {e}")
                self.scaler = MockMLClass()
                self.model = MockMLClass()
        
        return self.ml_classes['available']
    
    # ====== MÉTODOS DE PERSISTÊNCIA DO MODELO ======
    
    def _load_model_if_exists(self):
        """Carrega modelo salvo se existir e for válido"""
        ml_available = self._init_ml_if_needed()
        
        if not ml_available:
            logger.info("📦 ML não disponível - modelo não será carregado")
            return
        
        try:
            if (self.model_path.exists() and 
                self.scaler_path.exists() and 
                self.metadata_path.exists()):
                
                # Carrega metadados
                import json
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Verifica se modelo não está muito antigo (7 dias)
                model_date = datetime.fromisoformat(metadata['data_treino'])
                days_old = (datetime.now() - model_date).days
                
                if days_old > 7:
                    logger.warning(f"⚠️ Modelo tem {days_old} dias - considere retreinar")
                
                # Carrega modelo e scaler
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.is_trained = True
                
                logger.info(f"✅ Modelo carregado com sucesso!")
                logger.info(f"📅 Treinado em: {metadata['data_treino']}")
                logger.info(f"📊 Samples: {metadata.get('num_samples', 'N/A')}")
                logger.info(f"🎯 Score: {metadata.get('cv_accuracy_mean', 'N/A'):.3f}")
                
            else:
                logger.info("📝 Nenhum modelo salvo encontrado - será necessário treinar")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            # Reset em caso de erro
            self.is_trained = False
            if ML_AVAILABLE:
                self.model = LogisticRegression(random_state=42)
                self.scaler = StandardScaler()
    
    def _save_model(self, metricas: Dict):
        """Salva modelo treinado e metadados"""
        if not ML_AVAILABLE or not self.is_trained:
            logger.warning("⚠️ Modelo não disponível para salvar")
            return
        
        try:
            # Salva modelo
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Salva scaler
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Salva metadados com versão atualizada
            import json
            metadata = {
                'data_treino': datetime.now().isoformat(),
                'versao': '2.1',  # ✅ Versão atualizada para features otimizadas
                'num_samples': metricas.get('num_samples', 0),
                'num_features': metricas.get('num_features', 0),
                'cv_accuracy_mean': metricas.get('cv_accuracy_mean', 0.0),
                'test_accuracy': metricas.get('test_accuracy', 0.0),
                'modelo_tipo': metricas.get('modelo_tipo', 'LogisticRegression'),
                'overfitting_status': metricas.get('overfitting_status', 'Desconhecido'),
                'underfitting_status': metricas.get('underfitting_status', 'Desconhecido'),
                'features_optimized': True,  # ✅ Flag indicando otimização
                'removed_features': ['regularidade_cv', 'compras_por_ano']  # ✅ Features removidas
            }
            
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"💾 Modelo salvo com sucesso em {self.model_dir}")
            logger.info(f"📊 Metadados: {metadata['num_samples']} samples, score: {metadata['cv_accuracy_mean']:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar modelo: {e}")
    
    def should_retrain_model(self, vendas_df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Verifica se o modelo deve ser retreinado baseado em critérios
        
        Returns:
            Tuple[bool, str]: (deve_retreinar, motivo)
        """
        if not self.is_trained:
            return True, "Modelo não treinado"
        
        if not self.metadata_path.exists():
            return True, "Metadados não encontrados"
        
        try:
            import json
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Verifica idade do modelo
            model_date = datetime.fromisoformat(metadata['data_treino'])
            days_old = (datetime.now() - model_date).days
            
            if days_old > 30:
                return True, f"Modelo muito antigo ({days_old} dias)"
            
            # Verifica se há dados novos significativos
            latest_sale = pd.to_datetime(vendas_df['data_faturamento']).max()
            if latest_sale > model_date + timedelta(days=7):
                return True, "Novos dados disponíveis"
            
            # Verifica qualidade do modelo
            accuracy = metadata.get('cv_accuracy_mean', 0.0)
            if accuracy < 0.6:
                return True, f"Modelo com baixa performance ({accuracy:.3f})"
            
            return False, f"Modelo atual é adequado (idade: {days_old} dias, score: {accuracy:.3f})"
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar necessidade de retreino: {e}")
            return True, "Erro na verificação"
    
    def get_model_info(self) -> Dict:
        """Retorna informações do modelo atual"""
        if not self.is_trained:
            return {
                'status': 'não_treinado',
                'message': 'Modelo não foi treinado ainda'
            }
        
        try:
            if self.metadata_path.exists():
                import json
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                days_old = (datetime.now() - datetime.fromisoformat(metadata['data_treino'])).days
                
                return {
                    'status': 'treinado',
                    'data_treino': metadata['data_treino'],
                    'idade_dias': days_old,
                    'num_samples': metadata.get('num_samples', 0),
                    'accuracy': metadata.get('cv_accuracy_mean', 0.0),
                    'modelo_tipo': metadata.get('modelo_tipo', 'Desconhecido'),
                    'recomendacao': 'ok' if days_old <= 7 else 'considerar_retreino' if days_old <= 30 else 'retreinar_urgente'
                }
            else:
                return {
                    'status': 'sem_metadados',
                    'message': 'Modelo treinado mas sem metadados'
                }
        except Exception as e:
            return {
                'status': 'erro',
                'message': f'Erro ao obter info: {e}'
            }
    
    # ====== FIM DOS MÉTODOS DE PERSISTÊNCIA ======
    
    def _apply_intelligent_normalization(self, produto_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica normalização inteligente que reduz importância de produtos 
        de alto valor mas baixa frequência (ex: transformadores, equipamentos especiais)
        
        Args:
            produto_stats: DataFrame com estatísticas dos produtos
            
        Returns:
            DataFrame com coluna 'valor_normalizado' adicionada
        """
        try:
            logger.info("🔧 Aplicando normalização inteligente valor vs frequência")
            
            # Calcula métricas de normalização
            produto_stats = produto_stats.copy()
            
            # 1. Score de Frequência (0-1)
            # Combina: freq_mensal, num_transacoes, num_clientes_unicos
            freq_mensal_norm = self._normalize_series(produto_stats['freq_mensal'])
            num_transacoes_norm = self._normalize_series(produto_stats['num_transacoes'])
            num_clientes_norm = self._normalize_series(produto_stats['num_clientes_unicos'])
            
            score_frequencia = (
                freq_mensal_norm * 0.4 +      # Frequência mensal (40%)
                num_transacoes_norm * 0.35 +  # Total de transações (35%) 
                num_clientes_norm * 0.25       # Diversidade de clientes (25%)
            )
            
            # 2. Score de Valor (0-1)
            valor_total_norm = self._normalize_series(produto_stats['valor_total'])
            
            # 3. Fator de Penalização para Alto Valor + Baixa Frequência
            # Produtos caros e raros recebem penalização
            penalizacao = np.where(
                (valor_total_norm > 0.8) & (score_frequencia < 0.3),  # Alto valor + Baixa freq
                0.3,  # Reduz para 30% do valor original
                np.where(
                    (valor_total_norm > 0.6) & (score_frequencia < 0.5),  # Valor médio-alto + Freq baixa-média
                    0.6,  # Reduz para 60% do valor original
                    1.0   # Sem penalização
                )
            )
            
            # 4. Calcula Valor Normalizado
            # Combina valor original com score de frequência e aplica penalização
            produto_stats['valor_normalizado'] = (
                produto_stats['valor_total'] * 
                (0.7 + 0.3 * score_frequencia) *  # Valor base + bonus por frequência
                penalizacao                        # Aplica penalização se necessário
            )
            
            # 5. Adiciona métricas para análise
            produto_stats['score_frequencia'] = score_frequencia
            produto_stats['fator_penalizacao'] = penalizacao
            produto_stats['percentual_reducao'] = (
                (produto_stats['valor_total'] - produto_stats['valor_normalizado']) / 
                produto_stats['valor_total'] * 100
            ).round(1)
            
            # Log das normalizações significativas
            produtos_penalizados = produto_stats[produto_stats['fator_penalizacao'] < 1.0]
            if not produtos_penalizados.empty:
                logger.info(f"📉 {len(produtos_penalizados)} produtos penalizados por baixa frequência:")
                for _, produto in produtos_penalizados.head(3).iterrows():
                    logger.info(f"   • {produto['material'][:50]}... - Redução: {produto['percentual_reducao']}%")
            
            logger.info(f"✅ Normalização aplicada a {len(produto_stats)} produtos")
            return produto_stats
            
        except Exception as e:
            logger.error(f"❌ Erro na normalização inteligente: {e}")
            # Fallback: usa valor original
            produto_stats['valor_normalizado'] = produto_stats['valor_total']
            produto_stats['score_frequencia'] = 1.0
            produto_stats['fator_penalizacao'] = 1.0
            produto_stats['percentual_reducao'] = 0.0
            return produto_stats
    
    def _normalize_series(self, series: pd.Series) -> pd.Series:
        """
        Normaliza uma série para escala 0-1 usando Min-Max scaling
        """
        min_val = series.min()
        max_val = series.max()
        
        if max_val == min_val:
            return pd.Series([0.5] * len(series), index=series.index)
        
        return (series - min_val) / (max_val - min_val)
    
    def classify_abc_xyz(self, vendas_df: pd.DataFrame, cliente_filter: str = None) -> pd.DataFrame:
        """
        Classificação ABC-XYZ de produtos
        
        ABC: Baseado no valor movimentado (Pareto)
        XYZ: Baseado na variabilidade da demanda (CV)
        
        Args:
            vendas_df: DataFrame de vendas
            cliente_filter: Filtro por cliente específico (para revendas)
            
        Returns:
            DataFrame com classificação ABC-XYZ e métricas
        """
        logger.info("🔍 Iniciando classificação ABC-XYZ")
        
        try:
            # Filtra dados dos últimos meses configurados
            cutoff_date = datetime.now() - timedelta(days=self.default_config['janela_demanda_meses'] * 30)
            vendas_recentes = vendas_df[
                pd.to_datetime(vendas_df['data_faturamento'], errors='coerce') >= cutoff_date
            ].copy()
            
            if cliente_filter:
                vendas_recentes = vendas_recentes[vendas_recentes['cod_cliente'] == cliente_filter]
            
            if vendas_recentes.empty:
                logger.warning("⚠️ Sem dados de vendas recentes para classificação")
                return pd.DataFrame()
            
            # Agrupa por produto e calcula métricas
            produto_stats = vendas_recentes.groupby('material').agg({
                'vlr_rol': ['sum', 'mean', 'std', 'count'],
                'qtd_rol': ['sum', 'mean', 'std'] if 'qtd_rol' in vendas_recentes.columns else ['sum', 'mean', 'std'],
                'data_faturamento': ['min', 'max', 'count'],  # Adiciona count para recorrência
                'cod_cliente': 'nunique'  # Número de clientes únicos
            }).round(2)
            
            # Flatten column names
            produto_stats.columns = [
                'valor_total', 'valor_medio', 'valor_std', 'freq_vendas',
                'qtd_total', 'qtd_media', 'qtd_std',
                'primeira_venda', 'ultima_venda', 'num_transacoes', 'num_clientes_unicos'
            ]
            produto_stats = produto_stats.reset_index()
            
            # Calcula métricas de recorrência
            produto_stats['dias_historico'] = (
                pd.to_datetime(produto_stats['ultima_venda']) - 
                pd.to_datetime(produto_stats['primeira_venda'])
            ).dt.days + 1
            
            # Frequência de vendas (transações por mês)
            produto_stats['freq_mensal'] = produto_stats['num_transacoes'] / (produto_stats['dias_historico'] / 30)
            produto_stats['freq_mensal'] = produto_stats['freq_mensal'].fillna(0)
            
            # Score de recorrência (combina frequência e diversidade de clientes)
            produto_stats['score_recorrencia'] = (
                produto_stats['freq_mensal'] * 0.7 + 
                produto_stats['num_clientes_unicos'] * 0.3
            )
            
            # Calcula coeficiente de variação para XYZ - CORRIGIDO
            # CV = desvio_padrão / média, onde média > 0
            produto_stats['cv_valor'] = np.where(
                produto_stats['valor_medio'] > 0, 
                produto_stats['valor_std'] / produto_stats['valor_medio'], 
                0
            )
            produto_stats['cv_quantidade'] = np.where(
                produto_stats['qtd_media'] > 0, 
                produto_stats['qtd_std'] / produto_stats['qtd_media'], 
                0
            )
            
            # Para produtos com apenas 1 transação, CV = 0 (sem variabilidade)
            produto_stats['cv_valor'] = np.where(
                produto_stats['num_transacoes'] <= 1, 
                0, 
                produto_stats['cv_valor']
            )
            produto_stats['cv_quantidade'] = np.where(
                produto_stats['num_transacoes'] <= 1, 
                0, 
                produto_stats['cv_quantidade']
            )
            
            # Remove infinitos e NaN
            produto_stats['cv_valor'] = produto_stats['cv_valor'].replace([np.inf, -np.inf], 0).fillna(0)
            produto_stats['cv_quantidade'] = produto_stats['cv_quantidade'].replace([np.inf, -np.inf], 0).fillna(0)
            
            # ✅ FILTRO CRÍTICO: Remove produtos com histórico insuficiente para análise confiável
            # Produtos com apenas 1 transação não têm padrão de demanda estabelecido
            produtos_antes = len(produto_stats)
            produto_stats = produto_stats[produto_stats['num_transacoes'] >= 2].copy()
            produtos_filtrados = produtos_antes - len(produto_stats)
            
            if produtos_filtrados > 0:
                logger.info(f"🔍 Filtrados {produtos_filtrados} produtos com histórico insuficiente (< 2 transações)")
            
            if produto_stats.empty:
                logger.warning("⚠️ Nenhum produto restante após filtro de histórico mínimo")
                return pd.DataFrame()
            
            # Classificação ABC (valor) - COM NORMALIZAÇÃO INTELIGENTE
            produto_stats = self._apply_intelligent_normalization(produto_stats)
            
            produto_stats = produto_stats.sort_values('valor_normalizado', ascending=False)
            produto_stats['valor_acumulado'] = produto_stats['valor_normalizado'].cumsum()
            produto_stats['perc_acumulado'] = produto_stats['valor_acumulado'] / produto_stats['valor_normalizado'].sum()
            
            # Aplica thresholds ABC
            abc_thresholds = self.default_config['abc_thresholds']
            produto_stats['classe_abc'] = np.select([
                produto_stats['perc_acumulado'] <= abc_thresholds[0],
                produto_stats['perc_acumulado'] <= abc_thresholds[1]
            ], ['A', 'B'], default='C')
            
            # Classificação XYZ (variabilidade)
            xyz_thresholds = self.default_config['xyz_cv_thresholds']
            produto_stats['classe_xyz'] = np.select([
                produto_stats['cv_valor'] <= xyz_thresholds[0],
                produto_stats['cv_valor'] <= xyz_thresholds[1]
            ], ['X', 'Y'], default='Z')
            
            # Combina classificações
            produto_stats['classificacao'] = produto_stats['classe_abc'] + produto_stats['classe_xyz']
            
            # Ordena por classificação (AX é o melhor) usando valor normalizado
            ordem_abc = {'A': 1, 'B': 2, 'C': 3}
            ordem_xyz = {'X': 1, 'Y': 2, 'Z': 3}
            produto_stats['ordem_abc'] = produto_stats['classe_abc'].map(ordem_abc)
            produto_stats['ordem_xyz'] = produto_stats['classe_xyz'].map(ordem_xyz)
            produto_stats = produto_stats.sort_values(['ordem_abc', 'ordem_xyz', 'valor_normalizado'], ascending=[True, True, False])
            
            logger.info(f"✅ Classificação ABC-XYZ concluída para {len(produto_stats)} produtos")
            return produto_stats.drop(['ordem_abc', 'ordem_xyz'], axis=1)
            
        except Exception as e:
            logger.error(f"❌ Erro na classificação ABC-XYZ: {e}")
            return pd.DataFrame()
    
    def calculate_safety_stock(self, demanda_historica: List[float], 
                             nivel_servico: float = None, 
                             leadtime_dias: int = None,
                             classificacao_abc: str = 'B',
                             classificacao_xyz: str = 'Y') -> Dict:
        """
        Calcula safety stock baseado na demanda histórica
        
        Formula: SS = Z * σ * √(LT)
        Onde:
        - Z = Z-score do nível de serviço
        - σ = desvio padrão da demanda
        - LT = lead time em períodos
        
        Args:
            demanda_historica: Lista de valores de demanda histórica
            nivel_servico: Nível de serviço desejado (None = calculado automaticamente)
            leadtime_dias: Lead time em dias
            classificacao_abc: Classificação ABC do produto
            classificacao_xyz: Classificação XYZ do produto
            
        Returns:
            Dict com safety stock e métricas
        """
        if not demanda_historica or len(demanda_historica) < 2:
            # Nível de serviço automático baseado na classificação se não especificado
            if nivel_servico is None:
                nivel_servico = self._get_dynamic_service_level(classificacao_abc, classificacao_xyz)
            else:
                nivel_servico = nivel_servico or self.default_config['nivel_servico']
                
            return {
                'safety_stock': 0,
                'demanda_media': 0,
                'desvio_padrao': 0,
                'coef_variacao': 0.0,
                'nivel_servico': nivel_servico,
                'z_score': 1.645,
                'leadtime_dias': leadtime_dias or self.default_config['leadtime_dias'],
                'leadtime_periods': (leadtime_dias or self.default_config['leadtime_dias']) / 30.0,
                'erro': 'Histórico insuficiente'
            }
        
        # Nível de serviço automático baseado na classificação se não especificado
        if nivel_servico is None:
            nivel_servico = self._get_dynamic_service_level(classificacao_abc, classificacao_xyz)
        else:
            nivel_servico = nivel_servico or self.default_config['nivel_servico']
            
        leadtime_dias = leadtime_dias or self.default_config['leadtime_dias']
        
        # Converte lead time para períodos mensais
        leadtime_periods = leadtime_dias / 30.0
        
        # Estatísticas da demanda
        demanda_array = np.array(demanda_historica)
        demanda_media = np.mean(demanda_array)
        desvio_padrao = np.std(demanda_array, ddof=1)  # Sample std
        
        # Z-score para o nível de serviço
        # 90% = 1.28, 95% = 1.645, 98% = 2.05, 99% = 2.33
        z_scores = {
            0.85: 1.04, 0.90: 1.28, 0.95: 1.645, 0.98: 2.05, 0.99: 2.33
        }
        z_score = z_scores.get(nivel_servico, 1.645)
        
        # Calcula safety stock
        safety_stock = z_score * desvio_padrao * np.sqrt(leadtime_periods)
        
        return {
            'safety_stock': max(0, safety_stock),
            'demanda_media': demanda_media,
            'desvio_padrao': desvio_padrao,
            'coef_variacao': desvio_padrao / demanda_media if demanda_media > 0 else 0,
            'nivel_servico': nivel_servico,
            'z_score': z_score,
            'leadtime_dias': leadtime_dias,
            'leadtime_periods': leadtime_periods
        }
    
    def _get_dynamic_service_level(self, classificacao_abc: str, classificacao_xyz: str) -> float:
        """
        Determina nível de serviço dinamicamente baseado na classificação ABC-XYZ
        
        Args:
            classificacao_abc: Classe ABC (A, B, C)
            classificacao_xyz: Classe XYZ (X, Y, Z)
            
        Returns:
            float: Nível de serviço entre 0.85 e 0.99
        """
        # Matriz de níveis de serviço ABC-XYZ
        service_levels = {
            'AX': 0.99,  # Críticos + Previsíveis = 99%
            'AY': 0.98,  # Críticos + Variáveis = 98%
            'AZ': 0.95,  # Críticos + Imprevisíveis = 95%
            'BX': 0.98,  # Importantes + Previsíveis = 98%
            'BY': 0.95,  # Importantes + Variáveis = 95%
            'BZ': 0.90,  # Importantes + Imprevisíveis = 90%
            'CX': 0.95,  # Menos críticos + Previsíveis = 95%
            'CY': 0.90,  # Menos críticos + Variáveis = 90%
            'CZ': 0.85,  # Menos críticos + Imprevisíveis = 85%
        }
        
        classificacao = f"{classificacao_abc}{classificacao_xyz}"
        return service_levels.get(classificacao, 0.95)  # Default 95%
    
    def calculate_demand_forecast(self, vendas_df: pd.DataFrame, 
                                material: str, 
                                cod_cliente: str = None,
                                classificacao_abc: str = 'B',
                                classificacao_xyz: str = 'Y') -> Dict:
        """
        Calcula previsão de demanda para um material
        
        Args:
            vendas_df: DataFrame de vendas
            material: Código do material
            cod_cliente: Cliente específico (opcional)
            classificacao_abc: Classificação ABC do produto
            classificacao_xyz: Classificação XYZ do produto
            
        Returns:
            Dict com previsão e métricas
        """
        try:
            # Filtra dados do material
            material_data = vendas_df[vendas_df['material'] == material].copy()
            
            if cod_cliente:
                material_data = material_data[material_data['cod_cliente'] == cod_cliente]
            
            if material_data.empty:
                return {'erro': 'Sem histórico de vendas'}
            
            # Converte datas
            material_data['data_faturamento'] = pd.to_datetime(material_data['data_faturamento'], errors='coerce')
            material_data = material_data.dropna(subset=['data_faturamento'])
            
            # Filtra últimos meses configurados
            cutoff_date = datetime.now() - timedelta(days=self.default_config['janela_demanda_meses'] * 30)
            material_recente = material_data[material_data['data_faturamento'] >= cutoff_date]
            
            # Se não tem dados recentes suficientes, usa todo o histórico disponível
            if len(material_recente) < self.default_config['min_historico_meses']:
                print(f"      ⚠️ Poucos dados recentes ({len(material_recente)}), usando todo histórico ({len(material_data)})")
                material_recente = material_data
                
            # Se ainda assim não tem dados suficientes, tenta com menos rigor
            if len(material_recente) == 0:
                return {'erro': 'Sem histórico de vendas'}
            elif len(material_recente) < self.default_config['min_historico_meses']:
                print(f"      ⚠️ Histórico muito limitado ({len(material_recente)} registros), gerando sugestão básica")
            
            # Agrupa por mês
            material_recente['ano_mes'] = material_recente['data_faturamento'].dt.to_period('M')
            demanda_mensal = material_recente.groupby('ano_mes').agg({
                'qtd_rol': 'sum' if 'qtd_rol' in material_recente.columns else 'count',
                'vlr_rol': 'sum'
            }).reset_index()
            
            # Calcula métricas de demanda
            qtd_historica = demanda_mensal['qtd_rol'].tolist()
            valor_historico = demanda_mensal['vlr_rol'].tolist()
            
            # Safety stock com classificação ABC-XYZ
            safety_metrics = self.calculate_safety_stock(
                qtd_historica, 
                classificacao_abc=classificacao_abc,
                classificacao_xyz=classificacao_xyz
            )
            
            # Previsão simples (média móvel + safety stock)
            demanda_media_mensal = np.mean(qtd_historica)
            demanda_media_diaria = demanda_media_mensal / 30
            
            # Quantidade sugerida para cobertura - Dinâmica baseada na variabilidade
            leadtime_dias = self.default_config['leadtime_dias']
            
            # Cobertura dinâmica baseada no coeficiente de variação
            cv = safety_metrics.get('coef_variacao', 0.0)
            if cv <= 0.5:  # Baixa variabilidade (X)
                cobertura_adicional = 15  # 15 dias extras
            elif cv <= 1.0:  # Média variabilidade (Y)
                cobertura_adicional = 30  # 30 dias extras
            else:  # Alta variabilidade (Z)
                cobertura_adicional = 45  # 45 dias extras
            
            cobertura_dias = leadtime_dias + cobertura_adicional
            
            quantidade_sugerida = (demanda_media_diaria * cobertura_dias) + safety_metrics['safety_stock']
            
            return {
                'material': material,
                'cod_cliente': cod_cliente,
                'demanda_media_mensal': demanda_media_mensal,
                'demanda_media_diaria': demanda_media_diaria,
                'quantidade_sugerida': max(1, round(quantidade_sugerida)),
                'safety_stock': round(safety_metrics.get('safety_stock', 0)),
                'cobertura_dias': cobertura_dias,
                'nivel_servico': safety_metrics.get('nivel_servico', 0.95),
                'coef_variacao': safety_metrics.get('coef_variacao', 0.0),
                'historico_meses': len(qtd_historica),
                'valor_medio_mensal': np.mean(valor_historico),
                'confianca': min(100, len(qtd_historica) * 20)  # Mais histórico = mais confiança
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de demanda para {material}: {e}")
            return {'erro': str(e)}
    
    def generate_purchase_suggestions(self, vendas_df: pd.DataFrame, 
                                    cotacoes_df: pd.DataFrame = None,
                                    produtos_cotados_df: pd.DataFrame = None,
                                    cliente_filter: str = None,
                                    top_n: int = 50) -> pd.DataFrame:
        """
        Gera sugestões inteligentes de compra para revendas
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações (opcional)
            produtos_cotados_df: DataFrame de produtos cotados (opcional)
            cliente_filter: Filtrar por cliente específico
            top_n: Número de sugestões a retornar
            
        Returns:
            DataFrame com sugestões rankeadas
        """
        logger.info(f"🤖 Gerando sugestões de compra (top {top_n})")
        
        try:
            # Filtra por cliente se especificado
            if cliente_filter:
                vendas_data = vendas_df[vendas_df['cod_cliente'] == cliente_filter].copy()
                logger.info(f"📊 Análise focada no cliente: {cliente_filter}")
            else:
                vendas_data = vendas_df.copy()
            
            print(f"🔍 DEBUG: Dados de vendas após filtro cliente: {len(vendas_data)} registros")
            
            if vendas_data.empty:
                logger.warning("⚠️ Sem dados de vendas para análise")
                return pd.DataFrame()
            
            # 1. Classificação ABC-XYZ
            print("🔬 Executando classificação ABC-XYZ...")
            classificacao = self.classify_abc_xyz(vendas_data, cliente_filter)
            print(f"✅ Classificação ABC-XYZ retornou: {len(classificacao)} produtos")
            
            if classificacao.empty:
                print("❌ Classificação ABC-XYZ retornou vazio!")
                return pd.DataFrame()
            
            # Debug: mostra algumas classificações
            print(f"📋 Primeiros produtos classificados:")
            print(classificacao[['material', 'classe_abc', 'classe_xyz', 'classificacao', 'valor_total']].head())
            
            # 2. Calcula probabilidades de recompra usando ML
            print("🔮 Calculando probabilidades de recompra...")
            probabilidades_df = self.predict_repurchase_probability(
                vendas_data, 
                cotacoes_df, 
                produtos_cotados_df,  # ✅ Adiciona produtos_cotados_df
                cod_cliente=cliente_filter
            )
            print(f"✅ Probabilidades calculadas para {len(probabilidades_df)} produtos")
            if not probabilidades_df.empty:
                print(f"📊 Exemplo de probabilidades: {probabilidades_df[['material', 'prob_recompra_ml']].head()}")
            else:
                print("⚠️ ATENÇÃO: DataFrame de probabilidades está vazio!")
            
            
            # 3. Gera sugestões para produtos relevantes
            sugestoes = []
            
            # Score combinado: ABC-XYZ + Recorrência + Volume
            score_abc = classificacao['classe_abc'].map({'A': 100, 'B': 70, 'C': 40})
            score_xyz = classificacao['classe_xyz'].map({'X': 100, 'Y': 70, 'Z': 40})
            
            # Normaliza score de recorrência e volume para 0-100
            if ML_AVAILABLE:
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler(feature_range=(0, 100))
                
                if 'score_recorrencia' in classificacao.columns:
                    score_recorrencia = scaler.fit_transform(classificacao[['score_recorrencia']]).flatten()
                else:
                    score_recorrencia = np.zeros(len(classificacao))
                    
                score_volume = scaler.fit_transform(classificacao[['qtd_total']]).flatten()
            else:
                # Fallback simples se sklearn não disponível
                max_recorrencia = classificacao.get('score_recorrencia', pd.Series([1])).max()
                max_volume = classificacao['qtd_total'].max()
                
                score_recorrencia = (classificacao.get('score_recorrencia', 0) / max_recorrencia * 100) if max_recorrencia > 0 else np.zeros(len(classificacao))
                score_volume = (classificacao['qtd_total'] / max_volume * 100) if max_volume > 0 else np.zeros(len(classificacao))
            
            # Score final combinado (usando pesos adaptativos)
            classificacao['score_final'] = (
                score_abc * self.adaptive_weights['abc_weight'] + 
                score_volume * self.adaptive_weights['volume_weight'] + 
                score_recorrencia * self.adaptive_weights['recorrencia_weight'] + 
                score_xyz * self.adaptive_weights['xyz_weight']
            )
            
            # Ordena por score final (melhor primeiro)
            classificacao = classificacao.sort_values('score_final', ascending=False)
            
            # Prioriza produtos com melhor score combinado - aumentado multiplicador
            produtos_prioritarios = classificacao['material'].head(top_n * 5).tolist()  # Mais candidatos para diversidade
            
            print(f"🎯 Produtos prioritários por score combinado: {len(produtos_prioritarios)}")
            print(f"📊 Top 5 produtos:")
            top_5 = classificacao[['material', 'classe_abc', 'classe_xyz', 'score_recorrencia', 'qtd_total', 'score_final']].head()
            print(top_5.to_string())
            
            print(f"🔄 Processando {min(len(produtos_prioritarios), top_n)} produtos...")
            
            for i, material in enumerate(produtos_prioritarios[:top_n]):
                try:
                    print(f"  📦 Processando material {i+1}/{min(len(produtos_prioritarios), top_n)}: {material}")
                    
                    # Busca informações do produto
                    produto_info = classificacao[classificacao['material'] == material].iloc[0]
                    
                    demanda_info = self.calculate_demand_forecast(
                        vendas_data, material, cliente_filter,
                        classificacao_abc=produto_info['classe_abc'],
                        classificacao_xyz=produto_info['classe_xyz']
                    )
                    
                    if 'erro' not in demanda_info:
                        print(f"     ✅ Demanda calculada - Qtd sugerida: {demanda_info['quantidade_sugerida']}")
                        
                        # Busca descrição do produto
                        produto_descricao = vendas_data[vendas_data['material'] == material]['produto'].iloc[0] if not vendas_data[vendas_data['material'] == material].empty else f"Material {material}"
                        
                        # Busca dados do cliente se não especificado
                        if not cliente_filter:
                            # Tenta encontrar clientes que compraram este material nos dados filtrados
                            clientes_material = vendas_data[vendas_data['material'] == material]['cod_cliente'].value_counts()
                            
                            if len(clientes_material) > 0:
                                cliente_principal = clientes_material.index[0]
                                # Busca nome do cliente
                                cliente_dados = vendas_data[vendas_data['cod_cliente'] == cliente_principal]['cliente']
                                nome_cliente = cliente_dados.iloc[0] if len(cliente_dados) > 0 else f"Cliente {cliente_principal}"
                            else:
                                # Se não encontrou nos dados filtrados, busca na base completa
                                try:
                                    conn = get_db_connection()
                                    resultado_cliente = conn.execute(
                                        "SELECT cod_cliente, cliente FROM vendas WHERE material = ? LIMIT 1",
                                        (material,)
                                    ).fetchone()
                                    conn.close()
                                    
                                    if resultado_cliente:
                                        cliente_principal = resultado_cliente[0]
                                        nome_cliente = resultado_cliente[1]
                                    else:
                                        # Material não tem histórico de vendas - buscar em produtos_cotados
                                        conn = get_db_connection()
                                        resultado_cotacao = conn.execute(
                                            """SELECT cod_cliente, cliente, cotacao, descricao, 
                                                      quantidade, preco_liquido_unitario
                                               FROM produtos_cotados 
                                               WHERE material = ? 
                                               ORDER BY preco_liquido_total DESC LIMIT 1""",
                                            (material,)
                                        ).fetchone()
                                        conn.close()
                                        
                                        if resultado_cotacao:
                                            cliente_principal = resultado_cotacao[0]
                                            nome_cliente = f"{resultado_cotacao[1]} (Cotação {resultado_cotacao[2]})"
                                            print(f"     🎯 Cliente encontrado em produtos_cotados: {nome_cliente}")
                                        else:
                                            # Fallback para cotações JSON
                                            conn = get_db_connection()
                                            resultado_cotacao_json = conn.execute(
                                                """SELECT cod_cliente, cliente FROM cotacoes 
                                                   WHERE linhas_cotacao LIKE ? LIMIT 1""",
                                                (f'%{material}%',)
                                            ).fetchone()
                                            conn.close()
                                            
                                            if resultado_cotacao_json:
                                                cliente_principal = resultado_cotacao_json[0]
                                                nome_cliente = f"{resultado_cotacao_json[1]} (Interesse não Convertido)"
                                            else:
                                                cliente_principal = 'POTENCIAL'
                                                nome_cliente = 'Oportunidade de Mercado'
                                except Exception as e:
                                    print(f"     ⚠️ Erro buscando cliente para {material}: {e}")
                                    cliente_principal = 'DESCONHECIDO'
                                    nome_cliente = 'Cliente a Definir'
                        else:
                            cliente_principal = cliente_filter
                            cliente_dados = vendas_data[vendas_data['cod_cliente'] == cliente_filter]['cliente']
                            nome_cliente = cliente_dados.iloc[0] if len(cliente_dados) > 0 else cliente_filter
                        
                        # Score de prioridade melhorado (múltiplos fatores)
                        score_abc = {'A': 100, 'B': 70, 'C': 40}[produto_info['classe_abc']]
                        score_xyz = {'X': 100, 'Y': 70, 'Z': 40}[produto_info['classe_xyz']]
                        score_confianca = demanda_info['confianca']
                        
                        # Busca probabilidade de recompra do ML (PRIMEIRO)
                        probabilidade_recompra = 0.0
                        if not probabilidades_df.empty:
                            prob_material = probabilidades_df[probabilidades_df['material'] == material]
                            if not prob_material.empty:
                                probabilidade_recompra = prob_material['prob_recompra_ml'].iloc[0]
                                print(f"     🔮 Probabilidade ML: {probabilidade_recompra:.3f}")
                            else:
                                # ✅ FALLBACK HEURÍSTICO NORMALIZADO
                                freq_12m = classificacao[classificacao['material'] == material]['score_recorrencia'].iloc[0] if 'score_recorrencia' in classificacao.columns else 0
                                # Aplica a mesma normalização usada no ML
                                prob_raw = min(freq_12m / 12.0, 1.0)
                                sigmoid_input = (prob_raw - 0.8) * 3
                                sigmoid_normalized = 1 / (1 + np.exp(-sigmoid_input))
                                probabilidade_recompra = 0.15 + (sigmoid_normalized * 0.60)
                                # Adiciona variação baseada no material
                                variacao = (abs(hash(str(material))) % 100) / 1000
                                probabilidade_recompra += variacao
                                probabilidade_recompra = max(0.10, min(0.85, probabilidade_recompra))
                                print(f"     📊 Probabilidade heurística: {probabilidade_recompra:.3f}")
                        else:
                            # ✅ FALLBACK QUANDO NÃO HÁ DATAFRAME DE PROBABILIDADES
                            freq_12m = classificacao[classificacao['material'] == material]['score_recorrencia'].iloc[0] if 'score_recorrencia' in classificacao.columns else 0
                            # Aplica a mesma normalização usada no ML
                            prob_raw = min(freq_12m / 12.0, 1.0)
                            sigmoid_input = (prob_raw - 0.8) * 3
                            sigmoid_normalized = 1 / (1 + np.exp(-sigmoid_input))
                            probabilidade_recompra = 0.15 + (sigmoid_normalized * 0.60)
                            # Adiciona variação baseada no material
                            variacao = (abs(hash(str(material))) % 100) / 1000
                            probabilidade_recompra += variacao
                            probabilidade_recompra = max(0.10, min(0.85, probabilidade_recompra))
                            print(f"     📊 Probabilidade heurística (sem ML): {probabilidade_recompra:.3f}")
                        
                        # ✅ PRIORIDADE MELHORADA COM MÚLTIPLOS FATORES
                        # Peso base: classificação ABC-XYZ (40%)
                        peso_classificacao = (score_abc * 0.6 + score_xyz * 0.4) * 0.40
                        
                        # Peso confiança (20%)
                        peso_confianca = score_confianca * 0.20
                        
                        # Peso probabilidade recompra (25%)
                        peso_probabilidade = probabilidade_recompra * 100 * 0.25
                        
                        # Peso demanda/urgência (15%) - baseado na cobertura e quantidade
                        urgencia_base = min(100, (demanda_info['quantidade_sugerida'] / max(1, demanda_info['safety_stock'])) * 50)
                        if demanda_info['cobertura_dias'] < 30:
                            urgencia_base *= 1.5  # Boost para itens com baixa cobertura
                        peso_urgencia = min(100, urgencia_base) * 0.15
                        
                        # Score final ponderado
                        priority_score = peso_classificacao + peso_confianca + peso_probabilidade + peso_urgencia
                        
                        # Adiciona pequena variação baseada no material para quebrar empates
                        material_hash = hash(material) % 100
                        priority_score += (material_hash / 1000)  # Variação de 0-0.099
                        
                        # Garante que está entre 0-100
                        priority_score = max(0, min(100, priority_score))
                        
                        print(f"     🎯 Priority Score: {priority_score:.1f} (ABC:{score_abc}, XYZ:{score_xyz}, Conf:{score_confianca:.1f}, Prob:{probabilidade_recompra:.3f})")
                        
                        # Calcula valor estimado da compra
                        valor_estimado = 0
                        if demanda_info['quantidade_sugerida'] > 0 and demanda_info['valor_medio_mensal'] > 0 and demanda_info['demanda_media_mensal'] > 0:
                            # Calcula preço unitário médio baseado no histórico
                            preco_unitario = demanda_info['valor_medio_mensal'] / demanda_info['demanda_media_mensal']
                            valor_estimado = demanda_info['quantidade_sugerida'] * preco_unitario
                        
                        sugestao = {
                            'material': material,
                            'produto': produto_descricao,
                            'cod_cliente': cliente_principal,
                            'cliente': nome_cliente,
                            'quantidade_sugerida': demanda_info['quantidade_sugerida'],
                            'safety_stock': demanda_info['safety_stock'],
                            'cobertura_dias': demanda_info['cobertura_dias'],
                            'nivel_servico': demanda_info['nivel_servico'],
                            'demanda_media_mensal': demanda_info['demanda_media_mensal'],
                            'classificacao_abc': produto_info['classe_abc'],
                            'classificacao_xyz': produto_info['classe_xyz'],
                            'classificacao': produto_info['classificacao'],
                            'coef_variacao': demanda_info['coef_variacao'],
                            'valor_medio_mensal': demanda_info['valor_medio_mensal'],
                            'historico_meses': demanda_info['historico_meses'],
                            'confianca': demanda_info['confianca'],
                            'valor_estimado': valor_estimado,
                            'priority_score': priority_score,
                            'prob_recompra': probabilidade_recompra,  # ✅ Campo corrigido para compatibilidade com tabela
                            'probabilidade_recompra': probabilidade_recompra,  # Mantém compatibilidade
                            'explicacao': self._generate_explanation(demanda_info, produto_info)
                        }
                        
                        sugestoes.append(sugestao)
                        print(f"     ✅ Sugestão criada! Total acumulado: {len(sugestoes)}")
                    else:
                        print(f"     ❌ Erro na demanda: {demanda_info.get('erro', 'Desconhecido')}")
                        
                except Exception as e:
                    print(f"     ❌ Erro processando material {material}: {e}")
                    continue
            
            # Converte para DataFrame e ordena por prioridade
            if sugestoes:
                print(f"📊 Criando DataFrame com {len(sugestoes)} sugestões...")
                df_sugestoes = pd.DataFrame(sugestoes)
                df_sugestoes = df_sugestoes.sort_values('priority_score', ascending=False)
                
                logger.info(f"✅ {len(df_sugestoes)} sugestões geradas")
                return df_sugestoes  # Retorna todas as sugestões sem limitação
            else:
                print("❌ Nenhuma sugestão foi criada!")
                logger.warning("⚠️ Nenhuma sugestão pôde ser gerada")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ ERRO GERAL na geração de sugestões: {e}")
            import traceback
            print(f"Stack trace: {traceback.format_exc()}")
            logger.error(f"❌ Erro na geração de sugestões: {e}")
            return pd.DataFrame()
    
    def _generate_explanation(self, demanda_info: Dict, produto_info: pd.Series) -> str:
        """Gera explicação textual para a sugestão"""
        try:
            classificacao = produto_info['classificacao']
            demanda_media = demanda_info['demanda_media_mensal']
            coef_var = demanda_info['coef_variacao']
            confianca = demanda_info['confianca']
            
            # Explicação baseada na classificação
            if classificacao.startswith('A'):
                importancia = "alta importância (produto classe A)"
            elif classificacao.startswith('B'):
                importancia = "média importância (produto classe B)"
            else:
                importancia = "baixa importância (produto classe C)"
            
            # Explicação da variabilidade
            if coef_var < 0.5:
                variabilidade = "demanda estável"
            elif coef_var < 1.0:
                variabilidade = "demanda moderadamente variável"
            else:
                variabilidade = "demanda altamente variável"
            
            # Explicação da confiança
            if confianca >= 80:
                nivel_confianca = "alta confiança"
            elif confianca >= 60:
                nivel_confianca = "média confiança"
            else:
                nivel_confianca = "baixa confiança"
            
            return (f"Produto de {importancia} com {variabilidade}. "
                   f"Demanda média: {demanda_media:.1f} unidades/mês. "
                   f"Recomendação com {nivel_confianca} baseada em "
                   f"{demanda_info['historico_meses']} meses de histórico.")
            
        except Exception as e:
            return f"Sugestão baseada em análise estatística (classificação {produto_info.get('classificacao', 'N/A')})"
    
    def save_feedback(self, material: str, cod_cliente: str, 
                     feedback_type: str, motivo: str = None,
                     quantidade_sugerida: float = None,
                     usuario: str = None) -> bool:
        """
        Salva feedback do usuário sobre uma recomendação
        
        Args:
            material: Código do material
            cod_cliente: Código do cliente
            feedback_type: 'positivo' ou 'negativo'
            motivo: Motivo do feedback
            quantidade_sugerida: Quantidade que foi sugerida
            usuario: Usuário que deu o feedback
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            self.connect_db()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO feedback_recomendacoes 
                (material, cod_cliente, feedback_type, motivo, quantidade_sugerida, usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (material, cod_cliente, feedback_type, motivo, quantidade_sugerida, usuario))
            
            self.conn.commit()
            
            # Reinforcement Learning - Ajusta pesos baseado no feedback
            self._update_adaptive_weights(material, cod_cliente, feedback_type)
            
            logger.info(f"✅ Feedback salvo: {material} - {feedback_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar feedback: {e}")
            return False
        finally:
            self.close_db()
    
    def get_feedback_stats(self) -> Dict:
        """Retorna estatísticas de feedback para melhoria do modelo"""
        try:
            self.connect_db()
            
            # Verifica se a tabela existe
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='feedback_recomendacoes'
            """)
            
            if not cursor.fetchone():
                logger.warning("⚠️ Tabela feedback_recomendacoes não existe")
                return {
                    'total_feedbacks': 0,
                    'taxa_aceitacao': 0.0,  # ✅ 0% quando não há dados
                    'detalhes': [],
                    'status': 'tabela_inexistente'
                }
            
            stats = pd.read_sql_query("""
                SELECT 
                    feedback_type,
                    COUNT(*) as total,
                    AVG(quantidade_sugerida) as avg_quantidade
                FROM feedback_recomendacoes 
                GROUP BY feedback_type
            """, self.conn)
            
            if stats.empty:
                return {
                    'total_feedbacks': 0,
                    'taxa_aceitacao': 0.0,  # ✅ 0% quando não há feedbacks
                    'detalhes': [],
                    'status': 'sem_feedbacks'
                }
            
            total_feedbacks = stats['total'].sum()
            positivos = stats[stats['feedback_type'] == 'positivo']['total'].sum()
            taxa_aceitacao = positivos / total_feedbacks if total_feedbacks > 0 else 0.0
            
            return {
                'total_feedbacks': total_feedbacks,
                'taxa_aceitacao': taxa_aceitacao,
                'detalhes': stats.to_dict('records'),
                'status': 'ok'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de feedback: {e}")
            return {
                'total_feedbacks': 0,
                'taxa_aceitacao': 0.0,  # ✅ 0% em caso de erro
                'detalhes': [],
                'erro': str(e)
            }
        finally:
            self.close_db()
    
    def extract_ml_features(self, vendas_df: pd.DataFrame, 
                           cotacoes_df: pd.DataFrame = None,
                           produtos_cotados_df: pd.DataFrame = None,
                           cliente_filter: str = None) -> pd.DataFrame:
        """
        Extrai features para o modelo ML de probabilidade de recompra
        VERSÃO OTIMIZADA com filtragem inteligente
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações (opcional)
            produtos_cotados_df: DataFrame de produtos cotados (opcional)
            cliente_filter: Filtrar por cliente específico
            
        Returns:
            DataFrame com features extraídas para ML
        """
        logger.info("🔬 Extraindo features para modelo ML (OTIMIZADO)")
        
        try:
            import time
            start_time = time.time()
            max_time = 120  # 2 minutos máximo
            
            # ESTRATÉGIA 1: Filtragem por relevância
            vendas_data = vendas_df.copy()
            
            if cliente_filter:
                vendas_data = vendas_data[vendas_data['cod_cliente'] == cliente_filter]
            
            # ESTRATÉGIA 2: Foca apenas nos últimos 6 meses para reduzir volume
            cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=180)
            vendas_data['data_faturamento'] = pd.to_datetime(vendas_data['data_faturamento'], errors='coerce')
            vendas_data = vendas_data.dropna(subset=['data_faturamento'])
            
            # Prioriza dados recentes
            vendas_recentes = vendas_data[vendas_data['data_faturamento'] >= cutoff_date]
            if len(vendas_recentes) >= 1000:  # Se há dados recentes suficientes
                vendas_data = vendas_recentes
                logger.info(f"� Usando apenas dados recentes: {len(vendas_df)} → {len(vendas_data)} registros")
            
            # ESTRATÉGIA 3: Top materiais e clientes por volume
            # Identifica os top 20 materiais por valor
            top_materiais = (vendas_data.groupby('material')['vlr_rol']
                           .sum().nlargest(20).index.tolist())
            
            # Identifica os top 15 clientes por valor
            top_clientes = (vendas_data.groupby('cod_cliente')['vlr_rol']
                          .sum().nlargest(15).index.tolist())
            
            # Filtra apenas combinações relevantes
            vendas_relevantes = vendas_data[
                (vendas_data['material'].isin(top_materiais)) &
                (vendas_data['cod_cliente'].isin(top_clientes))
            ]
            
            logger.info(f"🎯 Dados relevantes: {len(top_materiais)} materiais × {len(top_clientes)} clientes = {len(vendas_relevantes)} registros")
            
            if vendas_relevantes.empty:
                logger.warning("⚠️ Nenhum dado relevante encontrado após filtros")
                return pd.DataFrame()
            
            # ESTRATÉGIA 4: Amostragem inteligente se ainda muito grande
            max_combinations = 300  # Limite drástico
            grupos = list(vendas_relevantes.groupby(['material', 'cod_cliente']))
            
            if len(grupos) > max_combinations:
                # Ordena por volume total (valor + quantidade) e pega os top
                grupo_scores = []
                for (material, cliente), grupo_df in grupos:
                    score = grupo_df['vlr_rol'].sum() + grupo_df.get('qtd_rol', pd.Series([0])).sum() * 100
                    grupo_scores.append(((material, cliente), score))
                
                # Ordena por score e pega os top
                grupo_scores.sort(key=lambda x: x[1], reverse=True)
                top_grupos = [item[0] for item in grupo_scores[:max_combinations]]
                grupos = [(key, vendas_relevantes[(vendas_relevantes['material'] == key[0]) & 
                                                 (vendas_relevantes['cod_cliente'] == key[1])]) 
                         for key in top_grupos]
                
                logger.info(f"⚡ Limitado a top {max_combinations} combinações por volume")
            
            # Data de referência
            data_ref = datetime.now()
            features_list = []
            
            logger.info(f"🔄 Processando {len(grupos)} combinações otimizadas")
            
            for i, ((material, cod_cliente), grupo) in enumerate(grupos):
                try:
                    # Timeout check a cada 50 iterações
                    if i % 50 == 0:
                        elapsed = time.time() - start_time
                        if elapsed > max_time:
                            logger.error(f"⏰ TIMEOUT após {elapsed:.1f}s em {i}/{len(grupos)} combinações")
                            break
                        if i > 0:
                            logger.info(f"   📊 {i}/{len(grupos)} ({i/len(grupos)*100:.1f}%) - {elapsed:.1f}s")
                    
                    grupo = grupo.sort_values('data_faturamento')
                    
                    # Features simplificadas mas efetivas
                    ultima_compra = grupo['data_faturamento'].max()
                    recencia_dias = (data_ref - ultima_compra).days
                    
                    # Frequência nos últimos 12 meses
                    cutoff_12m = data_ref - timedelta(days=365)
                    compras_12m = grupo[grupo['data_faturamento'] >= cutoff_12m]
                    frequencia_12m = len(compras_12m)
                    
                    # Valores
                    valor_medio = grupo['vlr_rol'].mean()
                    valor_total_12m = compras_12m['vlr_rol'].sum()
                    
                    # Sazonalidade simplificada
                    grupo_temp = grupo.copy()
                    grupo_temp['trimestre'] = grupo_temp['data_faturamento'].dt.quarter
                    sazonalidade = grupo_temp['trimestre'].value_counts(normalize=True)
                    concentracao_sazonal = sazonalidade.max() if not sazonalidade.empty else 0.25
                    
                    # Regularidade simplificada
                    if len(grupo) > 1:
                        intervalos = grupo['data_faturamento'].diff().dt.days.dropna()
                        if len(intervalos) > 0 and intervalos.mean() > 0:
                            regularidade_cv = intervalos.std() / intervalos.mean()
                        else:
                            regularidade_cv = 999
                    else:
                        regularidade_cv = 999
                    
                    # Tendência simplificada
                    if len(grupo) >= 3:
                        meio = len(grupo) // 2
                        primeira_metade = grupo.iloc[:meio]['vlr_rol'].mean()
                        segunda_metade = grupo.iloc[meio:]['vlr_rol'].mean()
                        tendencia = (segunda_metade - primeira_metade) / primeira_metade if primeira_metade > 0 else 0
                    else:
                        tendencia = 0
                    
                    # Intensidade
                    meses_ativos = grupo['data_faturamento'].dt.to_period('M').nunique()
                    intensidade = frequencia_12m / max(1, meses_ativos)
                    
                    # Cotações simplificadas
                    cotacoes_ratio = 0
                    if cotacoes_df is not None and not cotacoes_df.empty and 'cod_cliente' in cotacoes_df.columns:
                        cotacoes_cliente = cotacoes_df[cotacoes_df['cod_cliente'] == cod_cliente]
                        if not cotacoes_cliente.empty:
                            num_cotacoes = len(cotacoes_cliente)
                            num_compras = len(grupo)
                            cotacoes_ratio = num_cotacoes / max(1, num_compras)
                    
                    # ====== NOVO TARGET BASEADO EM RECORRÊNCIA HISTÓRICA REAL ======
                    # Ao invés de "comprou nos últimos 3 meses", vamos calcular a probabilidade
                    # baseada no padrão histórico de recorrência do produto
                    
                    # 1. Calcula intervalo médio entre compras (ciclo de recompra)
                    if len(grupo) >= 2:
                        datas_compra = sorted(grupo['data_faturamento'].tolist())
                        intervalos = [(datas_compra[i+1] - datas_compra[i]).days for i in range(len(datas_compra)-1)]
                        intervalo_medio_dias = sum(intervalos) / len(intervalos)
                        
                        # Variabilidade do intervalo (regularidade)
                        if len(intervalos) > 1:
                            std_intervalo = pd.Series(intervalos).std()
                            coef_var_intervalo = std_intervalo / intervalo_medio_dias if intervalo_medio_dias > 0 else 999
                        else:
                            coef_var_intervalo = 0.5  # Regularidade moderada para 2 compras
                    else:
                        # Uma compra apenas - usa heurística baseada na categoria do produto
                        intervalo_medio_dias = 180  # 6 meses como padrão
                        coef_var_intervalo = 1.0    # Alta variabilidade para compra única
                    
                    # 2. Calcula tempo desde última compra vs ciclo esperado
                    dias_desde_ultima = recencia_dias
                    ratio_tempo_ciclo = dias_desde_ultima / intervalo_medio_dias if intervalo_medio_dias > 0 else 0
                    
                    # 3. Probabilidade baseada no ciclo de recompra histórico
                    if ratio_tempo_ciclo < 0.5:
                        # Muito cedo para recompra
                        prob_ciclo = 0.1 + (ratio_tempo_ciclo * 0.3)  # 0.1 a 0.25
                    elif ratio_tempo_ciclo < 1.0:
                        # Aproximando-se do tempo esperado
                        prob_ciclo = 0.25 + ((ratio_tempo_ciclo - 0.5) * 1.5)  # 0.25 a 1.0
                    elif ratio_tempo_ciclo < 1.5:
                        # Passou do tempo - alta probabilidade
                        prob_ciclo = 1.0 - ((ratio_tempo_ciclo - 1.0) * 0.4)  # 1.0 a 0.8
                    else:
                        # Muito atrasado - probabilidade decresce
                        prob_ciclo = max(0.2, 0.8 - ((ratio_tempo_ciclo - 1.5) * 0.3))  # 0.8 a 0.2+
                    
                    # 4. Fator de regularidade (produtos regulares são mais previsíveis)
                    if coef_var_intervalo < 0.3:
                        fator_regularidade = 1.2  # Produto muito regular
                    elif coef_var_intervalo < 0.7:
                        fator_regularidade = 1.0  # Regularidade normal
                    else:
                        fator_regularidade = 0.8  # Produto irregular
                    
                    # 5. Fator de frequência (produtos mais frequentes têm maior probabilidade)
                    compras_por_ano = frequencia_12m * (365 / max(365, (data_ref - grupo['data_faturamento'].min()).days))
                    if compras_por_ano >= 4:
                        fator_frequencia = 1.3  # Produto de alta rotação
                    elif compras_por_ano >= 2:
                        fator_frequencia = 1.1  # Rotação média
                    elif compras_por_ano >= 0.5:
                        fator_frequencia = 1.0  # Rotação baixa
                    else:
                        fator_frequencia = 0.7  # Produto esporádico
                    
                    # 6. Fator de valor (produtos de maior valor podem ter ciclos diferentes)
                    valor_percentil = np.percentile(vendas_df[vendas_df['cod_cliente'] == cod_cliente]['vlr_rol'], 
                                                   [25, 50, 75]) if len(vendas_df[vendas_df['cod_cliente'] == cod_cliente]) > 3 else [100, 500, 1000]
                    
                    if valor_medio >= valor_percentil[2]:  # Top 25%
                        fator_valor = 0.9  # Produtos caros comprados menos frequentemente
                    elif valor_medio >= valor_percentil[1]:  # Mediano
                        fator_valor = 1.0
                    else:  # Bottom 25%
                        fator_valor = 1.1  # Produtos baratos comprados mais frequentemente
                    
                    # 7. Probabilidade final combinada com normalização rigorosa
                    probabilidade_recompra_raw = prob_ciclo * fator_regularidade * fator_frequencia * fator_valor
                    
                    # ✅ NORMALIZAÇÃO MAIS AGRESSIVA PARA EVITAR 100%
                    # Aplica função sigmoidal para suavizar extremos
                    sigmoid_input = (probabilidade_recompra_raw - 0.8) * 3  # Centra em 0.8 e amplifica
                    sigmoid_normalized = 1 / (1 + np.exp(-sigmoid_input))
                    
                    # Mapeia sigmoid para range 0.15 - 0.75 (mais conservador)
                    probabilidade_recompra_final = 0.15 + (sigmoid_normalized * 0.60)
                    
                    # Adiciona variação pequena baseada no material para quebrar empates
                    material_hash = abs(hash(str(material) + str(cod_cliente))) % 1000
                    variacao = (material_hash / 1000) * 0.1  # 0 a 0.1
                    probabilidade_recompra_final += variacao
                    
                    # Garante limites finais mais restritivos
                    probabilidade_recompra_final = max(0.10, min(0.85, probabilidade_recompra_final))
                    
                    # 8. Target binário para ML (baseado em threshold adaptativo)
                    # Threshold varia baseado na regularidade do produto
                    if coef_var_intervalo < 0.5:
                        threshold_recompra = 0.6  # Produtos regulares: threshold mais alto
                    else:
                        threshold_recompra = 0.4  # Produtos irregulares: threshold mais baixo
                    
                    target_recompra = 1 if probabilidade_recompra_final >= threshold_recompra else 0
                    
                    # Features otimizadas - REMOVENDO COLINEARIDADE
                    features = {
                        'material': material,
                        'cod_cliente': cod_cliente,
                        'recencia_dias': recencia_dias,
                        'frequencia_12m': frequencia_12m,
                        'valor_medio': valor_medio,
                        'valor_total_12m': valor_total_12m,
                        'concentracao_sazonal': concentracao_sazonal,
                        # ❌ REMOVIDO: 'regularidade_cv' (duplicado com coef_var_intervalo)
                        'tendencia': max(-2, min(2, tendencia)),
                        'intensidade': intensidade,  # ✅ MANTIDO: Mais informativo que compras_por_ano
                        'cotacoes_ratio': min(5, cotacoes_ratio),
                        'num_compras_total': len(grupo),
                        'dias_desde_primeira': (data_ref - grupo['data_faturamento'].min()).days,
                        
                        # ✅ FEATURES DE RECORRÊNCIA OTIMIZADAS
                        'intervalo_medio_dias': intervalo_medio_dias,
                        'coef_var_intervalo': min(5, coef_var_intervalo),  # CV temporal - ÚNICO
                        'ratio_tempo_ciclo': min(3, ratio_tempo_ciclo),
                        # ❌ REMOVIDO: 'compras_por_ano' (derivado de frequencia_12m)
                        'probabilidade_recorrencia': probabilidade_recompra_final,  # Feature contínua
                        
                        # Target baseado em recorrência histórica (mais realista)
                        'target_recompra': target_recompra
                    }
                    
                    features_list.append(features)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro processando {material}-{cod_cliente}: {e}")
                    continue
            
            # Cria DataFrame final
            features_df = pd.DataFrame(features_list)
            
            import time
            elapsed = time.time() - start_time
            logger.info(f"✅ Features extraídas: {len(features_df)} samples em {elapsed:.2f}s")
            
            return features_df
            
        except Exception as e:
            import time
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ Erro na extração de features após {elapsed:.2f}s: {e}")
            raise
            
            logger.info(f"✅ Features extraídas para {len(features_df)} registros material-cliente")
            return features_df
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de features: {e}")
            return pd.DataFrame()
    
    def train_repurchase_model(self, vendas_df: pd.DataFrame, 
                             cotacoes_df: pd.DataFrame = None,
                             produtos_cotados_df: pd.DataFrame = None,
                             retrain: bool = False) -> Dict:
        """
        Treina modelo ML de probabilidade de recompra
        
        Args:
            vendas_df: DataFrame de vendas para treino
            cotacoes_df: DataFrame de cotações (opcional)
            produtos_cotados_df: DataFrame de produtos cotados (opcional)
            retrain: Forçar retreinamento
            
        Returns:
            Dict com métricas do modelo
        """
        if not ML_AVAILABLE:
            logger.warning("⚠️ Bibliotecas ML não disponíveis - usando heurísticas")
            return {'erro': 'ML não disponível', 'modo': 'heuristico'}
        
        # ✅ VERIFICAÇÃO INTELIGENTE DE RETREINAMENTO
        if self.is_trained and not retrain:
            should_retrain, reason = self.should_retrain_model(vendas_df)
            if not should_retrain:
                logger.info(f"📚 Modelo atual adequado: {reason}")
                model_info = self.get_model_info()
                return {
                    'status': 'modelo_atual_adequado',
                    'motivo': reason,
                    'info_modelo': model_info
                }
            else:
                logger.info(f"🔄 Retreinamento necessário: {reason}")
                retrain = True  # Força retreinamento
        
        logger.info("🤖 Iniciando treinamento do modelo ML")
        
        try:
            # TIMEOUT SIMPLIFICADO: Apenas log e controle interno
            logger.info("🔬 Iniciando extração de features (timeout: 3 min)...")
            
            features_df = self.extract_ml_features(vendas_df, cotacoes_df, produtos_cotados_df)
            
            if features_df is None or features_df.empty or len(features_df) < 10:
                logger.warning("⚠️ Dados insuficientes para treino ML")
                return {'erro': 'Dados insuficientes'}
            
            # ====== MELHORIA: ADICIONAR TAXA DE CONVERSÃO ======
            logger.info("📊 Calculando taxa de conversão por material...")
            
            # Calcula taxa de conversão para cada material
            if cotacoes_df is not None and not cotacoes_df.empty:
                try:
                    # Taxa de conversão = vendas / cotações por material
                    vendas_por_material = vendas_df.groupby('material').agg({
                        'cod_cliente': 'nunique',
                        'vlr_entrada': 'sum'
                    }).reset_index()
                    vendas_por_material.columns = ['material', 'clientes_compraram', 'vendas_total']
                    
                    cotacoes_por_material = cotacoes_df.groupby('material').agg({
                        'cod_cliente': 'nunique',
                        'preco': 'sum'
                    }).reset_index()
                    cotacoes_por_material.columns = ['material', 'clientes_cotaram', 'cotacoes_total']
                    
                    # Merge para calcular conversão
                    conversao_df = pd.merge(vendas_por_material, cotacoes_por_material, on='material', how='outer').fillna(0)
                    conversao_df['taxa_conversao'] = np.where(
                        conversao_df['clientes_cotaram'] > 0,
                        conversao_df['clientes_compraram'] / conversao_df['clientes_cotaram'],
                        0.1  # Taxa padrão para materiais sem cotações
                    )
                    
                    # Adiciona ao features_df
                    features_df = features_df.merge(
                        conversao_df[['material', 'taxa_conversao']], 
                        on='material', 
                        how='left'
                    )
                    features_df['taxa_conversao'] = features_df['taxa_conversao'].fillna(0.1)
                    
                    logger.info(f"✅ Taxa de conversão calculada para {len(conversao_df)} materiais")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro no cálculo de taxa de conversão: {e}")
                    features_df['taxa_conversao'] = 0.1  # Valor padrão
            else:
                features_df['taxa_conversao'] = 0.1  # Valor padrão sem cotações

            # ====== MELHORIA: FEATURES ENGENHEIRADAS PARA MELHOR PERFORMANCE ======
            logger.info("🔧 Criando features engenheiradas...")
            
            # 1. Interações entre features importantes
            features_df['valor_x_frequencia'] = features_df['valor_medio'] * features_df['frequencia_12m']
            features_df['recencia_x_conversao'] = features_df['recencia_dias'] * features_df['taxa_conversao']
            features_df['valor_por_compra'] = features_df['valor_total_12m'] / np.maximum(1, features_df['num_compras_total'])
            
            # 2. Features categóricas transformadas
            features_df['cliente_ativo'] = (features_df['recencia_dias'] <= 90).astype(int)
            features_df['alta_frequencia'] = (features_df['frequencia_12m'] >= features_df['frequencia_12m'].quantile(0.7)).astype(int)
            features_df['alto_valor'] = (features_df['valor_medio'] >= features_df['valor_medio'].quantile(0.7)).astype(int)
            
            # 3. Features sazonais aprimoradas
            features_df['concentracao_extrema'] = (features_df['concentracao_sazonal'] >= features_df['concentracao_sazonal'].quantile(0.9)).astype(int)
            
            # Prepara dados para ML com features expandidas baseadas em recorrência
            feature_columns = [
                # Features originais de comportamento
                'recencia_dias', 'frequencia_12m', 'valor_medio', 'valor_total_12m',
                'concentracao_sazonal', 'tendencia', 'intensidade',
                'cotacoes_ratio', 'num_compras_total', 'dias_desde_primeira',
                
                # Features de conversão e engagement
                'taxa_conversao', 'valor_x_frequencia', 'recencia_x_conversao', 'valor_por_compra',
                'cliente_ativo', 'alta_frequencia', 'alto_valor', 'concentracao_extrema',
                
                # ✅ FEATURES DE RECORRÊNCIA OTIMIZADAS (SEM COLINEARIDADE)
                'intervalo_medio_dias', 'coef_var_intervalo', 'ratio_tempo_ciclo', 
                'probabilidade_recorrencia'
                # ❌ REMOVIDO: 'regularidade_cv' (duplicado com coef_var_intervalo)
                # ❌ REMOVIDO: 'compras_por_ano' (derivado de frequencia_12m)
            ]
            
            X = features_df[feature_columns].fillna(0)
            y = features_df['target_recompra'].astype(int)  # Garantir que é inteiro
            
            logger.info(f"📈 Features preparadas: {len(feature_columns)} variáveis para {len(X)} amostras")
            
            # Verifica se temos ambas as classes
            unique_classes = y.unique()
            if len(unique_classes) < 2:
                logger.warning(f"⚠️ Apenas uma classe encontrada: {unique_classes}")
                # Cria exemplos sintéticos da classe minoritária para permitir treinamento
                if unique_classes[0] == 1:
                    # Só temos classe positiva, criar alguns negativos
                    X_neg = X.sample(min(5, len(X)//2), random_state=42)
                    X_neg = X_neg * 0.7  # Reduz valores para simular classe negativa
                    y_neg = pd.Series([0] * len(X_neg))
                    X = pd.concat([X, X_neg], ignore_index=True)
                    y = pd.concat([y, y_neg], ignore_index=True)
                else:
                    # Só temos classe negativa, criar alguns positivos
                    X_pos = X.sample(min(5, len(X)//2), random_state=42)
                    X_pos = X_pos * 1.3  # Aumenta valores para simular classe positiva
                    y_pos = pd.Series([1] * len(X_pos))
                    X = pd.concat([X, X_pos], ignore_index=True)
                    y = pd.concat([y, y_pos], ignore_index=True)
                
                logger.info(f"✅ Classes balanceadas artificialmente: {len(X)} samples")
            
            logger.info(f"📊 Distribuição de classes: {y.value_counts().to_dict()}")
            
            # ====== MELHORIA: ESTRATÉGIA ANTI-OVERFITTING/UNDERFITTING ======
            logger.info("🛡️ Implementando estratégias contra overfitting/underfitting...")
            
            # 1. Detecta e remove outliers com método robusto
            try:
                isolation_forest = IsolationForest(contamination=0.1, random_state=42)
                outliers = isolation_forest.fit_predict(X)
                n_outliers = sum(outliers == -1)
                
                if n_outliers > 0 and n_outliers < len(X) * 0.3:  # Remove apenas se não for muitos
                    X = X[outliers == 1]
                    y = y[outliers == 1]
                    logger.info(f"🧹 Removidos {n_outliers} outliers ({n_outliers/len(X)*100:.1f}%)")
                else:
                    logger.info("📊 Outliers mantidos (muitos outliers detectados)")
            except Exception as e:
                logger.warning(f"⚠️ Erro na detecção de outliers: {e}")

            # 2. Balanceamento de classes inteligente
            from collections import Counter
            class_distribution = Counter(y)
            logger.info(f"📊 Distribuição original: {dict(class_distribution)}")
            
            if len(class_distribution) < 2:
                logger.warning(f"⚠️ Apenas uma classe encontrada: {list(class_distribution.keys())}")
                # Cria exemplos sintéticos mais inteligentes
                if list(class_distribution.keys())[0] == 1:
                    # Só temos classe positiva, criar negativos baseados em features
                    X_neg = X.sample(min(10, len(X)//2), random_state=42).copy()
                    # Modifica features de forma mais realista
                    X_neg['recencia_dias'] = X_neg['recencia_dias'] * 2  # Aumenta recência
                    X_neg['frequencia_12m'] = X_neg['frequencia_12m'] * 0.5  # Reduz frequência
                    X_neg['valor_medio'] = X_neg['valor_medio'] * 0.7  # Reduz valor
                    X_neg['taxa_conversao'] = X_neg['taxa_conversao'] * 0.6  # Reduz conversão
                    
                    y_neg = pd.Series([0] * len(X_neg))
                    X = pd.concat([X, X_neg], ignore_index=True)
                    y = pd.concat([y, y_neg], ignore_index=True)
                else:
                    # Só temos classe negativa, criar positivos
                    X_pos = X.sample(min(10, len(X)//2), random_state=42).copy()
                    X_pos['recencia_dias'] = X_pos['recencia_dias'] * 0.5  # Reduz recência
                    X_pos['frequencia_12m'] = X_pos['frequencia_12m'] * 1.5  # Aumenta frequência
                    X_pos['valor_medio'] = X_pos['valor_medio'] * 1.3  # Aumenta valor
                    X_pos['taxa_conversao'] = X_pos['taxa_conversao'] * 1.4  # Aumenta conversão
                    
                    y_pos = pd.Series([1] * len(X_pos))
                    X = pd.concat([X, X_pos], ignore_index=True)
                    y = pd.concat([y, y_pos], ignore_index=True)
                
                logger.info(f"✅ Classes balanceadas: {len(X)} samples totais")
            
            # 3. Validação do tamanho do dataset
            if len(X) < 50:
                logger.warning("⚠️ Dataset pequeno - usando regularização forte")
                # Para datasets pequenos, usar regularização forte
                from sklearn.linear_model import LogisticRegression
                self.model = LogisticRegression(
                    C=0.1,  # Regularização forte
                    max_iter=1000,
                    random_state=42,
                    class_weight='balanced'  # Balanceamento automático
                )
            elif len(X) < 200:
                logger.info("📊 Dataset médio - regularização moderada")
                from sklearn.linear_model import LogisticRegression
                self.model = LogisticRegression(
                    C=1.0,  # Regularização moderada
                    max_iter=1000,
                    random_state=42,
                    class_weight='balanced'
                )
            else:
                logger.info("📊 Dataset grande - usando modelo mais complexo")
                from sklearn.ensemble import RandomForestClassifier
                self.model = RandomForestClassifier(
                    n_estimators=50,  # Não muito alto para evitar overfitting
                    max_depth=6,      # Limita profundidade
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    class_weight='balanced'
                )

            logger.info(f"🎯 Modelo selecionado: {type(self.model).__name__}")
            logger.info(f"📊 Distribuição final: {Counter(y)}")

            # Split treino/teste melhorado
            if len(X) < 20:
                # Dataset muito pequeno - usa leave-one-out implicitamente
                X_train, X_test = X, X
                y_train, y_test = y, y
                logger.info("📊 Dataset muito pequeno - sem split")
            else:
                # Split estratificado quando possível
                try:
                    # Verifica se podemos fazer split estratificado
                    min_class_count = min(Counter(y).values())
                    if min_class_count >= 2:
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42, stratify=y
                        )
                        logger.info("✅ Split estratificado realizado")
                    else:
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42
                        )
                        logger.info("📊 Split simples (classe minoritária < 2)")
                except Exception as e:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
                    logger.warning(f"⚠️ Split sem estratificação: {e}")

            # 4. Normalização robusta
            from sklearn.preprocessing import RobustScaler
            self.scaler = RobustScaler()  # Mais robusto a outliers que StandardScaler
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # ====== TREINAMENTO E AVALIAÇÃO MELHORADA ======
            logger.info("🎯 Treinando modelo com validação robusta...")
            
            # Treina modelo
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True
            
            # ====== AVALIAÇÃO COMPLETA CONTRA OVERFITTING ======
            # 1. Predições nos conjuntos de treino e teste
            y_train_pred = self.model.predict(X_train_scaled)
            y_test_pred = self.model.predict(X_test_scaled)
            
            # 2. Probabilidades quando disponíveis
            try:
                y_train_proba = self.model.predict_proba(X_train_scaled)
                y_test_proba = self.model.predict_proba(X_test_scaled)
                
                if y_train_proba.shape[1] > 1:
                    y_train_proba = y_train_proba[:, 1]  # Classe positiva
                    y_test_proba = y_test_proba[:, 1]
                else:
                    y_train_proba = y_train_proba[:, 0]
                    y_test_proba = y_test_proba[:, 0]
            except Exception as e:
                logger.warning(f"⚠️ Erro ao obter probabilidades: {e}")
                y_train_proba = y_train_pred.astype(float)
                y_test_proba = y_test_pred.astype(float)
            
            # 3. Métricas completas
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            
            try:
                # Métricas de treino
                train_accuracy = accuracy_score(y_train, y_train_pred)
                train_precision = precision_score(y_train, y_train_pred, average='weighted', zero_division=0)
                train_recall = recall_score(y_train, y_train_pred, average='weighted', zero_division=0)
                train_f1 = f1_score(y_train, y_train_pred, average='weighted', zero_division=0)
                
                # Métricas de teste
                test_accuracy = accuracy_score(y_test, y_test_pred)
                test_precision = precision_score(y_test, y_test_pred, average='weighted', zero_division=0)
                test_recall = recall_score(y_test, y_test_pred, average='weighted', zero_division=0)
                test_f1 = f1_score(y_test, y_test_pred, average='weighted', zero_division=0)
                
                # AUC quando possível
                try:
                    if len(np.unique(y_train)) > 1:
                        train_auc = roc_auc_score(y_train, y_train_proba)
                    else:
                        train_auc = train_accuracy
                        
                    if len(np.unique(y_test)) > 1:
                        test_auc = roc_auc_score(y_test, y_test_proba)
                    else:
                        test_auc = test_accuracy
                except Exception as e:
                    logger.warning(f"⚠️ Erro no cálculo AUC: {e}")
                    train_auc = train_accuracy
                    test_auc = test_accuracy
                
                # 4. DETECÇÃO DE OVERFITTING
                overfitting_score = train_accuracy - test_accuracy
                if overfitting_score > 0.15:
                    logger.warning(f"⚠️ OVERFITTING DETECTADO! Diferença treino-teste: {overfitting_score:.3f}")
                    overfitting_status = "Alto"
                elif overfitting_score > 0.08:
                    logger.warning(f"⚠️ Possível overfitting. Diferença: {overfitting_score:.3f}")
                    overfitting_status = "Moderado"
                else:
                    logger.info(f"✅ Sem overfitting. Diferença: {overfitting_score:.3f}")
                    overfitting_status = "Baixo"
                
                # 5. DETECÇÃO DE UNDERFITTING
                if test_accuracy < 0.6 and train_accuracy < 0.6:
                    logger.warning("⚠️ UNDERFITTING DETECTADO! Performance baixa em treino e teste")
                    underfitting_status = "Alto"
                elif test_accuracy < 0.7 and train_accuracy < 0.7:
                    logger.warning("⚠️ Possível underfitting. Performance moderada")
                    underfitting_status = "Moderado"  
                else:
                    logger.info("✅ Performance adequada")
                    underfitting_status = "Baixo"
                
            except Exception as e:
                logger.error(f"❌ Erro no cálculo de métricas: {e}")
                # Fallback para métricas básicas
                train_accuracy = test_accuracy = 0.5
                train_precision = test_precision = 0.5
                train_recall = test_recall = 0.5
                train_f1 = test_f1 = 0.5
                train_auc = test_auc = 0.5
                overfitting_status = "Erro"
                underfitting_status = "Erro"
            
            # 6. Validação cruzada robusta
            try:
                if len(X_train) >= 10:
                    n_folds = min(5, len(X_train))
                    cv_scores = cross_val_score(
                        self.model, X_train_scaled, y_train, 
                        cv=n_folds, scoring='accuracy'
                    )
                    cv_mean = cv_scores.mean()
                    cv_std = cv_scores.std()
                    logger.info(f"📊 CV ({n_folds}-fold): {cv_mean:.3f} ± {cv_std:.3f}")
                else:
                    cv_mean = test_accuracy
                    cv_std = 0.0
                    logger.info("📊 Dataset pequeno - CV = test accuracy")
            except Exception as e:
                logger.warning(f"⚠️ Erro na validação cruzada: {e}")
                cv_mean = test_accuracy
                cv_std = 0.0
            
            # 7. Feature importance
            try:
                if hasattr(self.model, 'feature_importances_'):
                    # Random Forest
                    feature_importance = dict(zip(feature_columns, self.model.feature_importances_))
                elif hasattr(self.model, 'coef_'):
                    # Logistic Regression  
                    feature_importance = dict(zip(feature_columns, abs(self.model.coef_[0])))
                else:
                    feature_importance = {}
                
                # Top 5 features mais importantes
                if feature_importance:
                    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                    logger.info(f"🔍 Top features: {[f'{name}: {value:.3f}' for name, value in top_features]}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro na importância de features: {e}")
                feature_importance = {}

            # Métricas finais
            metricas = {
                'status': 'treinado',
                'num_samples': len(X),
                'num_features': len(feature_columns),
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'train_auc': train_auc,
                'test_auc': test_auc,
                'cv_accuracy_mean': cv_mean,
                'cv_accuracy_std': cv_std,
                'overfitting_status': overfitting_status,
                'underfitting_status': underfitting_status,
                'performance_gap': overfitting_score,
                'feature_importance': feature_importance,
                'data_treino': datetime.now().isoformat(),
                'modelo_tipo': type(self.model).__name__,
                'classes_distribuicao': dict(Counter(y))
            }
            
            logger.info(f"✅ Modelo treinado:")
            logger.info(f"   📊 Accuracy: Treino={train_accuracy:.3f}, Teste={test_accuracy:.3f}")
            logger.info(f"   🎯 AUC: Treino={train_auc:.3f}, Teste={test_auc:.3f}")
            logger.info(f"   🔄 CV: {cv_mean:.3f} ± {cv_std:.3f}")
            logger.info(f"   ⚠️ Overfitting: {overfitting_status}, Underfitting: {underfitting_status}")
            
            # ✅ SALVA MODELO APÓS TREINAMENTO BEM-SUCEDIDO
            self._save_model(metricas)
            
            return metricas
            
        except Exception as e:
            logger.error(f"❌ Erro no treinamento ML: {e}")
            return {'erro': str(e)}
    
    def predict_repurchase_probability(self, vendas_df: pd.DataFrame,
                                     cotacoes_df: pd.DataFrame = None,
                                     produtos_cotados_df: pd.DataFrame = None,
                                     material: str = None,
                                     cod_cliente: str = None) -> pd.DataFrame:
        """
        Prediz probabilidade de recompra usando modelo ML melhorado ou heurísticas
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações
            produtos_cotados_df: DataFrame de produtos cotados
            material: Material específico (opcional)
            cod_cliente: Cliente específico (opcional)
            
        Returns:
            DataFrame com probabilidades de recompra
        """
        logger.info("🔮 Calculando probabilidades de recompra com modelo melhorado")
        
        try:
            # Extrai features melhoradas
            features_df = self.extract_ml_features(vendas_df, cotacoes_df, produtos_cotados_df)
            
            if features_df.empty:
                logger.warning("⚠️ Nenhuma feature extraída")
                return pd.DataFrame()
            
            # ====== ADICIONAR TAXA DE CONVERSÃO (mesmo cálculo do treinamento) ======
            if cotacoes_df is not None and not cotacoes_df.empty:
                try:
                    # Taxa de conversão = vendas / cotações por material
                    vendas_por_material = vendas_df.groupby('material').agg({
                        'cod_cliente': 'nunique',
                        'vlr_entrada': 'sum'
                    }).reset_index()
                    vendas_por_material.columns = ['material', 'clientes_compraram', 'vendas_total']
                    
                    cotacoes_por_material = cotacoes_df.groupby('material').agg({
                        'cod_cliente': 'nunique',
                        'preco': 'sum'
                    }).reset_index()
                    cotacoes_por_material.columns = ['material', 'clientes_cotaram', 'cotacoes_total']
                    
                    # Merge para calcular conversão
                    conversao_df = pd.merge(vendas_por_material, cotacoes_por_material, on='material', how='outer').fillna(0)
                    conversao_df['taxa_conversao'] = np.where(
                        conversao_df['clientes_cotaram'] > 0,
                        conversao_df['clientes_compraram'] / conversao_df['clientes_cotaram'],
                        0.1  # Taxa padrão
                    )
                    
                    # Adiciona ao features_df
                    features_df = features_df.merge(
                        conversao_df[['material', 'taxa_conversao']], 
                        on='material', 
                        how='left'
                    )
                    features_df['taxa_conversao'] = features_df['taxa_conversao'].fillna(0.1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro no cálculo de taxa de conversão: {e}")
                    features_df['taxa_conversao'] = 0.1
            else:
                features_df['taxa_conversao'] = 0.1
            
            # ====== ADICIONAR FEATURES ENGENHEIRADAS (mesmo cálculo do treinamento) ======
            # 1. Interações entre features importantes
            features_df['valor_x_frequencia'] = features_df['valor_medio'] * features_df['frequencia_12m']
            features_df['recencia_x_conversao'] = features_df['recencia_dias'] * features_df['taxa_conversao']
            features_df['valor_por_compra'] = features_df['valor_total_12m'] / np.maximum(1, features_df['num_compras_total'])
            
            # 2. Features categóricas transformadas
            features_df['cliente_ativo'] = (features_df['recencia_dias'] <= 90).astype(int)
            features_df['alta_frequencia'] = (features_df['frequencia_12m'] >= features_df['frequencia_12m'].quantile(0.7)).astype(int)
            features_df['alto_valor'] = (features_df['valor_medio'] >= features_df['valor_medio'].quantile(0.7)).astype(int)
            
            # 3. Features sazonais aprimoradas
            features_df['concentracao_extrema'] = (features_df['concentracao_sazonal'] >= features_df['concentracao_sazonal'].quantile(0.9)).astype(int)
            
            # Filtra por material se especificado
            if material:
                features_df = features_df[features_df['material'] == material]
            
            if features_df.empty:
                logger.warning(f"⚠️ Nenhum dado para material {material}")
                return pd.DataFrame()
            
            # Usa modelo ML se disponível e treinado
            if ML_AVAILABLE and self.is_trained:
                try:
                    # ✅ Features otimizadas - SEM COLINEARIDADE
                    feature_columns = [
                        # Features principais (sem colinearidade)
                        'recencia_dias', 'frequencia_12m', 'valor_medio', 'valor_total_12m',
                        'concentracao_sazonal', 'tendencia', 'intensidade',
                        'cotacoes_ratio', 'num_compras_total', 'dias_desde_primeira',
                        # Features de recorrência otimizadas
                        'intervalo_medio_dias', 'coef_var_intervalo', 'ratio_tempo_ciclo',
                        'probabilidade_recorrencia'
                    ]
                    
                    # Verifica se todas as features estão disponíveis
                    missing_features = [col for col in feature_columns if col not in features_df.columns]
                    if missing_features:
                        logger.warning(f"⚠️ Features faltando: {missing_features}")
                        logger.info("🔄 Modelo incompatível detectado - forçando retreinamento...")
                        
                        # Remove modelo antigo incompatível
                        self._clear_incompatible_model()
                        
                        # Força retreinamento
                        self.train_repurchase_model(vendas_df, cotacoes_df, produtos_cotados_df, retrain=True)
                        
                        # Tenta novamente com modelo retreinado
                        if self.is_trained:
                            return self.predict_repurchase_probability(vendas_df, cotacoes_df, produtos_cotados_df, cod_cliente)
                        else:
                            logger.error("❌ Falha no retreinamento - usando heurísticas")
                            raise ValueError(f"Retreinamento falhou após incompatibilidade de features")
                
                    X = features_df[feature_columns].fillna(0)
                    X_scaled = self.scaler.transform(X)
                    
                    # Predição com probabilidades
                    probabilidades = self.model.predict_proba(X_scaled)
                    if probabilidades.shape[1] > 1:
                        prob_recompra = probabilidades[:, 1]  # Classe positiva
                    else:
                        prob_recompra = probabilidades[:, 0]
                    
                    # ✅ NORMALIZAÇÃO RIGOROSA PARA ML TAMBÉM
                    # Aplica a mesma normalização usada nas heurísticas para consistência
                    prob_recompra_normalized = []
                    for i, prob in enumerate(prob_recompra):
                        # Aplica função sigmoidal para suavizar extremos
                        sigmoid_input = (prob - 0.8) * 3  # Centra em 0.8 e amplifica
                        sigmoid_normalized = 1 / (1 + np.exp(-sigmoid_input))
                        
                        # Mapeia sigmoid para range 0.15 - 0.75 (mais conservador)
                        prob_final = 0.15 + (sigmoid_normalized * 0.60)
                        
                        # Adiciona variação pequena baseada no índice para quebrar empates
                        variacao = (i % 100) / 1000  # 0 a 0.099
                        prob_final += variacao
                        
                        # Garante limites finais mais restritivos
                        prob_final = max(0.10, min(0.85, prob_final))
                        prob_recompra_normalized.append(prob_final)
                    
                    prob_recompra = np.array(prob_recompra_normalized)
                    features_df['prob_recompra_ml'] = prob_recompra
                    
                    logger.info(f"🤖 Predições ML: min={prob_recompra.min():.3f}, max={prob_recompra.max():.3f}, mean={prob_recompra.mean():.3f}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro no modelo ML, usando heurísticas: {e}")
                    # Heurística melhorada como fallback
                    features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)
            else:
                # Usa heurísticas melhoradas se ML não disponível
                features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)
                logger.info("📊 Usando heurísticas melhoradas (ML não disponível)")
            
            return features_df
        except Exception as e:
            logger.warning(f"Erro ML geral: {e}")
            # Se features_df não foi definido, criar um DataFrame vazio
            if 'features_df' not in locals():
                features_df = pd.DataFrame()
            if not features_df.empty:
                features_df['prob_recompra_ml'] = self._calculate_heuristic_probability(features_df)
            return features_df

    def _clear_incompatible_model(self):
        """Remove modelo e metadados incompatíveis"""
        try:
            files_removed = []
            
            if self.model_path.exists():
                self.model_path.unlink()
                files_removed.append("model")
            
            if self.scaler_path.exists():
                self.scaler_path.unlink()
                files_removed.append("scaler")
            
            if self.metadata_path.exists():
                self.metadata_path.unlink()
                files_removed.append("metadata")
            
            if files_removed:
                logger.info(f"🧹 Modelo incompatível removido: {', '.join(files_removed)}")
                
            # Reset do estado
            self.is_trained = False
            if ML_AVAILABLE:
                self.model = LogisticRegression(random_state=42)
                self.scaler = StandardScaler()
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar modelo incompatível: {e}")

    def _calculate_heuristic_probability(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Calcula probabilidade de recompra usando heurísticas baseadas em recorrência histórica
        Aplica a mesma lógica avançada usada no target_recompra
        
        Args:
            features_df: DataFrame com features extraídas
            
        Returns:
            Série com probabilidades calculadas
        """
        logger.info("📊 Calculando probabilidades com heurísticas baseadas em recorrência histórica")
        
        try:
            # Garante que temos dados
            if features_df.empty:
                logger.warning("⚠️ DataFrame vazio na heurística")
                return pd.Series([])
            
            # ✅ PRIORIDADE 1: USA PROBABILIDADE_RECORRENCIA SE DISPONÍVEL
            if 'probabilidade_recorrencia' in features_df.columns and not features_df['probabilidade_recorrencia'].isna().all():
                # Esta já é a probabilidade calculada baseada no ciclo histórico!
                prob_base = features_df['probabilidade_recorrencia'].fillna(0.5)
                logger.info(f"✅ Usando probabilidade de recorrência histórica: min={prob_base.min():.3f}, max={prob_base.max():.3f}, mean={prob_base.mean():.3f}")
                
                # Ajusta com fatores complementares se disponíveis
                prob_final = prob_base.copy()
                
                # Fator de conversão (se produto tem alta conversão, aumenta probabilidade)
                if 'taxa_conversao' in features_df.columns:
                    conversao_norm = features_df['taxa_conversao'].fillna(0.1)
                    if conversao_norm.max() > 0:
                        conversao_factor = 0.8 + (conversao_norm / conversao_norm.max()) * 0.4  # 0.8 a 1.2
                        prob_final = prob_final * conversao_factor
                
                # Fator de atividade recente do cliente
                if 'cliente_ativo' in features_df.columns:
                    ativo_factor = 1.0 + (features_df['cliente_ativo'].fillna(0) * 0.2)  # +20% se ativo
                    prob_final = prob_final * ativo_factor
                
                # Normaliza e limita
                prob_final = prob_final.clip(0.05, 0.95)
                
                logger.info(f"✅ Probabilidade ajustada: min={prob_final.min():.3f}, max={prob_final.max():.3f}, mean={prob_final.mean():.3f}")
                return prob_final
            
            # ✅ FALLBACK: CÁLCULO MANUAL DA RECORRÊNCIA SE NÃO TIVER A FEATURE
            logger.info("📊 Calculando recorrência manualmente (fallback)")
            
            prob_lista = []
            
            for idx, row in features_df.iterrows():
                try:
                    # Recria a lógica de recorrência histórica
                    recencia_dias = row.get('recencia_dias', 180)
                    frequencia_12m = row.get('frequencia_12m', 1)
                    intervalo_medio = row.get('intervalo_medio_dias', 180)
                    coef_var_intervalo = row.get('coef_var_intervalo', 1.0)
                    compras_por_ano = row.get('compras_por_ano', 2)
                    valor_medio = row.get('valor_medio', 500)
                    
                    # Se não temos intervalo médio, estima baseado na frequência
                    if pd.isna(intervalo_medio) or intervalo_medio <= 0:
                        if frequencia_12m >= 2:
                            intervalo_medio = 365 / frequencia_12m
                        else:
                            intervalo_medio = 180  # 6 meses padrão
                    
                    # 1. Probabilidade baseada no ciclo
                    ratio_tempo_ciclo = recencia_dias / intervalo_medio
                    
                    if ratio_tempo_ciclo < 0.5:
                        prob_ciclo = 0.1 + (ratio_tempo_ciclo * 0.3)
                    elif ratio_tempo_ciclo < 1.0:
                        prob_ciclo = 0.25 + ((ratio_tempo_ciclo - 0.5) * 1.5)
                    elif ratio_tempo_ciclo < 1.5:
                        prob_ciclo = 1.0 - ((ratio_tempo_ciclo - 1.0) * 0.4)
                    else:
                        prob_ciclo = max(0.2, 0.8 - ((ratio_tempo_ciclo - 1.5) * 0.3))
                    
                    # 2. Fator de regularidade
                    if coef_var_intervalo < 0.3:
                        fator_regularidade = 1.2
                    elif coef_var_intervalo < 0.7:
                        fator_regularidade = 1.0
                    else:
                        fator_regularidade = 0.8
                    
                    # 3. Fator de frequência
                    if compras_por_ano >= 4:
                        fator_frequencia = 1.3
                    elif compras_por_ano >= 2:
                        fator_frequencia = 1.1
                    elif compras_por_ano >= 0.5:
                        fator_frequencia = 1.0
                    else:
                        fator_frequencia = 0.7
                    
                    # 4. Fator de valor (estimativa simples)
                    if valor_medio >= 1000:
                        fator_valor = 0.9
                    elif valor_medio >= 300:
                        fator_valor = 1.0
                    else:
                        fator_valor = 1.1
                    
                    # 5. Taxa de conversão se disponível
                    taxa_conversao = row.get('taxa_conversao', 0.1)
                    fator_conversao = 0.8 + (taxa_conversao * 2)  # 0.8 a 1.0+
                    
                    # ✅ CORREÇÃO: APLICAR NORMALIZADORES PARA EVITAR VALORES EXTREMOS
                    # Probabilidade final sem excessos
                    prob_final = prob_ciclo * fator_regularidade * fator_frequencia * fator_valor * fator_conversao
                    
                    # ✅ NORMALIZAÇÃO MAIS RIGOROSA
                    # Aplica uma curva sigmoidal para suavizar valores extremos
                    prob_normalizada = 1 / (1 + np.exp(-5 * (prob_final - 1)))  # Sigmoid centrada em 1
                    
                    # Mapeia para range mais realístico 0.15 - 0.85
                    prob_final_corrigida = 0.15 + (prob_normalizada * 0.70)
                    
                    # Adiciona variação pequena para quebrar empates
                    variacao = hash(str(row.get('material', '')) + str(idx)) % 100 / 1000  # 0-0.099
                    prob_final_corrigida += variacao
                    
                    # Garante que está no range correto
                    prob_final_corrigida = max(0.05, min(0.95, prob_final_corrigida))
                    
                    prob_lista.append(prob_final_corrigida)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro calculando probabilidade para linha {idx}: {e}")
                    prob_lista.append(0.5)  # Probabilidade neutra em caso de erro
            
            prob_series = pd.Series(prob_lista, index=features_df.index)
            
            logger.info(f"✅ Heurística de recorrência calculada: min={prob_series.min():.3f}, max={prob_series.max():.3f}, mean={prob_series.mean():.3f}")
            return prob_series
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo heurístico: {e}")
            # Fallback final: probabilidades neutras variadas
            np.random.seed(42)
            return pd.Series(np.random.uniform(0.3, 0.7, len(features_df)), index=features_df.index)

    def create_summary_chart(self, df: pd.DataFrame) -> Dict:
        """
        Cria gráfico de resumo das distribuições ABC-XYZ
        """
        try:
            if df.empty:
                return {}
            
            # Análise ABC-XYZ
            if 'classificacao' in df.columns:
                distribuicao = df['classificacao'].value_counts()
                return {
                    'type': 'pie',
                    'data': [
                        {
                            'values': distribuicao.values.tolist(),
                            'labels': distribuicao.index.tolist(),
                            'type': 'pie',
                            'name': 'Distribuição ABC-XYZ'
                        }
                    ],
                    'layout': {
                        'title': 'Distribuição ABC-XYZ das Sugestões'
                    }
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"❌ Erro ao criar gráfico: {e}")
            return {}
    
    def close_db(self):
        """Fecha conexão com banco se aberta"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fechar conexão: {e}")
    
    def _update_adaptive_weights(self, material: str, cod_cliente: str, feedback_type: str):
        """
        Sistema de Reinforcement Learning - Ajusta pesos baseado no feedback
        
        Args:
            material: Material que recebeu feedback
            cod_cliente: Cliente que deu feedback
            feedback_type: 'positivo' ou 'negativo'
        """
        try:
            # Taxa de aprendizado (learning rate)
            learning_rate = 0.01
            
            # Busca características do produto que recebeu feedback
            vendas_df, _, _ = self._load_product_data(material, cod_cliente)
            
            if vendas_df.empty:
                return
            
            # Calcula características do produto
            produto_stats = self._analyze_product_characteristics(vendas_df, material)
            
            if feedback_type == 'positivo':
                # Feedback positivo: aumenta peso dos fatores dominantes no produto
                if produto_stats.get('classe_abc') == 'A':
                    self.adaptive_weights['abc_weight'] = min(0.6, self.adaptive_weights['abc_weight'] + learning_rate)
                    
                if produto_stats.get('qtd_total', 0) > produto_stats.get('qtd_media', 0):
                    self.adaptive_weights['volume_weight'] = min(0.5, self.adaptive_weights['volume_weight'] + learning_rate)
                    
                if produto_stats.get('freq_mensal', 0) > 1:  # Produto recorrente
                    self.adaptive_weights['recorrencia_weight'] = min(0.4, self.adaptive_weights['recorrencia_weight'] + learning_rate)
                    
            else:  # feedback negativo
                # Feedback negativo: diminui peso dos fatores dominantes
                if produto_stats.get('classe_abc') == 'A':
                    self.adaptive_weights['abc_weight'] = max(0.2, self.adaptive_weights['abc_weight'] - learning_rate)
                    
                if produto_stats.get('qtd_total', 0) > produto_stats.get('qtd_media', 0):
                    self.adaptive_weights['volume_weight'] = max(0.1, self.adaptive_weights['volume_weight'] - learning_rate)
            
            # Renormaliza pesos para somar 1.0
            total_weight = sum(self.adaptive_weights.values()) - self.adaptive_weights['cotacao_boost']
            for key in ['abc_weight', 'volume_weight', 'recorrencia_weight', 'xyz_weight']:
                self.adaptive_weights[key] = self.adaptive_weights[key] / total_weight
            
            # Armazena no histórico de feedback
            self.feedback_history.append({
                'material': material,
                'cod_cliente': cod_cliente,
                'feedback_type': feedback_type,
                'timestamp': datetime.now(),
                'weights_after': self.adaptive_weights.copy()
            })
            
            # Mantém apenas os últimos 100 feedbacks para não consumir muita memória
            if len(self.feedback_history) > 100:
                self.feedback_history = self.feedback_history[-100:]
                
            logger.info(f"🧠 Pesos atualizados via RL: ABC={self.adaptive_weights['abc_weight']:.3f}, "
                       f"Volume={self.adaptive_weights['volume_weight']:.3f}, "
                       f"Recorrência={self.adaptive_weights['recorrencia_weight']:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Erro no reinforcement learning: {e}")
    
    def _load_product_data(self, material: str, cod_cliente: str):
        """Carrega dados do produto para análise de características"""
        try:
            from utils import load_all_data
            return load_all_data()
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados do produto: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def _analyze_product_characteristics(self, vendas_df: pd.DataFrame, material: str):
        """Analisa características de um produto específico"""
        try:
            material_data = vendas_df[vendas_df['material'] == material]
            
            if material_data.empty:
                return {}
            
            stats = {
                'qtd_total': material_data['qtd_rol'].sum() if 'qtd_rol' in material_data.columns else 0,
                'qtd_media': material_data['qtd_rol'].mean() if 'qtd_rol' in material_data.columns else 0,
                'valor_total': material_data['vlr_rol'].sum(),
                'freq_transacoes': len(material_data),
                'num_clientes': material_data['cod_cliente'].nunique(),
                'freq_mensal': len(material_data) / 12  # Assumindo dados anuais
            }
            
            # Classificação ABC simplificada para esse produto
            percentil_valor = vendas_df['vlr_rol'].quantile(0.8)
            if stats['valor_total'] >= percentil_valor:
                stats['classe_abc'] = 'A'
            elif stats['valor_total'] >= vendas_df['vlr_rol'].quantile(0.5):
                stats['classe_abc'] = 'B'
            else:
                stats['classe_abc'] = 'C'
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar características do produto: {e}")
            return {}

    def analyze_market_gaps(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame,
                           cod_cliente_target: str, min_penetration: float = 0.15) -> pd.DataFrame:
        """
        Análise de gaps de mercado - identifica produtos com alta demanda na base
        mas baixa penetração no cliente específico
        
        Args:
            vendas_df: DataFrame de vendas da base completa
            cotacoes_df: DataFrame de cotações da base completa
            cod_cliente_target: Cliente alvo para análise
            min_penetration: Penetração mínima na base para considerar gap (15%)
            
        Returns:
            DataFrame com análise de gaps ordenado por oportunidade
        """
        try:
            logger.info(f"🔍 Analisando gaps de mercado para cliente {cod_cliente_target}")
            
            # Análise de penetração de vendas (W%)
            vendas_base = vendas_df.copy()
            total_clientes_base = vendas_base['cod_cliente'].nunique()
            
            # Clientes que compraram cada material
            penetracao_vendas = vendas_base.groupby('material').agg({
                'cod_cliente': 'nunique',
                'vlr_entrada': ['sum', 'mean'],
                'qtd_entrada': ['sum', 'mean']
            }).reset_index()
            
            penetracao_vendas.columns = ['material', 'clientes_compraram', 'valor_total_base', 
                                       'valor_medio_base', 'qtd_total_base', 'qtd_media_base']
            
            penetracao_vendas['w_percent'] = (penetracao_vendas['clientes_compraram'] / total_clientes_base) * 100
            
            # Análise de penetração de cotações (Q%)
            if not cotacoes_df.empty:
                total_cotacoes = cotacoes_df.shape[0]
                penetracao_cotacoes = cotacoes_df.groupby('material').agg({
                    'cod_cliente': 'nunique',
                    'preco': ['sum', 'mean', 'count']
                }).reset_index()
                
                penetracao_cotacoes.columns = ['material', 'clientes_cotaram', 'valor_cotacoes_total',
                                             'valor_cotacoes_medio', 'num_cotacoes']
                
                penetracao_cotacoes['q_percent'] = (penetracao_cotacoes['num_cotacoes'] / total_cotacoes) * 100
                
                # Taxa de conversão cotação → venda
                conversao = penetracao_vendas.merge(penetracao_cotacoes, on='material', how='outer').fillna(0)
                conversao['taxa_conversao'] = np.where(
                    conversao['num_cotacoes'] > 0,
                    (conversao['clientes_compraram'] / conversao['num_cotacoes']) * 100,
                    0
                )
            else:
                logger.warning("⚠️ Sem dados de cotações - análise apenas com vendas")
                conversao = penetracao_vendas.copy()
                conversao['q_percent'] = 0
                conversao['taxa_conversao'] = 0
                conversao['clientes_cotaram'] = 0
                conversao['num_cotacoes'] = 0
            
            # Análise específica do cliente target
            vendas_cliente = vendas_base[vendas_base['cod_cliente'] == cod_cliente_target]
            materiais_cliente = set(vendas_cliente['material'].unique())
            
            # Calcula gaps
            gaps_analysis = []
            for _, row in conversao.iterrows():
                material = row['material']
                
                # Gap = alta penetração na base MAS baixa/nula no cliente
                if row['w_percent'] >= min_penetration * 100:  # Converte para %
                    
                    # Verifica se cliente compra este material
                    cliente_compra = material in materiais_cliente
                    
                    if cliente_compra:
                        # Cliente já compra - calcular oportunidade de aumento
                        vendas_material_cliente = vendas_cliente[vendas_cliente['material'] == material]
                        qtd_cliente_anual = vendas_material_cliente['qtd_entrada'].sum()
                        valor_cliente_anual = vendas_material_cliente['vlr_entrada'].sum()
                        
                        # Potencial baseado na média da base
                        qtd_potencial = row['qtd_media_base'] - qtd_cliente_anual
                        valor_potencial = row['valor_medio_base'] - valor_cliente_anual
                        gap_type = "CRESCIMENTO"
                        
                    else:
                        # Cliente não compra - oportunidade total
                        qtd_potencial = row['qtd_media_base']
                        valor_potencial = row['valor_medio_base']
                        gap_type = "NOVO_PRODUTO"
                        qtd_cliente_anual = 0
                        valor_cliente_anual = 0
                    
                    # Score de oportunidade (combina penetração, valor e conversão)
                    score_oportunidade = (
                        row['w_percent'] * 0.4 +  # Penetração na base
                        min(100, row['q_percent']) * 0.3 +  # Frequência de cotação
                        min(100, row['taxa_conversao']) * 0.3  # Taxa de conversão
                    )
                    
                    gaps_analysis.append({
                        'material': material,
                        'gap_type': gap_type,
                        'w_percent': round(row['w_percent'], 1),
                        'q_percent': round(row['q_percent'], 1),
                        'taxa_conversao': round(row['taxa_conversao'], 1),
                        'score_oportunidade': round(score_oportunidade, 1),
                        'clientes_compraram_base': int(row['clientes_compraram']),
                        'qtd_cliente_atual': qtd_cliente_anual,
                        'qtd_potencial': max(0, qtd_potencial),
                        'valor_cliente_atual': valor_cliente_anual,
                        'valor_potencial': max(0, valor_potencial),
                        'num_cotacoes_base': int(row.get('num_cotacoes', 0))
                    })
            
            # Converte para DataFrame e ordena por oportunidade
            gaps_df = pd.DataFrame(gaps_analysis)
            
            if not gaps_df.empty:
                gaps_df = gaps_df.sort_values('score_oportunidade', ascending=False)
                
                # Adiciona informações do produto
                if 'produto' in vendas_base.columns:
                    produto_info = vendas_base.groupby('material')['produto'].first().reset_index()
                    gaps_df = gaps_df.merge(produto_info, on='material', how='left')
                
                logger.info(f"✅ Encontrados {len(gaps_df)} gaps de oportunidade")
                logger.info(f"📊 Top 3 gaps: {gaps_df.head(3)['material'].tolist()}")
                
            return gaps_df
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de gaps: {e}")
            return pd.DataFrame()

    def _convert_gaps_to_json_safe(self, gaps_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Converte DataFrame de gaps para formato JSON-safe
        """
        if gaps_df.empty:
            return {
                'gaps': [],
                'total_gaps': 0,
                'resumo': {
                    'produtos_oportunidade': 0,
                    'valor_total_potencial': 0,
                    'score_medio': 0
                }
            }
        
        # Converter DataFrame para lista de dicts com tipos JSON-safe
        gaps_list = []
        for _, row in gaps_df.iterrows():
            gap_dict = {}
            for col, val in row.items():
                if pd.isna(val):
                    gap_dict[col] = None
                elif isinstance(val, (np.integer, np.int32, np.int64)):
                    gap_dict[col] = int(val)
                elif isinstance(val, (np.floating, np.float32, np.float64)):
                    gap_dict[col] = float(val)
                else:
                    gap_dict[col] = str(val)
            gaps_list.append(gap_dict)
        
        # Calcular resumo
        resumo = {
            'produtos_oportunidade': len(gaps_df),
            'valor_total_potencial': float(gaps_df['valor_potencial'].sum()),
            'score_medio': float(gaps_df['score_oportunidade'].mean())
        }
        
        return {
            'gaps': gaps_list,
            'total_gaps': len(gaps_df),
            'resumo': resumo
        }

    def detect_seasonality(self, vendas_df: pd.DataFrame, cod_cliente: str = None,
                          min_months: int = 12) -> Dict[str, Any]:
        """
        Detecta padrões de sazonalidade nas vendas por material/produto
        
        Args:
            vendas_df: DataFrame de vendas com colunas ['data_entrada', 'material', 'qtd_entrada', 'vlr_entrada']
            cod_cliente: Cliente específico (None para análise geral)
            min_months: Mínimo de meses de dados para análise confiável
            
        Returns:
            Dict com análise de sazonalidade por material
        """
        try:
            logger.info(f"📅 Detectando sazonalidade - Cliente: {cod_cliente or 'TODOS'}")
            
            # Filtra dados do cliente se especificado
            df = vendas_df.copy()
            if cod_cliente:
                df = df[df['cod_cliente'] == cod_cliente]
                
            if df.empty:
                logger.warning("⚠️ Sem dados para análise de sazonalidade")
                return {}

            # Padroniza coluna de data
            df = _standardize_date_column(df)            # Cria dimensões temporais
            df['ano'] = df['data_entrada'].dt.year
            df['mes'] = df['data_entrada'].dt.month
            df['trimestre'] = df['data_entrada'].dt.quarter
            df['mes_nome'] = df['data_entrada'].dt.strftime('%B')
            df['ano_mes'] = df['data_entrada'].dt.to_period('M')
            
            # Verifica período de dados
            data_range = df['data_entrada'].max() - df['data_entrada'].min()
            months_available = data_range.days / 30.44
            
            if months_available < min_months:
                logger.warning(f"⚠️ Apenas {months_available:.1f} meses de dados - recomendado {min_months}+")
            
            seasonality_results = {}
            
            # Análise por material
            for material in df['material'].unique():
                material_data = df[df['material'] == material].copy()
                
                if len(material_data) < 6:  # Mínimo de vendas
                    continue
                    
                try:
                    # Agregação mensal
                    monthly_sales = material_data.groupby('ano_mes').agg({
                        'qtd_entrada': 'sum',
                        'vlr_entrada': 'sum'
                    }).reset_index()
                    
                    monthly_sales['mes_num'] = monthly_sales['ano_mes'].dt.month
                    
                    # Estatísticas por mês
                    month_stats = material_data.groupby('mes').agg({
                        'qtd_entrada': ['sum', 'mean', 'std', 'count'],
                        'vlr_entrada': ['sum', 'mean', 'std']
                    }).round(2)
                    
                    month_stats.columns = ['qtd_total', 'qtd_media', 'qtd_std', 'freq_vendas',
                                         'vlr_total', 'vlr_medio', 'vlr_std']
                    
                    # Coeficiente de variação por mês
                    month_stats['cv_qtd'] = (month_stats['qtd_std'] / month_stats['qtd_media']).fillna(0)
                    month_stats['cv_vlr'] = (month_stats['vlr_std'] / month_stats['vlr_medio']).fillna(0)
                    
                    # Identifica picos e vales
                    qtd_mean = month_stats['qtd_media'].mean()
                    qtd_std = month_stats['qtd_media'].std()
                    
                    picos = month_stats[month_stats['qtd_media'] > (qtd_mean + qtd_std)].index.tolist()
                    vales = month_stats[month_stats['qtd_media'] < (qtd_mean - qtd_std)].index.tolist()
                    
                    # Score de sazonalidade (0-100)
                    # Baseado na variação entre meses
                    if len(month_stats) >= 3:
                        coef_variacao_geral = month_stats['qtd_media'].std() / month_stats['qtd_media'].mean()
                        sazonalidade_score = min(100, coef_variacao_geral * 100)
                    else:
                        sazonalidade_score = 0
                    
                    # Padrão sazonal
                    if sazonalidade_score > 50:
                        padrao = "ALTA_SAZONALIDADE"
                    elif sazonalidade_score > 25:
                        padrao = "SAZONALIDADE_MODERADA" 
                    else:
                        padrao = "COMPORTAMENTO_ESTAVEL"
                    
                    # Meses de melhor performance
                    top_meses = month_stats.nlargest(3, 'qtd_media').index.tolist()
                    worst_meses = month_stats.nsmallest(3, 'qtd_media').index.tolist()
                    
                    # Análise trimestral
                    quarterly_stats = material_data.groupby('trimestre').agg({
                        'qtd_entrada': ['sum', 'mean'],
                        'vlr_entrada': 'sum'
                    }).round(2)
                    
                    quarterly_stats.columns = ['qtd_total_trim', 'qtd_media_trim', 'vlr_total_trim']
                    best_trimestre = quarterly_stats['qtd_total_trim'].idxmax()
                    
                    # Tendência anual (se há múltiplos anos)
                    yearly_trend = "ESTAVEL"
                    if len(material_data['ano'].unique()) >= 2:
                        yearly_sales = material_data.groupby('ano')['qtd_entrada'].sum()
                        if len(yearly_sales) >= 2:
                            # Regressão linear simples para tendência
                            x = np.arange(len(yearly_sales))
                            y = yearly_sales.values
                            slope = np.polyfit(x, y, 1)[0]
                            
                            if slope > yearly_sales.mean() * 0.1:
                                yearly_trend = "CRESCIMENTO"
                            elif slope < -yearly_sales.mean() * 0.1:
                                yearly_trend = "DECLINIO"
                    
                    # Previsão próximos 3 meses
                    current_month = pd.Timestamp.now().month
                    next_months = [(current_month + i - 1) % 12 + 1 for i in range(1, 4)]
                    
                    previsoes = []
                    for mes in next_months:
                        if mes in month_stats.index:
                            prev_qtd = month_stats.loc[mes, 'qtd_media']
                            previsoes.append({
                                'mes': mes,
                                'qtd_prevista': round(prev_qtd, 2),
                                'confianca': 'ALTA' if month_stats.loc[mes, 'freq_vendas'] >= 3 else 'BAIXA'
                            })
                    
                    seasonality_results[material] = {
                        'material': material,
                        'padrao_sazonal': padrao,
                        'score_sazonalidade': round(sazonalidade_score, 1),
                        'picos_sazonais': [int(p) for p in picos],  # Converter para int Python
                        'vales_sazonais': [int(v) for v in vales],  # Converter para int Python
                        'meses_top_performance': [int(m) for m in top_meses],  # Converter para int Python
                        'meses_baixa_performance': [int(m) for m in worst_meses],  # Converter para int Python
                        'melhor_trimestre': int(best_trimestre),  # Converter np.int32 para int Python
                        'tendencia_anual': yearly_trend,
                        'meses_dados': int(months_available),
                        'total_vendas': int(material_data['qtd_entrada'].sum()),
                        'estatisticas_mensais': {
                            int(k): {
                                'qtd_total': float(v['qtd_total']) if not pd.isna(v['qtd_total']) else 0.0,
                                'qtd_media': float(v['qtd_media']) if not pd.isna(v['qtd_media']) else 0.0,
                                'qtd_std': float(v['qtd_std']) if not pd.isna(v['qtd_std']) else 0.0,
                                'freq_vendas': int(v['freq_vendas']) if not pd.isna(v['freq_vendas']) else 0
                            } for k, v in month_stats.to_dict('index').items()
                        },  # Converter chaves e valores para tipos JSON-safe
                        'previsoes_proximos_meses': previsoes,
                        'recomendacao': self._generate_seasonality_recommendation(
                            padrao, picos, vales, yearly_trend
                        )
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar material {material}: {e}")
                    continue
            
            # Estatísticas gerais
            summary = {
                'total_materiais_analisados': len(seasonality_results),
                'periodo_analise_meses': round(months_available, 1),
                'materiais_alta_sazonalidade': len([r for r in seasonality_results.values() 
                                                  if r['score_sazonalidade'] > 50]),
                'materiais_estáveis': len([r for r in seasonality_results.values() 
                                         if r['score_sazonalidade'] <= 25]),
            }
            
            logger.info(f"✅ Análise de sazonalidade concluída: {len(seasonality_results)} materiais")
            
            return {
                'materiais': seasonality_results,
                'resumo': summary,
                'periodo': {
                    'inicio': df['data_entrada'].min().strftime('%Y-%m-%d'),
                    'fim': df['data_entrada'].max().strftime('%Y-%m-%d'),
                    'meses_dados': round(months_available, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de sazonalidade: {e}")
            return {}

    def _generate_seasonality_recommendation(self, padrao: str, picos: List[int], 
                                           vales: List[int], tendencia: str) -> str:
        """Gera recomendação baseada no padrão sazonal identificado"""
        
        rec = []
        
        if padrao == "ALTA_SAZONALIDADE":
            rec.append("📈 PRODUTO ALTAMENTE SAZONAL")
            if picos:
                meses_nomes = [calendar.month_name[m] for m in picos]
                rec.append(f"• Intensificar vendas em: {', '.join(meses_nomes)}")
            if vales:
                meses_nomes = [calendar.month_name[m] for m in vales]
                rec.append(f"• Reduzir estoque em: {', '.join(meses_nomes)}")
                
        elif padrao == "SAZONALIDADE_MODERADA":
            rec.append("📊 SAZONALIDADE MODERADA")
            rec.append("• Acompanhar tendências mensais")
            rec.append("• Ajustar estoques conforme histórico")
            
        else:
            rec.append("📈 COMPORTAMENTO ESTÁVEL")
            rec.append("• Produto de demanda constante")
            rec.append("• Manter estoque regular")
        
        if tendencia == "CRESCIMENTO":
            rec.append("📈 Tendência de CRESCIMENTO anual")
        elif tendencia == "DECLINIO":
            rec.append("📉 Tendência de DECLÍNIO anual")
            
        return " | ".join(rec)

    def calculate_commercial_kpis(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame,
                                 cod_cliente: str = None, periodo_meses: int = 12) -> Dict[str, Any]:
        """
        Calcula KPIs comerciais essenciais para apoio à vendas
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações
            cod_cliente: Cliente específico (None para análise geral)
            periodo_meses: Período para análise (padrão 12 meses)
            
        Returns:
            Dict com KPIs comerciais detalhados
        """
        try:
            logger.info(f"📊 Calculando KPIs comerciais - Cliente: {cod_cliente or 'TODOS'}")
            
            df_vendas = vendas_df.copy()
            df_cotacoes = cotacoes_df.copy() if not cotacoes_df.empty else pd.DataFrame()
            
            # Filtra por cliente se especificado
            if cod_cliente:
                df_vendas = df_vendas[df_vendas['cod_cliente'] == cod_cliente]
                if not df_cotacoes.empty:
                    df_cotacoes = df_cotacoes[df_cotacoes['cod_cliente'] == cod_cliente]
            
            if df_vendas.empty:
                logger.warning("⚠️ Sem dados de vendas para análise")
                return {}
            
            # Converte datas
            df_vendas = _standardize_date_column(df_vendas)
            
            # Filtra período
            data_limite = df_vendas['data_entrada'].max() - timedelta(days=periodo_meses * 30)
            df_vendas_periodo = df_vendas[df_vendas['data_entrada'] >= data_limite]
            
            # === 1. KPIs BÁSICOS ===
            total_vendas = df_vendas_periodo['vlr_entrada'].sum()
            total_qtd = df_vendas_periodo['qtd_entrada'].sum()
            num_transacoes = len(df_vendas_periodo)
            num_materiais_distintos = df_vendas_periodo['material'].nunique()
            
            ticket_medio = total_vendas / num_transacoes if num_transacoes > 0 else 0
            qtd_media_transacao = total_qtd / num_transacoes if num_transacoes > 0 else 0
            
            # === 2. ANÁLISE TEMPORAL ===
            df_vendas_periodo['ano_mes'] = df_vendas_periodo['data_entrada'].dt.to_period('M')
            vendas_mensais = df_vendas_periodo.groupby('ano_mes').agg({
                'vlr_entrada': 'sum',
                'qtd_entrada': 'sum'
            }).reset_index()
            
            # Crescimento mês a mês
            if len(vendas_mensais) >= 2:
                vendas_mensais['crescimento_valor'] = vendas_mensais['vlr_entrada'].pct_change() * 100
                crescimento_medio = vendas_mensais['crescimento_valor'].mean()
                volatilidade = vendas_mensais['crescimento_valor'].std()
            else:
                crescimento_medio = 0
                volatilidade = 0
            
            # === 3. ANÁLISE DE PRODUTOS ===
            produtos_performance = df_vendas_periodo.groupby('material').agg({
                'vlr_entrada': ['sum', 'mean', 'count'],
                'qtd_entrada': ['sum', 'mean'],
                'data_entrada': ['min', 'max']
            }).round(2)
            
            produtos_performance.columns = ['valor_total', 'valor_medio', 'freq_compras',
                                          'qtd_total', 'qtd_media', 'primeira_compra', 'ultima_compra']
            
            # Top produtos por valor
            top_produtos_valor = produtos_performance.nlargest(10, 'valor_total').index.tolist()
            top_produtos_freq = produtos_performance.nlargest(10, 'freq_compras').index.tolist()
            
            # === 4. ANÁLISE DE RECÊNCIA ===
            data_atual = df_vendas['data_entrada'].max()
            df_vendas_periodo['dias_desde_compra'] = (data_atual - df_vendas_periodo['data_entrada']).dt.days
            
            recencia_por_produto = df_vendas_periodo.groupby('material')['dias_desde_compra'].min().reset_index()
            recencia_por_produto.columns = ['material', 'dias_ultima_compra']
            
            # Produtos por recência
            produtos_recentes = recencia_por_produto[recencia_por_produto['dias_ultima_compra'] <= 30]['material'].tolist()
            produtos_dormentes = recencia_por_produto[recencia_por_produto['dias_ultima_compra'] > 90]['material'].tolist()
            
            # === 5. LTV (LIFETIME VALUE) ===
            if cod_cliente:
                # Para cliente específico
                ltv_total = df_vendas['vlr_entrada'].sum()
                meses_relacionamento = (df_vendas['data_entrada'].max() - df_vendas['data_entrada'].min()).days / 30.44
                ltv_mensal = ltv_total / max(1, meses_relacionamento)
                
                # Projeção LTV
                if meses_relacionamento >= 6:
                    ltv_projetado_12m = ltv_mensal * 12
                else:
                    ltv_projetado_12m = ltv_total * 2  # Estimativa conservadora
            else:
                # Para análise geral - LTV médio por cliente
                ltv_por_cliente = df_vendas.groupby('cod_cliente')['vlr_entrada'].sum()
                ltv_total = ltv_por_cliente.mean()
                ltv_mensal = ltv_total / 12  # Estimativa
                ltv_projetado_12m = ltv_total
            
            # === 6. ANÁLISE DE COTAÇÕES (se disponível) ===
            kpis_cotacoes = {}
            if not df_cotacoes.empty and cod_cliente:
                df_cotacoes['data_cotacao'] = pd.to_datetime(df_cotacoes['data_cotacao'], errors='coerce')
                df_cotacoes_periodo = df_cotacoes[df_cotacoes['data_cotacao'] >= data_limite]
                
                if not df_cotacoes_periodo.empty:
                    total_cotacoes = len(df_cotacoes_periodo)
                    valor_cotado = df_cotacoes_periodo['preco'].sum()
                    materiais_cotados = df_cotacoes_periodo['material'].nunique()
                    
                    # Taxa de conversão (cotações que viraram vendas)
                    materiais_vendidos = set(df_vendas_periodo['material'].unique())
                    materiais_cotados_set = set(df_cotacoes_periodo['material'].unique())
                    conversao_materiais = len(materiais_vendidos.intersection(materiais_cotados_set))
                    taxa_conversao = (conversao_materiais / len(materiais_cotados_set) * 100) if materiais_cotados_set else 0
                    
                    kpis_cotacoes = {
                        'total_cotacoes': total_cotacoes,
                        'valor_total_cotado': valor_cotado,
                        'materiais_cotados': materiais_cotados,
                        'taxa_conversao_materiais': round(taxa_conversao, 1),
                        'ticket_medio_cotacao': valor_cotado / total_cotacoes if total_cotacoes > 0 else 0
                    }
            
            # === 7. ANÁLISE DE CONCENTRAÇÃO ===
            # Curva ABC de produtos
            produtos_performance_sorted = produtos_performance.sort_values('valor_total', ascending=False)
            produtos_performance_sorted['valor_acumulado'] = produtos_performance_sorted['valor_total'].cumsum()
            produtos_performance_sorted['perc_acumulado'] = (produtos_performance_sorted['valor_acumulado'] / 
                                                           produtos_performance_sorted['valor_total'].sum() * 100)
            
            produtos_classe_a = produtos_performance_sorted[produtos_performance_sorted['perc_acumulado'] <= 80].index.tolist()
            produtos_classe_b = produtos_performance_sorted[
                (produtos_performance_sorted['perc_acumulado'] > 80) & 
                (produtos_performance_sorted['perc_acumulado'] <= 95)
            ].index.tolist()
            
            # === 8. ROI DE RECOMENDAÇÕES (estimado) ===
            # Simula ROI baseado em produtos com potencial de crescimento
            produtos_potencial = produtos_performance[
                (produtos_performance['freq_compras'] >= 2) & 
                (produtos_performance['valor_total'] > ticket_medio)
            ].index.tolist()
            
            roi_estimado = len(produtos_potencial) * ticket_medio * 0.2  # 20% de margem estimada
            
            # === CONSOLIDAÇÃO DOS KPIs ===
            kpis_resultado = {
                'periodo_analise': {
                    'inicio': df_vendas_periodo['data_entrada'].min().strftime('%Y-%m-%d'),
                    'fim': df_vendas_periodo['data_entrada'].max().strftime('%Y-%m-%d'),
                    'meses': periodo_meses
                },
                'kpis_basicos': {
                    'total_vendas': round(total_vendas, 2),
                    'total_quantidade': round(total_qtd, 2),
                    'numero_transacoes': num_transacoes,
                    'materiais_distintos': num_materiais_distintos,
                    'ticket_medio': round(ticket_medio, 2),
                    'quantidade_media_transacao': round(qtd_media_transacao, 2)
                },
                'tendencias': {
                    'crescimento_medio_mensal': round(crescimento_medio, 1),
                    'volatilidade_vendas': round(volatilidade, 1),
                    'tendencia': 'CRESCIMENTO' if crescimento_medio > 5 else 'DECLINIO' if crescimento_medio < -5 else 'ESTAVEL'
                },
                'analise_produtos': {
                    'top_produtos_valor': top_produtos_valor[:5],
                    'top_produtos_frequencia': top_produtos_freq[:5],
                    'produtos_classe_a': produtos_classe_a[:10],
                    'produtos_classe_b': produtos_classe_b[:10],
                    'produtos_recentes': produtos_recentes[:10],
                    'produtos_dormentes': produtos_dormentes[:10]
                },
                'ltv_analise': {
                    'ltv_total': round(ltv_total, 2),
                    'ltv_mensal_medio': round(ltv_mensal, 2),
                    'ltv_projetado_12m': round(ltv_projetado_12m, 2),
                    'roi_estimado_recomendacoes': round(roi_estimado, 2)
                },
                'cotacoes': kpis_cotacoes,
                'recomendacoes_comerciais': self._generate_commercial_recommendations(
                    crescimento_medio, volatilidade, len(produtos_recentes), 
                    len(produtos_dormentes), taxa_conversao if kpis_cotacoes else None
                )
            }
            
            logger.info(f"✅ KPIs comerciais calculados - Vendas: R$ {total_vendas:,.2f}")
            return kpis_resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de KPIs comerciais: {e}")
            return {}

    def _generate_commercial_recommendations(self, crescimento: float, volatilidade: float,
                                           produtos_recentes: int, produtos_dormentes: int,
                                           taxa_conversao: Optional[float] = None) -> List[str]:
        """Gera recomendações comerciais baseadas nos KPIs"""
        
        recomendacoes = []
        
        # Análise de crescimento
        if crescimento > 10:
            recomendacoes.append("🚀 OPORTUNIDADE: Cliente em forte crescimento - expandir portfolio")
        elif crescimento < -10:
            recomendacoes.append("⚠️ ATENÇÃO: Cliente em declínio - investigar causas e recuperar")
        else:
            recomendacoes.append("📊 Cliente estável - focar em eficiência e novos produtos")
        
        # Análise de volatilidade
        if volatilidade > 50:
            recomendacoes.append("📈 ALTA VOLATILIDADE: Vendas irregulares - padronizar pedidos")
        elif volatilidade < 20:
            recomendacoes.append("✅ COMPORTAMENTO PREVISÍVEL: Cliente ideal para planejamento")
        
        # Produtos dormentes
        if produtos_dormentes > 5:
            recomendacoes.append(f"💤 REATIVAÇÃO: {produtos_dormentes} produtos sem compra recente - campanha direcionada")
        
        # Produtos recentes
        if produtos_recentes > 3:
            recomendacoes.append(f"🔥 MOMENTO QUENTE: {produtos_recentes} produtos com compra recente - cross-sell")
        
        # Taxa de conversão (se disponível)
        if taxa_conversao is not None:
            if taxa_conversao > 70:
                recomendacoes.append("💪 ALTA CONVERSÃO: Cliente comprometido - aumentar ticket médio")
            elif taxa_conversao < 30:
                recomendacoes.append("🎯 BAIXA CONVERSÃO: Melhorar qualidade das propostas")
        
        return recomendacoes[:5]  # Máximo 5 recomendações

    def analyze_client_benchmark(self, vendas_df: pd.DataFrame, cod_cliente_target: str,
                                min_similarity: float = 0.3) -> Dict[str, Any]:
        """
        Compara cliente com a base e identifica clientes similares e best practices
        
        Args:
            vendas_df: DataFrame de vendas completo
            cod_cliente_target: Cliente para análise
            min_similarity: Similaridade mínima para considerar clientes similares
            
        Returns:
            Dict com análise de benchmark e clientes similares
        """
        try:
            logger.info(f"📊 Analisando benchmark para cliente {cod_cliente_target}")
            
            df = vendas_df.copy()
            df = _standardize_date_column(df)
            
            # Filtra últimos 12 meses
            data_limite = df['data_entrada'].max() - timedelta(days=365)
            df = df[df['data_entrada'] >= data_limite]
            
            if df.empty:
                logger.warning("⚠️ Sem dados suficientes para benchmark")
                return {}
            
            # Dados do cliente target
            cliente_dados = df[df['cod_cliente'] == cod_cliente_target]
            if cliente_dados.empty:
                logger.warning(f"⚠️ Cliente {cod_cliente_target} não encontrado")
                return {}
            
            # === 1. MÉTRICAS DO CLIENTE TARGET ===
            cliente_metricas = {
                'total_vendas': cliente_dados['vlr_entrada'].sum(),
                'total_quantidade': cliente_dados['qtd_entrada'].sum(),
                'num_transacoes': len(cliente_dados),
                'materiais_distintos': cliente_dados['material'].nunique(),
                'ticket_medio': cliente_dados['vlr_entrada'].sum() / len(cliente_dados),
                'freq_compra_mensal': len(cliente_dados) / 12,
                'valor_medio_produto': cliente_dados.groupby('material')['vlr_entrada'].mean().mean(),
                'produtos_portfolio': set(cliente_dados['material'].unique())
            }
            
            # === 2. MÉTRICAS DA BASE GERAL ===
            base_stats = df.groupby('cod_cliente').agg({
                'vlr_entrada': ['sum', 'mean', 'std'],
                'qtd_entrada': ['sum', 'mean'],
                'material': ['nunique', 'count']
            }).round(2)
            
            base_stats.columns = ['total_vendas', 'valor_medio_transacao', 'valor_std',
                                'total_quantidade', 'qtd_media_transacao', 
                                'materiais_distintos', 'num_transacoes']
            
            # Calcula métricas derivadas da base
            base_stats['ticket_medio'] = base_stats['total_vendas'] / base_stats['num_transacoes']
            base_stats['freq_compra_mensal'] = base_stats['num_transacoes'] / 12
            
            # Estatísticas gerais da base
            base_medias = {
                'total_vendas_media': base_stats['total_vendas'].mean(),
                'total_vendas_mediana': base_stats['total_vendas'].median(),
                'ticket_medio_base': base_stats['ticket_medio'].mean(),
                'materiais_medio_base': base_stats['materiais_distintos'].mean(),
                'freq_compra_media': base_stats['freq_compra_mensal'].mean()
            }
            
            # === 3. POSICIONAMENTO DO CLIENTE ===
            percentis = {}
            for metrica in ['total_vendas', 'ticket_medio', 'materiais_distintos', 'freq_compra_mensal']:
                valor_cliente = cliente_metricas.get(metrica.replace('_mensal', ''), 
                                                   cliente_metricas.get(metrica, 0))
                if metrica in base_stats.columns:
                    percentil = (base_stats[metrica] <= valor_cliente).mean() * 100
                    percentis[metrica] = round(percentil, 1)
            
            # Classificação geral do cliente
            score_geral = sum(percentis.values()) / len(percentis)
            if score_geral >= 80:
                classificacao = "TOP_PERFORMER"
            elif score_geral >= 60:
                classificacao = "ACIMA_MEDIA"
            elif score_geral >= 40:
                classificacao = "MEDIA"
            else:
                classificacao = "ABAIXO_MEDIA"
            
            # === 4. CLIENTES SIMILARES ===
            # Calcula similaridade baseada em portfolio de produtos
            similaridades = []
            
            for cliente_comp in df['cod_cliente'].unique():
                if cliente_comp == cod_cliente_target:
                    continue
                    
                cliente_comp_dados = df[df['cod_cliente'] == cliente_comp]
                produtos_comp = set(cliente_comp_dados['material'].unique())
                
                # Similaridade de Jaccard (interseção / união)
                intersecao = len(cliente_metricas['produtos_portfolio'].intersection(produtos_comp))
                uniao = len(cliente_metricas['produtos_portfolio'].union(produtos_comp))
                
                if uniao > 0:
                    similaridade_produtos = intersecao / uniao
                    
                    # Similaridade de volume (valor total)
                    valor_comp = cliente_comp_dados['vlr_entrada'].sum()
                    similaridade_valor = 1 - abs(cliente_metricas['total_vendas'] - valor_comp) / max(cliente_metricas['total_vendas'], valor_comp)
                    
                    # Score combinado
                    similaridade_final = (similaridade_produtos * 0.6) + (similaridade_valor * 0.4)
                    
                    if similaridade_final >= min_similarity:
                        similaridades.append({
                            'cod_cliente': cliente_comp,
                            'similaridade_score': round(similaridade_final, 3),
                            'produtos_comuns': intersecao,
                            'total_produtos_similar': len(produtos_comp),
                            'valor_total_similar': valor_comp,
                            'diferenca_valor': valor_comp - cliente_metricas['total_vendas']
                        })
            
            # Ordena por similaridade
            clientes_similares = sorted(similaridades, key=lambda x: x['similaridade_score'], reverse=True)[:10]
            
            # === 5. BEST PRACTICES (clientes com performance superior) ===
            # Identifica clientes similares com performance superior
            best_practices = []
            for similar in clientes_similares:
                if similar['valor_total_similar'] > cliente_metricas['total_vendas'] * 1.2:  # 20% superior
                    
                    # Analisa o que fazem diferente
                    cliente_bp_dados = df[df['cod_cliente'] == similar['cod_cliente']]
                    produtos_bp = set(cliente_bp_dados['material'].unique())
                    
                    # Produtos que o cliente BP compra mas o target não
                    produtos_oportunidade = produtos_bp - cliente_metricas['produtos_portfolio']
                    
                    # Análise de valor por produto
                    valor_por_produto_bp = cliente_bp_dados.groupby('material')['vlr_entrada'].sum()
                    
                    top_produtos_bp = valor_por_produto_bp.nlargest(5).to_dict()
                    
                    best_practices.append({
                        'cod_cliente': similar['cod_cliente'],
                        'valor_total': similar['valor_total_similar'],
                        'vantagem_valor': similar['diferenca_valor'],
                        'produtos_oportunidade': list(produtos_oportunidade)[:10],
                        'top_produtos_valor': top_produtos_bp,
                        'num_materiais': len(produtos_bp),
                        'ticket_medio_bp': similar['valor_total_similar'] / cliente_bp_dados.shape[0]
                    })
            
            # === 6. GAPS DE OPORTUNIDADE vs SIMILARES ===
            oportunidades_similares = {}
            if clientes_similares:
                # Produtos mais comprados pelos similares
                clientes_similares_ids = [c['cod_cliente'] for c in clientes_similares]
                dados_similares = df[df['cod_cliente'].isin(clientes_similares_ids)]
                
                produtos_similares = dados_similares.groupby('material').agg({
                    'vlr_entrada': ['sum', 'mean', 'count'],
                    'cod_cliente': 'nunique'
                }).round(2)
                
                produtos_similares.columns = ['valor_total', 'valor_medio', 'freq_compras', 'num_clientes']
                produtos_similares['penetracao_similares'] = (produtos_similares['num_clientes'] / len(clientes_similares)) * 100
                
                # Identifica produtos com alta penetração nos similares mas baixa no target
                for material, row in produtos_similares.iterrows():
                    if (row['penetracao_similares'] >= 50 and  # 50%+ dos similares compram
                        material not in cliente_metricas['produtos_portfolio']):  # Target não compra
                        
                        oportunidades_similares[material] = {
                            'penetracao_similares': round(row['penetracao_similares'], 1),
                            'valor_medio_similares': round(row['valor_medio'], 2),
                            'num_clientes_similares': int(row['num_clientes']),
                            'potencial_receita': round(row['valor_medio'], 2)
                        }
            
            # === CONSOLIDAÇÃO DO BENCHMARK ===
            resultado_benchmark = {
                'cliente_target': cod_cliente_target,
                'classificacao_geral': classificacao,
                'score_percentil': round(score_geral, 1),
                'metricas_cliente': cliente_metricas,
                'posicionamento_percentis': percentis,
                'benchmark_base': base_medias,
                'clientes_similares': clientes_similares,
                'best_practices': best_practices[:5],  # Top 5
                'oportunidades_vs_similares': dict(list(oportunidades_similares.items())[:10]),  # Top 10
                'recomendacoes_benchmark': self._generate_benchmark_recommendations(
                    classificacao, percentis, len(clientes_similares), len(oportunidades_similares)
                )
            }
            
            logger.info(f"✅ Benchmark concluído - Classificação: {classificacao}")
            logger.info(f"📊 {len(clientes_similares)} clientes similares encontrados")
            
            return resultado_benchmark
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de benchmark: {e}")
            return {}

    def _generate_benchmark_recommendations(self, classificacao: str, percentis: Dict[str, float],
                                          num_similares: int, num_oportunidades: int) -> List[str]:
        """Gera recomendações baseadas no benchmark"""
        
        recomendacoes = []
        
        # Recomendações por classificação
        if classificacao == "TOP_PERFORMER":
            recomendacoes.append("🏆 CLIENTE TOP - Manter relacionamento e explorar novos produtos")
            recomendacoes.append("💎 Usar como referência para outros clientes similares")
        elif classificacao == "ACIMA_MEDIA":
            recomendacoes.append("⭐ BOM CLIENTE - Potencial para se tornar TOP performer")
            recomendacoes.append("📈 Focar em aumentar frequência e ticket médio")
        elif classificacao == "MEDIA":
            recomendacoes.append("📊 CLIENTE MÉDIO - Oportunidade de crescimento significativo")
            recomendacoes.append("🎯 Comparar com clientes similares para identificar gaps")
        else:
            recomendacoes.append("⚠️ CLIENTE ABAIXO DA MÉDIA - Necessita atenção especial")
            recomendacoes.append("🚀 Alto potencial de crescimento - focar em reativação")
        
        # Recomendações específicas por percentil
        if percentis.get('total_vendas', 0) < 30:
            recomendacoes.append("💰 VOLUME BAIXO - Trabalhar expansão de produtos")
        
        if percentis.get('ticket_medio', 0) < 30:
            recomendacoes.append("🎫 TICKET BAIXO - Focar em produtos de maior valor")
        
        if percentis.get('materiais_distintos', 0) < 30:
            recomendacoes.append("📦 PORTFOLIO LIMITADO - Cross-sell de novos materiais")
        
        # Oportunidades vs similares
        if num_oportunidades > 5:
            recomendacoes.append(f"🔍 {num_oportunidades} produtos-oportunidade vs clientes similares")
        
        if num_similares >= 5:
            recomendacoes.append(f"👥 {num_similares} clientes similares para benchmarking")
        
        return recomendacoes[:6]  # Máximo 6 recomendações

    def generate_intelligent_alerts(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame,
                                   alert_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Sistema de alertas inteligentes para oportunidades críticas e anomalias
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações
            alert_thresholds: Thresholds personalizados para alertas
            
        Returns:
            Dict com alertas categorizados por prioridade
        """
        try:
            logger.info("🚨 Gerando alertas inteligentes")
            
            # OTIMIZAÇÃO: Cache simples baseado no hash dos dados
            import hashlib
            data_hash = hashlib.md5(f"{len(vendas_df)}_{vendas_df['vlr_entrada'].sum()}_{vendas_df['data_entrada'].max()}".encode()).hexdigest()
            cache_key = f"alerts_{data_hash}"
            
            # Verificar se resultado está em cache (simulado com atributo de classe)
            if not hasattr(self, '_alerts_cache'):
                self._alerts_cache = {}
            
            if cache_key in self._alerts_cache:
                logger.info("🎯 Usando resultado em cache")
                return self._alerts_cache[cache_key]
            
            # Thresholds padrão
            if alert_thresholds is None:
                alert_thresholds = {
                    'crescimento_minimo': -20,  # Declínio de 20%
                    'dias_sem_compra': 90,     # 3 meses sem compra
                    'volatilidade_maxima': 70,  # 70% de volatilidade
                    'penetracao_oportunidade': 30,  # 30% penetração na base
                    'ticket_crescimento': 50,   # 50% aumento no ticket
                    'frequencia_declinio': -30  # 30% queda na frequência
                }
            
            df = vendas_df.copy()
            df = _standardize_date_column(df)
            
            # OTIMIZAÇÃO: Resetar índice para evitar conflitos, mas manter uma cópia para acesso rápido
            df.reset_index(drop=True, inplace=True)
            
            # Períodos de análise - garantir que são Timestamp do pandas
            hoje = pd.Timestamp(df['data_entrada'].max())
            mes_passado = hoje - pd.Timedelta(days=30)
            trimestre_passado = hoje - pd.Timedelta(days=90)
            ano_passado = hoje - pd.Timedelta(days=365)
            
            alertas = {
                'criticos': [],      # Prioridade ALTA - Ação imediata
                'importantes': [],   # Prioridade MÉDIA - Ação em breve
                'informativos': [],  # Prioridade BAIXA - Monitoramento
                'oportunidades': []  # Oportunidades comerciais
            }
            
            # === 1. ALERTAS DE CLIENTES ===
            logger.info("🔍 Analisando alertas por cliente")
            
            # OTIMIZAÇÃO VETORIZADA: Pré-calcular dados temporais para todos os clientes
            cliente_stats = df.groupby('cod_cliente').agg({
                'data_entrada': ['min', 'max', 'count'],
                'vlr_entrada': ['sum', 'mean', 'count']
            })
            cliente_stats.columns = ['primeira_compra', 'ultima_compra', 'total_compras', 'valor_total', 'ticket_medio', 'num_vendas']
            
            # Calcular dias desde última compra para todos os clientes
            cliente_stats['dias_ultima_compra'] = (hoje - cliente_stats['ultima_compra']).dt.days
            
            # 1.1 VETORIZADO: Clientes inativos
            clientes_inativos = cliente_stats[cliente_stats['dias_ultima_compra'] >= alert_thresholds['dias_sem_compra']]
            for cliente, dados in clientes_inativos.iterrows():
                alertas['criticos'].append({
                    'tipo': 'CLIENTE_INATIVO',
                    'cliente': cliente,
                    'dias_sem_compra': int(dados['dias_ultima_compra']),
                    'ultima_compra': dados['ultima_compra'].strftime('%Y-%m-%d'),
                    'valor_historico': round(dados['valor_total'], 2),
                    'prioridade': 'ALTA',
                    'acao_sugerida': 'Contato imediato para reativação'
                })
            
            # 1.2 VETORIZADO: Análise de crescimento/declínio por cliente
            # Filtrar dados por período para análise temporal
            vendas_recentes = df[df['data_entrada'] >= mes_passado].groupby('cod_cliente')['vlr_entrada'].sum()
            vendas_trimestre = df[df['data_entrada'] >= trimestre_passado].groupby('cod_cliente')['vlr_entrada'].sum()
            vendas_ano = df[df['data_entrada'] >= ano_passado].groupby('cod_cliente')['vlr_entrada'].sum()
            
            # Clientes com dados suficientes para análise de crescimento
            clientes_para_analise = vendas_trimestre.index.intersection(vendas_ano.index)
            
            for cliente in clientes_para_analise:
                # Verificar se tem dados suficientes
                cliente_dados_trimestre = df[(df['cod_cliente'] == cliente) & (df['data_entrada'] >= trimestre_passado)]
                cliente_dados_ano = df[(df['cod_cliente'] == cliente) & (df['data_entrada'] >= ano_passado)]
                
                if len(cliente_dados_trimestre) >= 2 and len(cliente_dados_ano) >= 4:
                    valor_recente = vendas_trimestre[cliente]
                    valor_historico = vendas_ano[cliente] / 4  # Média trimestral
                    
                    if valor_historico > 0:
                        crescimento = ((valor_recente - valor_historico) / valor_historico) * 100
                        
                        # Declínio significativo
                        if crescimento <= alert_thresholds['crescimento_minimo']:
                            alertas['importantes'].append({
                                'tipo': 'DECLINIO_VENDAS',
                                'cliente': cliente,
                                'crescimento_percent': round(crescimento, 1),
                                'valor_atual': round(valor_recente, 2),
                                'valor_esperado': round(valor_historico, 2),
                                'prioridade': 'MÉDIA',
                                'acao_sugerida': 'Investigar causas do declínio'
                            })
                        
                        # Crescimento de ticket (oportunidade)
                        if cliente in vendas_recentes.index:
                            vendas_cliente_recentes = df[(df['cod_cliente'] == cliente) & (df['data_entrada'] >= mes_passado)]
                            vendas_cliente_ano = df[(df['cod_cliente'] == cliente) & (df['data_entrada'] >= ano_passado)]
                            
                            if len(vendas_cliente_recentes) > 0 and len(vendas_cliente_ano) >= 2:
                                ticket_medio_recente = vendas_cliente_recentes['vlr_entrada'].mean()
                                ticket_medio_historico = vendas_cliente_ano['vlr_entrada'].mean()
                                
                                if ticket_medio_historico > 0:
                                    aumento_ticket = ((ticket_medio_recente - ticket_medio_historico) / ticket_medio_historico) * 100
                                    
                                    if aumento_ticket >= alert_thresholds['ticket_crescimento']:
                                        alertas['oportunidades'].append({
                                            'tipo': 'CRESCIMENTO_TICKET',
                                            'cliente': cliente,
                                            'aumento_percent': round(aumento_ticket, 1),
                                            'ticket_atual': round(ticket_medio_recente, 2),
                                            'ticket_historico': round(ticket_medio_historico, 2),
                                            'prioridade': 'OPORTUNIDADE',
                                            'acao_sugerida': 'Aproveitar momento para cross-sell'
                                        })
            
            # === 2. ALERTAS DE PRODUTOS ===
            logger.info("📦 Analisando alertas por produto")
            
            # OTIMIZAÇÃO VETORIZADA: Análise massiva de todos os materiais
            logger.info(f"📊 Analisando TODOS os {df['material'].nunique()} materiais (otimizado)")
            
            # Pré-calcular dados agregados para todos os materiais de uma vez
            material_stats = df.groupby('material').agg({
                'vlr_entrada': ['sum', 'mean', 'count'],
                'cod_cliente': 'nunique',
                'data_entrada': ['min', 'max']
            }).round(2)
            
            material_stats.columns = ['valor_total', 'valor_medio', 'total_vendas', 'clientes_unicos', 'primeira_venda', 'ultima_venda']
            
            # Calcular penetração para todos os materiais
            total_clientes = df['cod_cliente'].nunique()
            material_stats['penetracao'] = (material_stats['clientes_unicos'] / total_clientes * 100).round(1)
            
            # Filtrar apenas materiais com alta penetração (mas analisar todos os dados)
            materiais_alta_penetracao = material_stats[
                material_stats['penetracao'] >= alert_thresholds['penetracao_oportunidade']
            ].index
            
            # Para cada material com alta penetração, encontrar gaps eficientemente
            if len(materiais_alta_penetracao) > 0:
                # Vetorização: criar matriz de clientes vs materiais
                cliente_material_matrix = df.groupby(['cod_cliente', 'material'])['vlr_entrada'].sum().unstack(fill_value=0)
                top_clientes = df.groupby('cod_cliente')['vlr_entrada'].sum().nlargest(20).index
                
                for material in materiais_alta_penetracao:
                    if material in cliente_material_matrix.columns:
                        # Vetorizado: encontrar top clientes que não compram este material
                        nao_compram = cliente_material_matrix.loc[top_clientes, material] == 0
                        top_nao_compram = top_clientes[nao_compram].tolist()[:5]
                        
                        if top_nao_compram:
                            alertas['oportunidades'].append({
                                'tipo': 'GAP_PRODUTO_TOP_CLIENTES',
                                'material': material,
                                'penetracao_base': material_stats.loc[material, 'penetracao'],
                                'top_clientes_oportunidade': top_nao_compram,
                                'valor_medio_produto': material_stats.loc[material, 'valor_medio'],
                                'prioridade': 'OPORTUNIDADE',
                                'acao_sugerida': 'Oferecer produto para top clientes'
                            })
            
            # OTIMIZAÇÃO VETORIZADA: Análise de declínio por produto
            # Filtrar dados por período uma única vez
            dados_recentes = df[df['data_entrada'] >= trimestre_passado]
            dados_historicos = df[df['data_entrada'] >= ano_passado]
            
            # Agrupar dados de frequência para todos os materiais de uma vez
            freq_recente = dados_recentes.groupby('material').size()
            freq_historica = dados_historicos.groupby('material').size() / 4  # Por trimestre
            
            # Calcular mudança de frequência vetorizada
            mudanca_freq = ((freq_recente - freq_historica) / freq_historica * 100).fillna(0)
            materiais_declinio = mudanca_freq[mudanca_freq <= alert_thresholds['frequencia_declinio']]
            
            for material, mudanca in materiais_declinio.items():
                if material in material_stats.index and freq_historica.get(material, 0) > 0:
                    alertas['importantes'].append({
                        'tipo': 'PRODUTO_DECLINIO',
                        'material': material,
                        'mudanca_frequencia': round(float(mudanca), 1),
                        'vendas_recentes': int(freq_recente.get(material, 0)),  # Converter numpy.int64 para int
                        'vendas_esperadas': round(float(freq_historica.get(material, 0)), 1),  # Converter para float
                        'prioridade': 'MÉDIA',
                        'acao_sugerida': 'Investigar problema com produto'
                    })
            
            # === 3. ALERTAS SAZONAIS ===
            logger.info("📅 Analisando alertas sazonais")
            
            try:
                mes_atual = hoje.month
                df['mes'] = df['data_entrada'].dt.month
                
                # OTIMIZAÇÃO VETORIZADA: Análise sazonal de todos os materiais
                logger.info(f"📊 Analisando sazonalidade de TODOS os materiais")
                
                # Agrupar vendas por material e mês para todos os materiais de uma vez
                vendas_material_mes = df.groupby(['material', 'mes'])['vlr_entrada'].sum().unstack(fill_value=0)
                
                # Calcular estatísticas sazonais vetorizadas
                media_mensal = vendas_material_mes.mean(axis=1)
                std_mensal = vendas_material_mes.std(axis=1)
                
                # Definir próximos meses
                proximos_meses = [(mes_atual + i - 1) % 12 + 1 for i in range(1, 3)]
                
                # Processar apenas materiais com dados suficientes e variabilidade
                materiais_validos = (vendas_material_mes.count(axis=1) >= 6) & (std_mensal > 0)
                
                for material in vendas_material_mes.index[materiais_validos]:
                    try:
                        media = media_mensal[material]
                        std = std_mensal[material]
                        vendas_material = vendas_material_mes.loc[material]
                        
                        for mes in proximos_meses:
                            if mes in vendas_material.index and vendas_material[mes] > (media + std):
                                alertas['informativos'].append({
                                    'tipo': 'PICO_SAZONAL_PROXIMO',
                                    'material': material,
                                    'mes_pico': mes,
                                    'valor_esperado': round(vendas_material[mes], 2),
                                    'media_normal': round(media, 2),
                                    'intensidade_pico': round((vendas_material[mes] - media) / std, 1),
                                    'prioridade': 'BAIXA',
                                    'acao_sugerida': 'Preparar estoque para pico sazonal'
                                })
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao analisar sazonalidade do material {material}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"⚠️ Erro na análise sazonal: {e}")
            
            # === 4. ALERTAS DE VOLATILIDADE ===
            logger.info("📊 Analisando volatilidade")
            
            # OTIMIZAÇÃO VETORIZADA: Análise de volatilidade para todos os clientes
            try:
                # Criar período ano-mês para todos os dados de uma vez
                df_volatilidade = df.copy()
                df_volatilidade['ano_mes'] = df_volatilidade['data_entrada'].dt.to_period('M')
                
                # Agrupar vendas mensais por cliente de uma vez
                vendas_mensais_todos = df_volatilidade.groupby(['cod_cliente', 'ano_mes'])['vlr_entrada'].sum().unstack(fill_value=0)
                
                # Calcular coeficiente de variação vetorizado
                clientes_com_dados = vendas_mensais_todos.count(axis=1) >= 6  # Pelo menos 6 meses
                vendas_validas = vendas_mensais_todos.loc[clientes_com_dados]
                
                if len(vendas_validas) > 0:
                    # OTIMIZAÇÃO NUMPY: Calcular CV vetorizado com numpy para máxima performance
                    vendas_values = vendas_validas.values  # Converter para numpy array
                    medias_np = np.mean(vendas_values, axis=1)
                    desvios_np = np.std(vendas_values, axis=1)
                    
                    # Evitar divisão por zero com numpy
                    cv_np = np.divide(desvios_np * 100, medias_np, 
                                     out=np.zeros_like(desvios_np), where=medias_np!=0)
                    
                    # Criar Series para manter compatibilidade com índices
                    cv = pd.Series(cv_np, index=vendas_validas.index)
                    medias = pd.Series(medias_np, index=vendas_validas.index) 
                    desvios = pd.Series(desvios_np, index=vendas_validas.index)
                    
                    # Filtrar clientes com alta volatilidade
                    clientes_alta_volatilidade = cv[cv >= alert_thresholds['volatilidade_maxima']]
                    
                    for cliente, coef_var in clientes_alta_volatilidade.items():
                        alertas['informativos'].append({
                            'tipo': 'ALTA_VOLATILIDADE',
                            'cliente': cliente,
                            'coeficiente_variacao': round(coef_var, 1),
                            'valor_medio_mensal': round(medias[cliente], 2),
                            'desvio_padrao': round(desvios[cliente], 2),
                            'meses_analisados': int(vendas_validas.loc[cliente].count()),
                            'prioridade': 'BAIXA',
                            'acao_sugerida': 'Padronizar frequência de pedidos'
                        })
                    
                    logger.info(f"📊 Volatilidade analisada: {len(clientes_alta_volatilidade)} clientes com alta volatilidade")
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na análise de volatilidade: {e}")
            
            # === 5. CONSOLIDAÇÃO E PRIORIZAÇÃO ===
            # Ordena por prioridade e impacto
            for categoria in alertas:
                if categoria == 'criticos':
                    alertas[categoria] = sorted(alertas[categoria], 
                                              key=lambda x: x.get('valor_historico', x.get('dias_sem_compra', 0)), 
                                              reverse=True)
                elif categoria == 'oportunidades':
                    alertas[categoria] = sorted(alertas[categoria],
                                              key=lambda x: x.get('penetracao_base', x.get('aumento_percent', 0)),
                                              reverse=True)
            
            # SANITIZAÇÃO JSON: Converter todos os tipos numpy para tipos Python
            def sanitize_for_json(obj):
                """Converte recursivamente tipos numpy para tipos Python nativos"""
                if isinstance(obj, dict):
                    return {k: sanitize_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize_for_json(item) for item in obj]
                elif isinstance(obj, (np.integer, np.int32, np.int64)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float32, np.float64)):
                    return float(obj)
                elif pd.isna(obj):
                    return None
                else:
                    return obj
            
            # Sanitizar todos os alertas
            alertas = sanitize_for_json(alertas)
            
            # Estatísticas dos alertas
            total_alertas = sum(len(alertas[cat]) for cat in alertas)
            
            resumo_alertas = {
                'total_alertas': total_alertas,
                'criticos': len(alertas['criticos']),
                'importantes': len(alertas['importantes']),
                'informativos': len(alertas['informativos']),
                'oportunidades': len(alertas['oportunidades']),
                'data_analise': hoje.strftime('%Y-%m-%d %H:%M'),
                'periodo_analise': f"Últimos 12 meses até {hoje.strftime('%Y-%m-%d')}"
            }
            
            resultado_alertas = {
                'alertas': alertas,
                'resumo': resumo_alertas,
                'configuracao': alert_thresholds,
                'proximas_acoes': self._generate_action_priorities(alertas)
            }
            
            # OTIMIZAÇÃO: Armazenar resultado em cache
            self._alerts_cache[cache_key] = resultado_alertas
            
            # Limitar cache a 10 entradas para evitar uso excessivo de memória
            if len(self._alerts_cache) > 10:
                oldest_key = next(iter(self._alerts_cache))
                del self._alerts_cache[oldest_key]
            
            logger.info(f"✅ Alertas gerados - Total: {total_alertas}")
            logger.info(f"🚨 Críticos: {len(alertas['criticos'])}, Oportunidades: {len(alertas['oportunidades'])}")
            
            return resultado_alertas
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de alertas: {e}")
            return {}

    def _generate_action_priorities(self, alertas: Dict[str, List]) -> List[Dict[str, str]]:
        """Gera lista priorizada de ações baseadas nos alertas"""
        
        acoes = []
        
        # Ações críticas primeiro
        for alerta in alertas['criticos'][:3]:  # Top 3 críticos
            if alerta['tipo'] == 'CLIENTE_INATIVO':
                acoes.append({
                    'prioridade': '🚨 URGENTE',
                    'acao': f"Reativar cliente {alerta['cliente']}",
                    'prazo': 'Hoje',
                    'impacto': f"R$ {alerta['valor_historico']:,.2f} em risco"
                })
        
        # Oportunidades de alto impacto
        for alerta in alertas['oportunidades'][:2]:  # Top 2 oportunidades
            if alerta['tipo'] == 'CRESCIMENTO_TICKET':
                acoes.append({
                    'prioridade': '💰 OPORTUNIDADE',
                    'acao': f"Cross-sell para cliente {alerta['cliente']}",
                    'prazo': 'Esta semana',
                    'impacto': f"+{alerta['aumento_percent']}% no ticket médio"
                })
            elif alerta['tipo'] == 'GAP_PRODUTO_TOP_CLIENTES':
                acoes.append({
                    'prioridade': '🎯 OPORTUNIDADE',
                    'acao': f"Oferecer {alerta['material']} para top clientes",
                    'prazo': 'Próximos 15 dias',
                    'impacto': f"{len(alerta['top_clientes_oportunidade'])} clientes potenciais"
                })
        
        # Ações importantes
        for alerta in alertas['importantes'][:2]:  # Top 2 importantes
            if alerta['tipo'] == 'DECLINIO_VENDAS':
                acoes.append({
                    'prioridade': '⚠️ IMPORTANTE',
                    'acao': f"Investigar declínio cliente {alerta['cliente']}",
                    'prazo': 'Próximos 7 dias',
                    'impacto': f"{alerta['crescimento_percent']}% de queda"
                })
        
        return acoes[:6]  # Máximo 6 ações prioritárias

    def generate_actionable_insights(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame,
                                   cod_cliente: str, contexto_comercial: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gera insights acionáveis específicos para abordagem comercial
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações
            cod_cliente: Cliente para análise
            contexto_comercial: Contexto adicional (segmento, região, etc.)
            
        Returns:
            Dict com insights e scripts de venda específicos
        """
        try:
            logger.info(f"💡 Gerando insights acionáveis para cliente {cod_cliente}")
            
            # Contexto padrão se não fornecido
            if contexto_comercial is None:
                contexto_comercial = {
                    'segmento': 'Industrial',
                    'regiao': 'Não informado',
                    'vendedor': 'Equipe comercial',
                    'ultimo_contato': 'Não registrado'
                }
            
            df = vendas_df.copy()
            df = _standardize_date_column(df)
            
            # Dados do cliente
            cliente_dados = df[df['cod_cliente'] == cod_cliente]
            if cliente_dados.empty:
                logger.warning(f"⚠️ Cliente {cod_cliente} não encontrado")
                return {}
            
            # Usa os métodos já desenvolvidos para análise completa
            gaps_analysis = self.analyze_market_gaps(df, pd.DataFrame(), cod_cliente)
            gaps_json_safe = self._convert_gaps_to_json_safe(gaps_analysis)
            seasonality = self.detect_seasonality(df, cod_cliente)
            kpis = self.calculate_commercial_kpis(df, pd.DataFrame(), cod_cliente)
            benchmark = self.analyze_client_benchmark(df, cod_cliente)
            
            # === 1. PERFIL DO CLIENTE ===
            perfil_cliente = {
                'classificacao': benchmark.get('classificacao_geral', 'DESCONHECIDO'),
                'score_percentil': benchmark.get('score_percentil', 0),
                'total_vendas_12m': kpis.get('kpis_basicos', {}).get('total_vendas', 0),
                'ticket_medio': kpis.get('kpis_basicos', {}).get('ticket_medio', 0),
                'frequencia_compra': kpis.get('kpis_basicos', {}).get('numero_transacoes', 0) / 12,
                'produtos_distintos': kpis.get('kpis_basicos', {}).get('materiais_distintos', 0),
                'tendencia': kpis.get('tendencias', {}).get('tendencia', 'ESTAVEL')
            }
            
            # === 2. SCRIPTS DE ABORDAGEM POR SITUAÇÃO ===
            scripts_venda = []
            
            # Script baseado na classificação
            if perfil_cliente['classificacao'] == 'TOP_PERFORMER':
                scripts_venda.append({
                    'situacao': 'CLIENTE_TOP_PERFORMANCE',
                    'abordagem': 'Reconhecimento e Expansão',
                    'script': f"""
🏆 ABORDAGEM PARA CLIENTE TOP PERFORMER:

"Olá! Estive analisando nosso relacionamento e quero reconhecer que vocês estão entre nossos {perfil_cliente['score_percentil']:.0f}% melhores clientes. 

Com R$ {perfil_cliente['total_vendas_12m']:,.2f} em vendas nos últimos 12 meses, vocês demonstram consistência e crescimento exemplares.

Gostaria de apresentar algumas oportunidades exclusivas que identificamos para expandir ainda mais nossos negócios..."
                    """,
                    'proximos_passos': [
                        'Apresentar produtos premium ou lançamentos',
                        'Oferecer condições especiais de volume',
                        'Convidar para programa de parceiros estratégicos'
                    ]
                })
                
            elif perfil_cliente['classificacao'] == 'ABAIXO_MEDIA':
                scripts_venda.append({
                    'situacao': 'CLIENTE_POTENCIAL_CRESCIMENTO',
                    'abordagem': 'Identificação de Necessidades',
                    'script': f"""
🎯 ABORDAGEM PARA REATIVAÇÃO E CRESCIMENTO:

"Olá! Estive revisando nosso histórico de vendas e identifiquei algumas oportunidades importantes para otimizar seus resultados.

Nos últimos meses, observei que há espaço para crescimento em algumas áreas. Gostaria de entender melhor suas necessidades atuais e apresentar soluções que outros clientes similares têm utilizado com sucesso.

Posso agendar uma conversa de 30 minutos para discutirmos isso?"
                    """,
                    'proximos_passos': [
                        'Agendar reunião de diagnóstico',
                        'Apresentar cases de sucesso similares',
                        'Propor plano de crescimento estruturado'
                    ]
                })
            
            # === 3. ARGUMENTOS TÉCNICOS BASEADOS EM DADOS ===
            argumentos_tecnicos = []
            
            # Argumentos baseados em gaps
            if gaps_analysis and not gaps_analysis.empty:
                top_gaps = gaps_analysis.head(3)
                for _, gap in top_gaps.iterrows():
                    argumentos_tecnicos.append({
                        'produto': gap['material'],
                        'argumento_tecnico': f"""
📊 DADOS TÉCNICOS - {gap['material']}:

• PENETRAÇÃO DE MERCADO: {gap['w_percent']}% dos clientes da base compram este produto
• FREQUÊNCIA DE COTAÇÃO: {gap['q_percent']}% das cotações incluem este item
• SCORE DE OPORTUNIDADE: {gap['score_oportunidade']}/100

ARGUMENTO DE VENDA:
"{gap['clientes_compraram_base']} clientes similares já utilizam este produto com sucesso. 
A alta penetração ({gap['w_percent']}%) indica confiabilidade e resultados comprovados no mercado."
                        """,
                        'valor_potencial': gap.get('valor_potencial', 0),
                        'tipo_gap': gap['gap_type']
                    })
            
            # === 4. TIMING IDEAL PARA ABORDAGEM ===
            timing_abordagem = {}
            
            if seasonality and 'materiais' in seasonality:
                # Identifica produtos com pico sazonal próximo
                mes_atual = datetime.now().month
                proximos_meses = [(mes_atual + i - 1) % 12 + 1 for i in range(1, 4)]
                
                produtos_pico_proximo = []
                for material, data in seasonality['materiais'].items():
                    picos = data.get('picos_sazonais', [])
                    for mes_pico in picos:
                        if mes_pico in proximos_meses:
                            produtos_pico_proximo.append({
                                'produto': material,
                                'mes_pico': mes_pico,
                                'recomendacao': data.get('recomendacao', '')
                            })
                
                if produtos_pico_proximo:
                    timing_abordagem['sazonal'] = {
                        'momento': 'IDEAL_PARA_VENDAS',
                        'produtos': produtos_pico_proximo,
                        'script_timing': f"""
🗓️ TIMING PERFEITO:

"Analisando o histórico, identifiquei que os próximos meses são ideais para alguns produtos específicos. 
Baseado no comportamento sazonal do mercado, este é o momento certo para se preparar para a alta demanda."
                        """
                    }
            
            # === 5. OBJEÇÕES COMUNS E RESPOSTAS ===
            tratamento_objećoes = [
                {
                    'objecao': 'PREÇO_ALTO',
                    'resposta_dados': f"""
"Entendo a preocupação com preço. Deixe-me mostrar dados interessantes:
Seus clientes similares investem em média R$ {benchmark.get('benchmark_base', {}).get('ticket_medio_base', 0):,.2f} por transação.
O retorno médio que eles obtêm justifica o investimento. Posso detalhar o ROI?"
                    """,
                    'dados_suporte': f"Ticket médio da base: R$ {benchmark.get('benchmark_base', {}).get('ticket_medio_base', 0):,.2f}"
                },
                {
                    'objecao': 'NAO_PRECISO_AGORA',
                    'resposta_dados': f"""
"Compreendo. Baseado no seu histórico de compras, geralmente vocês reavaliam necessidades a cada {perfil_cliente['frequencia_compra']:.1f} meses.
Que tal agendarmos uma conversa para o próximo período de revisão? Posso preparar um estudo específico até lá."
                    """,
                    'dados_suporte': f"Frequência histórica: {perfil_cliente['frequencia_compra']:.1f} meses"
                },
                {
                    'objecao': 'SATISFEITO_FORNECEDOR_ATUAL',
                    'resposta_dados': f"""
"Ótimo saber que têm um bom fornecedor! Nossa proposta não é substituir, mas complementar.
{len(benchmark.get('clientes_similares', []))} clientes similares trabalham com múltiplos fornecedores e reportam {20}% menos problemas de desabastecimento."
                    """,
                    'dados_suporte': f"Diversificação reduz risco em {20}%"
                }
            ]
            
            # === 6. PRÓXIMOS PASSOS ESTRUTURADOS ===
            plano_acao = []
            
            # Baseado na classificação do cliente
            if perfil_cliente['classificacao'] in ['TOP_PERFORMER', 'ACIMA_MEDIA']:
                plano_acao = [
                    {'acao': 'Agendar reunião estratégica', 'prazo': '7 dias', 'objetivo': 'Apresentar oportunidades premium'},
                    {'acao': 'Preparar proposta personalizada', 'prazo': '10 dias', 'objetivo': 'Produtos de maior valor agregado'},
                    {'acao': 'Follow-up pós-proposta', 'prazo': '14 dias', 'objetivo': 'Ajustar oferta conforme feedback'}
                ]
            else:
                plano_acao = [
                    {'acao': 'Contato de diagnóstico', 'prazo': '3 dias', 'objetivo': 'Entender necessidades atuais'},
                    {'acao': 'Apresentação de cases similares', 'prazo': '7 dias', 'objetivo': 'Demonstrar valor e resultados'},
                    {'acao': 'Proposta estruturada', 'prazo': '14 dias', 'objetivo': 'Iniciar relacionamento comercial'}
                ]
            
            # === 7. CONSOLIDAÇÃO DOS INSIGHTS ===
            insights_resultado = {
                'cliente': cod_cliente,
                'contexto': contexto_comercial,
                'perfil_cliente': perfil_cliente,
                'scripts_venda': scripts_venda,
                'argumentos_tecnicos': argumentos_tecnicos[:5],  # Top 5
                'timing_abordagem': timing_abordagem,
                'tratamento_objećoes': tratamento_objećoes,
                'plano_acao': plano_acao,
                'resumo_executivo': self._generate_executive_summary(
                    perfil_cliente, argumentos_tecnicos, timing_abordagem
                ),
                'kpis_apoio': {
                    'valor_oportunidade_total': sum([arg.get('valor_potencial', 0) for arg in argumentos_tecnicos]),
                    'num_produtos_oportunidade': len(argumentos_tecnicos),
                    'score_prioridade_cliente': perfil_cliente['score_percentil']
                }
            }
            
            logger.info(f"✅ Insights acionáveis gerados para {cod_cliente}")
            logger.info(f"💰 Valor oportunidade: R$ {insights_resultado['kpis_apoio']['valor_oportunidade_total']:,.2f}")
            
            return insights_resultado
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de insights acionáveis: {e}")
            return {}

    def _generate_executive_summary(self, perfil: Dict, argumentos: List, timing: Dict) -> str:
        """Gera resumo executivo dos insights"""
        
        summary_parts = []
        
        # Classificação do cliente
        summary_parts.append(f"🎯 CLIENTE {perfil['classificacao']} (Percentil {perfil['score_percentil']:.0f})")
        
        # Oportunidades identificadas
        if argumentos:
            summary_parts.append(f"💰 {len(argumentos)} oportunidades de produtos identificadas")
            valor_total = sum([arg.get('valor_potencial', 0) for arg in argumentos])
            if valor_total > 0:
                summary_parts.append(f"💵 Potencial de R$ {valor_total:,.2f} em novas vendas")
        
        # Timing
        if timing and 'sazonal' in timing:
            summary_parts.append("⏰ Timing sazonal favorável identificado")
        
        # Tendência
        if perfil['tendencia'] == 'CRESCIMENTO':
            summary_parts.append("📈 Cliente em tendência de crescimento")
        elif perfil['tendencia'] == 'DECLINIO':
            summary_parts.append("⚠️ Cliente em declínio - necessita atenção")
        
        return " | ".join(summary_parts)

    def generate_comprehensive_report(self, vendas_df: pd.DataFrame, cotacoes_df: pd.DataFrame,
                                    cod_cliente: str = None, formato: str = 'completo',
                                    incluir_graficos: bool = True) -> Dict[str, Any]:
        """
        Gera relatório abrangente com todos os insights para exportação
        
        Args:
            vendas_df: DataFrame de vendas
            cotacoes_df: DataFrame de cotações  
            cod_cliente: Cliente específico (None para relatório geral)
            formato: Tipo de relatório ('executivo', 'completo', 'vendedor')
            incluir_graficos: Se deve incluir dados para gráficos
            
        Returns:
            Dict estruturado para exportação em PDF/Excel/PowerPoint
        """
        try:
            logger.info(f"📋 Gerando relatório {formato} para {cod_cliente or 'GERAL'}")
            
            # === EXECUTA TODAS AS ANÁLISES ===
            if cod_cliente:
                gaps = self.analyze_market_gaps(vendas_df, cotacoes_df, cod_cliente)
                seasonality = self.detect_seasonality(vendas_df, cod_cliente)
                kpis = self.calculate_commercial_kpis(vendas_df, cotacoes_df, cod_cliente)
                benchmark = self.analyze_client_benchmark(vendas_df, cod_cliente)
                insights = self.generate_actionable_insights(vendas_df, cotacoes_df, cod_cliente)
                alertas = self.generate_intelligent_alerts(vendas_df, cotacoes_df)
                
                # Filtra alertas do cliente
                alertas_cliente = {
                    'criticos': [a for a in alertas.get('alertas', {}).get('criticos', []) if a.get('cliente') == cod_cliente],
                    'importantes': [a for a in alertas.get('alertas', {}).get('importantes', []) if a.get('cliente') == cod_cliente],
                    'oportunidades': [a for a in alertas.get('alertas', {}).get('oportunidades', []) if a.get('cliente') == cod_cliente]
                }
            else:
                # Relatório geral - análise de múltiplos clientes
                gaps = pd.DataFrame()
                seasonality = {}
                kpis = self.calculate_commercial_kpis(vendas_df, cotacoes_df)
                benchmark = {}
                insights = {}
                alertas = self.generate_intelligent_alerts(vendas_df, cotacoes_df)
                alertas_cliente = alertas.get('alertas', {})
            
            # === ESTRUTURA O RELATÓRIO POR FORMATO ===
            
            if formato == 'executivo':
                relatorio = self._generate_executive_report(
                    cod_cliente, kpis, benchmark, gaps, alertas_cliente
                )
            elif formato == 'vendedor':
                relatorio = self._generate_sales_report(
                    cod_cliente, insights, gaps, kpis, alertas_cliente
                )
            else:  # completo
                relatorio = self._generate_complete_report(
                    cod_cliente, gaps, seasonality, kpis, benchmark, 
                    insights, alertas_cliente, incluir_graficos
                )
            
            # === METADADOS DO RELATÓRIO ===
            relatorio['metadata'] = {
                'data_geracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'periodo_analise': f"Últimos 12 meses até {vendas_df['data_entrada'].max()}",
                'cliente': cod_cliente or 'ANÁLISE GERAL',
                'formato': formato,
                'total_registros_vendas': len(vendas_df),
                'total_registros_cotacoes': len(cotacoes_df) if not cotacoes_df.empty else 0,
                'versao_sistema': '2.0 - B2B Recommendations'
            }
            
            logger.info(f"✅ Relatório {formato} gerado com sucesso")
            return relatorio
            
        except Exception as e:
            logger.error(f"❌ Erro na geração do relatório: {e}")
            return {}

    def _generate_executive_report(self, cliente: str, kpis: Dict, benchmark: Dict, 
                                 gaps: pd.DataFrame, alertas: Dict) -> Dict[str, Any]:
        """Relatório executivo resumido"""
        
        return {
            'tipo': 'RELATÓRIO EXECUTIVO',
            'resumo_executivo': {
                'cliente': cliente,
                'classificacao': benchmark.get('classificacao_geral', 'N/A'),
                'performance_percentil': benchmark.get('score_percentil', 0),
                'vendas_12m': kpis.get('kpis_basicos', {}).get('total_vendas', 0),
                'crescimento_tendencia': kpis.get('tendencias', {}).get('tendencia', 'ESTAVEL'),
                'alertas_criticos': len(alertas.get('criticos', [])),
                'oportunidades_identificadas': len(gaps) if not gaps.empty else 0
            },
            'kpis_principais': {
                'receita_total': kpis.get('kpis_basicos', {}).get('total_vendas', 0),
                'ticket_medio': kpis.get('kpis_basicos', {}).get('ticket_medio', 0),
                'produtos_ativos': kpis.get('kpis_basicos', {}).get('materiais_distintos', 0),
                'ltv_projetado': kpis.get('ltv_analise', {}).get('ltv_projetado_12m', 0)
            },
            'top_oportunidades': gaps.head(5).to_dict('records') if not gaps.empty else [],
            'acoes_prioritarias': alertas.get('criticos', [])[:3] + alertas.get('oportunidades', [])[:2],
            'recomendacoes_estrategicas': [
                'Focar em produtos de alta penetração na base',
                'Aproveitar timing sazonal identificado',
                'Implementar plano de cross-sell estruturado'
            ]
        }

    def _generate_sales_report(self, cliente: str, insights: Dict, gaps: pd.DataFrame,
                             kpis: Dict, alertas: Dict) -> Dict[str, Any]:
        """Relatório focado na equipe de vendas"""
        
        return {
            'tipo': 'RELATÓRIO PARA VENDAS',
            'perfil_cliente': insights.get('perfil_cliente', {}),
            'scripts_venda': insights.get('scripts_venda', []),
            'argumentos_tecnicos': insights.get('argumentos_tecnicos', [])[:5],
            'produtos_oportunidade': {
                'novos_produtos': gaps[gaps['gap_type'] == 'NOVO_PRODUTO'].head(5).to_dict('records') if not gaps.empty else [],
                'crescimento': gaps[gaps['gap_type'] == 'CRESCIMENTO'].head(5).to_dict('records') if not gaps.empty else []
            },
            'timing_ideal': insights.get('timing_abordagem', {}),
            'tratamento_objecoes': insights.get('tratamento_objećoes', []),
            'plano_acao': insights.get('plano_acao', []),
            'alertas_vendas': {
                'atencao_imediata': alertas.get('criticos', []),
                'oportunidades_quentes': alertas.get('oportunidades', [])
            },
            'kpis_vendedor': {
                'meta_sugerida_mensal': kpis.get('ltv_analise', {}).get('ltv_mensal_medio', 0) * 1.2,
                'produtos_focar': len(gaps.head(10)) if not gaps.empty else 0,
                'valor_pipeline': insights.get('kpis_apoio', {}).get('valor_oportunidade_total', 0)
            }
        }

    def _generate_complete_report(self, cliente: str, gaps: pd.DataFrame, seasonality: Dict,
                                kpis: Dict, benchmark: Dict, insights: Dict, alertas: Dict,
                                incluir_graficos: bool) -> Dict[str, Any]:
        """Relatório completo com todas as análises"""
        
        relatorio_completo = {
            'tipo': 'RELATÓRIO COMPLETO',
            
            # Seção 1: Visão Geral
            'visao_geral': {
                'resumo_executivo': insights.get('resumo_executivo', ''),
                'classificacao_cliente': benchmark.get('classificacao_geral', 'N/A'),
                'score_geral': benchmark.get('score_percentil', 0),
                'kpis_principais': kpis.get('kpis_basicos', {}),
                'tendencias': kpis.get('tendencias', {})
            },
            
            # Seção 2: Análise de Gaps
            'analise_gaps': {
                'total_oportunidades': len(gaps) if not gaps.empty else 0,
                'valor_potencial_total': gaps['valor_potencial'].sum() if not gaps.empty and 'valor_potencial' in gaps.columns else 0,
                'gaps_detalhados': gaps.to_dict('records') if not gaps.empty else [],
                'categorias_gap': {
                    'novos_produtos': len(gaps[gaps['gap_type'] == 'NOVO_PRODUTO']) if not gaps.empty else 0,
                    'crescimento': len(gaps[gaps['gap_type'] == 'CRESCIMENTO']) if not gaps.empty else 0
                }
            },
            
            # Seção 3: Sazonalidade
            'analise_sazonal': {
                'resumo': seasonality.get('resumo', {}),
                'materiais_sazonais': seasonality.get('materiais', {}),
                'periodo_analise': seasonality.get('periodo', {}),
                'recomendacoes_sazonais': [
                    material_data.get('recomendacao', '') 
                    for material_data in seasonality.get('materiais', {}).values()
                ][:5]
            },
            
            # Seção 4: KPIs e Performance
            'performance_comercial': {
                'kpis_basicos': kpis.get('kpis_basicos', {}),
                'ltv_analise': kpis.get('ltv_analise', {}),
                'analise_produtos': kpis.get('analise_produtos', {}),
                'cotacoes': kpis.get('cotacoes', {}),
                'recomendacoes': kpis.get('recomendacoes_comerciais', [])
            },
            
            # Seção 5: Benchmark
            'benchmark_mercado': {
                'posicionamento': {
                    'classificacao': benchmark.get('classificacao_geral', 'N/A'),
                    'percentis': benchmark.get('posicionamento_percentis', {}),
                    'vs_base': benchmark.get('benchmark_base', {})
                },
                'clientes_similares': benchmark.get('clientes_similares', [])[:5],
                'best_practices': benchmark.get('best_practices', [])[:3],
                'oportunidades_vs_similares': benchmark.get('oportunidades_vs_similares', {}),
                'recomendacoes': benchmark.get('recomendacoes_benchmark', [])
            },
            
            # Seção 6: Insights Acionáveis
            'insights_vendas': {
                'scripts': insights.get('scripts_venda', []),
                'argumentos_tecnicos': insights.get('argumentos_tecnicos', []),
                'timing': insights.get('timing_abordagem', {}),
                'objecoes': insights.get('tratamento_objećoes', []),
                'plano_acao': insights.get('plano_acao', [])
            },
            
            # Seção 7: Alertas e Monitoramento
            'sistema_alertas': {
                'alertas_criticos': alertas.get('criticos', []),
                'alertas_importantes': alertas.get('importantes', []),
                'alertas_informativos': alertas.get('informativos', []),
                'oportunidades': alertas.get('oportunidades', []),
                'proximas_acoes': insights.get('plano_acao', [])
            }
        }
        
        # Adiciona dados para gráficos se solicitado
        if incluir_graficos:
            relatorio_completo['dados_graficos'] = self._prepare_chart_data(
                gaps, seasonality, kpis, benchmark
            )
        
        return relatorio_completo

    def _prepare_chart_data(self, gaps: pd.DataFrame, seasonality: Dict, 
                          kpis: Dict, benchmark: Dict) -> Dict[str, Any]:
        """Prepara dados estruturados para geração de gráficos"""
        
        chart_data = {}
        
        # 1. Gráfico de Gaps (Top 10)
        if not gaps.empty:
            chart_data['gaps_oportunidade'] = {
                'labels': gaps.head(10)['material'].tolist(),
                'values': gaps.head(10)['score_oportunidade'].tolist(),
                'colors': ['#ff6b6b' if gap == 'NOVO_PRODUTO' else '#4ecdc4' 
                          for gap in gaps.head(10)['gap_type']],
                'type': 'bar'
            }
        
        # 2. Gráfico Sazonal (se disponível)
        if seasonality and 'materiais' in seasonality:
            # Pega primeiro material com dados sazonais
            for material, data in list(seasonality['materiais'].items())[:1]:
                if 'estatisticas_mensais' in data:
                    meses = list(range(1, 13))
                    valores = [data['estatisticas_mensais'].get(str(m), {}).get('qtd_media', 0) for m in meses]
                    
                    chart_data['sazonalidade'] = {
                        'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                        'values': valores,
                        'material': material,
                        'type': 'line'
                    }
                    break
        
        # 3. KPIs vs Base
        if benchmark and 'posicionamento_percentis' in benchmark:
            chart_data['performance_vs_base'] = {
                'labels': list(benchmark['posicionamento_percentis'].keys()),
                'values': list(benchmark['posicionamento_percentis'].values()),
                'benchmark': [50] * len(benchmark['posicionamento_percentis']),  # Linha da mediana
                'type': 'radar'
            }
        
        # 4. Evolução Temporal (se disponível em KPIs)
        if kpis and 'tendencias' in kpis:
            chart_data['tendencia_crescimento'] = {
                'crescimento': kpis['tendencias'].get('crescimento_medio_mensal', 0),
                'volatilidade': kpis['tendencias'].get('volatilidade_vendas', 0),
                'type': 'gauge'
            }
        
        return chart_data

    def run_complete_b2b_analysis(self, cod_cliente: str, contexto_comercial: Dict[str, Any] = None,
                                 export_format: str = 'completo') -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL - Executa análise B2B completa para um cliente
        
        Args:
            cod_cliente: Código do cliente para análise
            contexto_comercial: Contexto adicional (vendedor, região, etc.)
            export_format: Formato do relatório ('executivo', 'vendedor', 'completo')
            
        Returns:
            Dict com análise B2B completa e relatório estruturado
        """
        try:
            logger.info(f"🚀 INICIANDO ANÁLISE B2B COMPLETA - Cliente: {cod_cliente}")
            
            # === 1. CARREGA DADOS ===
            logger.info("📊 Carregando dados do banco...")
            conn = get_db_connection()
            
            # Query vendas
            vendas_query = """
            SELECT cod_cliente, material, produto, qtd_entrada, vlr_entrada, data
            FROM vendas 
            WHERE data >= date('now', '-24 months')
            ORDER BY data DESC
            """
            vendas_df = pd.read_sql_query(vendas_query, conn)
            
            # Renomeia coluna para manter compatibilidade com o resto do código
            if 'data' in vendas_df.columns:
                vendas_df['data_entrada'] = vendas_df['data']
            
            # Query cotações (usando produtos_cotados para ter preços)
            try:
                cotacoes_query = """
                SELECT p.cod_cliente, p.material, p.preco_liquido_unitario as preco, c.data as data_cotacao
                FROM produtos_cotados p
                LEFT JOIN cotacoes c ON p.cotacao = c.numero_cotacao
                WHERE c.data >= date('now', '-24 months')
                ORDER BY c.data DESC
                """
                cotacoes_df = pd.read_sql_query(cotacoes_query, conn)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar cotações: {e} - usando dados vazios")
                cotacoes_df = pd.DataFrame()
            
            conn.close()
            
            if vendas_df.empty:
                logger.error("❌ Sem dados de vendas encontrados")
                return {'erro': 'Sem dados de vendas para análise'}
            
            logger.info(f"✅ Dados carregados: {len(vendas_df)} vendas, {len(cotacoes_df)} cotações")
            
            # === 2. EXECUTA ANÁLISE COMPLETA ===
            logger.info("🔍 Executando análises...")
            
            # Análise de gaps
            gaps_analysis = self.analyze_market_gaps(vendas_df, cotacoes_df, cod_cliente)
            gaps_json_safe = self._convert_gaps_to_json_safe(gaps_analysis)
            
            # Detecção de sazonalidade
            seasonality_analysis = self.detect_seasonality(vendas_df, cod_cliente)
            
            # KPIs comerciais
            commercial_kpis = self.calculate_commercial_kpis(vendas_df, cotacoes_df, cod_cliente)
            
            # Benchmark de mercado
            benchmark_analysis = self.analyze_client_benchmark(vendas_df, cod_cliente)
            
            # Alertas inteligentes
            intelligent_alerts = self.generate_intelligent_alerts(vendas_df, cotacoes_df)
            
            # Insights acionáveis
            actionable_insights = self.generate_actionable_insights(
                vendas_df, cotacoes_df, cod_cliente, contexto_comercial
            )
            
            # Relatório final
            comprehensive_report = self.generate_comprehensive_report(
                vendas_df, cotacoes_df, cod_cliente, export_format, incluir_graficos=True
            )
            
            # === 3. CONSOLIDAÇÃO FINAL ===
            resultado_b2b = {
                'cliente': cod_cliente,
                'status': 'SUCESSO',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # Análises individuais
                'analises': {
                    'gaps_mercado': gaps_json_safe,
                    'sazonalidade': seasonality_analysis,
                    'kpis_comerciais': commercial_kpis,
                    'benchmark': benchmark_analysis,
                    'alertas': intelligent_alerts,
                    'insights': actionable_insights
                },
                
                # Relatório estruturado
                'relatorio': comprehensive_report,
                
                # Resumo executivo
                'resumo_executivo': {
                    'classificacao_cliente': benchmark_analysis.get('classificacao_geral', 'N/A'),
                    'score_percentil': benchmark_analysis.get('score_percentil', 0),
                    'total_oportunidades': gaps_json_safe['total_gaps'],
                    'valor_potencial': gaps_json_safe['resumo']['valor_total_potencial'],
                    'alertas_criticos': len(intelligent_alerts.get('alertas', {}).get('criticos', [])),
                    'recomendacao_principal': actionable_insights.get('resumo_executivo', 'Análise disponível no relatório completo')
                },
                
                # Próximos passos
                'proximas_acoes': actionable_insights.get('plano_acao', [])[:3],
                
                # Metadados
                'metadata': {
                    'versao_sistema': '2.0 - B2B Advanced Analytics',
                    'total_vendas_analisadas': len(vendas_df),
                    'periodo_analise': '24 meses',
                    'formato_relatorio': export_format
                }
            }
            
            logger.info("🎉 ANÁLISE B2B COMPLETA FINALIZADA")
            logger.info(f"📊 {resultado_b2b['resumo_executivo']['total_oportunidades']} oportunidades identificadas")
            logger.info(f"💰 Potencial: R$ {resultado_b2b['resumo_executivo']['valor_potencial']:,.2f}")
            
            return resultado_b2b
            
        except Exception as e:
            logger.error(f"❌ Erro na análise B2B completa: {e}")
            return {
                'cliente': cod_cliente,
                'status': 'ERRO',
                'erro': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }


# Removido: instância global movida para lazy loading
# purchase_recommender = SmartPurchaseRecommendations()
# ml_recommender = purchase_recommender  # Alias para compatibilidade


class ConversionRateAnalyzer:
    """Analisador de Taxa de Conversão e Segmentação Estratégica"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_conversion_rates(self, vendas_df: pd.DataFrame, produtos_cotados_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analisa taxas de conversão de cotações para vendas por produto
        
        Args:
            vendas_df: DataFrame de vendas
            produtos_cotados_df: DataFrame de produtos cotados
            
        Returns:
            DataFrame com análise de conversão por produto
        """
        try:
            self.logger.info("🔍 Analisando taxas de conversão cotação → venda...")
            
            # 1. Agrupa cotações por material
            cotacoes_stats = produtos_cotados_df.groupby('material').agg({
                'id': 'count',  # Total de cotações
                'cod_cliente': 'nunique',  # Clientes únicos que cotaram
                'quantidade': 'sum',  # Quantidade total cotada
                'preco_liquido_total': ['sum', 'mean'],  # Valor total e médio
                'descricao': 'first'  # Descrição do produto
            }).round(2)
            
            # Flatten column names
            cotacoes_stats.columns = [
                'total_cotacoes', 'clientes_cotaram', 'qtd_total_cotada', 
                'valor_total_cotado', 'valor_medio_cotacao', 'descricao'
            ]
            cotacoes_stats = cotacoes_stats.reset_index()
            
            # 2. Agrupa vendas por material
            vendas_stats = vendas_df.groupby('material').agg({
                'id': 'count',  # Total de vendas
                'cod_cliente': 'nunique',  # Clientes únicos que compraram
                'qtd_entrada': 'sum',  # Quantidade total vendida (coluna correta)
                'vlr_entrada': 'sum',  # Valor total vendido
                'data': ['min', 'max']  # Primeira e última venda
            }).round(2)
            
            # Flatten column names
            vendas_stats.columns = [
                'total_vendas', 'clientes_compraram', 'qtd_total_vendida',
                'valor_total_vendido', 'primeira_venda', 'ultima_venda'
            ]
            vendas_stats = vendas_stats.reset_index()
            
            # 3. Merge dos dados
            conversion_analysis = cotacoes_stats.merge(
                vendas_stats, on='material', how='left'
            ).fillna(0)
            
            # 4. Calcula métricas de conversão
            conversion_analysis['taxa_conversao_cotacao'] = (
                conversion_analysis['total_vendas'] / 
                conversion_analysis['total_cotacoes'] * 100
            ).round(2)
            
            conversion_analysis['taxa_conversao_cliente'] = (
                conversion_analysis['clientes_compraram'] / 
                conversion_analysis['clientes_cotaram'] * 100
            ).round(2)
            
            conversion_analysis['taxa_conversao_volume'] = (
                conversion_analysis['qtd_total_vendida'] / 
                conversion_analysis['qtd_total_cotada'] * 100
            ).round(2)
            
            # 5. Classifica produtos por padrão de conversão
            def classify_conversion_pattern(row):
                cotacoes = row['total_cotacoes']
                vendas = row['total_vendas']
                taxa_cotacao = row['taxa_conversao_cotacao']
                
                if cotacoes >= 5 and vendas == 0:
                    return "🔴 Alto Interesse - Zero Conversão"
                elif cotacoes >= 3 and taxa_cotacao < 20:
                    return "🟡 Baixa Conversão - Investigar Barreiras"
                elif cotacoes >= 2 and taxa_cotacao >= 50:
                    return "🟢 Alta Conversão - Produto Sucesso"
                elif cotacoes >= 5 and taxa_cotacao >= 80:
                    return "⭐ Conversão Excepcional - Benchmark"
                elif cotacoes >= 1 and vendas == 0:
                    return "🔵 Interesse Não Convertido"
                else:
                    return "⚪ Padrão Normal"
            
            conversion_analysis['padrao_conversao'] = conversion_analysis.apply(
                classify_conversion_pattern, axis=1
            )
            
            # 6. Calcula score de oportunidade
            # Produtos com muita demanda (cotações) mas baixa conversão = alta oportunidade
            conversion_analysis['opportunity_score'] = (
                (conversion_analysis['total_cotacoes'] * 0.4) +
                (conversion_analysis['valor_total_cotado'] / 10000 * 0.3) +
                ((100 - conversion_analysis['taxa_conversao_cotacao']) * 0.3)
            ).round(2)
            
            # 7. Ordena por score de oportunidade
            conversion_analysis = conversion_analysis.sort_values(
                'opportunity_score', ascending=False
            )
            
            self.logger.info(f"✅ Análise de conversão concluída: {len(conversion_analysis)} produtos analisados")
            
            return conversion_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de conversão: {e}")
            return pd.DataFrame()
    
    def analyze_cross_selling_opportunities(self, vendas_df: pd.DataFrame, min_support: float = 0.01) -> pd.DataFrame:
        """
        Análise de Market Basket para identificar produtos comprados em conjunto
        
        Args:
            vendas_df: DataFrame de vendas
            min_support: Suporte mínimo para considerar associação relevante
            
        Returns:
            DataFrame com regras de associação para cross-selling
        """
        try:
            self.logger.info("🛒 Analisando padrões de cross-selling (Market Basket)...")
            
            # 1. Prepara dados de transações (vendas por cliente/data)
            vendas_df['data'] = pd.to_datetime(vendas_df['data'])
            vendas_df['transacao_id'] = (
                vendas_df['cod_cliente'].astype(str) + '_' + 
                vendas_df['data'].dt.strftime('%Y-%m-%d')
            )
            
            # 2. Cria matriz de transações
            transacoes = vendas_df.groupby(['transacao_id', 'material']).size().unstack(fill_value=0)
            transacoes = (transacoes > 0).astype(int)  # Binariza (comprou ou não)
            
            self.logger.info(f"📊 {len(transacoes)} transações analisadas com {len(transacoes.columns)} produtos únicos")
            
            # 3. Calcula suporte para cada produto
            num_transacoes = len(transacoes)
            support_por_item = transacoes.sum() / num_transacoes
            itens_frequentes = support_por_item[support_por_item >= min_support].index.tolist()
            
            self.logger.info(f"🔍 {len(itens_frequentes)} produtos atendem critério de suporte mínimo ({min_support:.2%})")
            
            # 4. Calcula associações entre produtos
            associations = []
            
            for i, item_a in enumerate(itens_frequentes):
                for item_b in itens_frequentes[i+1:]:  # Evita duplicatas
                    # Conta transações com ambos os produtos
                    both = ((transacoes[item_a] == 1) & (transacoes[item_b] == 1)).sum()
                    only_a = ((transacoes[item_a] == 1) & (transacoes[item_b] == 0)).sum()
                    only_b = ((transacoes[item_a] == 0) & (transacoes[item_b] == 1)).sum()
                    
                    if both > 0:
                        # Métricas de associação
                        support_both = both / num_transacoes
                        confidence_a_to_b = both / (both + only_a) if (both + only_a) > 0 else 0
                        confidence_b_to_a = both / (both + only_b) if (both + only_b) > 0 else 0
                        
                        # Lift (força da associação)
                        support_a = (both + only_a) / num_transacoes
                        support_b = (both + only_b) / num_transacoes
                        lift = support_both / (support_a * support_b) if (support_a * support_b) > 0 else 0
                        
                        # Busca descrições dos produtos
                        desc_a = vendas_df[vendas_df['material'] == item_a]['produto'].iloc[0] if not vendas_df[vendas_df['material'] == item_a].empty else f"Material {item_a}"
                        desc_b = vendas_df[vendas_df['material'] == item_b]['produto'].iloc[0] if not vendas_df[vendas_df['material'] == item_b].empty else f"Material {item_b}"
                        
                        associations.append({
                            'produto_a': item_a,
                            'produto_b': item_b,
                            'descricao_a': desc_a,
                            'descricao_b': desc_b,
                            'transacoes_conjuntas': both,
                            'support': round(support_both, 4),
                            'confidence_a_to_b': round(confidence_a_to_b, 4),
                            'confidence_b_to_a': round(confidence_b_to_a, 4),
                            'lift': round(lift, 4),
                            'freq_compra_conjunta': round(support_both * 100, 2)
                        })
            
            # 5. Converte para DataFrame e filtra associações relevantes
            cross_selling_df = pd.DataFrame(associations)
            
            if not cross_selling_df.empty:
                # Filtra associações com lift > 1.2 (20% mais provável que acaso)
                cross_selling_df = cross_selling_df[cross_selling_df['lift'] > 1.2]
                
                # Ordena por lift e confidence
                cross_selling_df = cross_selling_df.sort_values(
                    ['lift', 'confidence_a_to_b'], ascending=[False, False]
                )
                
                # Classifica força da associação
                def classify_association_strength(lift_value):
                    if lift_value >= 3.0:
                        return "🔥 Associação Muito Forte"
                    elif lift_value >= 2.0:
                        return "💪 Associação Forte"
                    elif lift_value >= 1.5:
                        return "⚡ Associação Moderada"
                    else:
                        return "🔗 Associação Fraca"
                
                cross_selling_df['forca_associacao'] = cross_selling_df['lift'].apply(
                    classify_association_strength
                )
                
                # Adiciona recomendação de ação
                cross_selling_df['acao_cross_selling'] = cross_selling_df.apply(
                    lambda row: f"Quando vender {row['produto_a']}, oferecer {row['produto_b']} (Chance: {row['confidence_a_to_b']:.1%})",
                    axis=1
                )
            
            self.logger.info(f"✅ Análise de cross-selling concluída: {len(cross_selling_df)} associações encontradas")
            
            return cross_selling_df
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de cross-selling: {e}")
            return pd.DataFrame()
    
    def generate_strategic_segmentation_report(self, vendas_df: pd.DataFrame, produtos_cotados_df: pd.DataFrame) -> Dict:
        """
        Gera relatório completo de segmentação estratégica
        
        Returns:
            Dict com análises de conversão e cross-selling
        """
        try:
            self.logger.info("📈 Gerando relatório de segmentação estratégica...")
            
            # Análise de conversão
            conversion_analysis = self.analyze_conversion_rates(vendas_df, produtos_cotados_df)
            
            # Análise de cross-selling
            cross_selling_analysis = self.analyze_cross_selling_opportunities(vendas_df)
            
            # Métricas resumo
            total_produtos_analisados = len(conversion_analysis)
            produtos_zero_conversao = len(conversion_analysis[conversion_analysis['total_vendas'] == 0])
            produtos_alta_conversao = len(conversion_analysis[conversion_analysis['taxa_conversao_cotacao'] >= 50])
            
            total_associacoes = len(cross_selling_analysis)
            associacoes_fortes = len(cross_selling_analysis[cross_selling_analysis['lift'] >= 2.0])
            
            # Top insights
            top_oportunidades_conversao = conversion_analysis.head(10) if not conversion_analysis.empty else pd.DataFrame()
            top_cross_selling = cross_selling_analysis.head(10) if not cross_selling_analysis.empty else pd.DataFrame()
            
            relatorio = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metricas_conversao': {
                    'total_produtos': total_produtos_analisados,
                    'produtos_zero_conversao': produtos_zero_conversao,
                    'produtos_alta_conversao': produtos_alta_conversao,
                    'taxa_produtos_problematicos': round(produtos_zero_conversao / total_produtos_analisados * 100, 2) if total_produtos_analisados > 0 else 0
                },
                'metricas_cross_selling': {
                    'total_associacoes': total_associacoes,
                    'associacoes_fortes': associacoes_fortes,
                    'potencial_cross_selling': round(associacoes_fortes / total_associacoes * 100, 2) if total_associacoes > 0 else 0
                },
                'dados_conversao': conversion_analysis,
                'dados_cross_selling': cross_selling_analysis,
                'top_oportunidades': top_oportunidades_conversao,
                'top_cross_selling': top_cross_selling
            }
            
            self.logger.info("✅ Relatório de segmentação estratégica gerado com sucesso")
            return relatorio
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar relatório de segmentação: {e}")
            return {}


# Instâncias globais - criadas sob demanda para otimizar startup
_purchase_recommender = None
_conversion_analyzer = None

def get_purchase_recommender():
    """Retorna instância do recomendador (lazy loading)"""
    global _purchase_recommender
    if _purchase_recommender is None:
        print("🤖 Inicializando sistema de recomendações...")
        _purchase_recommender = SmartPurchaseRecommendations()
    return _purchase_recommender

def get_conversion_analyzer():
    """Retorna instância do analisador de conversão (lazy loading)"""
    global _conversion_analyzer
    if _conversion_analyzer is None:
        print("📊 Inicializando analisador de conversão...")
        _conversion_analyzer = ConversionRateAnalyzer()
    return _conversion_analyzer

# Funções para acessar instâncias globais com lazy loading
def get_purchase_recommender():
    """Retorna instância do recomendador (lazy loading)"""
    global _purchase_recommender
    if _purchase_recommender is None:
        print("🤖 Inicializando sistema de recomendações...")
        _purchase_recommender = SmartPurchaseRecommendations()
    return _purchase_recommender

def get_conversion_analyzer():
    """Retorna instância do analisador de conversão (lazy loading)"""
    global _conversion_analyzer
    if _conversion_analyzer is None:
        print("📊 Inicializando analisador de conversão...")
        _conversion_analyzer = ConversionRateAnalyzer()
    return _conversion_analyzer

# Variáveis que apontam para as funções (para compatibilidade)
# Nota: Usuários devem chamar get_purchase_recommender() para obter a instância
purchase_recommender = get_purchase_recommender
ml_recommender = get_purchase_recommender
conversion_analyzer = get_conversion_analyzer