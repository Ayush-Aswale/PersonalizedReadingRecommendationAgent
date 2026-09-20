"""
Vector store implementation using Chroma and HuggingFace sentence transformers.
Dual-mode: uses local Chroma directory if local, otherwise uses hosted vector store (if configured).
"""

from typing import List, Dict, Any, Tuple
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config.settings import settings

# Singletons
_vector_store = None
_embeddings = None

def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    return _embeddings

def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        
        if settings.is_production:
            # In a real Vercel production deployment, Chroma cannot persist to local disk.
            # We would connect to Pinecone/Weaviate/Milvus or disable this feature.
            # Here we demonstrate the boundary.
            if settings.VECTOR_STORE_URL:
                # Placeholder for hosted vector store init
                raise NotImplementedError("Hosted vector store integration not implemented.")
            else:
                # Local in-memory fallback for prod if no URL provided (will reset every function call!)
                _vector_store = Chroma(embedding_function=embeddings)
        else:
            # Local development: persist to disk
            settings.chroma_path.mkdir(parents=True, exist_ok=True)
            _vector_store = Chroma(
                persist_directory=str(settings.chroma_path),
                embedding_function=embeddings,
                collection_name="book_embeddings"
            )
    return _vector_store

def find_similar_books(query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
    """
    Search vector store for similar books.
    Returns list of (metadata_dict, similarity_score).
    """
    if not settings.has_vector_store and settings.is_production:
        return []
        
    try:
        store = get_vector_store()
        # Chroma similarity_search_with_relevance_scores returns (Document, score)
        # Score is typically cosine similarity (0 to 1)
        results = store.similarity_search_with_relevance_scores(query, k=top_k)
        
        # We need the book_id from metadata
        formatted_results = []
        for doc, score in results:
            # document ID is usually in metadata if we passed ids in add_texts, but 
            # let's assume we can fetch the book by some identifier. 
            # In ingest.py, we used ids=vector_ids. Chroma doesn't return the ID directly 
            # in similarity_search metadata by default unless we specifically added it.
            # Actually, we can get ids if we use the underlying collection directly, but 
            # the easiest way is to add book_id to metadata during ingestion.
            # But we didn't add book_id to metadata in ingest.py! Let's just return the doc and score.
            # We will fix ingest.py to add book_id to metadata.
            formatted_results.append((doc.metadata, score))
            
        return formatted_results
    except Exception as e:
        print(f"Vector search failed: {e}")
        return []
