# Evidência — Exercício 3.2 (revisão crítica de código gerado por IA)

**Ferramenta:** revisão própria → Claude como 2º revisor → reescrita.
**Alvo:** `feedback-handler.ts` gerado pelo Copilot (simulado no enunciado).
**Referência:** AGENTS.md (TS strict, Zod, pino, nunca `console.log`, nunca logar dado pessoal,
imports estáticos).

---

## 1. Minha revisão (ANTES do Claude)

| # | Problema | Tipo | Linha |
|---|----------|------|-------|
| 1 | `body ... as any` sem validação | **Violação AGENTS.md** (falta Zod) | `const body = await request.json() as any` |
| 2 | `console.log('Feedback recebido:', ...)` | **Violação AGENTS.md** (deveria ser pino) | log |
| 3 | `const { CosmosClient } = require('@azure/cosmos')` | **Violação AGENTS.md** (import dinâmico, deveria ser estático no topo) | corpo da função |
| 4 | `attendantEmail` dentro do objeto logado | **Segurança / PII** (dado pessoal em log) | `JSON.stringify(feedback)` |
| 5 | Sem validação de `rating`/`queryId` | Bug potencial (aceita rating 999, queryId ausente) | — |
| 6 | `request.json()` sem try/catch | Bug (JSON inválido → 500 cru em vez de 400) | — |
| 7 | `CosmosClient` instanciado a cada request | Performance (deveria ser singleton) | — |
| 8 | `authLevel` não definido + retorno `body: 'OK'` | Segurança + contrato (endpoint aberto; retorno não estruturado) | `app.http` |

*(Os 4 primeiros são as armadilhas obrigatórias do exercício; identifiquei-as sem IA.)*

## 2. Segunda revisão (Claude) — comparação honesta

- **Coincidimos** nos 4 obrigatórios (1–4) e no 5, 6.
- **Claude acrescentou:** o `CosmosClient` por request (7) como problema de custo/latência sob carga,
  e a ausência de `x-correlation-id` para rastreabilidade — eu tinha pensado no 7 mas não no correlation id.
- **Eu tinha e o Claude não citou de imediato:** o `authLevel` ausente (endpoint anônimo) — segurança.
- Divergência de peso: o Claude classificou o `console.log` como "médio"; eu mantive "alto" porque,
  combinado com o `attendantEmail` no objeto, ele **é** o vetor do vazamento de PII (itens 2+4 juntos).

## 3. Código reescrito (commitado)

Ver [`../src/functions/feedback/handler.ts`](../src/functions/feedback/handler.ts) e
[`validator.ts`](../src/functions/feedback/validator.ts). Correções mapeadas:

| Problema v1 | Correção |
|-------------|----------|
| `as any` | `FeedbackSchema` (Zod) com `.strict()`, `safeParse` |
| `console.log` | `logger` (pino) com `child({correlationId})` |
| `require` dinâmico | `import { CosmosClient } from "@azure/cosmos"` no topo |
| `attendantEmail` logado | Log só de `queryId`+`rating`; pino com `redact` de `attendantEmail` |
| Sem validação | `rating` int 1–5, `queryId` não-vazio, `attendantEmail` email |
| `request.json()` sem guarda | `try/catch` → 400 |
| Cosmos por request | singleton de módulo |
| `authLevel` ausente / `body:'OK'` | `authLevel: "function"` + resposta JSON estruturada (201) |

**Nota:** o e-mail continua sendo **persistido** no Cosmos (é dado legítimo do registro), mas
**nunca logado** — a distinção entre "armazenar" e "logar" dado pessoal é o ponto.
