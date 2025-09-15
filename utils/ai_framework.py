# 🤖 AI-Ready Analytics Framework
# Preparação do código atual para integração com IA futura

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict

@dataclass
class AnalysisMetadata:
    """Metadados estruturados para análises AI-friendly"""
    name: str
    description: str
    category: str
    parameters: List[str]
    output_format: str
    complexity: str  # 'simple', 'intermediate', 'complex'
    ai_interpretable: bool
    natural_language_description: str
    example_queries: List[str]

@dataclass
class AnalysisResult:
    """Resultado estruturado para consumo por IA"""
    data: Any
    metadata: AnalysisMetadata
    insights: List[str]
    summary: str
    recommendations: List[str]
    confidence_score: float
    execution_time: float
    timestamp: datetime

class UserInteractionLogger:
    """Sistema de logging para coletar padrões de uso"""
    
    def __init__(self, log_file: str = "user_interactions.log"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def log_analysis_request(self, user_id: str, analysis_type: str, 
                           parameters: Dict, execution_time: float):
        """Log de solicitações de análise para identificar padrões"""
        log_data = {
            'event_type': 'analysis_request',
            'user_id': user_id,
            'analysis_type': analysis_type,
            'parameters': parameters,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        logging.info(json.dumps(log_data))
    
    def log_export_action(self, user_id: str, export_format: str, 
                         data_size: int, analysis_type: str):
        """Log de exportações para entender preferências"""
        log_data = {
            'event_type': 'data_export',
            'user_id': user_id,
            'export_format': export_format,
            'data_size': data_size,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat()
        }
        logging.info(json.dumps(log_data))
    
    def log_feedback(self, user_id: str, analysis_type: str, 
                    rating: int, feedback_text: str):
        """Log de feedback para treinamento futuro da IA"""
        log_data = {
            'event_type': 'user_feedback',
            'user_id': user_id,
            'analysis_type': analysis_type,
            'rating': rating,
            'feedback_text': feedback_text,
            'timestamp': datetime.now().isoformat()
        }
        logging.info(json.dumps(log_data))

class AIReadyAnalytics:
    """
    Framework para análises preparadas para IA
    Wrapper das análises atuais com metadados ricos
    """
    
    def __init__(self):
        self.logger = UserInteractionLogger()
        self.available_analyses = self._define_analyses_catalog()
    
    def _define_analyses_catalog(self) -> Dict[str, AnalysisMetadata]:
        """Catálogo de análises disponíveis com metadados IA-friendly"""
        return {
            'gaps_oportunidade': AnalysisMetadata(
                name='gaps_oportunidade',
                description='Identifica oportunidades de venda baseado em gaps de produtos',
                category='vendas',
                parameters=['filtro_ano', 'filtro_cliente', 'top_n'],
                output_format='dataframe',
                complexity='intermediate',
                ai_interpretable=True,
                natural_language_description='Analisa quais produtos clientes compraram no passado mas não compraram recentemente, identificando oportunidades de cross-sell',
                example_queries=[
                    'Quais produtos o cliente X parou de comprar?',
                    'Que oportunidades de venda existem para este ano?',
                    'Mostre produtos que clientes deixaram de comprar'
                ]
            ),
            'analise_sazonalidade': AnalysisMetadata(
                name='analise_sazonalidade',
                description='Analisa padrões sazonais de vendas por produto e cliente',
                category='tendencias',
                parameters=['produto', 'anos_analise'],
                output_format='chart_data',
                complexity='intermediate',
                ai_interpretable=True,
                natural_language_description='Identifica padrões temporais nas vendas, mostrando meses de maior e menor demanda por produto',
                example_queries=[
                    'Em que meses as vendas são maiores?',
                    'Qual a sazonalidade deste produto?',
                    'Quando devo me preparar para maior demanda?'
                ]
            ),
            'clientes_inativos': AnalysisMetadata(
                name='clientes_inativos',
                description='Identifica clientes que pararam de comprar e calcula risco de perda',
                category='relacionamento',
                parameters=['dias_inatividade', 'valor_minimo'],
                output_format='dataframe',
                complexity='simple',
                ai_interpretable=True,
                natural_language_description='Lista clientes que não fazem pedidos há um tempo determinado, categorizando o risco de perda',
                example_queries=[
                    'Quais clientes estão inativos?',
                    'Que clientes preciso contatar urgentemente?',
                    'Mostre clientes em risco de perda'
                ]
            ),
            'analise_cotacoes': AnalysisMetadata(
                name='analise_cotacoes',
                description='Analisa efetividade de cotações e taxa de conversão',
                category='vendas',
                parameters=['periodo', 'produto', 'vendedor'],
                output_format='summary_stats',
                complexity='complex',
                ai_interpretable=True,
                natural_language_description='Calcula taxa de conversão de cotações em vendas, identifica gargalos no processo comercial',
                example_queries=[
                    'Qual minha taxa de conversão de cotações?',
                    'Por que algumas cotações não viram venda?',
                    'Como melhorar meu processo comercial?'
                ]
            )
        }
    
    def get_analysis_metadata(self, analysis_name: str) -> Optional[AnalysisMetadata]:
        """Retorna metadados de uma análise específica"""
        return self.available_analyses.get(analysis_name)
    
    def list_available_analyses(self) -> List[AnalysisMetadata]:
        """Lista todas as análises disponíveis"""
        return list(self.available_analyses.values())
    
    def search_analyses_by_query(self, query: str) -> List[AnalysisMetadata]:
        """
        Busca análises baseado em uma query em linguagem natural
        Preparação para futuro NLP matching
        """
        query_lower = query.lower()
        relevant_analyses = []
        
        for analysis in self.available_analyses.values():
            # Busca simples por palavras-chave (será substituída por NLP)
            if (query_lower in analysis.description.lower() or
                query_lower in analysis.natural_language_description.lower() or
                any(query_lower in example.lower() for example in analysis.example_queries)):
                relevant_analyses.append(analysis)
        
        return relevant_analyses
    
    def execute_analysis_with_metadata(self, analysis_name: str, 
                                     parameters: Dict, user_id: str = "default") -> AnalysisResult:
        """
        Executa análise e retorna resultado estruturado para IA
        """
        start_time = datetime.now()
        
        # Buscar metadados da análise
        metadata = self.get_analysis_metadata(analysis_name)
        if not metadata:
            raise ValueError(f"Análise '{analysis_name}' não encontrada")
        
        # Executar análise (aqui chamaríamos as funções existentes)
        # Por enquanto, estrutura mock - será integrado com código real
        if analysis_name == 'gaps_oportunidade':
            data, insights = self._execute_gaps_analysis(parameters)
        elif analysis_name == 'analise_sazonalidade':
            data, insights = self._execute_seasonality_analysis(parameters)
        elif analysis_name == 'clientes_inativos':
            data, insights = self._execute_inactive_clients_analysis(parameters)
        elif analysis_name == 'analise_cotacoes':
            data, insights = self._execute_quotations_analysis(parameters)
        else:
            raise ValueError(f"Análise '{analysis_name}' não implementada")
        
        # Calcular tempo de execução
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Gerar resumo e recomendações (será feito por IA no futuro)
        summary = self._generate_summary(data, insights, analysis_name)
        recommendations = self._generate_recommendations(data, insights, analysis_name)
        
        # Log da interação
        self.logger.log_analysis_request(user_id, analysis_name, parameters, execution_time)
        
        # Retornar resultado estruturado
        return AnalysisResult(
            data=data,
            metadata=metadata,
            insights=insights,
            summary=summary,
            recommendations=recommendations,
            confidence_score=0.85,  # Será calculado dinamicamente
            execution_time=execution_time,
            timestamp=datetime.now()
        )
    
    def _execute_gaps_analysis(self, parameters: Dict):
        """Mock da análise de gaps - será integrado com código real"""
        # Simulação de dados para estrutura
        data = {
            'opportunities': [
                {'cliente': 'Cliente A', 'produto': 'Motor 5CV', 'valor_oportunidade': 15000},
                {'cliente': 'Cliente B', 'produto': 'Contator 25A', 'valor_oportunidade': 8500}
            ],
            'total_opportunities': 2,
            'total_value': 23500
        }
        
        insights = [
            "Identificadas 2 oportunidades principais de cross-sell",
            "Valor total de oportunidades: R$ 23.500",
            "Cliente A tem maior potencial (R$ 15.000)"
        ]
        
        return data, insights
    
    def _execute_seasonality_analysis(self, parameters: Dict):
        """Mock da análise de sazonalidade"""
        data = {
            'monthly_pattern': {
                'jan': 0.8, 'fev': 0.9, 'mar': 1.1, 'abr': 1.0,
                'mai': 1.0, 'jun': 0.9, 'jul': 0.8, 'ago': 1.2,
                'set': 1.3, 'out': 1.4, 'nov': 1.2, 'dez': 1.0
            },
            'peak_months': ['setembro', 'outubro'],
            'low_months': ['janeiro', 'julho']
        }
        
        insights = [
            "Padrão sazonal identificado com pico em setembro-outubro",
            "Vendas 40% maiores no 2º semestre",
            "Janeiro e julho são meses de menor demanda"
        ]
        
        return data, insights
    
    def _execute_inactive_clients_analysis(self, parameters: Dict):
        """Mock da análise de clientes inativos"""
        data = {
            'inactive_clients': [
                {'cliente': 'Cliente X', 'dias_inativo': 120, 'risco': 'alto', 'valor_historico': 50000},
                {'cliente': 'Cliente Y', 'dias_inativo': 95, 'risco': 'medio', 'valor_historico': 25000}
            ],
            'total_risk_value': 75000,
            'clients_at_risk': 2
        }
        
        insights = [
            "2 clientes em risco de perda (>90 dias inativos)",
            "Valor em risco: R$ 75.000 em faturamento histórico",
            "Cliente X requer ação urgente (120 dias inativo)"
        ]
        
        return data, insights
    
    def _execute_quotations_analysis(self, parameters: Dict):
        """Mock da análise de cotações"""
        data = {
            'conversion_rate': 0.34,
            'total_quotations': 150,
            'converted_quotations': 51,
            'lost_value': 230000,
            'avg_time_to_convert': 12.5
        }
        
        insights = [
            "Taxa de conversão: 34% (acima da média do setor)",
            "R$ 230.000 em cotações não convertidas",
            "Tempo médio para conversão: 12,5 dias"
        ]
        
        return data, insights
    
    def _generate_summary(self, data: Any, insights: List[str], analysis_type: str) -> str:
        """Gera resumo executivo - será feito por IA no futuro"""
        summary_templates = {
            'gaps_oportunidade': f"Análise identificou {data.get('total_opportunities', 0)} oportunidades no valor de R$ {data.get('total_value', 0):,.2f}",
            'analise_sazonalidade': f"Padrão sazonal mostra picos em {', '.join(data.get('peak_months', []))} e baixas em {', '.join(data.get('low_months', []))}",
            'clientes_inativos': f"{data.get('clients_at_risk', 0)} clientes em risco representando R$ {data.get('total_risk_value', 0):,.2f}",
            'analise_cotacoes': f"Taxa de conversão de {data.get('conversion_rate', 0)*100:.1f}% com R$ {data.get('lost_value', 0):,.2f} em oportunidades perdidas"
        }
        
        return summary_templates.get(analysis_type, "Resumo não disponível")
    
    def _generate_recommendations(self, data: Any, insights: List[str], analysis_type: str) -> List[str]:
        """Gera recomendações automáticas - será feito por IA no futuro"""
        recommendations_templates = {
            'gaps_oportunidade': [
                "Contatar clientes com maiores oportunidades identificadas",
                "Preparar propostas específicas para produtos em gap",
                "Monitorar conversão das oportunidades semanalmente"
            ],
            'analise_sazonalidade': [
                "Preparar estoque para período de alta demanda",
                "Ajustar estratégia comercial para meses de baixa",
                "Implementar campanhas promocionais nos vales"
            ],
            'clientes_inativos': [
                "Contatar urgentemente clientes com >90 dias de inatividade",
                "Implementar programa de reativação personalizado",
                "Investigar motivos da inatividade dos principais clientes"
            ],
            'analise_cotacoes': [
                "Reduzir tempo de resposta para melhorar conversão",
                "Analisar cotações perdidas para identificar padrões",
                "Implementar follow-up automático pós-cotação"
            ]
        }
        
        return recommendations_templates.get(analysis_type, ["Analisar resultados", "Definir plano de ação"])

# Instância global para uso no dashboard
ai_analytics = AIReadyAnalytics()

# Função de conveniência para integração fácil
def get_ai_ready_analysis(analysis_name: str, parameters: Dict, user_id: str = "default") -> AnalysisResult:
    """Função helper para facilitar integração com código existente"""
    return ai_analytics.execute_analysis_with_metadata(analysis_name, parameters, user_id)

def search_available_analyses(query: str) -> List[AnalysisMetadata]:
    """Função helper para buscar análises por query"""
    return ai_analytics.search_analyses_by_query(query)

# Preparação para futuro NLP
class SimpleNLPMatcher:
    """
    Matcher simples que será substituído por NLP real na Fase 2
    """
    
    INTENT_KEYWORDS = {
        'faturamento': ['faturamento', 'vendas', 'receita', 'valor vendido'],
        'clientes': ['cliente', 'comprador', 'consumidor', 'empresa'],
        'produtos': ['produto', 'material', 'item', 'mercadoria'],
        'temporal': ['mês', 'ano', 'período', 'data', 'quando'],
        'ranking': ['top', 'maior', 'melhor', 'principal', 'primeiro'],
        'tendencia': ['tendência', 'padrão', 'sazonalidade', 'crescimento'],
        'oportunidade': ['oportunidade', 'gap', 'potencial', 'chance'],
        'problema': ['problema', 'inativo', 'risco', 'perda']
    }
    
    @classmethod
    def extract_intent(cls, question: str) -> List[str]:
        """Extrai intenções básicas da pergunta"""
        question_lower = question.lower()
        detected_intents = []
        
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_intents.append(intent)
        
        return detected_intents
    
    @classmethod
    def suggest_analysis(cls, question: str) -> List[str]:
        """Sugere análises baseado na pergunta"""
        intents = cls.extract_intent(question)
        
        suggestions = []
        
        if 'oportunidade' in intents or 'gap' in intents:
            suggestions.append('gaps_oportunidade')
        
        if 'tendencia' in intents or 'temporal' in intents:
            suggestions.append('analise_sazonalidade')
        
        if 'problema' in intents or ('clientes' in intents and any(word in question.lower() for word in ['inativo', 'risco', 'perda'])):
            suggestions.append('clientes_inativos')
        
        if 'faturamento' in intents or 'vendas' in intents:
            suggestions.extend(['analise_cotacoes', 'gaps_oportunidade'])
        
        return list(set(suggestions))  # Remove duplicatas

# Função para testar o matcher simples
def test_nlp_matching():
    """Testa o sistema de matching simples"""
    test_questions = [
        "Quais são as oportunidades de venda?",
        "Mostre clientes inativos",
        "Qual a tendência de vendas?",
        "Como está o faturamento?",
        "Que produtos têm maior potencial?"
    ]
    
    for question in test_questions:
        intents = SimpleNLPMatcher.extract_intent(question)
        suggestions = SimpleNLPMatcher.suggest_analysis(question)
        print(f"Pergunta: {question}")
        print(f"Intenções: {intents}")
        print(f"Análises sugeridas: {suggestions}")
        print("---")

if __name__ == "__main__":
    # Teste do framework
    print("🤖 AI-Ready Analytics Framework")
    print("================================")
    
    # Listar análises disponíveis
    print("\n📊 Análises Disponíveis:")
    for analysis in ai_analytics.list_available_analyses():
        print(f"- {analysis.name}: {analysis.description}")
    
    # Teste de busca
    print("\n🔍 Teste de Busca:")
    results = ai_analytics.search_analyses_by_query("oportunidades de venda")
    for result in results:
        print(f"- {result.name}: {result.natural_language_description}")
    
    # Teste NLP matching
    print("\n🧠 Teste NLP Simples:")
    test_nlp_matching()
