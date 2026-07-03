# Evidência — Exercício 2.1 (uso de ferramentas + iteração)

**Ferramenta:** assistente de geração de código (Claude Code — mesmo tipo de agente que o Copilot).
Fluxo: **gerar `.mcp.json` cru → avaliar (segurança) → refinar**.

---

## 1. Prompt de geração

> "Complete o `.mcp/mcp.json` a partir do exemplo mínimo do Anexo C (github + filesystem),
> adicionando os servers do projeto NovaTech: Azure AI Search, Azure OpenAI, Azure DevOps e Confluence."

## 2. Geração crua (v1 — output direto, sem revisão de segurança)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_abc123..." }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "azure-ai-search": {
      "command": "npx",
      "args": ["-y", "@azure/mcp-ai-search"],
      "env": { "AZURE_SEARCH_ADMIN_KEY": "xxxxx" }
    },
    "azure-openai": {
      "command": "npx",
      "args": ["-y", "@azure/mcp-openai"],
      "env": { "AZURE_OPENAI_API_KEY": "xxxxx" }
    },
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp"],
      "env": { "AZURE_DEVOPS_PAT": "xxxxx" }
    },
    "confluence": {
      "command": "npx",
      "args": ["-y", "mcp-atlassian"],
      "env": { "CONFLUENCE_API_TOKEN": "xxxxx" }
    }
  }
}
```

## 3. Avaliação crítica do v1 (revisão de segurança — "devil's advocate")

| # | Problema no v1 | Por que é grave | Correção |
|---|----------------|-----------------|----------|
| 1 | Token literal (`github_pat_abc123...`) | Segredo commitado no repo → vazamento | Referência `${GITHUB_TOKEN}` (env) |
| 2 | `filesystem` com `"."` (raiz) | Expõe `.env`, `infra/` (Bicep de prod), `.mcp/` | Restringir a `./src ./specs ./skills ./prompts` |
| 3 | `AZURE_SEARCH_ADMIN_KEY` | Admin key deixa o agente recriar/apagar índice | **Query key** + `MCP_READ_ONLY=true` |
| 4 | `@azure/mcp-ai-search` / `@azure/mcp-openai` | **Não existem** como pacotes públicos | Marcar como **custom (a construir)**: `node ./mcp-servers/.../dist/index.js` |
| 5 | Confluence sem `READ_ONLY_MODE` nem filtro de space | Dado do cliente exposto e escrita habilitada | `READ_ONLY_MODE=true` + `CONFLUENCE_SPACES_FILTER=NOVATECH` |
| 6 | Sem `type: "stdio"` | Formato incompleto vs. Anexo C | Adicionado em todos |

## 4. Versão refinada (v2 — commitada)

Ver [`../.mcp/mcp.json`](../.mcp/mcp.json). Diferença v1 → v2:

| Item | v1 | v2 |
|------|----|----|
| Segredos | tokens literais | `${ENV_VAR}` em todos |
| Filesystem | raiz `"."` | 4 pastas de trabalho |
| AI Search | admin key | query key + read-only |
| AI Search / OpenAI | pacotes públicos inexistentes | custom (`node ./mcp-servers/...`) |
| Confluence | escrita liberada | read-only + filtro de space |
| Least privilege | ausente | tabela de permissão por server (ver `.spec/exercicio-2.1`) |

**Resultado:** `.mcp.json` válido (JSON parseado), coerente com o mapeamento, e endurecido por
least privilege. As 3 análises de risco do documento principal saíram desta revisão.
