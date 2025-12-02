"""
FastAPI Application - Dashboard WEG API
Backend REST API para o dashboard de vendas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Adicionar o diretório raiz ao path para importar utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend.api.routes import auth, vendas, cotacoes, kpis, uploads, reports, users

app = FastAPI(
    title="Dashboard WEG API",
    description="API REST para o sistema de análise comercial WEG",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])
app.include_router(vendas.router, prefix="/api/vendas", tags=["Vendas"])
app.include_router(cotacoes.router, prefix="/api/cotacoes", tags=["Cotações"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["KPIs"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(reports.router, prefix="/api/reports", tags=["Relatórios"])
app.include_router(users.router, prefix="/api/users", tags=["Usuários"])


@app.get("/api/health")
async def health_check():
    """Endpoint de health check"""
    return JSONResponse({
        "status": "healthy",
        "version": "2.0.0",
        "service": "Dashboard WEG API"
    })


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Dashboard WEG API",
        "docs": "/api/docs",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
