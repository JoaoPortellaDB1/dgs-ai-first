# dgs-ai-first — Certificação AI First DB1 | Fase 1

**Participante:** João Portella  
**Papel:** Desenvolvedor  
**Cenário:** Assistente de IA com RAG para a NovaTech (empresa de logística)

---

## O que é este projeto

Prova de conceito de um pipeline de RAG (Retrieval-Augmented Generation) que permite
ao time de atendimento da NovaTech fazer perguntas em linguagem natural e receber respostas
baseadas na documentação oficial da empresa, com citação de fonte.

## Estrutura

```
dgs-ai-first/
├── .spec/                          # Análises e especificações
│   ├── exercicio-1.1-analise-viabilidade-tecnica.md
│   ├── exercicio-1.2-prototipacao-system-prompt.md
│   └── exercicio-1.3-pipeline-rag-spec.md
├── evidencias/                     # Histórico de iteração com Claude
│   ├── ex-1.1-iteracao-claude.md
│   ├── ex-1.2-testes-v1-v2.md
│   └── ex-1.3-resultados.md
└── pipeline-rag/                   # Código Python do pipeline
    ├── docs/                       # Documentos da NovaTech (fonte de dados)
    ├── ingest.py                   # Ingestão: chunking + embeddings → ChromaDB
    ├── search.py                   # Busca semântica nos chunks
    ├── prompt_builder.py           # Montagem do prompt para o LLM
    ├── test_pipeline.py            # 5 casos de teste com avaliação de retrieval
    └── requirements.txt
```

## Como rodar

```bash
cd pipeline-rag
pip install -r requirements.txt
python ingest.py          # processa os docs e cria o banco vetorial
python test_pipeline.py   # roda os 5 testes e gera test_results.json
```

## Stack técnica

- **Python 3.10+**
- **ChromaDB** — vector store local (sem servidor)
- **sentence-transformers** — modelo `paraphrase-multilingual-MiniLM-L12-v2` (PT-BR)
- **Claude** — LLM para geração das respostas (via chat, sem API)

## Exercícios

| Exercício | Entregável | Localização |
|-----------|-----------|-------------|
| 1.1 — Análise de viabilidade técnica | Documento com análise + iteração Claude | `.spec/exercicio-1.1-*.md` + `evidencias/ex-1.1-*.md` |
| 1.2 — Prototipação de system prompt | Prompt v1, v2, testes comparativos | `.spec/exercicio-1.2-*.md` + `evidencias/ex-1.2-*.md` |
| 1.3 — Pipeline de RAG funcional | Código Python + 5 testes com resultados | `pipeline-rag/` + `evidencias/ex-1.3-*.md` |

## Cenário 2 — Estruturação do Trabalho

Exercícios 2.1 (MCP servers), 2.2 (SDD + query endpoint) e 2.3 (Skills). Estrutura espelha o
Anexo C do projeto `db1/novatech-assistant`. Detalhes em [`cenario-2/README.md`](cenario-2/README.md).

## Cenário 3 — Governança e Validação

Exercícios 3.1 (structured output + verificações determinísticas / harness de código) e 3.2
(revisão crítica de código gerado por IA). Detalhes em [`cenario-3/README.md`](cenario-3/README.md).
