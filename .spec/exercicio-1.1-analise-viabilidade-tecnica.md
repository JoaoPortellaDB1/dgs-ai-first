# Exercício 1.1 — Análise de Viabilidade Técnica

## Contexto

Análise das características da documentação da NovaTech e seu impacto no pipeline de RAG.
Desenvolvida com iteração usando Claude como revisor.

---

## Análise por tipo de fonte

### 1. PDFs com tabelas complexas (SharePoint — ~800 docs)

**Desafio para o pipeline:** Tabelas com 15+ colunas perdem estrutura na extração de texto puro.
Ferramentas como PyMuPDF ou pdfplumber extraem tabelas como texto linear, quebrando a relação entre
colunas e valores. Uma tabela de multiplicadores regionais pode virar "Sul 1.3 Sudeste 1.1 Norte 1.8"
sem rótulos claros — o LLM pode não conseguir associar o valor à região correta.

**Impacto nas respostas:** Alta. Perguntas sobre frete (ex: "multiplicador do Sudeste") dependem de
tabelas. Se a tabela for mal extraída, o retrieval pode trazer o valor errado ou nenhum valor.

**Estratégia de tratamento:**
- Usar pdfplumber com extração específica de tabelas (método `extract_tables()`)
- Converter tabelas para Markdown antes de chunkar: `| Região | Multiplicador |`
- Manter a tabela inteira como um único chunk (não dividir no meio de uma tabela)

---

### 2. PDFs escaneados / OCR (~15% da base = ~120 docs)

**Desafio:** Imagens de texto precisam de OCR. Qualidade do OCR varia com qualidade do scan.
Documentos antigos escaneados com ruído geram texto com erros ("1.8" pode virar "1,8" ou "1.B").

**Impacto nas respostas:** Médio-alto. Erros de OCR contaminam os embeddings e podem impedir
recuperação por similaridade ("Regiäo Norte" não é semanticamente idêntico a "Região Norte").

**Estratégia:**
- Usar Tesseract OCR com pré-processamento de imagem (deskew, contraste)
- Pós-processamento: regex para corrigir padrões comuns (vírgula/ponto em decimais, caracteres especiais)
- Marcar chunks de documentos OCR com metadado `source_quality: "ocr"` para o LLM poder alertar o atendente

---

### 3. Wiki Confluence (~400 páginas)

**Desafio:** Links internos entre páginas (`[Ver PROC-042]`) não são seguidos na extração.
Macros customizadas do Confluence (ex: tabelas dinâmicas, painéis de status) podem não renderizar.
Estrutura hierárquica (página → subpágina) se perde na extração plana.

**Impacto:** Médio. Contexto cruzado entre páginas não é capturado automaticamente.

**Estratégia:**
- Usar a API REST do Confluence para extrair conteúdo já renderizado (HTML) em vez de exportar PDF
- Resolver links internos na ingestão: substituir `[Ver PROC-042]` pelo conteúdo referenciado (ou pelo título + URL)
- Preservar hierarquia como metadado: `parent_page`, `breadcrumb`

---

### 4. Planilhas XLSX (~50 arquivos)

**Desafio:** Fórmulas interdependentes (`=B2*VLOOKUP(...)`) não têm significado semântico.
O LLM recebe o resultado calculado, não a lógica. Múltiplas abas com nomes técnicos.

**Impacto:** Médio. Planilhas de referência (ex: tabela de fretes) são críticas mas estáticas.

**Estratégia:**
- Converter para CSV ou Markdown (pandas: `df.to_markdown()`)
- Avaliar cada aba individualmente: se for dado de referência, indexar. Se for fórmula/cálculo interno, excluir.
- Capturar valores calculados, não fórmulas

---

## Estimativa de tokens da base

A regra prática é: 1 token ≈ 0,75 palavras (ou 1 palavra ≈ 1,33 tokens).
Documentos normativos e técnicos tendem a ser mais densos que texto corrido — estimativa conservadora: 500 palavras/página para PDFs.

| Fonte | Qtde | Tamanho médio | Palavras total | Tokens (÷ 0,75) | Com overhead (+30%) |
|-------|------|---------------|----------------|-----------------|---------------------|
| PDFs SharePoint | 800 docs | 10 páginas × 500 palavras/pág | 4.000.000 | ~5.333.000 | ~6.933.000 |
| Wiki Confluence | 400 páginas | 1.500 palavras/pág | 600.000 | ~800.000 | ~1.040.000 |
| Planilhas XLSX | 50 arquivos | 5.000 palavras/arquivo (tabelas convertidas para Markdown são verbosas) | 250.000 | ~333.000 | ~433.000 |
| **Total** | | | **4.850.000** | **~6.466.000** | **~8.406.000 tokens** |

