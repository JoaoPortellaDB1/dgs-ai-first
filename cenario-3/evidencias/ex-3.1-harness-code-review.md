# Evidência — Exercício 3.1 (structured output + verificações determinísticas)

**Ferramenta:** assistente de geração (Claude Code — mesmo tipo que o Copilot) + Claude para code review.
Fluxo: **gerar cru → code review → corrigir**.
**Conexão:** este é o `response-validator.ts` previsto na **task T-06** do `tasks.md` do Cenário 2, e
implementa em código (determinístico) os guardrails que o Product Specialist formalizou (Cenário 2)
e que a exceção de carga perigosa do POL-001 (Anexo A) exige.

---

## Probabilístico vs determinístico (a ideia central)

O **prompt** pede "cite a fonte" e "carga perigosa não pode ser devolvida" — mas isso é
**probabilístico**: o modelo pode esquecer. O structured output + este validador são
**determinísticos**: se o contrato ou os guardrails falham, a resposta é **bloqueada**, não só logada.

## 1. Geração crua (v1)

```typescript
import { z } from "zod";

export const AssistantResponseSchema = z.object({
  answer: z.string(),
  source_document: z.string(),
  confidence_score: z.number(),
});

export function validateResponse(raw: any) {
  const resp = AssistantResponseSchema.parse(raw);
  if (!resp.source_document) {
    console.log("resposta sem fonte");
  }
  if (resp.answer.includes("carga perigosa") && resp.answer.includes("devolução") &&
      !resp.answer.includes("não pode")) {
    console.log("possível inversão de regra");
  }
  return resp;
}
```

## 2. Code review (com Claude) — 4 problemas reais

| # | Problema | Por que importa | Correção |
|---|----------|-----------------|----------|
| 1 | **Só loga, não bloqueia** (`console.log` + `return resp`) | A resposta ruim segue pro atendente mesmo assim — o guardrail é decorativo | Retornar `{ ok:false, safeResponse }` e o chamador usa a resposta segura |
| 2 | **Schema sem `.strict()`** | Aceita campos extras que o modelo invente (ex: `internal_notes`) — vaza pra resposta | `.strict()` no schema |
| 3 | **Guardrail 2 frágil** (`includes("devolução")` / `includes("não pode")`) | Falha com "devolver"/"devolvida", com acentos e caixa; "não pode" não cobre "não é possível" | Normalizar (minúsculas, sem acento) + regex `/devolu[cv]/` + lista de padrões de negação |
| 4 | **Tipos frouxos** (`source_document: string`, `confidence_score` sem range, `raw: any`) | Aceita fonte vazia, confiança 7.5, e `parse` lança em vez de tratar | `source_document: z.array(...).min(1)`, `confidence_score.min(0).max(1)`, `safeParse` com `raw: unknown` |

## 3. Versão corrigida (commitada)

Ver [`../src/services/response-validator.ts`](../src/services/response-validator.ts):
- `AssistantResponseSchema` com `.strict()`, `source_document` como array não-vazio, `confidence_score` 0–1.
- `validateAssistantResponse` **bloqueia** e devolve `SAFE_RESPONSE` em qualquer falha (contrato ou guardrail).
- Guardrail 2 robusto: `mentionsDangerousReturn` (normalização + `/devolu[cv]/`) e `containsNegation` (7 padrões).

**Teste mental dos guardrails:**
- `{answer:"...", source_document:[], confidence_score:0.9}` → bloqueado (`sem_source_document`).
- `answer:"Sim, carga perigosa pode ser devolvida"` → bloqueado (`carga_perigosa_devolucao_sem_negativa`).
- `answer:"Carga perigosa NÃO pode ser devolvida pelo processo padrão"` → passa (tem negação).
- `{..., extra:"x"}` → bloqueado (`structured_output_invalido`, `.strict()`).
