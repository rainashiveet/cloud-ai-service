"""
AI Inference Module for Cloud-Native AI Service
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    answer: str
    retrieved_docs: List[str]
    similarity_scores: List[float]
    latency_ms: float
    query: str


class EmbeddingModel:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        start_time = time.time()

        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        load_time = (time.time() - start_time) * 1000
        logger.info(
            f"Model loaded successfully. Dimension: {self.dimension}, "
            f"Load time: {load_time:.2f}ms"
        )

    def encode(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class FAISSIndex:

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.documents: List[str] = []

        self.index = faiss.IndexFlatIP(dimension)
        logger.info(f"Initialized FAISS index with dimension {dimension}")

    def add_documents(self, documents: List[str], embeddings: np.ndarray) -> None:

        if len(documents) != embeddings.shape[0]:
            raise ValueError("Documents and embeddings count mismatch")

        faiss.normalize_L2(embeddings)

        self.index.add(embeddings.astype(np.float32))
        self.documents.extend(documents)

        logger.info(f"Added {len(documents)} documents to index")

    def search(self, query_embedding: np.ndarray, k: int = 3):

        if self.index.ntotal == 0:
            return [], []

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        faiss.normalize_L2(query_embedding)

        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(
            query_embedding.astype(np.float32), k
        )

        retrieved_docs = [self.documents[i] for i in indices[0]]
        similarity_scores = scores[0].tolist()

        return retrieved_docs, similarity_scores


class RAGPipeline:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):

        logger.info("Initializing RAG pipeline")

        self.embedding_model = EmbeddingModel(model_name)
        self.index = FAISSIndex(self.embedding_model.dimension)
        self._is_indexed = False

    # -------------------------
    # NEW PART (file loading)
    # -------------------------
    def index_from_file(self, file_path: str) -> None:

        logger.info(f"Indexing knowledge file: {file_path}")

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"{file_path} not found")

        text = path.read_text(encoding="utf-8")

        documents = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not documents:
            raise ValueError("Knowledge file is empty")

        self.index_documents(documents)

    # -------------------------

    def index_documents(self, documents: List[str]) -> None:

        logger.info(f"Indexing {len(documents)} documents")

        start = time.time()

        embeddings = self.embedding_model.encode(documents)
        self.index.add_documents(documents, embeddings)

        self._is_indexed = True

        logger.info(
            f"Indexing completed in {(time.time() - start) * 1000:.2f} ms"
        )

    def retrieve(self, query: str, k: int = 3):

        if not self._is_indexed:
            return [], []

        query_embedding = self.embedding_model.encode_single(query)

        return self.index.search(query_embedding, k)

    def generate_answer(
        self,
        query: str,
        retrieved_docs: List[str],
        similarity_scores: List[float]
    ) -> str:

        if not retrieved_docs:
            return "No relevant information found."

        top_score = similarity_scores[0]

        if top_score > 0.7:
            confidence = "high confidence"
        elif top_score > 0.5:
            confidence = "moderate confidence"
        else:
            confidence = "low confidence"

        parts = []
        parts.append(f"Based on retrieved data ({confidence}):\n")
        parts.append(retrieved_docs[0])

        if len(retrieved_docs) > 1:
            parts.append("\n\nRelated info:\n")
            parts.append(retrieved_docs[1][:200])

        return "".join(parts)

    def query(self, query: str, k: int = 3) -> InferenceResult:

        start = time.time()

        docs, scores = self.retrieve(query, k)
        answer = self.generate_answer(query, docs, scores)

        latency = (time.time() - start) * 1000

        return InferenceResult(
            answer=answer,
            retrieved_docs=docs,
            similarity_scores=scores,
            latency_ms=latency,
            query=query
        )

    def is_ready(self) -> bool:
        return self._is_indexed and self.index.index.ntotal > 0


_pipeline_instance: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    global _pipeline_instance

    if _pipeline_instance is None:
        logger.info("Creating pipeline instance")

        _pipeline_instance = RAGPipeline()

        # ⬇⬇⬇ THIS IS THE IMPORTANT LINE
        _pipeline_instance.index_from_file("data/knowledge.txt")

    return _pipeline_instance


def run_inference(query: str, k: int = 3) -> Dict[str, Any]:

    pipeline = get_pipeline()
    result = pipeline.query(query, k)

    return {
        "answer": result.answer,
        "query": result.query,
        "retrieved_documents": result.retrieved_docs,
        "similarity_scores": result.similarity_scores,
        "latency_ms": round(result.latency_ms, 2),
        "status": "success"
    }
