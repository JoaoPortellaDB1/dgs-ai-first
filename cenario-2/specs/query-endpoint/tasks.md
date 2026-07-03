# Tasks — Query Endpoint

**Papel:** Desenvolvedor · **Cenário 2 — Exercício 2.2**
**Deriva de:** `specs/query-endpoint/plan.md` (fornecido) · **Aprovação:** Tech Lead (Gate 2)
**Prior decisions:** ADR-0002 (context budget ~4K system + ~8K chunks), ADR-0003 (contradições
por vigência), system prompt em `/prompts/system-prompt.md`.

> Cada task é **atômica**: implementável e testável isoladamente. Estimativa: P (≤2h), M (meio dia), G (1-2 dias).

---

### T-01 — Schema e validação de input (Zod)
- **Descrição:** Definir `QueryRequestSchema` em `src/functions/query/validator.ts` e a função
  `parseQueryRequest(body)` que valida e devolve `{ success, data | error }`.
- **Critérios de aceite:**
  - `question` ausente ou vazia → erro de validação (nunca chega ao handler como válido).
  - `question` com mais de 1000 caracteres → rejeitada (proteção contra payload abusivo).
  - `clientTier`, quando presente, só aceita `Gold | Silver | Standard` (nunca "Platinum").
  - JSON malformado não lança exceção não tratada — retorna erro estruturado.
- **Dependências:** nenhuma.
- **Estimativa:** P

### T-02 — Handler HTTP com validação e contrato de erro
- **Descrição:** Implementar `src/functions/query/handler.ts` (Azure Functions v4, `app.http`),
  que lê o body, chama `parseQueryRequest`, e responde. Nesta task a busca/geração ainda é stub.
- **Critérios de aceite:**
  - `POST /api/query` sem campo `question` → **HTTP 400** com body `{ error, details }`.
  - `POST /api/query` com `question` válida → **HTTP 200** com envelope contendo `source_document` (stub por enquanto).
  - Toda resposta (200 e erro) inclui header `x-correlation-id`.
  - Nenhuma exceção interna vaza `message`/stack para o cliente.
  - Log estruturado via pino (nunca `console.log`); a pergunta do cliente **não** é logada em nível `info`.
- **Dependências:** T-01.
- **Estimativa:** M

### T-03 — Integração com Azure AI Search (retrieval)
- **Descrição:** `src/services/search.ts` — `queryIndex(question, topK=5)` usando a query key,
  devolvendo chunks com `source`, `section`, `doc_date`, `score`. Dedup por vigência (ADR-0003).
- **Critérios de aceite:**
  - Retorna no máximo `topK` chunks ordenados por score.
  - Quando há duas versões do mesmo documento, mantém a de `doc_date` mais recente.
  - Falha do AI Search vira erro tratado (não 500 cru) — retry com backoff.
- **Dependências:** T-02.
- **Estimativa:** M

### T-04 — Montagem de prompt com context budget (ADR-0002)
- **Descrição:** `src/services/prompt-builder.ts` — monta system prompt (de `/prompts/system-prompt.md`)
  + chunks + pergunta, respeitando ~4K system / ~8K chunks; ordena chunks anti *lost-in-the-middle*.
- **Critérios de aceite:**
  - Contexto total montado nunca excede o budget definido (trunca chunks excedentes, loga o corte).
  - Se todos os chunks são do FAQ (informal), injeta aviso de baixa confiança.
  - Se há conflito de versão residual, injeta a nota da ADR-0003.
- **Dependências:** T-03.
- **Estimativa:** M

### T-05 — Geração via Azure OpenAI e envelope de resposta
- **Descrição:** `src/services/completion.ts` + `response-builder.ts` — chama GPT-4o e devolve
  `{ answer, source_document[], confidence, correlationId }`.
- **Critérios de aceite:**
  - `source_document` presente em 100% das respostas (mesmo confiança baixa) — VC-02 do QA.
  - Timeout e retry com backoff exponencial nas chamadas Azure.
  - Resposta cabe no contrato Zod de saída (`QueryResponseSchema`).
- **Dependências:** T-04.
- **Estimativa:** M

### T-06 — Validação determinística da resposta (harness)
- **Descrição:** `src/services/response-validator.ts` — checagem pós-geração: a resposta contém
  citação de fonte? menciona tier inexistente? Bloqueia/deriva se falhar (enforcement determinístico).
- **Critérios de aceite:**
  - Resposta sem `source_document` é rejeitada antes de sair.
  - Menção a tier fora de `Gold/Silver/Standard` é sinalizada.
- **Dependências:** T-05.
- **Estimativa:** P

---

**Ordem de execução:** T-01 → T-02 → T-03 → T-04 → T-05 → T-06.
**Implementado nesta entrega:** T-01 e T-02 (setup + validação), conforme pedido no exercício.
