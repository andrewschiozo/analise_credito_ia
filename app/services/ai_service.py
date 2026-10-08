import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from app.core.simulacao_status_enum import SimulacaoStatus
from app.services.rag_service import RAGService

class ParecerIADTO(BaseModel):
    status_sugerido: str = Field(..., description="Deve ser estritamente: APROVADO, REPROVADO ou ANALISE_MANUAL")
    taxa_juros_sugerida: float = Field(..., description="Taxa de juros mensal sugerida em percentual (ex: 2.15)")
    margem_comprometida_percentual: float = Field(..., description="Percentual comprometido da renda mensal com a parcela")
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

    def analisar_credito(self, renda_centavos: int, valor_solicitado_centavos: int, prazo_meses: int, finalidade: str) -> Dict[str, Any]:
        """Analisa a proposta de crédito aplicando regras de negócio via IA estruturada."""

        # força response estruturado
        self.structured_llm = self.llm.with_structured_output(ParecerIADTO)

        # conversao de centavos para reais
        renda_reais = renda_centavos / 100
        valor_reais = valor_solicitado_centavos / 100

        conteudo_rag = self.rag_service.recuperar_contexto(finalidade)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um analista de risco de crédito sênior de um banco digital brasileiro. "
                       "Analise a solicitação de empréstimo considerando a renda mensal, o valor solicitado e o prazo. "
                       "Políticas do Banco : "
                       "{conteudo_rag}"
                       "Se a proposta violar qualquer regra, rejeite ou mande para análise manual. Retorne estritamente o formato solicitado."),
            ("user", "Dados da Simulação:\n"
                     "- Renda Mensal: R$ {renda_reais}\n"
                     "- Valor Solicitado: R$ {valor_reais}\n"
                     "- Prazo: {prazo_meses} meses\n"
                     "- Finalidade: {finalidade}")
        ])

        chain = prompt | self.structured_llm

        resultado: ParecerIADTO = chain.invoke({
            "renda_reais": f"{renda_reais:.2f}",
            "valor_reais": f"{valor_reais:.2f}",
            "prazo_meses": str(prazo_meses),
            "finalidade": finalidade,
            "conteudo_rag": conteudo_rag
        })
        
        # mapper status da IA para simulacao status enum
        mapa_status = {
            "APROVADO": SimulacaoStatus.APROVADO_IA.value,
            "REPROVADO": SimulacaoStatus.REPROVADO_IA.value,
            "ANALISE_MANUAL": SimulacaoStatus.ANALISE_MANUAL.value
        }
        
        status_final = mapa_status.get(resultado.status_sugerido.upper(), SimulacaoStatus.ANALISE_MANUAL.value)

        return {
            "status": status_final,
            "parecer_ia": resultado.model_dump_json(),
            "tokens_gastos": 150 # chumbado por enquanto
        }