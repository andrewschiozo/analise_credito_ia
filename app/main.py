from fastapi import FastAPI
from app.api.v1.client_router import router as client_router
from app.api.v1.backoffice_router import router as backoffice_router

app = FastAPI(
    title="Análise de Crédito para Pessoa Física com IA",
    description="API de Análise e Revisão de Crédito PF com IA e Governança",
    version="1.0.0"
)

app.include_router(client_router)
app.include_router(backoffice_router)

@app.get("/health", tags=["Healthcheck"])
def health_check():
    return {"status": "healthy", "system": "online"}