# Plataforma de Análise de Crédito para Pessoa Física com IA 

Sistema de automação e apoio à decisão para concessão de crédito a Pessoa Física (PF), desenvolvido com arquitetura orientada a microsserviços (BFF), motor de IA baseado em LangChain/Pydantic e ciclo de feedback humano (*Human-in-the-Loop*).

## Arquitetura & Tecnologias
* **Backend:** FastAPI (Python 3.14) estruturado como Backend for Frontend (BFF).
* **Persistência & Migrações:** MySQL 8.0 gerenciado via SQLAlchemy e Alembic.
* **Motor de IA:** Integração com LLM via API do Google GenAI / LangChain com saída estrita estruturada (Pydantic Schema).
* **Infraestrutura:** Containerização completa via Docker Compose.
* **Governança:** Controles de LGPD (consentimento de dados), rastreabilidade de tokens/custos e auditoria de decisões.


## Desenho da Jornada
1. **Jornada do Cliente (Público / Mobile):** Envio de dados cadastrais e simulação de crédito com aceite explícito de LGPD.
2. **Motor de Decisão (IA):** O modelo analisa a proposta à luz das políticas de crédito vigentes e emite um parecer estruturado (`APROVADO_IA`, `REPROVADO_IA` ou `ANALISE_MANUAL`) com zero alucinação de taxas.
3. **Mesa de Crédito (Back-Office / Web):** O analista humano consulta as simulações pendentes e realiza a aprovação/rejeição final, gerando dados de feedback para auditoria e evolução contínua.


## Como Executar

### 1. Clone o repositório:

```bash
git clone https://github.com/andrewschiozo/analise_credito_ia.git
cd analise_credito_ia
```

### 2. .env
```bash
cp .env.example .env
```
(Preencha sua GOOGLE_API_KEY dentro do .env)

### 3. Docker compose
```bash
docker compose up --build
```

ou com as dependências de dev

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```
### 4. URLs
Swagger UI: http://localhost:8082/docs