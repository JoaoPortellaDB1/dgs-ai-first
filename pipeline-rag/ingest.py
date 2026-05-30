"""
Pipeline de ingestão: lê documentos .md, divide em chunks semânticos,
gera embeddings e armazena no ChromaDB.
"""

import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech_docs"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MAX_CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def extract_metadata(filename: str, content: str) -> dict:
    version = "unknown"
    date = "unknown"

    version_match = re.search(r"\*\*Versão:\*\*\s*(.+)", content)
    if version_match:
        version = version_match.group(1).strip()

    date_match = re.search(r"\*\*(?:Última atualização|Data de emissão):\*\*\s*(.+)", content)
    if date_match:
        date = date_match.group(1).strip()

    quality = "informal" if "FAQ" in filename else "formal"

    return {"source": filename, "doc_version": version, "doc_date": date, "source_quality": quality}


def split_into_chunks(filename: str, content: str) -> list[dict]:
    metadata = extract_metadata(filename, content)
    chunks = []
    chunk_index = 0

    # Divide por seções (##, ###). Tabelas ficam inteiras no chunk da seção.
    sections = re.split(r"(?=\n#{1,3} )", content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        section_title_match = re.match(r"#{1,3} (.+)", section)
        section_title = section_title_match.group(1).strip() if section_title_match else "intro"

        if estimate_tokens(section) <= MAX_CHUNK_TOKENS:
            chunks.append({
                "text": section,
                "metadata": {**metadata, "section": section_title, "chunk_index": chunk_index},
            })
            chunk_index += 1
        else:
            # Seção grande: divide por parágrafos mantendo overlap
            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            buffer = ""
            for para in paragraphs:
                if estimate_tokens(buffer + "\n\n" + para) > MAX_CHUNK_TOKENS and buffer:
                    chunks.append({
                        "text": buffer.strip(),
                        "metadata": {**metadata, "section": section_title, "chunk_index": chunk_index},
                    })
                    chunk_index += 1
                    # overlap: mantém último parágrafo do buffer anterior
                    last_para = buffer.strip().split("\n\n")[-1]
                    buffer = last_para + "\n\n" + para
                else:
                    buffer = buffer + "\n\n" + para if buffer else para

            if buffer.strip():
                chunks.append({
                    "text": buffer.strip(),
                    "metadata": {**metadata, "section": section_title, "chunk_index": chunk_index},
                })
                chunk_index += 1

    return chunks


def load_documents(docs_dir: str) -> list[dict]:
    docs = []
    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(docs_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({"filename": fname, "content": content})
    return docs


def ingest_to_chromadb(chunks: list[dict]) -> None:
    print(f"Carregando modelo de embeddings: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Recria a coleção para garantir estado limpo
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [c["metadata"] for c in chunks]

    print(f"Gerando embeddings para {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
    print(f"Ingestão concluída: {len(chunks)} chunks armazenados no ChromaDB.")


def main():
    print("=== INGESTÃO DE DOCUMENTOS NOVATECH ===\n")
    docs = load_documents(DOCS_DIR)
    print(f"Documentos encontrados: {len(docs)}")

    all_chunks = []
    for doc in docs:
        chunks = split_into_chunks(doc["filename"], doc["content"])
        print(f"  {doc['filename']}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\nTotal de chunks: {len(all_chunks)}")
    total_tokens = sum(estimate_tokens(c["text"]) for c in all_chunks)
    print(f"Tokens estimados: ~{total_tokens:,}")

    ingest_to_chromadb(all_chunks)


if __name__ == "__main__":
    main()
