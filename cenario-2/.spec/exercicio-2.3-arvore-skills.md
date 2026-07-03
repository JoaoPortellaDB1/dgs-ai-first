# Exercício 2.3 — Estratégia de Skills do Projeto

**Papel:** Desenvolvedor · **Cenário 2** · **Estrutura:** Anexo C (`/skills/{foundation,domain,artifact}/`)
**SKILL.md base gerado:** [`skills/foundation/typescript-conventions.md`](../skills/foundation/typescript-conventions.md)

---

## Hierarquia

- **Foundation** — convenções globais que valem para *qualquer* código do repo. Toda skill de
  nível acima pressupõe estas.
- **Domain** — padrões por camada/tecnologia (como um endpoint é estruturado, como um teste é escrito).
- **Artifact** — receitas de geração ponta a ponta ("crie um endpoint RAG completo"), que
  compõem skills de Foundation + Domain.

## Árvore de skills (criação e consumo multi-papel)

| Skill | Nível | Cria | Consome (papel + agente) | Frequência |
|-------|-------|------|--------------------------|------------|
| `typescript-conventions` | Foundation | Tech Lead | Todos os devs + Copilot/Claude Code | Altíssima (toda geração de TS) |
| `error-handling` | Foundation | Tech Lead | Devs + Copilot | Alta |
| `project-structure` | Foundation | Tech Lead | Devs + Copilot | Média (novos módulos) |
| `azure-functions-endpoint` | Domain | Dev Sênior | Devs + Copilot | Alta (vários endpoints) |
| `azure-ai-search-integration` | Domain | Dev Sênior | Devs + Copilot | Média |
| `react-components` | Domain | Dev (front) | Devs front + Copilot | Média (painel web) |
| `testing-patterns` | Domain | **QA** | Devs + QA + Copilot | Alta |
| `create-rag-endpoint` | Artifact | Dev Sênior | Devs + Copilot | Média |
| `create-integration-test` | Artifact | **QA** | Devs + QA + Copilot | Alta |
| `create-react-card` | Artifact | Dev (front) | Devs front + Copilot | Baixa/Média |
| `create-product-spec` | Artifact | **Product Specialist** | PS + Claude | Média (1 por módulo) |

**Visão de time (não é só para dev):** o QA é dono das skills de teste (`testing-patterns`,
`create-integration-test`) — quem define o padrão de qualidade é quem entende de qualidade.
O Product Specialist cria `create-product-spec` (template SDD de `requirements.md`). O Tech Lead
é dono das Foundation porque são as regras constitucionais do repo. Assim as skills refletem
autoria por competência, não "dev faz tudo".

## Dependências entre skills

```
create-rag-endpoint  ──requer──►  azure-functions-endpoint ──requer──►  typescript-conventions
        │                                 │                                    ▲
        └──requer──► azure-ai-search-integration ──requer──► error-handling ───┘

create-integration-test ──requer──► testing-patterns ──requer──► typescript-conventions
```

Toda Artifact declara no topo quais Foundation/Domain ler antes — é o que garante geração
consistente (o agente carrega a base antes da receita).

## Por que `typescript-conventions` é a Foundation mais importante

É a única skill consumida por **todas** as outras (Domain e Artifact). Se ela estiver fraca,
o Copilot gera `as any`, `console.log` e imports bagunçados que contaminam todo o resto.
Por isso é a escolhida para o SKILL.md concreto deste exercício.