**Overhead considerado (+30%):** reformatação de tabelas para Markdown, metadados por chunk
(`source`, `section`, `doc_version`, `doc_date`), overlap entre chunks (~10%), e headers de seção repetidos.

**Conclusão:** Base estimada em ~8–9M tokens. Mesmo o GPT-4o com 128K de janela só conseguiria
processar menos de 2% da base em uma única chamada. RAG não é opcional — é a única arquitetura viável.

---

## Análise de orçamento de contexto por query

Janela do GPT-4o: 128.000 tokens
Tokens úteis por query: 128.000 − ~2.000 (overhead de API/system) = **~126.000 tokens disponíveis**

| Parte do contexto | Tokens estimados | Tipo |
|-------------------|-----------------|------|
| System prompt + guardrails | ~350 | Estático |
| Metadados do cliente (tier) | ~50 | Dinâmico |
| Chunks recuperados (7 chunks × 500 tokens) | ~3.500 | Dinâmico |
| Histórico de conversa (últimas 6 trocas) | ~600 | Dinâmico, crescente |
| Pergunta do atendente | ~30 | Dinâmico |
| **Total por query** | **~4.530** | |

**Quantos chunks cabem teoricamente?** 126.000 ÷ 500 tokens/chunk ≈ 252 chunks por query.
Na prática, **5–10 chunks é o ideal**: mais do que isso adiciona ruído e activa o efeito
*lost in the middle* — informação no meio de contextos longos é subprocessada pelo modelo.
Escolha de **7 chunks** equilibra cobertura e precisão.

**Risco real: context rot em conversas longas no Teams.** Se o histórico de conversa crescer
sem limite, após 20+ trocas ele sozinho pode consumir 10K+ tokens, comprimindo o espaço
para os chunks e degradando a qualidade das respostas.

**Mitigação:** Limitar histórico a últimas 6 trocas (~600 tokens). Resumir ou descartar trocas mais antigas.

---

## Estratégia de chunking

**Abordagem escolhida: chunking semântico por seção**

- Dividir por cabeçalhos Markdown (##, ###) em vez de tamanho fixo
- Tamanho máximo: 500 tokens por chunk
- Overlap: ~50 tokens entre chunks adjacentes (evita perder contexto em fronteiras)
- Tabelas: mantidas inteiras como chunk único, independente do tamanho

**Por que não chunking fixo (512 tokens)?**
Chunking fixo ignora a estrutura do documento. Uma seção de 200 tokens e outra de 800 tokens
são igualmente importantes — dividir a segunda ao meio pode cortar uma tabela ou separar
uma regra de sua exceção.

**Efeito lost in the middle:**
Informação no meio de um contexto longo é menos processada pelo LLM. Por isso, os chunks mais
relevantes devem ser posicionados no início e no fim do contexto, não no meio. O `prompt_builder.py`
implementa essa ordenação.

---

## Iteração com Claude — Rodada 2 (revisão crítica)

**Prompt enviado ao Claude:**
> "Revise minha análise técnica e identifique pontos fracos ou estimativas otimistas."

**Feedback do Claude (4 pontos):**

1. **Estimativa de tokens subestimada:** Documentos legais/normativos tendem a ser mais densos.
   Com 10% de docs OCR e reformatação de tabelas, o overhead pode elevar a base para ~4,5M tokens.
   → *Incorporado: adicionei margem de +25% na estimativa*

2. **Context rot em conversas longas não estava endereçado:** O histórico de conversa cresce
   indefinidamente em sessões do Teams. Após 15-20 trocas, o contexto explode.
   → *Incorporado: adicionei limite de 6 trocas e menção a summarização*

3. **Documentos contraditórios não tratados na estratégia:** PROC-042 v1 e v2 coexistem.
   Se os dois forem ingeridos sem metadado de versão, o retrieval pode trazer ambos.
   → *Incorporado: search.py implementa deduplicação por família de documento e data*

4. **Perguntas multi-domínio ignoradas:** "Posso devolver carga perigosa com frete expresso?"
   cruza POL-001, PROC-042 e FAQ. Com 3 chunks fixos, pode não trazer contexto suficiente.
   → *Mitigação proposta: aumentar n_results para 5-7 em queries com múltiplas entidades*
