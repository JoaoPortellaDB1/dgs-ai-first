# Evidência — Exercício 1.3: Resultados dos Testes do Pipeline

## Como rodar

```bash
cd pipeline-rag
pip install -r requirements.txt
python ingest.py      # ingere os docs e cria o ChromaDB
python test_pipeline.py  # roda os 5 testes
```

---

## Resultados de retrieval (após rodar test_pipeline.py)

| Teste | Pergunta | Retrieval | Chunks recuperados (top 3) |
|-------|----------|-----------|---------------------------|
| 1 | Prazo de devolução? | FULL | POL-001 §3.1, POL-001 §3.2, POL-001 §3.3 |
| 2 | Posso devolver carga perigosa? | SOURCE_ONLY | POL-001 §3.5 (errou seção), POL-001 §3.1, FAQ-03 |
| 3 | SLA do cliente Gold? | SOURCE_ONLY | SLA-2024 §1, SLA-2024 §4, SLA-2024 §2 |
| 4 | Frete 600kg para Manaus? | FULL | PROC-042v2 §2.1, PROC-042v2 §2, PROC-042v2 §3 |
| 5 | SLA do cliente Platinum? | FULL | SLA-2024 §1, FAQ-15, SLA-2024 §2 |

**Resultado geral: 3/5 FULL, 2/5 SOURCE_ONLY**

---

## Problemas identificados

### Problema 1 — Teste 2: Seção errada para carga perigosa
A query "posso devolver carga perigosa?" recuperou §3.5 (custos) em vez de §3.2 (exceções).
Semanticamente, "devolver carga perigosa" está mais próximo de "custos de devolução" do que
de "exceções ao prazo", porque §3.5 usa a palavra "devolução" mais frequentemente.

**Causa raiz:** Mismatch semântico — a proibição está em §3.2 ("NÃO são elegíveis") mas a
pergunta usa "posso devolver", que é mais similar a §3.5 em embedding space.

**Proposta de correção:** HyDE (Hypothetical Document Embeddings) — gerar um documento
hipotético de resposta antes de buscar. Em vez de buscar "posso devolver carga perigosa?",
buscar "cargas perigosas não são elegíveis para devolução" (resposta hipotética).

### Problema 2 — Teste 3: SLA do Gold — seção de classificação aparece antes da tabela
O retrieval retornou SLA §1 (classificação de clientes) com score maior que §2 (tabela de SLAs).
O §1 contém a palavra "Gold" várias vezes (definição do tier), então tem alta similaridade.
O §2 (que tem os valores reais) aparece em terceiro lugar.

**Causa raiz:** Frequência de termo supera relevância semântica real.

**Proposta de correção:** Re-ranking com cross-encoder após o retrieval inicial. O cross-encoder
avalia pares (query, chunk) e reordena com mais precisão que o embedding de similaridade.

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
