"""
Executa 5 testes de ponta a ponta no pipeline de RAG.
Para cada pergunta: busca chunks, monta prompt, avalia retrieval.
Salva resultados em test_results.json.
"""

import json
from search import search
from prompt_builder import build_prompt

TEST_CASES = [
    {
        "id": 1,
        "question": "Qual o prazo de devolução de mercadorias?",
        "expected_sources": ["POL-001-politica-devolucao.md"],
        "expected_sections": ["3.1", "3.2"],
        "trap": "A resposta correta menciona a exceção de cargas perigosas, não só o prazo geral de 7 dias.",
    },
    {
        "id": 2,
        "question": "Posso devolver carga perigosa?",
        "expected_sources": ["POL-001-politica-devolucao.md"],
        "expected_sections": ["3.2"],
        "trap": "Resposta correta: NÃO pode pelo processo padrão. Deve citar ramal 4500. Se disser que pode, é erro grave.",
    },
    {
        "id": 3,
        "question": "Qual o SLA do cliente Gold?",
        "expected_sources": ["SLA-2024-tabela-sla-clientes.md"],
        "expected_sections": ["2"],
        "trap": "Deve incluir SLA de incidentes críticos (resposta 30min, resolução 4h), não só o geral.",
    },
    {
        "id": 4,
        "question": "Quanto custa o frete para 600kg para Manaus?",
        "expected_sources": ["PROC-042-v2-frete-especial-revisado.md"],
        "expected_sections": ["2", "2.1"],
        "trap": "Deve usar PROC-042-v2 (Norte: 1.8), não v1 (Norte: 1.6). Fator de peso 1.0 para 500-1000kg.",
    },
    {
        "id": 5,
        "question": "Qual o SLA do cliente Platinum?",
        "expected_sources": ["SLA-2024-tabela-sla-clientes.md"],
        "expected_sections": ["1"],
        "trap": "Tier Platinum não existe. Resposta correta: informar que só há Gold, Silver e Standard.",
    },
]


def evaluate_retrieval(retrieved: list[dict], expected_sources: list[str], expected_sections: list[str]) -> str:
    """
    Avalia qualidade do retrieval:
    - FULL: acertou a fonte E pelo menos uma seção esperada
    - SOURCE_ONLY: fonte certa, seção errada
    - PARTIAL: alguma fonte certa
    - MISS: nenhum chunk relevante
    """
    retrieved_sources = [c["metadata"].get("source", "") for c in retrieved]
    retrieved_sections = [c["metadata"].get("section", "") for c in retrieved]

    source_hit = any(src in retrieved_sources for src in expected_sources)
    section_hit = any(
        any(exp_sec in ret_sec for ret_sec in retrieved_sections)
        for exp_sec in expected_sections
    )

    if source_hit and section_hit:
        return "FULL"
    elif source_hit:
        return "SOURCE_ONLY"
    elif any(
        any(exp in ret for ret in retrieved_sources)
        for exp in expected_sources
    ):
        return "PARTIAL"
    else:
        return "MISS"


def run_tests():
    results = []
    print("=== TESTES DO PIPELINE RAG — NOVATECH ===\n")

    for tc in TEST_CASES:
        print(f"Teste {tc['id']}: {tc['question']}")

        retrieved = search(tc["question"], n_results=5, deduplicate_versions=True)
        retrieval_status = evaluate_retrieval(retrieved, tc["expected_sources"], tc["expected_sections"])

        prompt = build_prompt(tc["question"], retrieved[:3])

        print(f"  Retrieval: {retrieval_status}")
        print(f"  Chunks recuperados:")
        for c in retrieved:
            print(f"    [{c['similarity_score']:.3f}] {c['metadata'].get('source')} — {c['metadata'].get('section')}")
        print()

        results.append({
            "test_id": tc["id"],
            "question": tc["question"],
            "retrieval_status": retrieval_status,
            "trap": tc["trap"],
            "retrieved_chunks": [
                {
                    "source": c["metadata"].get("source"),
                    "section": c["metadata"].get("section"),
                    "similarity_score": c["similarity_score"],
                    "text_preview": c["text"][:150],
                }
                for c in retrieved
            ],
            "prompt_for_llm": prompt,
            "llm_response": "(cole aqui a resposta do Claude)",
            "evaluation": "(CORRETO / PARCIAL / INCORRETO)",
        })

    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Resultados salvos em test_results.json")
    print("\nResumo:")
    for r in results:
        print(f"  Teste {r['test_id']}: {r['retrieval_status']}")


if __name__ == "__main__":
    run_tests()
