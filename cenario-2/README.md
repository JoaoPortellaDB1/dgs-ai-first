# Cenário 2 — Fase de Estruturação do Trabalho

**Participante:** João Portella · **Papel:** Desenvolvedor
**Projeto de referência:** `db1/novatech-assistant` (estrutura no Anexo C)

Continuação do Cenário 1 (pipeline de RAG open-source, `../pipeline-rag/`). Aqui o foco é
**estruturar o ambiente e os artefatos que governam o desenvolvimento AI First**: MCP, SDD e Skills.
Estrutura de pastas espelha o Anexo C.

## Entregáveis

| Ex | Tema | Arquivos |
|----|------|----------|
| **2.1** | MCP servers + least privilege + riscos | [`.spec/exercicio-2.1-mcp-servers.md`](.spec/exercicio-2.1-mcp-servers.md), [`.mcp/mcp.json`](.mcp/mcp.json), [`evidencias/ex-2.1-uso-ferramentas.md`](evidencias/ex-2.1-uso-ferramentas.md) |
| **2.2** | SDD: tasks + 1ª task implementada + revisão | [`specs/query-endpoint/tasks.md`](specs/query-endpoint/tasks.md), [`src/functions/query/`](src/functions/query/), [`evidencias/ex-2.2-revisao-critica.md`](evidencias/ex-2.2-revisao-critica.md) |
| **2.3** | Estratégia de skills + SKILL.md Foundation | [`.spec/exercicio-2.3-arvore-skills.md`](.spec/exercicio-2.3-arvore-skills.md), [`skills/foundation/typescript-conventions.md`](skills/foundation/typescript-conventions.md) |

## Rastreabilidade com o Cenário 1

- ADR-0002 (context budget ~4K+~8K) → tasks T-04 e regra da skill / prompt-builder.
- ADR-0003 (contradições por vigência) → dedup em T-03 e aviso de conflito.
- Protótipo Dev 1.3 (ChromaDB) validou a abordagem RAG que aqui vira produção Azure.
