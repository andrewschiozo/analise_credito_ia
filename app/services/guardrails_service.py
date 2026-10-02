from fastapi import HTTPException, status
import re
import app.core.simulacao_status_enum as SimulacaoStatus

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

        if status_sugerido == SimulacaoStatus.APROVADO.value and (taxa_juros < 1.2 or taxa_juros > 12.0):
            raise ValueError(f"Output Guardrail: Taxa de juros sugerida ({taxa_juros}%) está fora dos limites permitidos.")
            
        return True