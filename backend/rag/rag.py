"""
ForestGuard AI - RAG ingestion and retrieval.

Input PDFs:
    documents/forest_fire_pdfs/

Generated artifacts:
    backend/rag/embeddings/forest_fire_embeddings.npy
    backend/rag/embeddings/forest_fire_passages.jsonl

Build:
    python -m backend.rag.rag --build

Test retrieval:
    python -m backend.rag.rag --query "How can forest fires be prevented?"
"""

import argparse
import json
from pathlib import Path

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Paths: based on the actual wildfire_assistant repository
# ---------------------------------------------------------

# backend/rag/rag.py -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PDF_DIR = PROJECT_ROOT / "documents" / "forest_fire_pdfs"

EMBEDDINGS_DIR = PROJECT_ROOT / "backend" / "rag" / "embeddings"

EMBEDDINGS_FILE = EMBEDDINGS_DIR / "forest_fire_embeddings.npy"
PASSAGES_FILE = EMBEDDINGS_DIR / "forest_fire_passages.jsonl"


# ---------------------------------------------------------
# RAG configuration
# ---------------------------------------------------------

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 4


# ---------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------

def extract_pdf_pages(pdf_path):
    """
    Extract text from a PDF while preserving its page numbers.
    """
    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        # Normalize whitespace
        text = " ".join(text.split())

        if text:
            pages.append({
                "title": pdf_path.stem,
                "page": page_number,
                "text": text
            })

    return pages


# ---------------------------------------------------------
# Text chunking
# ---------------------------------------------------------

def split_text(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):
    """
    Split text into overlapping character chunks.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and smaller than chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


# ---------------------------------------------------------
# Build the RAG knowledge base
# ---------------------------------------------------------

def build_knowledge_base():

    if not PDF_DIR.exists():
        raise FileNotFoundError(
            f"PDF directory does not exist:\n{PDF_DIR}"
        )

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in:\n{PDF_DIR}"
        )

    passages = []

    # Extract and chunk each PDF
    for pdf_path in pdf_files:

        print(f"Processing PDF: {pdf_path.name}")

        try:
            pages = extract_pdf_pages(pdf_path)

        except Exception as error:
            print(f"Could not process {pdf_path.name}: {error}")
            continue

        for page_data in pages:

            chunks = split_text(page_data["text"])

            for chunk_number, chunk in enumerate(chunks, start=1):

                passages.append({
                    "title": page_data["title"],
                    "page": page_data["page"],
                    "chunk": chunk_number,
                    "text": chunk
                })

    if not passages:
        raise RuntimeError(
            "No text was extracted from the PDFs."
        )

    print(f"\nTotal passages created: {len(passages)}")

    # Load sentence embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    passage_texts = [
        passage["text"]
        for passage in passages
    ]

    # Generate normalized embeddings
    embeddings = embedding_model.encode(
        passage_texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Ensure output directory exists
    EMBEDDINGS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save embeddings
    np.save(
        EMBEDDINGS_FILE,
        embeddings
    )

    # Save passages and source metadata
    with PASSAGES_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        for passage in passages:

            file.write(
                json.dumps(
                    passage,
                    ensure_ascii=False
                ) + "\n"
            )

    print("\nKnowledge base successfully created.")

    print(f"Embeddings saved to:\n{EMBEDDINGS_FILE}")
    print(f"Passages saved to:\n{PASSAGES_FILE}")

    print(f"Embedding matrix shape: {embeddings.shape}")


# ---------------------------------------------------------
# RAG retrieval
# ---------------------------------------------------------

class ForestFireRAG:

    def __init__(self):

        if not EMBEDDINGS_FILE.exists():
            raise FileNotFoundError(
                "Embeddings not found. Run:\n"
                "python -m backend.rag.rag --build"
            )

        if not PASSAGES_FILE.exists():
            raise FileNotFoundError(
                "Passages file not found. Run:\n"
                "python -m backend.rag.rag --build"
            )

        print("Loading embedding model...")

        self.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

        print("Loading saved embeddings...")

        self.embeddings = np.load(
            EMBEDDINGS_FILE
        )

        print("Loading passages...")

        with PASSAGES_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            self.passages = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        if len(self.embeddings) != len(self.passages):

            raise ValueError(
                "Mismatch between embeddings and passages: "
                f"{len(self.embeddings)} embeddings, "
                f"{len(self.passages)} passages."
            )

        print("RAG system loaded successfully.")

    def retrieve(self, query, top_k=DEFAULT_TOP_K):
        """
        Retrieve the top-k passages most similar to the query.
        """

        query = query.strip()

        if not query:
            return []

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        # Embed the user question
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        # Embeddings are normalized, so dot product = cosine similarity
        scores = np.dot(
            self.embeddings,
            query_embedding
        )

        # Highest similarity first
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for index in top_indices:

            passage = dict(
                self.passages[int(index)]
            )

            passage["score"] = float(
                scores[int(index)]
            )

            results.append(passage)

        return results

    def format_context(self, query, top_k=DEFAULT_TOP_K):
        """
        Return retrieved text formatted for the Qwen prompt,
        along with source metadata for the frontend.
        """

        retrieved_passages = self.retrieve(
            query,
            top_k=top_k
        )

        context_parts = []

        sources = []

        for passage in retrieved_passages:

            source_text = (
                f"[Source: {passage['title']}, "
                f"page {passage['page']}]\n"
                f"{passage['text']}"
            )

            context_parts.append(source_text)

            sources.append({
                "title": passage["title"],
                "page": passage["page"],
                "score": passage["score"]
            })

        context = "\n\n".join(context_parts)

        return context, sources


# ---------------------------------------------------------
# Command-line execution
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--build",
        action="store_true",
        help="Create the RAG embeddings from PDF files"
    )

    parser.add_argument(
        "--query",
        type=str,
        help="Test retrieval using a question"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K
    )

    args = parser.parse_args()

    if args.build:

        build_knowledge_base()

    elif args.query:

        rag = ForestFireRAG()

        results = rag.retrieve(
            args.query,
            top_k=args.top_k
        )

        print("\nRetrieved passages:\n")

        for result in results:

            print(
                f"\nSource: {result['title']}"
                f" | Page: {result['page']}"
                f" | Score: {result['score']:.4f}"
            )

            print(result["text"])

            print("-" * 80)

    else:

        parser.print_help()


if __name__ == "__main__":
    main()