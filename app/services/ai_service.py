import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.simulacao_status_enum import SimulacaoStatus

class ParecerIADTO(BaseModel):
    status_sugerido: str = Field(..., description="Deve ser estritamente: APROVADO, REPROVADO ou ANALISE_MANUAL")
    taxa_juros_sugerida: float = Field(..., description="Taxa de juros mensal sugerida em percentual (ex: 2.15)")
    margem_comprometida_percentual: float = Field(..., description="Percentual comprometido da renda mensal com a parcela")
    motivo_tecnico: str = Field(..., description="Justificativa técnica detalhada baseada em risco de crédito")

class AIService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemma-4-26b-a4b-it",
            temperature=0.1, # baixa temperatura pra evitar respostas criativas
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        # força response estruturado
        self.structured_llm = self.llm.with_structured_output(ParecerIADTO)

    def analisar_credito(self, renda_centavos: int, valor_solicitado_centavos: int, prazo_meses: int, finalidade: str) -> Dict[str, Any]:
        """Analisa a proposta de crédito aplicando regras de negócio via IA estruturada."""
        
        # conversao de centavos para reais
        renda_reais = renda_centavos / 100
        valor_reais = valor_solicitado_centavos / 100
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um analista de risco de crédito sênior de um banco digital brasileiro. "
                       "Analise a solicitação de empréstimo considerando a renda mensal, o valor solicitado e o prazo. "
                       "Regras básicas: "
                       "1. Se a parcela estimada comprometer mais do que 35% da renda, o status deve ser REPROVADO ou ANALISE_MANUAL. "
                       "2. Forneça uma taxa de juros realista para o mercado PF brasileiro. "
                       "Retorne estritamente o formato solicitado."),
            ("user", "Dados da Simulação:\n"
                     f"- Renda Mensal: R$ {renda_reais:.2f}\n"
                     f"- Valor Solicitado: R$ {valor_reais:.2f}\n"
                     f"- Prazo: {prazo_meses} meses\n"
                     f"- Finalidade: {finalidade}")
        ])

        chain = prompt | self.structured_llm

        resultado: ParecerIADTO = chain.invoke({})
        
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