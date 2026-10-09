import json
import os

from sqlalchemy.orm import Session
from app.core.simulacao_status_enum import SimulacaoStatus
from app.repositories.simulacao_repository import SimulacaoRepository
from app.services.guardrails_service import GuardrailsService
from app.services.ai_service import AIService
from app.schemas.simulacao_create import SimulacaoCreateSchema
from app.models.simulacao import SimulacaoModel
from app.util.calculos import calcular_prestacao_price, calcular_margem_comprometida
from typing import Optional, List, Tuple

class CreditService:
    def __init__(self, db: Session):
        self.repository = SimulacaoRepository(db)
        self.guardrails_service = GuardrailsService()
        self.ai_service = AIService()

    def processar_nova_simulacao(self, dados: SimulacaoCreateSchema) -> SimulacaoModel:
        """Orquestra a criação da simulação, disparo síncrono da IA e atualização do status."""

        self.guardrails_service.validar_entrada(dados.finalidade)
        simulacao = self.repository.criar(dados)

        try:
            return self._executar_esteira_credito(simulacao)
        except Exception as e:
            return self._registrar_falha_sistema(simulacao.id, str(e))

    def _executar_esteira_credito(self, simulacao: SimulacaoModel) -> SimulacaoModel:
        """Coordena o funil qualitativo (IA) e o funil quantitativo (Matemática)."""

        analise_ia = self.ai_service.analisar_credito(
            simulacao.renda_mensal_centavos,
            simulacao.valor_solicitado_centavos,
            simulacao.prazo_meses,
            simulacao.finalidade
        )
        
        parecer_dict = json.loads(analise_ia["parecer_ia"])
        status_ia = analise_ia["status"]
        taxa_juros = parecer_dict.get("taxa_juros_sugerida", 0.0)

        self.guardrails_service.validar_saida_ia(taxa_juros, status_ia)

        if status_ia in [SimulacaoStatus.REPROVADO_IA.value, SimulacaoStatus.ANALISE_MANUAL.value]:
            return self._atualizar_simulacao(simulacao.id, status_ia, parecer_dict, analise_ia["tokens_gastos"])

        status_final, parecer_dict = self._avaliar_regras_quantitativas(simulacao, taxa_juros, parecer_dict)
        
        return self._atualizar_simulacao(simulacao.id, status_final, parecer_dict, analise_ia["tokens_gastos"])

    def _avaliar_regras_quantitativas(self, simulacao: SimulacaoModel, taxa_juros: float, parecer_dict: dict) -> Tuple[str, dict]:
        """Aplica a matemática financeira e impõe limites rígidos sobre o veredito da IA."""
        valor_reais = simulacao.valor_solicitado_centavos / 100
        renda_reais = simulacao.renda_mensal_centavos / 100
        
        parcela = calcular_prestacao_price(valor_reais, taxa_juros, simulacao.prazo_meses)
        margem = calcular_margem_comprometida(parcela, renda_reais)
        limite_margem = float(os.getenv("MARGEM_CONSIGNAVEL_MAXIMA"))

        parecer_dict["margem_calculada"] = round(margem, 2)

        if margem > limite_margem:
            parecer_dict["motivo_tecnico"] += f" [Revisado] Margem de {margem:.1f}% excedeu o limite de {limite_margem}%."
            return SimulacaoStatus.ANALISE_MANUAL.value, parecer_dict
            
        parecer_dict["motivo_tecnico"] += f" [Confirmado] Margem de {margem:.1f}%."
        return SimulacaoStatus.APROVADO_IA.value, parecer_dict

    def _atualizar_simulacao(self, simulacao_id: int, status: str, parecer_dict: dict, tokens: int) -> SimulacaoModel:
        """Atualiza a análise da simulação."""
        return self.repository.atualizar_status_e_parecer(
            simulacao_id=simulacao_id,
            status=status,
            parecer_ia=json.dumps(parecer_dict),
            tokens_gastos=tokens
        )

    def _registrar_falha_sistema(self, simulacao_id: int, erro: str) -> SimulacaoModel:
        """Garante que a simulação não se perca em caso de crash (timeout, alucinação grave)."""
        return self.repository.atualizar_status_e_parecer(
            simulacao_id=simulacao_id,
            status=SimulacaoStatus.ANALISE_MANUAL.value,
            parecer_ia=json.dumps({"erro_sistema": erro}),
            tokens_gastos=0
        )
 
    def obter_simulacao(self, simulacao_id: int) -> Optional[SimulacaoModel]:
        return self.repository.buscar_por_id(simulacao_id)

    def listar_simulacoes(self, status: Optional[str] = None) -> List[SimulacaoModel]:
        return self.repository.listar_por_status(status)