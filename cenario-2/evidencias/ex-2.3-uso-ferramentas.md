# Evidência — Exercício 2.3 (autoria e teste de skill)

**Ferramenta:** assistente de geração de código (Claude Code — mesmo tipo de agente que o Copilot).
Fluxo: **gerar SKILL.md cru → avaliar → refinar → testar empiricamente**.

---

## 1. Geração crua da skill (v1 — narrativa, do jeito que sai sem guidance)

> Prompt: "Crie o SKILL.md da skill Foundation `typescript-conventions` do projeto."

```markdown
# typescript-conventions

Use boas práticas de TypeScript neste projeto. Escreva código limpo e legível.
Ative o strict mode. Trate erros adequadamente. Evite usar `any`. Use nomes
descritivos para variáveis e funções. Faça logging quando apropriado. Valide
entradas do usuário. Mantenha os imports organizados.
```

## 2. Avaliação do v1 (contra a rubrica)

**Problema central:** é **narrativa/descritiva**, não **prescritiva**. Pela regra de corte
da skill de avaliação, skill narrativa → **D3 ≤ 1**. Um agente lê "trate erros adequadamente"
e não sabe o que fazer. Faltam:
- Exemplos de código **DO/DON'T** concretos.
- Anti-padrões **específicos** que o LLM realmente gera (não "evite any" genérico).
- Regra acionável (o que fazer no lugar de `console.log`, de `as any`, etc.).

## 3. Versão refinada (v2 — commitada)

Ver [`../skills/foundation/typescript-conventions.md`](../skills/foundation/typescript-conventions.md).
Mudanças concretas do v1 → v2:

| v1 (narrativo) | v2 (prescritivo) |
|----------------|------------------|
| "Evite usar any" | Tabela de anti-padrões: `as any` → modele o tipo ou valide com Zod (com exemplo) |
| "Faça logging quando apropriado" | "NÃO DEVE `console.*`; DEVE usar pino de `src/shared/logger.ts`" + bloco DO/DON'T |
| "Trate erros" | "Lançar erros de `src/shared/errors.ts`; nunca `throw \"string\"`" + exemplo |
| "Valide entradas" | Bloco DO com Zod `safeParse` vs DON'T com `body as T` |
| (nada) | Critérios de maturidade da skill (testada em 3+ gerações) |

## 4. Teste empírico da skill (o que muda no output do agente)

Mesmo prompt de geração de endpoint, **sem** e **com** a skill no contexto:

**SEM a skill** → o agente gerou o handler cru do exercício 2.2 (`authLevel: anonymous`,
`context.log` da pergunta, `as { question: string }`, `request.json()` sem guarda). 5 problemas.

**COM a skill** (`typescript-conventions` no contexto) → o agente gerou:
- `authLevel: "function"`;
- validação com **Zod** em vez de `as`;
- **pino** em vez de `console.log`, com a pergunta só em `debug`;
- `try/catch` no parse do body.

**Conclusão:** a skill mudou o comportamento do agente de forma verificável (5 problemas → 0
dos mesmos problemas). Isso confirma o critério "skill concreta melhora o output do Copilot".

## 5. Limitação reconhecida (honestidade)

A skill não é definitiva — é artefato vivo. Ela cobre convenções de TS, mas não impede, por
exemplo, um erro de lógica de negócio (usar multiplicador da versão errada do PROC-042). Isso
depende da skill de domínio + validação determinística (T-06). A skill sobe de "rascunho" para
"madura" só após 3+ gerações reais validadas em PR.
