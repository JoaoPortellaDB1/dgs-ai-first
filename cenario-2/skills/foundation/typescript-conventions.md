# Skill (Foundation): typescript-conventions

**Nível:** Foundation · **Dono:** Tech Lead · **Consumida por:** todas as skills Domain e Artifact.
**Ativação:** "gerar/editar qualquer código TypeScript neste repositório".
**Dependências:** nenhuma (é a base da hierarquia).

> Esta é a skill-base do projeto NovaTech Assistant. Todo agente (Copilot, Claude Code) DEVE
> aplicar estas regras antes de qualquer padrão de camada. Derivada das ADRs do Cenário 1
> (TypeScript strict, pino, Zod).

---

## Regras prescritivas

1. **`strict: true` é lei.** DEVE compilar sem erros com `strict` ligado. NÃO DEVE usar `as any`
   nem `@ts-ignore` para silenciar o compilador — corrija o tipo.
2. **Sem `console.*`.** Todo log DEVE usar o logger pino de `src/shared/logger.ts`.
3. **Validar dado externo com Zod.** Todo input de fronteira (HTTP body, resposta de API externa,
   env) DEVE ser validado com um schema Zod antes de ser usado como tipo confiável.
4. **Imports estáticos e ordenados.** DEVE usar `import` estático no topo. NÃO DEVE usar
   `require()` dinâmico. Ordem: node builtins → libs externas → internos (`src/...`).
5. **Erros tipados.** Lançar erros de `src/shared/errors.ts` (custom errors), nunca `throw "string"`.
6. **Sem `any` implícito nem `!` gratuito.** Preferir narrowing e `unknown` a `any`; evitar o
   non-null assertion `!` — trate o caso nulo.
7. **`type`/`interface` explícito no contorno público** de funções exportadas (parâmetros e retorno).

---

## Exemplos (DO / DON'T)

### Validação de input

```typescript
// ✅ DO — valida com Zod, tipo derivado do schema
import { z } from "zod";
const BodySchema = z.object({ question: z.string().min(1).max(1000) });
export function parse(body: unknown) {
  return BodySchema.safeParse(body); // nunca confia no shape cru
}
```

```typescript
// ❌ DON'T — cast forçado, sem validação, sem tipo
export function parse(body: any) {
  return body as { question: string }; // mentira para o compilador
}
```

### Logging

```typescript
// ✅ DO
import { logger } from "../shared/logger";
logger.info({ tier }, "query processada");
```

```typescript
// ❌ DON'T
console.log("query processada " + tier); // proibido: sem estrutura, sem redaction
```

### Erros

```typescript
// ✅ DO
import { ValidationError } from "../shared/errors";
throw new ValidationError("clientTier inválido");
```

```typescript
// ❌ DON'T
throw "clientTier inválido"; // string solta, sem tipo, sem stack útil
```

---

## Anti-padrões que o Copilot realmente gera (e o que fazer)

| Anti-padrão gerado | Por que é ruim | Correção |
|--------------------|----------------|----------|
| `as any` / `as unknown as T` | Desliga o type-check; esconde bug em runtime | Modele o tipo ou valide com Zod |
| `console.log(...)` | Sem estrutura, sem redaction de PII, não vai pro sink de log | `logger.info/debug` (pino) |
| `const x = require("...")` dinâmico | Quebra tree-shaking e tipos; foge do strict | `import` estático no topo |
| `catch (e) { return e.message }` ao cliente | Vaza detalhe interno | Msg genérica ao cliente, detalhe no log |
| `foo!.bar` (non-null assertion em cascata) | Estoura em runtime quando é null | Narrowing / early-return |
| `function f(x)` sem tipo | `any` implícito silencioso | Tipar parâmetro e retorno |

---

## Critérios de maturidade desta skill

Considerada **madura** quando: testada com 3+ gerações reais de código no projeto, os anti-padrões
acima validados (o agente parou de gerá-los com a skill presente), e aprovada em review pelo
Tech Lead. Skill é artefato vivo — revisar a cada novo anti-padrão recorrente observado em PR.
