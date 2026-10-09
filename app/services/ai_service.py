import os

from app.core.simulacao_status_enum import SimulacaoStatus
from app.services.rag_service import RAGService
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing import Dict, Any

class ParecerIADTO(BaseModel):
    status_sugerido: str = Field(..., description="Deve ser estritamente: APROVADO, REPROVADO ou ANALISE_MANUAL")
    taxa_juros_sugerida: float = Field(..., description="Taxa de juros mensal sugerida em percentual (ex: 2.15)")
    motivo_tecnico: str = Field(
        ..., 
        max_length=150,
        description="Justificativa técnica extremamente direta e concisa. Máximo 150 caracteres."
    )

class AIService:
    def __init__(self):
        
        self.llm = init_chat_model(
            model=os.getenv("AI_MODEL"),
            model_provider=os.getenv("AI_PROVIDER"),
            api_key=os.getenv("AI_API_KEY"),
            temperature=0.1,
            max_tokens=300,
            max_retries=0
        )

        self.rag_service = RAGService()
        self.structured_llm = self.llm.with_structured_output(ParecerIADTO)

    def analisar_credito(self, renda_centavos: int, valor_solicitado_centavos: int, prazo_meses: int, finalidade: str) -> Dict[str, Any]:
        """Analisa a proposta de crédito aplicando regras de negócio via IA estruturada."""

        renda_reais = renda_centavos / 100
        valor_reais = valor_solicitado_centavos / 100

        conteudo_rag = self.rag_service.recuperar_contexto(finalidade)
        prompt = self._montar_prompt()
        
        chain = prompt | self.structured_llm
        resultado = chain.invoke({
            "renda_reais": f"{renda_reais:.2f}",
            "valor_reais": f"{valor_reais:.2f}",
            "prazo_meses": str(prazo_meses),
            "finalidade": finalidade,
            "conteudo_rag": conteudo_rag
        })

        return self._formatar_resposta(resultado)
        
    def _montar_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", "Você é um analista de risco de crédito sênior de um banco digital brasileiro. "
                       "Analise a solicitação de empréstimo ESTRITAMENTE pelas Políticas do Banco abaixo.\n\n"
                       "Políticas do Banco:\n{conteudo_rag}\n\n"
                       "Se a proposta violar qualquer regra, devolva REPROVADO ou ANALISE_MANUAL."),
            ("user", "Dados da Simulação:\n"
                     "- Renda Mensal: R$ {renda_reais}\n"
                     "- Valor Solicitado: R$ {valor_reais}\n"
                     "- Prazo: {prazo_meses} meses\n"
                     "- Finalidade: {finalidade}")
        ])
    
    def _formatar_resposta(self, resultado: ParecerIADTO) -> Dict[str, Any]:
        mapa_status = {
            "APROVADO": SimulacaoStatus.APROVADO_IA.value,
            "REPROVADO": SimulacaoStatus.REPROVADO_IA.value,
            "ANALISE_MANUAL": SimulacaoStatus.ANALISE_MANUAL.value
        }
        
        status_final = mapa_status.get(resultado.status_sugerido.upper(), SimulacaoStatus.ANALISE_MANUAL.value)

        return {
            "status": status_final,
            "parecer_ia": resultado.model_dump_json(),
            "tokens_gastos": 0
        }