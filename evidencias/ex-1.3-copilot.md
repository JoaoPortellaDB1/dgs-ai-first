# Evidência — Exercício 1.3: Uso do GitHub Copilot

Este arquivo documenta como o GitHub Copilot foi utilizado durante o desenvolvimento
do pipeline de RAG. O Copilot foi ativado no VS Code e usado para autocompletar,
gerar funções e sugerir tratamentos de edge cases.

---

## Interação 1 — Função de chunking semântico (ingest.py)

**Contexto:** Precisava de uma função que dividisse documentos Markdown por seção
(##, ###) mas que mantivesse tabelas inteiras, sem cortar no meio.

**Prompt digitado no comentário (Copilot inline):**
```python
# split markdown document by section headers (##, ###)
# keep tables intact as single chunks regardless of size
# max 500 tokens per chunk with 50 token overlap
def split_into_chunks(filename, content):
```

**Sugestão do Copilot (trecho):**
```python
def split_into_chunks(filename, content):
    sections = re.split(r'(?=\n#{1,3} )', content)
    chunks = []
    for section in sections:
        if '|' in section:  # table detected
            chunks.append(section)
        elif len(section) > 500:
            # split large sections by paragraph
            ...
```

**O que modifiquei:** A detecção de tabela pelo Copilot era frágil (`'|' in section`
pegaria qualquer pipe, não só tabelas Markdown). Substituí por verificação de padrão
`\|.*\|` em linha própria. Também adicionei o cálculo de tokens via `estimate_tokens()`
em vez de `len(section) > 500` (que conta caracteres, não tokens).

**Julgamento aplicado:** O Copilot gerou a estrutura base corretamente, mas o critério
de detecção de tabela era impreciso. A versão final usa lógica mais robusta.

---

## Interação 2 — Deduplicação de versões em search.py

**Contexto:** O pipeline recuperava chunks do PROC-042 v1 e v2 ao mesmo tempo,
potencialmente misturando multiplicadores diferentes na mesma resposta.

**Prompt no comentário:**
```python
# when multiple chunks from different versions of same document are returned,
# keep only the most recent by doc_date metadata
# doc families identified by prefix like "PROC-042" from filename
def _deduplicate_versions(results):
```

**Sugestão do Copilot:**
```python
def _deduplicate_versions(results):
    seen = {}
    for r in results:
        key = r['metadata']['source'].split('-v')[0]
        if key not in seen or r['metadata']['doc_date'] > seen[key]['metadata']['doc_date']:
            seen[key] = r
    return list(seen.values())
```

**O que modifiquei:** A lógica de extração de família com `.split('-v')[0]` funcionaria
para "PROC-042-v2" mas falharia para "POL-001-politica-devolucao.md" (sem `-v`).
Substituí por regex `re.match(r'([A-Z]+-\d+)', source)` que captura apenas o código
do documento. Também mantive a ordem original de similaridade na lista retornada,
o que o Copilot não fez.

---

## Interação 3 — Estrutura do prompt_builder.py

**Contexto:** Precisava de função que recebesse chunks e pergunta e montasse
o prompt respeitando a anatomia estático/dinâmico e o orçamento de contexto.

**Prompt no comentário:**
```python
# build complete prompt for LLM
# static: system_prompt (~350 tokens)
# dynamic: client tier, retrieved chunks ordered to avoid lost-in-the-middle,
#          conversation history (last 6 turns), user query
def build_prompt(query, chunks, client_tier=None, conversation_history=None):
```

**Sugestão do Copilot:** Gerou a estrutura de `parts = []` com `"\n".join(parts)` no final,
e a lógica básica de adicionar cada seção. Não incluiu a ordenação anti-lost-in-middle
nem os avisos de conflito de versão.

**O que adicionei:** Funções `_order_lost_in_middle()`, `_has_version_conflict()` e
`_is_faq_only()` — todas desenvolvidas manualmente porque requeriam julgamento de
arquitetura (não são geráveis por autocomplete sem contexto do projeto).

---

## Resumo

| Módulo | Copilot usou | Eu modifiquei / adicionei |
|--------|-------------|--------------------------|
| ingest.py | Estrutura de split por seção, loop de parágrafos | Detecção de tabela, cálculo de tokens real, overlap |
| search.py | Estrutura de deduplicação | Regex de família, preservação de ordem |
| prompt_builder.py | Estrutura de `parts = []` | Ordenação lost-in-middle, detecção de conflito, aviso de FAQ |
| test_pipeline.py | Estrutura do loop de testes, `json.dump` | Função `evaluate_retrieval` com critério FULL/SOURCE_ONLY/PARTIAL/MISS |

**Conclusão:** O Copilot acelerou a escrita da estrutura repetitiva e do boilerplate,
mas todas as decisões de arquitetura (deduplicação, ordenação, avaliação de retrieval)
foram implementadas com julgamento próprio após avaliar o que o Copilot sugeriu.
