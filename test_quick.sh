#!/bin/bash

echo "🧪 Teste Rápido do Dashboard WEG"
echo "=================================="
echo ""

# Verificar Python
echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python encontrado: $PYTHON_VERSION"
else
    echo "   ❌ Python não encontrado!"
    exit 1
fi

# Verificar Node.js
echo "2. Verificando Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js encontrado: $NODE_VERSION"
else
    echo "   ❌ Node.js não encontrado!"
    exit 1
fi

# Verificar dependências do backend
echo "3. Verificando dependências do backend..."
cd backend
if [ -f "requirements.txt" ]; then
    echo "   📦 Instalando dependências do backend..."
    pip install -q -r requirements.txt
    echo "   ✅ Dependências instaladas"
else
    echo "   ⚠️  requirements.txt não encontrado"
fi
cd ..

# Verificar dependências do frontend
echo "4. Verificando dependências do frontend..."
cd frontend
if [ -f "package.json" ]; then
    if [ ! -d "node_modules" ]; then
        echo "   📦 Instalando dependências do frontend..."
        npm install --silent
        echo "   ✅ Dependências instaladas"
    else
        echo "   ✅ Dependências já instaladas"
    fi
else
    echo "   ⚠️  package.json não encontrado"
fi
cd ..

# Verificar banco de dados
echo "5. Verificando banco de dados..."
if [ ! -d "instance" ]; then
    echo "   📁 Criando diretório instance..."
    mkdir -p instance
fi

if [ -f "setup_database.py" ]; then
    echo "   ✅ setup_database.py encontrado"
else
    echo "   ⚠️  setup_database.py não encontrado"
fi

echo ""
echo "=================================="
echo "✅ Verificações concluídas!"
echo ""
echo "Próximos passos:"
echo "1. Terminal 1 - Backend:"
echo "   cd backend && python -m uvicorn backend.api.main:app --reload"
echo ""
echo "2. Terminal 2 - Frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Acessar:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
