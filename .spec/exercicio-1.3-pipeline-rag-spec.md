# Exercício 1.3 — Especificação do Pipeline de RAG

## Arquitetura

Pipeline de RAG local usando ferramentas open-source, sem custo de API para embeddings.

```
Documentos .md
      ↓
  ingest.py          → ChromaDB (chroma_db/)
  (chunking +
   embeddings)
      ↓
  search.py          ← pergunta do atendente
  (busca semântica)
      ↓
  prompt_builder.py  → prompt completo
  (monta contexto)
      ↓
  LLM (Claude)       → resposta com citação de fonte
```

## Stack técnica

| Componente | Ferramenta | Motivo |
|------------|-----------|--------|
| Linguagem | Python 3.10+ | Stack padrão para ML/NLP |
| Embeddings | sentence-transformers `paraphrase-multilingual-MiniLM-L12-v2` | Suporte a PT-BR; gratuito |
| Vector store | ChromaDB (local) | Zero configuração; persiste em disco |
| LLM | Claude (via chat manual) | Sem custo de API para PoC |

## Módulos

### ingest.py
- Lê arquivos .md da pasta `docs/`
- Extrai metadados: `source`, `doc_version`, `doc_date`, `source_quality`
- Chunking semântico por seção Markdown (##, ###)
- Máximo 500 tokens por chunk, overlap de 50 tokens
- Tabelas Markdown mantidas inteiras como chunk único
- Gera embeddings e persiste no ChromaDB

### search.py
- Recebe query em linguagem natural
- Gera embedding da query com o mesmo modelo
- Busca N chunks mais similares (similaridade coseno)
- Deduplicação: quando dois chunks são da mesma família de documento (ex: PROC-042),
  mantém apenas o da versão mais recente (por `doc_date`)

### prompt_builder.py
- System prompt com 8 regras (estático, ~280 tokens)
- Contexto do cliente: tier atual (dinâmico, ~20 tokens)
- Avisos automáticos: conflito de versões, FAQ como única fonte
- Ordenação anti-lost-in-middle: melhor chunk no início, segundo no fim
- Histórico de conversa: últimas 6 trocas (dinâmico, ~600 tokens)
- Orçamento total estimado: ~3.500 tokens por query

### test_pipeline.py
- 5 casos de teste com perguntas realistas do domínio de logística
- Avaliação de retrieval: FULL / SOURCE_ONLY / PARTIAL / MISS
- Critério FULL: fonte correta E seção correta recuperadas
- Gera `test_results.json` com prompt pronto para colar no LLM

## Problemas identificados e mitigações

### Problema 1: PROC-042 v1 e v2 coexistem na base
Se ambas as versões forem recuperadas, o prompt pode ter multiplicadores contraditórios.

**Mitigação:** Deduplicação em `search.py` por família de documento + data mais recente.
Adicionalmente, o `prompt_builder.py` detecta conflito residual e injeta aviso no contexto.

### Problema 2: FAQ como fonte informal para perguntas críticas
O FAQ não foi validado por Compliance. Usar FAQ para informar prazos legais é arriscado.

**Mitigação:** Metadado `source_quality: "informal"` nos chunks do FAQ.
O `prompt_builder.py` detecta quando todos os chunks são do FAQ e injeta aviso ao LLM.
