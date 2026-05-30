"""
Busca semântica no ChromaDB. Recebe uma pergunta, retorna os N chunks
mais similares com score e metadados.
"""

import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech_docs"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None
_client = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _doc_family(source: str) -> str:
    """Extrai família do documento. Ex: 'PROC-042-v2-frete.md' → 'PROC-042'."""
    match = re.match(r"([A-Z]+-\d+)", source)
    return match.group(1) if match else source


def _deduplicate_versions(results: list[dict]) -> list[dict]:
    """Quando há duas versões do mesmo documento, mantém apenas a mais recente."""
    seen_families: dict[str, dict] = {}
    for r in results:
        family = _doc_family(r["metadata"].get("source", ""))
        if family not in seen_families:
            seen_families[family] = r
        else:
            existing_date = seen_families[family]["metadata"].get("doc_date", "")
            current_date = r["metadata"].get("doc_date", "")
            # Data no formato DD/MM/AAAA — compara string invertida para ordenar
            if current_date > existing_date:
                seen_families[family] = r

    # Reconstrói lista na ordem original de similaridade
    kept_ids = {id(v) for v in seen_families.values()}
    return [r for r in results if id(r) in kept_ids]


def search(query: str, n_results: int = 5, deduplicate_versions: bool = True) -> list[dict]:
    """
    Busca os chunks mais similares à query.

    Retorna lista de dicts com: text, metadata, similarity_score.
    """
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query]).tolist()

    raw = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    for doc, meta, dist in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        similarity = 1 - dist  # distância coseno → similaridade
        results.append({"text": doc, "metadata": meta, "similarity_score": round(similarity, 4)})

    if deduplicate_versions:
        results = _deduplicate_versions(results)

    return results


if __name__ == "__main__":
    query = "Qual o prazo de devolução de mercadorias?"
    print(f"Query: {query}\n")
    chunks = search(query, n_results=3)
    for i, c in enumerate(chunks, 1):
        print(f"--- Chunk {i} (score: {c['similarity_score']}) ---")
        print(f"Fonte: {c['metadata'].get('source')} | Seção: {c['metadata'].get('section')}")
        print(c["text"][:300])
        print()
