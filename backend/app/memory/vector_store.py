import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.supabase import get_supabase_client
from app.memory.embeddings import get_embedding, get_query_embedding


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def store_memory(
    user_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    memory_type: str = "fact",
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates text embeddings using Google Generative AI and inserts a new
    vector record into the Supabase jerry_memory table.
    """
    supabase = get_supabase_client()
    embedding = get_embedding(content)

    record = {
        "user_id": user_id,
        "content": content,
        "memory_type": memory_type,
        "embedding": embedding,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if thread_id:
        record["thread_id"] = thread_id

    response = supabase.table("jerry_memory").insert(record).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return record


def search_similar_memories(
    user_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Converts query to a 768-dimensional embedding and executes cosine similarity
    match against stored memory vectors in jerry_memory.
    Uses match_memories RPC if available, or falls back to vector distance query.
    """
    supabase = get_supabase_client()
    query_vector = get_query_embedding(query)

    # 1. Try Supabase RPC match_memories function
    try:
        rpc_params = {
            "query_embedding": query_vector,
            "match_count": top_k,
            "filter_user_id": user_id,
        }
        res = supabase.rpc("match_memories", rpc_params).execute()
        if res.data is not None:
            return res.data
    except Exception:
        pass

    # 2. Direct retrieval fallback: fetch user memories and sort by cosine similarity locally
    try:
        res = (
            supabase.table("jerry_memory")
            .select("id, user_id, thread_id, content, memory_type, metadata, embedding, created_at")
            .eq("user_id", user_id)
            .limit(100)
            .execute()
        )
        memories = res.data or []
        scored = []
        for m in memories:
            emb = m.get("embedding")
            if isinstance(emb, list) and len(emb) == len(query_vector):
                sim = _cosine_similarity(query_vector, emb)
                m_clean = dict(m)
                m_clean.pop("embedding", None)
                m_clean["similarity"] = sim
                scored.append(m_clean)
            else:
                m_clean = dict(m)
                m_clean.pop("embedding", None)
                m_clean["similarity"] = 0.0
                scored.append(m_clean)

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
    except Exception:
        return []
