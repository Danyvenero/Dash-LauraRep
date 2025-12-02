#!/bin/bash
# Script para executar o frontend

echo "🚀 Iniciando Frontend..."
echo "📦 Instalando dependências..."

cd frontend
npm install

echo "✅ Dependências instaladas"
echo "🌐 Iniciando servidor de desenvolvimento na porta 3000..."
echo ""

npm run dev
