# 🤖 Chat Interface - Preparação para Agente de IA
# Interface básica que evoluirá para agente conversacional completo

import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime
import json

def create_chat_interface():
    """
    Interface de chat básica para preparação do agente de IA
    Começará com comandos simples e evoluirá para NLP completo
    """
    
    chat_interface = dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-robot me-2"),
                "Assistente WEG (Beta) - Preparação para IA"
            ], className="mb-0"),
            dbc.Badge("Fase 1: Comandos Estruturados", color="info", className="ms-2")
        ]),
        dbc.CardBody([
            # Área de conversa
            html.Div(
                id="chat-messages",
                children=[
                    # Mensagem de boas-vindas
                    dbc.Alert([
                        html.Strong("🤖 Assistente WEG v1.0"), html.Br(),
                        "Olá! Estou em desenvolvimento para me tornar seu assistente de análise de dados.", html.Br(),
                        html.Strong("Comandos disponíveis:"), html.Br(),
                        "• 'ajuda' - Lista todos os comandos", html.Br(),
                        "• 'análises' - Mostra análises disponíveis", html.Br(),
                        "• 'oportunidades' - Executa análise de gaps", html.Br(),
                        "• 'clientes inativos' - Lista clientes em risco", html.Br(),
                        "• 'sazonalidade' - Analisa padrões temporais", html.Br(),
                        html.Hr(),
                        html.Small("💡 Em breve: perguntas em linguagem natural!", className="text-muted")
                    ], color="primary", className="mb-3")
                ],
                style={
                    'height': '400px',
                    'overflow-y': 'auto',
                    'border': '1px solid #dee2e6',
                    'border-radius': '0.375rem',
                    'padding': '15px',
                    'background-color': '#f8f9fa'
                }
            ),
            
            # Input de mensagem
            dbc.InputGroup([
                dbc.Input(
                    id="chat-input",
                    placeholder="Digite sua mensagem ou comando...",
                    type="text",
                    value=""
                ),
                dbc.Button(
                    [html.I(className="fas fa-paper-plane")],
                    id="chat-send-btn",
                    color="primary",
                    n_clicks=0
                )
            ], className="mt-3"),
            
            # Botões de comandos rápidos
            html.Div([
                html.P("Comandos Rápidos:", className="mb-2 mt-3 text-muted small"),
                dbc.ButtonGroup([
                    dbc.Button("📊 Análises", id="btn-quick-analyses", size="sm", outline=True),
                    dbc.Button("🎯 Oportunidades", id="btn-quick-opportunities", size="sm", outline=True),
                    dbc.Button("⚠️ Clientes Inativos", id="btn-quick-inactive", size="sm", outline=True),
                    dbc.Button("📈 Sazonalidade", id="btn-quick-seasonality", size="sm", outline=True),
                    dbc.Button("❓ Ajuda", id="btn-quick-help", size="sm", outline=True),
                ], className="flex-wrap")
            ])
        ])
    ], className="h-100")
    
    return chat_interface

def create_message_bubble(content, sender="bot", timestamp=None):
    """
    Cria uma bolha de mensagem no chat
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    
    if sender == "bot":
        return dbc.Alert([
            html.Div([
                html.Strong("🤖 Assistente WEG"),
                html.Small(f" - {timestamp}", className="text-muted ms-2")
            ], className="d-flex justify-content-between align-items-center mb-2"),
            html.Div(content)
        ], color="light", className="mb-2")
    else:
        return dbc.Alert([
            html.Div([
                html.Strong("👤 Você"),
                html.Small(f" - {timestamp}", className="text-muted ms-2")
            ], className="d-flex justify-content-between align-items-center mb-2"),
            html.Div(content)
        ], color="primary", className="mb-2")

class ChatBot:
    """
    Bot básico que processará comandos estruturados
    Base para futuro agente de IA com NLP
    """
    
    def __init__(self):
        self.commands = {
            'ajuda': self._cmd_help,
            'help': self._cmd_help,
            'análises': self._cmd_list_analyses,
            'analises': self._cmd_list_analyses,
            'oportunidades': self._cmd_opportunities,
            'gaps': self._cmd_opportunities,
            'clientes inativos': self._cmd_inactive_clients,
            'inativos': self._cmd_inactive_clients,
            'sazonalidade': self._cmd_seasonality,
            'tendências': self._cmd_seasonality,
            'tendencias': self._cmd_seasonality,
            'status': self._cmd_status,
            'info': self._cmd_info
        }
    
    def process_message(self, message: str) -> str:
        """
        Processa mensagem do usuário
        Futuro: será substituído por NLP/LLM
        """
        message_lower = message.lower().strip()
        
        # Busca comando exato
        if message_lower in self.commands:
            return self.commands[message_lower]()
        
        # Busca comando parcial
        for cmd, func in self.commands.items():
            if cmd in message_lower:
                return func()
        
        # Preparação para NLP: analisa intenção básica
        intent_analysis = self._analyze_intent(message)
        if intent_analysis:
            return intent_analysis
        
        # Resposta padrão
        return self._cmd_unknown(message)
    
    def _analyze_intent(self, message: str) -> str:
        """
        Análise simples de intenção - preparação para NLP
        """
        from utils.ai_framework import SimpleNLPMatcher
        
        intents = SimpleNLPMatcher.extract_intent(message)
        suggestions = SimpleNLPMatcher.suggest_analysis(message)
        
        if suggestions:
            response = f"🧠 **Análise de Intenção (Preparação NLP)**\n\n"
            response += f"Detectei interesse em: {', '.join(intents)}\n\n"
            response += f"Análises sugeridas:\n"
            for suggestion in suggestions:
                response += f"• {suggestion}\n"
            response += f"\n💡 *Em breve poderei executar essas análises automaticamente!*"
            return response
        
        return None
    
    def _cmd_help(self):
        return """
