# Evidência — Exercício 1.1: Iteração com Claude

Este arquivo documenta a conversa com o Claude usada para desenvolver e refinar
a análise de viabilidade técnica do exercício 1.1.

---

## Rodada 1 — Análise inicial

**Prompt enviado ao Claude:**

> Você vai me ajudar a analisar a viabilidade técnica de um pipeline de RAG para a NovaTech,
> empresa de logística. A base documental tem:
> - ~800 PDFs no SharePoint (alguns com tabelas complexas, ~15% escaneados)
> - ~400 páginas wiki no Confluence (com links internos e macros)
> - ~50 planilhas XLSX com fórmulas
>
> Para cada tipo de fonte, me diga: qual o principal desafio para o pipeline de RAG,
> como isso impacta a qualidade das respostas, e uma estratégia de tratamento.
> Depois, faça uma estimativa do total de tokens da base.

**Output do Claude (resumido):**

O Claude identificou os 4 desafios principais:

1. **PDFs com tabelas:** extração linear perde relação coluna-valor. Sugeriu pdfplumber com
   `extract_tables()` e conversão para Markdown antes do chunking.

2. **PDFs escaneados:** variação de qualidade do OCR gera erros em valores numéricos (crítico
   para multiplicadores de frete). Sugeriu Tesseract com pré-processamento + metadado de qualidade.

3. **Confluence:** macros não renderizam em exportação. Sugeriu API REST para extrair HTML renderizado.

4. **XLSX:** fórmulas sem significado semântico. Sugeriu converter valores calculados para Markdown.

**Estimativa de tokens:**
- PDFs: ~800 docs × 10 páginas × 250 palavras × 0.75 = ~1.500.000 tokens
- Wiki: ~400 páginas × 1.500 palavras × 0.75 = ~450.000 tokens
- XLSX: ~50 arquivos × 1.000 palavras × 0.75 = ~37.500 tokens
- Total inicial: ~2.000.000 tokens

---

## Rodada 2 — Revisão crítica

**Prompt enviado ao Claude:**

> Revise minha análise e identifique pontos fracos, estimativas otimistas ou riscos que não considerei.
> [colei o documento da análise inicial]

**Feedback do Claude (4 pontos identificados):**

1. **Tokens subestimados:** "Documentos normativos/legais são mais densos que a média. Com overhead
   de reformatação e metadados, 2M pode facilmente ser 3.5-4M tokens. Recomendo usar 300 palavras/página
   como estimativa conservadora."
   → *Ação: corrigi para 250 palavras/página com margem de 25%, chegando a ~3,6M tokens*

2. **Context rot não endereçado:** "Seu documento não menciona o risco de conversas longas no Teams.
   O histórico cresce indefinidamente e pode ultrapassar a janela de contexto após 15-20 trocas."
   → *Ação: adicionei análise de orçamento de contexto e estratégia de limitação do histórico*

3. **Documentos contraditórios:** "PROC-042 v1 e v2 coexistem. Sem estratégia de deduplicação,
   o retrieval pode trazer os dois e o LLM mistura multiplicadores."
   → *Ação: adicionei deduplicação por família+data no search.py*

4. **Perguntas multi-domínio:** "Uma pergunta como 'posso devolver carga perigosa com frete expresso?'
   cruza 3 documentos. Com n_results=3, pode não ter contexto suficiente."
   → *Ação: documentei mitigação de aumentar n_results para perguntas com múltiplas entidades*

**Conclusão da iteração:** O feedback do Claude melhorou o documento em 4 dimensões reais.
As versões iniciais tinham estimativas otimistas e omitiam riscos operacionais importantes.
