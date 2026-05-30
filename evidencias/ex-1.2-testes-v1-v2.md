# Evidência — Exercício 1.2: Testes Prompt v1 e v2

Este arquivo documenta os testes realizados com os prompts v1 e v2 usando o Claude como
ambiente de teste. Os chunks foram injetados manualmente conforme o Anexo B.

---

## Setup do teste

Para cada teste: abri o Claude, colei o system prompt como instrução inicial,
colei os chunks simulados do Anexo B como contexto, e enviei a pergunta como atendente.

---

## Teste A — Pergunta: "Qual o prazo de devolução para carga perigosa?"

**Chunks injetados:**
- POL-001-A (seção 3.1): prazo geral de 7 dias úteis
- POL-001-B (seção 3.2): exceções — cargas perigosas NÃO elegíveis, ramal 4500

### Resposta com Prompt v1:
> "O prazo de devolução é de 7 dias úteis após o recebimento confirmado no sistema de tracking.
> [Fonte: POL-001, seção 3.1]"

**Avaliação:** INCORRETO — mencionou apenas a regra geral, ignorou a exceção crítica (§3.2
estava no contexto). Resposta perigosa: induz o atendente a aceitar devolução de carga perigosa.

### Resposta com Prompt v2 (com Regra 4 — exceções primeiro):
> "ATENÇÃO: Cargas perigosas classificadas nas classes 1 a 6 da ANTT NÃO são elegíveis para
> devolução pelo processo padrão. [Fonte: POL-001, seção 3.2]
>
> Para esse caso, o cliente deve ligar para o setor de Gestão de Riscos (ramal 4500).
>
> Para cargas comuns: o prazo de devolução é de 7 dias úteis após o recebimento.
> [Fonte: POL-001, seção 3.1]"

**Avaliação:** CORRETO — exceção apresentada primeiro, regra geral depois, fonte citada.

---

## Teste B — Pergunta: "Qual o SLA do cliente Gold?"

**Chunks injetados:**
- SLA-2024-B (seção 2): tabela de chamados gerais — Gold: resposta 2h, resolução 24h
- SLA-2024-C (seção 2): incidentes críticos — Gold: resposta 30min, resolução 4h

### Resposta com Prompt v1:
> "O cliente Gold tem SLA de resposta de até 2 horas úteis e resolução em até 24 horas úteis.
> [Fonte: SLA-2024, seção 2]"

**Avaliação:** PARCIAL — correto para chamados gerais, mas omitiu SLA de incidentes críticos.

### Resposta com Prompt v2 (com Regra 6 — completude):
> "O cliente Gold possui os seguintes SLAs conforme SLA-2024, seção 2:
>
> Chamados gerais:
> - Primeira resposta: até 2 horas úteis
> - Resolução: até 24 horas úteis
>
> Incidentes críticos:
> - Primeira resposta: até 30 minutos
> - Resolução: até 4 horas"

**Avaliação:** CORRETO — tabela completa apresentada.

---

## Teste C — Conflito de versões: "Qual o multiplicador de frete para o Sudeste?"

**Chunks injetados:**
- PROC-042-B (v1): Sudeste = 1.0
- PROC-042v2-B (v2): Sudeste = 1.1

### Resposta com Prompt v2 (com Regras 7 e 8):
> "O multiplicador regional para o Sudeste é 1.1, conforme a versão mais recente do procedimento.
> [Fonte: PROC-042-v2, seção 2.1 — novembro/2023]
>
> Nota: existe uma versão anterior (PROC-042 v1) com multiplicador 1.0 para o Sudeste.
> Confirme que o contrato do cliente referencia a versão vigente."

**Avaliação:** CORRETO — priorizou v2, alertou sobre conflito, sem inventar nada.

---

## Resumo comparativo

| Teste | v1 | v2 |
|-------|----|----|
| Prazo devolução carga perigosa | INCORRETO | CORRETO |
| SLA Gold | PARCIAL | CORRETO |
| Conflito de versões | N/A | CORRETO |
