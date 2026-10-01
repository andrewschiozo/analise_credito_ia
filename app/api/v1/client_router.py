from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.simulacao_create import SimulacaoCreateSchema
from app.schemas.simulacao_response import SimulacaoResponseSchema
from app.services.credit_service import CreditService

router = APIRouter(prefix="/api/v1/client/simulacoes", tags=["Jornada do Cliente"])

@router.post("", response_model=SimulacaoResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_simulacao(dados: SimulacaoCreateSchema, db: Session = Depends(get_db)):
    """Recebe os dados cadastrais, valida LGPD, persiste e executa a análise síncrona da IA."""
    service = CreditService(db)
    simulacao = service.processar_nova_simulacao(dados)
    return simulacao

@router.get("/{simulacao_id}", response_model=SimulacaoResponseSchema)
def consultar_simulacao(simulacao_id: int, db: Session = Depends(get_db)):
    """Permite ao cliente consultar o status atual da sua simulação e o parecer emitido."""
    service = CreditService(db)
    simulacao = service.obter_simulacao(simulacao_id)
    if not simulacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulação não encontrada.")
    return simulacao