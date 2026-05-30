"""
Monta o prompt completo para enviar ao LLM.
Combina system prompt (estático) + contexto do cliente (dinâmico)
+ chunks recuperados (dinâmico) + histórico + pergunta.
"""

SYSTEM_PROMPT = """Você é o assistente oficial de atendimento da NovaTech, empresa de logística.
Seu papel é ajudar o time de atendimento a responder dúvidas de clientes com base exclusivamente na documentação oficial da NovaTech.

REGRAS OBRIGATÓRIAS:

1. USE APENAS informações presentes nos documentos fornecidos abaixo. Nunca use conhecimento externo.

2. CITE A FONTE em toda resposta, no formato: [Fonte: NOME-DO-DOCUMENTO, seção X.X]

3. NUNCA invente prazos, valores, multiplicadores ou procedimentos. Se o número não está no documento, não mencione.

4. EXCEÇÕES PRIMEIRO: Se a regra geral tem exceção relevante para a pergunta, mencione a exceção ANTES da regra geral. Exemplo: se a carga é perigosa, diga primeiro que não é elegível para devolução padrão antes de explicar o processo geral.

5. SEM RESPOSTA: Se a informação não estiver em nenhum documento fornecido, responda EXATAMENTE: "Não encontrei essa informação na documentação disponível. Recomendo escalar para o supervisor ou consultar o setor responsável."

6. RESPOSTA PARCIAL: Se tiver parte da informação mas não toda, apresente o que encontrou e indique explicitamente o que está faltando.

7. VERSÕES CONFLITANTES: Se houver duas versões do mesmo documento, use SEMPRE a mais recente (maior data de emissão).

8. CONFLITO EXPLÍCITO: Quando usar um documento que tem versão anterior com valores diferentes, adicione: "Nota: existe versão anterior com valores diferentes — confirme que o contrato do cliente referencia a versão vigente."

Responda sempre em português formal e acessível."""


def _order_lost_in_middle(chunks: list[dict]) -> list[dict]:
    """
    Reordena chunks para mitigar o efeito 'lost in the middle':
    coloca o melhor chunk no início, segundo melhor no fim,
    e os intermediários no meio.
    """
    if len(chunks) <= 2:
        return chunks
    ordered = [chunks[0]]
    ordered.extend(chunks[2:])
    ordered.append(chunks[1])
    return ordered


def _has_version_conflict(chunks: list[dict]) -> bool:
    """Detecta se há chunks de versões diferentes do mesmo documento base."""
    import re
    families = []
    for c in chunks:
        source = c["metadata"].get("source", "")
        match = re.match(r"([A-Z]+-\d+)", source)
        if match:
            families.append(match.group(1))
    return len(families) != len(set(families))


def _is_faq_only(chunks: list[dict]) -> bool:
    """Verifica se todos os chunks são do FAQ (fonte informal)."""
    return all("FAQ" in c["metadata"].get("source", "") for c in chunks)


def build_prompt(
    query: str,
    chunks: list[dict],
    client_tier: str = None,
    conversation_history: list[dict] = None,
) -> str:
    """
    Monta o prompt completo.

    Partes (estático/dinâmico):
    - SYSTEM_PROMPT: estático (~350 tokens)
    - Contexto do cliente: dinâmico (~20 tokens)
    - Avisos de conflito/FAQ: dinâmico (~30 tokens)
    - Chunks: dinâmico (~500 tokens cada, até 5 chunks = ~2.500 tokens)
    - Histórico: dinâmico, últimas 6 trocas (~600 tokens)
    - Pergunta: dinâmico (~20 tokens)
    Total estimado: ~3.500 tokens por query
    """
    parts = [SYSTEM_PROMPT]

    if client_tier:
        parts.append(f"\n--- CONTEXTO DO CLIENTE ---\nTier do cliente: {client_tier}")

    if _is_faq_only(chunks):
        parts.append(
            "\n⚠️ AVISO: Os únicos documentos recuperados são do FAQ informal. "
            "Este documento não foi validado por Compliance. Use com cautela e indique a limitação na resposta."
        )

    if _has_version_conflict(chunks):
        parts.append(
            "\n⚠️ AVISO: Foram recuperados chunks de versões diferentes do mesmo documento. "
            "Aplique a Regra 7: use a versão mais recente e aplique a Regra 8 na resposta."
        )

    ordered_chunks = _order_lost_in_middle(chunks)
    parts.append("\n--- DOCUMENTAÇÃO DISPONÍVEL ---")
    for i, chunk in enumerate(ordered_chunks, 1):
        source = chunk["metadata"].get("source", "desconhecido")
        section = chunk["metadata"].get("section", "")
        quality = chunk["metadata"].get("source_quality", "formal")
        quality_label = " [FONTE INFORMAL]" if quality == "informal" else ""
        parts.append(
            f"\n[Documento {i}] {source} — {section}{quality_label}\n{chunk['text']}"
        )

    if conversation_history:
        recent = conversation_history[-6:]
        parts.append("\n--- HISTÓRICO DA CONVERSA ---")
        for turn in recent:
            role = "Atendente" if turn["role"] == "user" else "Assistente"
            parts.append(f"{role}: {turn['content']}")

    parts.append(f"\n--- PERGUNTA DO ATENDENTE ---\n{query}")

    return "\n".join(parts)


if __name__ == "__main__":
    sample_chunks = [
        {
            "text": "O cliente pode solicitar devolução em até 7 dias úteis após o recebimento.",
            "metadata": {"source": "POL-001-politica-devolucao.md", "section": "3.1 Prazo geral", "source_quality": "formal"},
            "similarity_score": 0.91,
        },
        {
            "text": "Cargas perigosas classes 1 a 6 NÃO são elegíveis para devolução pelo processo padrão.",
            "metadata": {"source": "POL-001-politica-devolucao.md", "section": "3.2 Exceções", "source_quality": "formal"},
            "similarity_score": 0.85,
        },
    ]
    prompt = build_prompt("Posso devolver carga perigosa?", sample_chunks, client_tier="Gold")
    print(prompt)
