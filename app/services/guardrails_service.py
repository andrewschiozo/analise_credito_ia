import os
import re

from fastapi import HTTPException, status
from app.core.simulacao_status_enum import SimulacaoStatus

class GuardrailsService:
    def validar_entrada(self, finalidade: str) -> bool:
        """Input Guardrail: Barra tentativas de prompt injection ou entradas maliciosas."""

        padroes_bloqueados = [
            r"\b(ignore|esqueça|desconsidere)\b.*\b(regras|instruções)\b",
            r"\b(você é um|aja como|finja)\b",
            r"\bsystem prompt\b"
        ]

        for padrao in padroes_bloqueados:
            if re.search(padrao, finalidade, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entrada bloqueada por políticas de segurança."
                )
        return True

    def validar_saida_ia(self, taxa_juros: float, status_sugerido: str) -> bool:
        """Output Guardrail: Impede que a IA devolva dados fora das políticas do banco."""
        
        taxa_minima = float(os.getenv("TAXA_JUROS_MINIMA"))
        taxa_maxima = float(os.getenv("TAXA_JUROS_MAXIMA"))
        
        if status_sugerido == SimulacaoStatus.APROVADO_IA.value and (taxa_juros < taxa_minima or taxa_juros > taxa_maxima):
            raise ValueError(f"Output Guardrail: Taxa de juros sugerida ({taxa_juros}%) está fora dos limites permitidos.")
            
        return True