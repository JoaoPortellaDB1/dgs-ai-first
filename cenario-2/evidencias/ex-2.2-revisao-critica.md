# Evidência — Exercício 2.2 (implementação SDD + revisão crítica)

**Ferramentas:** Claude para gerar `tasks.md` a partir do `plan.md`; geração assistida do código
(handler + validator) no padrão do `plan` (TypeScript, Zod, Azure Functions v4, pino).
**Conexão com Cenário 1:** o protótipo open-source (Dev 1.3, ChromaDB) validou a abordagem de RAG;
aqui o mesmo fluxo vira produção com Azure e os padrões do projeto. As tasks referenciam ADR-0002
(context budget) e ADR-0003 (contradições por vigência).

---

## Revisão crítica do código gerado

A primeira geração do handler (v1, "estilo Copilot cru") funcionava, mas tinha **3 problemas
reais** que reprovariam num code review. Todos corrigidos na versão final commitada.

### Problema 1 — `authLevel: "anonymous"` (segurança)
O Copilot gera Azure Functions com `authLevel: "anonymous"` por padrão. Para um endpoint que
consulta documentação **interna do cliente**, isso expõe a API sem autenticação.
- **Ajuste:** `authLevel: "function"` (mínimo), com nota no plan de que produção deve ficar
  atrás de APIM + Entra ID. → ver `handler.ts` (`app.http`).

### Problema 2 — Log da pergunta em nível `info` (vazamento de dado do cliente)
A v1 fazia `context.log(\`query: ${question}\`)`. A pergunta do atendente pode conter dado
do cliente (nome, nº de contrato, CT-e). Logar isso em `info` joga PII no log agregado.
- **Ajuste:** pergunta só em `log.debug`; `info` registra apenas metadado (`hasTier`).
  Logger pino com `redact` de `authorization`/`token`/`apiKey`. → ver `logger.ts` e `handler.ts`.

### Problema 3 — `await request.json()` sem try/catch (contrato de erro quebrado)
A v1 chamava `request.json()` direto. Body malformado lança e o runtime devolve **500**, quando
o correto para input inválido é **400**. Além disso, a v1 devolvia `error.message` ao cliente,
vazando detalhe interno.
- **Ajuste:** `try/catch` em torno do parse → 400 controlado; mensagens de erro genéricas ao
  cliente, detalhe só no log. → ver `handler.ts`.

### Bônus — `question` sem limite de tamanho (robustez / custo)
Sem `.max()`, uma pergunta gigante infla tokens e custo, e é vetor de abuso.
- **Ajuste:** `z.string().trim().min(1).max(1000)` no `validator.ts`.

---

## Mapa das correções

| Problema | v1 (geração crua) | Final (revisado) | Critério de aceite tocado |
|----------|-------------------|------------------|---------------------------|
| Auth | `anonymous` | `function` | — (segurança) |
| Log de PII | `question` em `info` | `debug` + redact | T-02: pergunta não logada em info |
| JSON malformado | 500 + `error.message` | 400 controlado, msg genérica | T-02: sem exceção vazando |
| Tamanho | sem limite | `.max(1000)` | T-01: rejeita payload abusivo |

**Nota de honestidade:** para evidência de **Copilot** especificamente, gerar o handler no
VS Code Copilot Chat e colar aqui o output cru (antes das correções) — os 3 problemas acima são
exatamente os que a geração crua apresenta.
