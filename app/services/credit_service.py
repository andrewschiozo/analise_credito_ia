from sqlalchemy.orm import Session
from app.core.simulacao_status_enum import SimulacaoStatus
from app.repositories.simulacao_repository import SimulacaoRepository
from app.services.ai_service import AIService
from app.schemas.simulacao_create import SimulacaoCreateSchema
from app.models.simulacao import SimulacaoModel
from typing import Optional, List

class CreditService:
    def __init__(self, db: Session):
        self.repository = SimulacaoRepository(db)
        self.ai_service = AIService()

    def processar_nova_simulacao(self, dados: SimulacaoCreateSchema) -> SimulacaoModel:
        """Orquestra a criação da simulação, disparo síncrono da IA e atualização do status."""
        
        # cria a simulação PENDENTE_IA
        simulacao = self.repository.criar(dados)

        try:
            # executa a análise de crédito com IA
            analise = self.ai_service.analisar_credito(
                renda_centavos=simulacao.renda_mensal_centavos,
                valor_solicitado_centavos=simulacao.valor_solicitado_centavos,
                prazo_meses=simulacao.prazo_meses,
                finalidade=simulacao.finalidade
            )

            # atualiza a simulação com o resultado
            simulacao_atualizada = self.repository.atualizar_status_e_parecer(
                simulacao_id=simulacao.id,
                status=analise["status"],
                parecer_ia=analise["parecer_ia"],
                tokens_gastos=analise["tokens_gastos"]
            )
            return simulacao_atualizada

        except Exception as e:
            # se falhar, não perde a simulação, apenas marca como ANALISE_MANUAL e registra o erro
            self.repository.atualizar_status_e_parecer(
                simulacao_id=simulacao.id,
                status=SimulacaoStatus.ANALISE_MANUAL.value,
                parecer_ia=f'{{"erro_ia": "{str(e)}"}}',
                tokens_gastos=0
            )
            return self.repository.buscar_por_id(simulacao.id)

    def obter_simulacao(self, simulacao_id: int) -> Optional[SimulacaoModel]:
        return self.repository.buscar_por_id(simulacao_id)

    def listar_simulacoes(self, status: Optional[str] = None) -> List[SimulacaoModel]:
        return self.repository.listar_por_status(status)