📖 **Comandos Disponíveis**

**Análises de Dados:**
• `oportunidades` - Identifica gaps de produtos e oportunidades de venda
• `clientes inativos` - Lista clientes que pararam de comprar
• `sazonalidade` - Mostra padrões temporais de vendas
• `análises` - Lista todas as análises disponíveis

**Informações:**
• `status` - Status atual do sistema
• `info` - Informações sobre o assistente
• `ajuda` - Esta mensagem

**🚀 Próximas Funcionalidades (em desenvolvimento):**
• Perguntas em linguagem natural
• Geração automática de relatórios
• Insights proativos
• Análises personalizadas

*Digite qualquer comando ou use os botões abaixo!*
        """
    
    def _cmd_list_analyses(self):
        from utils.ai_framework import ai_analytics
        
        analyses = ai_analytics.list_available_analyses()
        
        response = "📊 **Análises Disponíveis**\n\n"
        for analysis in analyses:
            response += f"**{analysis.name}**\n"
            response += f"• {analysis.description}\n"
            response += f"• Categoria: {analysis.category}\n"
            response += f"• Complexidade: {analysis.complexity}\n\n"
        
        response += "💡 *Use os comandos específicos ou aguarde a funcionalidade de execução automática!*"
        return response
    
    def _cmd_opportunities(self):
        return """
🎯 **Análise de Oportunidades**

Esta análise identifica gaps de produtos - clientes que compraram determinados produtos no passado mas não compraram recentemente.

**Próximos passos:**
1. Acesse a aba "Gaps de Oportunidade" no dashboard
2. Configure os filtros desejados
3. Analise as oportunidades identificadas

**🔮 Em breve:** Execução automática com resultados diretamente no chat!

*Exemplo futuro: "Mostre oportunidades para cliente ABC nos últimos 6 meses"*
        """
    
    def _cmd_inactive_clients(self):
        return """
⚠️ **Clientes Inativos**

Esta análise identifica clientes que pararam de comprar e classifica o risco de perda.

**Critérios de Inatividade:**
• 30-90 dias: Atenção
• 90-180 dias: Preocupação
• 180+ dias: Crítico

**Próximos passos:**
1. Acesse a análise no dashboard
2. Configure período de análise
3. Implemente ações de reativação

**🔮 Em breve:** Alertas automáticos e sugestões de ação!
        """
    
    def _cmd_seasonality(self):
        return """
📈 **Análise de Sazonalidade**

Identifica padrões temporais nas vendas por produto e cliente.

**Insights Típicos:**
• Meses de maior/menor demanda
• Padrões por linha de produto
• Oportunidades de planejamento

**Próximos passos:**
1. Execute a análise no dashboard
2. Configure produtos de interesse
3. Use insights para planejamento

**🔮 Em breve:** Previsões automáticas e alertas sazonais!
        """
    
    def _cmd_status(self):
        return """
⚡ **Status do Sistema**

**Sistema Atual:** ✅ Operacional
**Versão:** 1.0 - Modelo Heurístico
**Última Atualização:** Hoje

