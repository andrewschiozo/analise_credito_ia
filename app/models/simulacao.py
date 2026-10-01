from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Text, Enum as SQLAlchemyEnum
from app.core.database import Base
from app.core.simulacao_status_enum import SimulacaoStatus

class SimulacaoModel(Base):
    __tablename__ = "simulacoes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpf = Column(String(11), index=True, nullable=False)
    nome_cliente = Column(String(255), nullable=False)
    renda_mensal_centavos = Column(BigInteger, nullable=False)
    valor_solicitado_centavos = Column(BigInteger, nullable=False)
    prazo_meses = Column(Integer, nullable=False)
    finalidade = Column(String(100), nullable=False)

    lgpd_consentimento = Column(Boolean, nullable=False, default=False)
    lgpd_data_aceite = Column(DateTime, default=datetime.utcnow)

    status = Column(String(50), nullable=False, default=SimulacaoStatus.PENDENTE_IA.value)
    parecer_ia = Column(Text, nullable=True)

    analista_id = Column(String(100), nullable=True)
    observacao_humana = Column(Text, nullable=True)

    tokens_gastos = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)