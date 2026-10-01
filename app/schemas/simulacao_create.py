from pydantic import BaseModel, Field, field_validator

class SimulacaoCreateSchema(BaseModel):
    cpf: str = Field(..., description="CPF do cliente contendo apenas números", min_length=11, max_length=11)
    nome_cliente: str = Field(..., description="Nome completo do cliente", min_length=3, max_length=255)
    renda_mensal_centavos: int = Field(..., description="Renda mensal informada em centavos", gt=0)
    valor_solicitado_centavos: int = Field(..., description="Valor do empréstimo solicitado em centavos", gt=0)
    prazo_meses: int = Field(..., description="Prazo desejado em meses", ge=1, le=360)
    finalidade: str = Field(..., description="Finalidade do crédito (ex: Capital de Giro, Reforma, Veículo)", max_length=100)
    lgpd_consentimento: bool = Field(..., description="Consentimento explícito para tratamento de dados (LGPD)")

    @field_validator("lgpd_consentimento")
    @classmethod
    def validar_consentimento_lgpd(cls, v: bool) -> bool:
        if not v:
            raise ValueError("O consentimento da LGPD é obrigatório para realizar a simulação de crédito.")
        return v