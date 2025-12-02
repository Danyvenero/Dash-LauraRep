#!/bin/bash
# Script para executar o backend

echo "🚀 Iniciando Backend API..."
echo "📦 Instalando dependências..."

cd backend
pip install -r requirements.txt

echo "✅ Dependências instaladas"
echo "🌐 Iniciando servidor na porta 8000..."
echo "📚 Documentação disponível em: http://localhost:8000/api/docs"
echo ""

python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