**Funcionalidades Ativas:**
✅ Análises pré-definidas
✅ Sistema de feedback
✅ Exportação de dados
✅ Interface responsiva

**Em Desenvolvimento:**
🔄 Agente de IA conversacional
🔄 NLP em português
🔄 Análises dinâmicas
🔄 Insights proativos

**Próxima Atualização:** Q1 2026 - NLP Básico
        """
    
    def _cmd_info(self):
        return """
🤖 **Sobre o Assistente WEG**

**Versão Atual:** 1.0 - Base Heurística
**Objetivo:** Evolução para agente de IA conversacional completo

**Roadmap de Evolução:**
• **Fase 1 (Atual):** Comandos estruturados e análises pré-definidas
• **Fase 2 (Q1 2026):** NLP básico e perguntas em linguagem natural
• **Fase 3 (Q2-Q3 2026):** IA conversacional completa com LLM
• **Fase 4 (Q4 2026):** Agente proativo com insights automáticos

**Tecnologias Futuras:**
• Processamento de linguagem natural (spaCy/transformers)
• Large Language Models (GPT-4/Claude/Local LLM)
• RAG (Retrieval Augmented Generation)
• Vector databases para contexto

*Acompanhe nossa evolução para o futuro da análise de dados!*
        """
    
    def _cmd_unknown(self, message):
        return f"""
❓ **Comando não reconhecido:** "{message}"

**Comandos disponíveis:**
• `ajuda` - Lista todos os comandos
• `análises` - Mostra análises disponíveis
• `oportunidades` - Análise de gaps
• `clientes inativos` - Lista clientes em risco

**🧠 Análise de Intenção (Beta):**
Detectei que você pode estar interessado em análises de dados. Em breve poderei entender perguntas como:
• "Qual foi o faturamento em janeiro?"
• "Quais clientes não compraram recentemente?"
• "Mostre produtos com maior potencial"

*Digite `ajuda` para ver todos os comandos ou use os botões rápidos!*
        """

# Instância global do chatbot
chatbot = ChatBot()

def register_chat_callbacks(app):
    """
    Registra callbacks do chat
    """
    
    @app.callback(
        [Output('chat-messages', 'children'),
         Output('chat-input', 'value')],
        [Input('chat-send-btn', 'n_clicks'),
         Input('chat-input', 'n_submit'),
         Input('btn-quick-analyses', 'n_clicks'),
         Input('btn-quick-opportunities', 'n_clicks'),
         Input('btn-quick-inactive', 'n_clicks'),
         Input('btn-quick-seasonality', 'n_clicks'),
         Input('btn-quick-help', 'n_clicks')],
        [State('chat-messages', 'children'),
         State('chat-input', 'value')]
    )
    def update_chat(send_clicks, input_submit, btn_analyses, btn_opportunities, 
                   btn_inactive, btn_seasonality, btn_help, current_messages, input_value):
        
        ctx = callback_context
        if not ctx.triggered:
            return current_messages, ""
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Determinar qual ação foi executada
        if trigger_id in ['chat-send-btn', 'chat-input'] and input_value:
            user_message = input_value
        elif trigger_id == 'btn-quick-analyses':
            user_message = "análises"
        elif trigger_id == 'btn-quick-opportunities':
            user_message = "oportunidades"
        elif trigger_id == 'btn-quick-inactive':
            user_message = "clientes inativos"
        elif trigger_id == 'btn-quick-seasonality':
            user_message = "sazonalidade"
        elif trigger_id == 'btn-quick-help':
            user_message = "ajuda"
        else:
            return current_messages, input_value
        
        # Processar mensagem
        if user_message.strip():
            # Adicionar mensagem do usuário
            user_bubble = create_message_bubble(user_message, sender="user")
            
            # Processar resposta do bot
            bot_response = chatbot.process_message(user_message)
            bot_bubble = create_message_bubble(
                dcc.Markdown(bot_response, dangerously_allow_html=True),
                sender="bot"
            )
            
            # Atualizar lista de mensagens
            new_messages = current_messages + [user_bubble, bot_bubble]
            
            # Log da interação para futura IA
            from utils.ai_framework import ai_logger
            ai_logger.log_analysis_request(
                user_id="chat_user",
                analysis_type="chat_interaction",
                parameters={"message": user_message, "response": bot_response[:100]},
                execution_time=0.1
            )
            
            return new_messages, ""
        
        return current_messages, input_value
