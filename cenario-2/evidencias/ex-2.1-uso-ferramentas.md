# Evidência — Exercício 2.1 (uso de ferramentas + iteração)

**Ferramentas:** Claude (chat) para mapeamento e revisão crítica; geração do `.mcp/mcp.json`
como artefato de código. *Nota de honestidade:* o `mcp.json` foi gerado e revisado em ambiente
assistido por IA; para capturar evidência de **Copilot** especificamente, basta reabrir o
`.mcp/mcp.json` no VS Code e pedir ao Copilot Chat "complete os servers Azure faltantes seguindo
o exemplo do Anexo C" — o conteúdo abaixo já reflete o resultado refinado.

---

## Rodada 1 — mapeamento inicial (rascunho)

Prompt (resumo): *"Mapear os MCP servers do projeto NovaTech a partir do Anexo C e da lista de
ferramentas (GitHub, Azure AI Search, Azure OpenAI, Azure DevOps, Confluence). Para cada um:
tools/resources/prompts, quem consome, público ou custom."*

Saída v1 (resumida) e **problemas que a auto-revisão pegou:**

1. **AI Search com admin key.** A v1 configurava o server de AI Search com a chave de
   administração ("porque é mais simples"). ❌ Viola least privilege — admin key permite
   recriar/apagar índice. → **Corrigido:** trocado para **query key** + `MCP_READ_ONLY=true`.

2. **Filesystem apontando para `.` (raiz).** A v1 liberava o repo inteiro. ❌ Expõe `.env`,
   `infra/` (Bicep de produção) e o próprio `.mcp/`. → **Corrigido:** restrito a
   `./src ./specs ./skills ./prompts`.

3. **AI Search e OpenAI marcados como "públicos".** ❌ Não existem servers MCP oficiais para
   AI Search / Azure OpenAI. → **Corrigido:** marcados como **custom (a construir)**, com
   `command: node ./mcp-servers/.../dist/index.js`, o que também é critério do exercício
   ("existe como público ou precisa ser construído?").

4. **Tokens literais no JSON.** A v1 tinha placeholders com aparência de token real.
   → **Corrigido:** tudo via `${ENV_VAR}`.

## Rodada 2 — revisão de segurança (Claude como devil's advocate)

Prompt (resumo): *"Aja como revisor de segurança. Que ataques esse mcp.json permite?"*

Contribuições incorporadas ao documento final:
- **Prompt injection** em conteúdo recuperado (AI Search/Confluence) acionando tools de escrita
  (GitHub/DevOps) → mantido gate humano nas tools de efeito colateral (risco 2).
- **Confluence = dado do cliente** saindo para modelo cloud → `READ_ONLY_MODE` + filtro de space
  + roteamento só para o Azure OpenAI do tenant (risco 1).

---

## Diferença v1 → final (o que mudou de fato)

| Item | v1 | Final |
|------|----|-------|
| AI Search | admin key | **query key** + read-only |
| Filesystem | raiz do repo | 4 pastas de trabalho |
| AI Search / OpenAI | "públicos" | **custom (a construir)** |
| Segredos | placeholders | `${ENV_VAR}` |
| Riscos | genéricos ("alguém pode invadir") | 3 riscos específicos com mitigação acionável |
