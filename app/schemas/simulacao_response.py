from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SimulacaoResponseSchema(BaseModel):
    id: int
    cpf: str
    nome_cliente: str
    renda_mensal_centavos: int
    valor_solicitado_centavos: int
    prazo_meses: int
    finalidade: str
    status: str
    parecer_ia: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True