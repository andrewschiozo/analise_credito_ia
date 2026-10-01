# Specs: Plataforma de Análise de Crédito PF

## 1. Visão Geral do Sistema
O sistema atua como um Backend-for-Frontend (BFF) em Python/FastAPI, gerenciando duas jornadas distintas:
1. **Jornada do Cliente (Mobile/Público):** Submissão de dados cadastrais e simulação de crédito com consentimento LGPD explícito.
2. **Jornada do Back-Office (Mesa de Crédito/Gerência):** Análise gerencial, visualização do parecer da IA, auditoria e aprovação/rejeição humana (*Human-in-the-Loop*).


## 2. Diretrizes de Arquitetura e Padrões de Código
Para garantir manutenibilidade, testabilidade e aderência a padrões sêniores de engenharia de software, o projeto seguirá rigorosamente:
* **Clean Code & Orientação a Objetos (OOP):** Classes coesas, responsabilidades bem definidas, uso intensivo de tipagem estrita (`typing` / Pydantic) e tratamento customizado de exceções. Nenhuma lógica de negócio complexa deve residir diretamente nos arquivos de rotas (controllers).
* **Arquitetura Hexagonal / Clean Architecture Simplificada:**
  * **Core / Domain:** Regras de negócio puras, entidades e contratos desacoplados de frameworks.
  * **Adapters / Infrastructure:** Camada de persistência (SQLAlchemy/MySQL) e integração externa (API do Google GenAI / LangChain).
  * **Entrypoints / API:** Rotas do FastAPI (BFF) atuando estritamente como adaptadores de entrada (recebem HTTP, validam payload e delegam para os serviços).


## 3. Arquitetura de Dados (MySQL / SQLAlchemy)

### Tabela: `simulacoes`
Guarda o ciclo de vida completo da proposta de crédito. Todos os valores monetários são armazenados em **centavos** (inteiros) para evitar erros de arredondamento.
* `id` (INT, PK, Auto Increment)
* `cpf` (VARCHAR(11), Indexado)
* `nome_cliente` (VARCHAR(255))
* `renda_mensal_centavos` (BIGINT) - Ex: R$ 5.000,00 armazenado como `500000`
* `valor_solicitado_centavos` (BIGINT) - Ex: R$ 20.000,00 armazenado como `2000000`
* `prazo_meses` (INT)
* `finalidade` (VARCHAR(100))
* `lgpd_consentimento` (BOOLEAN, Obrigatório)
* `lgpd_data_aceite` (TIMESTAMP)
* `status` (ENUM: `PENDENTE_IA`, `APROVADO_IA`, `REPROVADO_IA`, `ANALISE_MANUAL`, `APROVADO_HUMANO`, `REJEITADO_HUMANO`)
* `parecer_ia` (TEXT / JSON) - Justificativa técnica, score de risco e taxa sugerida gerada pela IA.
* `analista_id` (VARCHAR(100), Nullable) - Identificação do gerente que avaliou no back-office.
* `observacao_humana` (TEXT, Nullable) - Comentário do analista humano.
* `tokens_gastos` (INT) - Métrica de consumo da IA.
* `created_at` (TIMESTAMP)
* `updated_at` (TIMESTAMP)


## 4. Contrato de Endpoints (BFF)

### 4.1. Jornada do Cliente (Público)
* **`POST /api/v1/client/simulacoes`**
  * *Payload:* Dados da proposta (com valores em centavos) + `lgpd_consentimento: true`.
  * *Comportamento:* Valida o aceite LGPD, salva a simulação com status `PENDENTE_IA`, aciona o motor de IA do Gemini/LangChain de forma síncrona/estruturada e atualiza o status de acordo com o parecer.
* **`GET /api/v1/client/simulacoes/{id}`**
  * *Comportamento:* Permite ao cliente consultar o status atual da sua simulação e o parecer emitido.

### 4.2. Jornada do Back-Office (Mesa de Crédito)
* **`GET /api/v1/backoffice/simulacoes`**
  * *Query Params:* Filtrar por `status` (ex: `ANALISE_MANUAL`, `PENDENTE_IA`).
  * *Comportamento:* Lista todas the propostas para a equipe de análise humana.
* **`PATCH /api/v1/backoffice/simulacoes/{id}/analise`**
  * *Payload:* `acao` (`APROVAR` ou `REJEITAR`), `observacao_humana`, `analista_id`.
  * *Comportamento:* Executa o *Human-in-the-Loop*, alterando o status final (`APROVADO_HUMANO` ou `REJEITADO_HUMANO`) e salvando o feedback que servirá de histórico/auditoria.


## 5. O Motor de IA e Schema Pydantic (prevenção de alucinação)
Para garantir que a IA devolva estritamente dados corporativos válidos, a saída será forçada via Pydantic:
* `status_sugerido`: `APROVADO`, `REPROVADO` ou `ANALISE_MANUAL`
* `taxa_juros_sugerida`: float (ex: 1.85)
* `margem_comprometida_percentual`: float
* `motivo_tecnico`: string detalhando as regras de crédito violadas ou atendidas.