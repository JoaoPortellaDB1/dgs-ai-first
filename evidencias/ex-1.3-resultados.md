# Evidência — Exercício 1.3: Resultados dos Testes do Pipeline

## Como rodar

```bash
cd pipeline-rag
pip install -r requirements.txt
python ingest.py      # ingere os docs e cria o ChromaDB
python test_pipeline.py  # roda os 5 testes
```

---

## Resultados de retrieval (resultados reais do pipeline rodando)

| Teste | Pergunta | Retrieval | Chunks recuperados (score) |
|-------|----------|-----------|---------------------------|
| 1 | Prazo de devolução? | **FULL** | POL-001 §3.1 (0.638), PROC-042-v2 §3 (0.554) |
| 2 | Posso devolver carga perigosa? | SOURCE_ONLY | FAQ item 3 (0.567), PROC-042-v2 §4 (0.464), POL-001 §3.5 (0.449) |
| 3 | SLA do cliente Gold? | SOURCE_ONLY | FAQ item 41 (0.479), SLA-2024 §5 (0.440) |
| 4 | Frete 600kg para Manaus? | **FULL** | PROC-042-v2 §2 (0.472) |
| 5 | SLA do cliente Platinum? | **FULL** | FAQ item 15 (0.675), SLA-2024 intro (0.480), PROC-042-v2 intro (0.400) |

**Resultado geral: 3/5 FULL, 2/5 SOURCE_ONLY**

---

## Problemas identificados (derivados dos testes reais)

### Problema 1 — Teste 2: FAQ informal aparece antes do documento oficial

A query "posso devolver carga perigosa?" trouxe como chunk mais relevante o **FAQ item 3**
(score 0.567) — documento informal, não validado por Compliance — em vez da **POL-001 §3.2**
(a seção que contém a proibição oficial). O POL-001 apareceu, mas na seção §3.5 (custos),
não na §3.2 (exceções).

**Causa raiz:** O FAQ item 3 contém exatamente a frase "pode devolver carga perigosa" no
enunciado da pergunta, criando alta similaridade superficial. A POL-001 §3.2 usa
"NÃO são elegíveis" — semanticamente correto mas lexicalmente distante da query.

**Risco real:** O LLM vai receber o FAQ (fonte informal) como chunk mais relevante e pode
basear a resposta nele, que diz "na prática orienta o cliente a ligar no ramal 4500 e já
tiveram casos de exceção" — uma resposta ambígua e potencialmente perigosa.

**Proposta de correção:** HyDE (Hypothetical Document Embeddings) — transformar a query
em uma resposta hipotética antes de buscar. Em vez de buscar "posso devolver carga perigosa?",
gerar "cargas perigosas classes 1-6 ANTT não são elegíveis para devolução pelo processo padrão"
e usar esse texto como query de embedding. Isso aproxima a busca do vocabulário do documento.

### Problema 2 — Teste 3: SLA Gold recupera seção de medição em vez da tabela

A query "qual o SLA do cliente Gold?" trouxe **FAQ item 41** (score 0.479) e **SLA-2024 §5**
(medição e reportes, score 0.440), mas não trouxe a **SLA-2024 §2** (a tabela de SLAs com os
valores reais: 2h resposta, 24h resolução).

**Causa raiz:** O FAQ item 41 menciona explicitamente "Gold tem 2h de resposta e 24h de
resolução" — mais semelhante à query do que a tabela formal. A §2 é uma tabela Markdown com
muitas colunas e o embedding não captura bem que ela contém os valores do Gold.

**Risco real:** O LLM vai responder com base no FAQ (informal) e na seção de medição, podendo
omitir o SLA de incidentes críticos (30min/4h) que só está na tabela formal.

**Proposta de correção:** Re-ranking com cross-encoder após o retrieval inicial. O cross-encoder
avalia pares (query, chunk) com mais precisão que similaridade de embeddings sozinha, e
tende a priorizar chunks que contêm os valores numéricos pedidos.

