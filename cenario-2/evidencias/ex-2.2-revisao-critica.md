# Evidência — Exercício 2.2 (implementação SDD + revisão crítica)

**Ferramenta:** assistente de geração de código (Claude Code — mesmo tipo de agente que o GitHub
Copilot; geração real, não mock). Fluxo: **gerar cru → avaliar → refinar**.
**Conexão com Cenário 1:** o protótipo open-source (Dev 1.3, ChromaDB) validou a abordagem de RAG;
aqui o mesmo fluxo vira produção Azure com os padrões do `plan.md`.

---

## 1. Prompt de geração (T-02)

> "Implemente a primeira task do query endpoint: um Azure Function HTTP trigger (v4) em
> `src/functions/query/handler.ts` que recebe POST com `question` e valida o input."

## 2. Geração crua (v1 — output direto do assistente, sem a skill de convenções aplicada)

```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

export async function queryHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const body = (await request.json()) as { question: string };
  context.log(`query recebida: ${body.question}`);

  if (!body.question) {
    return { status: 400, jsonBody: { error: "question is required" } };
  }

  // TODO: buscar chunks no AI Search e gerar resposta
  return { status: 200, jsonBody: { answer: "TODO", source_document: [] } };
}

app.http("query", {
  methods: ["POST"],
  authLevel: "anonymous",
  handler: queryHandler,
});
```

## 3. Avaliação crítica do v1 (o que reprovaria num code review)

| # | Problema no v1 | Por que é grave | Gravidade |
|---|----------------|-----------------|-----------|
| 1 | `authLevel: "anonymous"` | Endpoint que consulta doc interna do cliente exposto sem auth | Alta (segurança) |
| 2 | `context.log(\`query recebida: ${body.question}\`)` | A pergunta pode ter dado do cliente (nome, contrato, CT-e) → PII no log em nível info | Alta (privacidade) |
| 3 | `await request.json()` sem try/catch | Body malformado lança → runtime devolve **500**, quando o certo é **400** | Média (contrato de erro) |
| 4 | `as { question: string }` | Cast mente pro compilador; sem validação real (aceita `question` vazia, tipo errado, tamanho ilimitado) | Alta (correção) |
| 5 | Sem `x-correlation-id` | Impossível rastrear a request nos logs | Média (observabilidade) |

## 4. Versão refinada (v2 — commitada)

Correções aplicadas (ver [`../src/functions/query/handler.ts`](../src/functions/query/handler.ts)
e [`validator.ts`](../src/functions/query/validator.ts)):

| Problema v1 | Correção v2 |
|-------------|-------------|
| `authLevel: "anonymous"` | `authLevel: "function"` (+ nota: produção atrás de APIM/Entra) |
| Log da pergunta em `info` | Pergunta só em `log.debug`; `info` só com metadado; pino com `redact` |
| `request.json()` sem guarda | `try/catch` → **400** controlado; msg genérica ao cliente |
| `as { question: string }` | **Zod** `QueryRequestSchema` com `.min(1).max(1000)` e `clientTier` restrito a Gold/Silver/Standard |
| Sem correlation id | `x-correlation-id` gerado e ecoado em toda resposta |

**Resultado:** o v2 atende os critérios de aceite de T-01 e T-02. As correções vieram da
skill `typescript-conventions` (Foundation) — que é justamente o que o exercício 2.3 formaliza
para que a *próxima* geração já saia limpa.
