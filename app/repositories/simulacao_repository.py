from sqlalchemy.orm import Session
from app.core.simulacao_status_enum import SimulacaoStatus
from app.models.simulacao import SimulacaoModel
from app.schemas.simulacao_create import SimulacaoCreateSchema
from typing import List, Optional

class SimulacaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dados: SimulacaoCreateSchema) -> SimulacaoModel:
        """Persiste uma nova simulação de crédito com status inicial PENDENTE_IA."""
        simulacao = SimulacaoModel(
            cpf=dados.cpf,
            nome_cliente=dados.nome_cliente,
            renda_mensal_centavos=dados.renda_mensal_centavos,
            valor_solicitado_centavos=dados.valor_solicitado_centavos,
            prazo_meses=dados.prazo_meses,
            finalidade=dados.finalidade,
            lgpd_consentimento=dados.lgpd_consentimento,
            status=SimulacaoStatus.PENDENTE_IA.value
        )
        self.db.add(simulacao)
        self.db.commit()
        self.db.refresh(simulacao)
        return simulacao

    def buscar_por_id(self, simulacao_id: int) -> Optional[SimulacaoModel]:
        """Busca uma simulação específica pelo ID."""
        return self.db.query(SimulacaoModel).filter(SimulacaoModel.id == simulacao_id).first()

    def listar_por_status(self, status: Optional[str] = None) -> List[SimulacaoModel]:
        """Lista simulações aplicando opcionalmente um filtro por status."""
        query = self.db.query(SimulacaoModel)
        if status:
            query = query.filter(SimulacaoModel.status == status)
        return query.all()

    def atualizar_status_e_parecer(self, simulacao_id: int, status: str, parecer_ia: str, tokens_gastos: int) -> Optional[SimulacaoModel]:
        """Atualiza o resultado da análise feita pela IA."""
        simulacao = self.buscar_por_id(simulacao_id)
        if simulacao:
            simulacao.status = status
            simulacao.parecer_ia = parecer_ia
            simulacao.tokens_gastos = tokens_gastos
            self.db.commit()
            self.db.refresh(simulacao)
        return simulacao