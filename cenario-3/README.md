# Cenário 3 — Fase de Governança e Validação

**Participante:** João Portella · **Papel:** Desenvolvedor
**Tópicos:** Harness Engineering (structured outputs + HITL) e Revisão Crítica de outputs de IA.

Fecha a trilha: usa as ADRs e o pipeline do Cenário 1 e o AGENTS.md/specs/skills/guardrails do
Cenário 2, amarrando tudo num harness de governança antes do go-live.

## Entregáveis

| Ex | Tema | Arquivos |
|----|------|----------|
| **3.1** | Structured output + verificações determinísticas | [`src/services/response-validator.ts`](src/services/response-validator.ts), [`evidencias/ex-3.1-harness-code-review.md`](evidencias/ex-3.1-harness-code-review.md) |
| **3.2** | Revisão crítica de código gerado por IA | [`src/functions/feedback/`](src/functions/feedback/handler.ts), [`evidencias/ex-3.2-revisao-feedback.md`](evidencias/ex-3.2-revisao-feedback.md) |

## Rastreabilidade

- 3.1 = task **T-06** do `tasks.md` do Cenário 2 (validação determinística da resposta).
- 3.1 implementa em código os **guardrails** do Product Specialist (Cenário 2) e a exceção de
  carga perigosa do **POL-001** (Anexo A).
- 3.2 aplica o **AGENTS.md** (Cenário 2) como régua da revisão; o `typescript-conventions`
  (skill Foundation do Cenário 2) já previa os anti-padrões encontrados (`as any`, `console.log`, `require` dinâmico).