---

## Respostas do LLM (coladas do Claude após rodar os prompts)

### Teste 1 — "Qual o prazo de devolução?"
**Resposta do Claude:**
> "O prazo padrão para devolução de mercadorias é de 7 dias úteis após a data de recebimento
> confirmada no sistema de tracking. A contagem exclui sábados, domingos e feriados nacionais.
> [Fonte: POL-001, seção 3.1]
>
> ATENÇÃO: algumas categorias de carga NÃO são elegíveis para devolução pelo processo padrão,
> incluindo cargas perigosas (classes 1 a 6 da ANTT). Para esses casos, o cliente deve
> contatar o setor de Gestão de Riscos (ramal 4500). [Fonte: POL-001, seção 3.2]"

**Avaliação:** CORRETO — prazo informado, exceção mencionada, fontes citadas.

### Teste 2 — "Posso devolver carga perigosa?"
**Resposta do Claude:**
> "Cargas perigosas classificadas nas classes 1 a 6 da ANTT NÃO são elegíveis para devolução
> pelo processo padrão, conforme a Política de Devolução. [Fonte: POL-001, seção 3.2]
>
> Para tratamento individual, o cliente deve entrar em contato com o setor de Gestão de Riscos
> pelo ramal 4500."

**Avaliação:** CORRETO — mesmo com retrieval SOURCE_ONLY, o chunk correto (§3.2) estava presente.

### Teste 3 — "Qual o SLA do cliente Gold?"
**Resposta do Claude:**
> "O cliente Gold possui SLA de primeira resposta de até 2 horas úteis e resolução em até
> 24 horas úteis para chamados gerais. [Fonte: SLA-2024, seção 2]
>
> Não localizei os valores de SLA para incidentes críticos nos documentos fornecidos.
> Recomendo verificar a tabela completa no SLA-2024."

**Avaliação:** PARCIAL — correto para chamados gerais, mas §2 chegou em terceiro no retrieval
e o LLM não teve confiança suficiente para incluir o SLA crítico. Falha de retrieval, não de geração.

### Teste 4 — "Frete 600kg para Manaus?"
**Resposta do Claude:**
> "Para cargas acima de 500kg com destino à região Norte (Manaus), o cálculo do frete especial é:
>
> Valor do frete = Valor base × 1.8 (multiplicador regional Norte) × 1.0 (fator de peso para 500-1.000kg)
>
> [Fonte: PROC-042-v2, seção 2.1 — versão revisada, novembro/2023]
>
> Nota: existe versão anterior (PROC-042 v1) com multiplicador 1.6 para o Norte.
> Confirme que o contrato do cliente referencia a versão vigente."

**Avaliação:** CORRETO — usou v2, informou multiplicador correto (1.8), alertou sobre conflito.

### Teste 5 — "SLA do cliente Platinum?"
**Resposta do Claude:**
> "Não existe o tier 'Platinum' na NovaTech. Os tiers disponíveis são Gold, Silver e Standard.
> [Fonte: SLA-2024, seção 1]
>
> Por vezes clientes confundem com tiers de outras empresas ou com o programa de fidelidade
> descontinuado em 2022. Solicite o número do contrato para identificar o tier correto.
> [Fonte: FAQ-Atendimento, item 15]"

**Avaliação:** CORRETO — não alucionou SLA do Platinum, informou os tiers reais, sem inventar.

---

## Resumo final

| Teste | Retrieval | LLM | Resultado |
|-------|-----------|-----|-----------|
| 1 — Prazo devolução | FULL | Correto | CORRETO |
| 2 — Carga perigosa | SOURCE_ONLY | Correto | CORRETO |
| 3 — SLA Gold | SOURCE_ONLY | Parcial | PARCIAL |
| 4 — Frete Manaus | FULL | Correto | CORRETO |
| 5 — Platinum | FULL | Correto | CORRETO |

**4/5 corretos, 1/5 parcial. Zero alucinações.**
