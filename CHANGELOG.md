# 📝 Changelog - Dashboard WEG

## [2.0.0] - 2025-01-28

### 🎉 Migração Completa para React + FastAPI

#### ✨ Adicionado

**Frontend:**
- ✅ Estrutura React + TypeScript + Vite
- ✅ Tailwind CSS configurado
- ✅ Sistema de autenticação JWT
- ✅ Layout principal com sidebar responsiva
- ✅ Página de Login
- ✅ Página Visão Geral (KPIs gerais)
- ✅ Página KPIs por Cliente com gráfico scatter
- ✅ Página KPIs de Propostas (estrutura)
- ✅ Página Produtos (Bolhas) com gráfico Plotly
- ✅ Página Funil & Ações completa
- ✅ Página Configurações com upload de arquivos
- ✅ Componente de upload com drag & drop
- ✅ Gráficos interativos (Recharts, Plotly)
- ✅ Dark mode toggle
- ✅ Exportações CSV
- ✅ Notificações toast

**Backend:**
- ✅ API REST com FastAPI
- ✅ Autenticação JWT
- ✅ Endpoints de KPIs
- ✅ Endpoints de vendas e cotações
- ✅ Endpoints de upload
- ✅ Endpoints de relatórios
- ✅ Endpoints de ETL
- ✅ Documentação Swagger automática
- ✅ CORS configurado

**Documentação:**
- ✅ Análise completa do código existente
- ✅ Plano de migração detalhado
- ✅ README de migração
- ✅ Guia de melhorias e sugestões
- ✅ Resumo executivo
- ✅ Quick start guide

### 🔄 Mudado

- Migração de Dash (Python) para React (TypeScript)
- Migração de Flask Session para JWT
- Separação frontend/backend
- Melhorias de UX/UI
- Performance otimizada

### 🐛 Corrigido

- Problemas de CORS
- Validação de uploads
- Tratamento de erros
- Persistência de tema

### 📚 Documentação

- Documentação completa da API (Swagger)
- Guias de instalação e uso
- Exemplos de uso

---

## [1.0.0] - Versão Original (Dash)

### Funcionalidades Originais

- Sistema de autenticação
- Upload de vendas e cotações
- KPIs gerais e por cliente
- Análise de propostas
- Gráfico de bolhas
- Funil de conversão
- Geração de relatórios PDF
- Exports CSV

---

**Próximas Versões Planejadas:**

- [ ] Dashboard executivo
- [ ] Análise preditiva
- [ ] Segmentação de clientes
- [ ] Filtros salvos
- [ ] Exportações avançadas (Excel, PDF, PowerPoint)
- [ ] Multi-idioma
- [ ] Geolocalização de clientes
