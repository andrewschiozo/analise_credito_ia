from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.simulacao_status_enum import SimulacaoStatus
from app.schemas.simulacao_response import SimulacaoResponseSchema
from app.services.credit_service import CreditService
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/api/v1/backoffice/simulacoes", tags=["Mesa de Crédito / Back-Office"])

class AnaliseHumanaSchema(BaseModel):
    acao: str = Field(..., description="Deve ser estritamente APROVAR ou REJEITAR")
    analista_id: str = Field(..., description="Identificação do gerente ou analista responsável")
    observacao_humana: str = Field(..., description="Justificativa da decisão humana")

@router.get("", response_model=List[SimulacaoResponseSchema])
def listar_simulacoes(status_filtro: Optional[str] = Query(None, alias="status"), db: Session = Depends(get_db)):
    """Lista propostas de crédito para a equipe de análise humana, com filtro opcional por status."""
    service = CreditService(db)
    return service.listar_simulacoes(status_filtro)

@router.patch("/{simulacao_id}/analise", response_model=SimulacaoResponseSchema)
def executar_human_in_the_loop(simulacao_id: int, payload: AnaliseHumanaSchema, db: Session = Depends(get_db)):
    """Executa a aprovação ou rejeição final por parte da mesa de crédito humana."""
    service = CreditService(db)
    simulacao = service.obter_simulacao(simulacao_id)
    
    if not simulacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulação não encontrada.")

    acao = payload.acao.upper()
    if acao == "APROVAR":
        novo_status = SimulacaoStatus.APROVADO_HUMANO.value
    elif acao == "REJEITAR":
        novo_status = SimulacaoStatus.REJEITADO_HUMANO.value
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ação inválida. Use APROVAR ou REJEITAR.")

    # Atualiza a simulação com a decisão humana via repositório
    simulacao_atualizada = service.repository.db.query(type(simulacao)).filter_by(id=simulacao_id).first()
    simulacao_atualizada.status = novo_status
    simulacao_atualizada.analista_id = payload.analista_id
    simulacao_atualizada.observacao_humana = payload.observacao_humana
    service.repository.db.commit()
    service.repository.db.refresh(simulacao_atualizada)

    return simulacao_atualizada