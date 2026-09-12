from typing import List
import google.generativeai as genai
from app.core.config import get_settings


def get_embedding(
    text: str,
    model: str = "models/gemini-embedding-001",
    output_dimensionality: int = 768,
) -> List[float]:
    """
    Converts input text into a 768-dimensional vector embedding using Google Generative AI
    with models/gemini-embedding-001.
    """
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in settings/environment.")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    clean_text = text.replace("\n", " ").strip()
    if not clean_text:
        return [0.0] * output_dimensionality

    try:
        response = genai.embed_content(
            model=model,
            content=clean_text,
            task_type="retrieval_document",
            output_dimensionality=output_dimensionality,
        )
        return response["embedding"]
    except Exception:
        # Retry with fallback model if needed
        response = genai.embed_content(
            model="models/gemini-embedding-2-preview",
            content=clean_text,
            task_type="retrieval_document",
            output_dimensionality=output_dimensionality,
        )
        return response["embedding"]


def get_query_embedding(
    query: str,
    model: str = "models/gemini-embedding-001",
    output_dimensionality: int = 768,
) -> List[float]:
    """
    Generates a 768-dimensional embedding optimized for retrieval search queries.
    """
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in settings/environment.")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    clean_query = query.replace("\n", " ").strip()
    if not clean_query:
        return [0.0] * output_dimensionality

    try:
        response = genai.embed_content(
            model=model,
            content=clean_query,
            task_type="retrieval_query",
            output_dimensionality=output_dimensionality,
        )
        return response["embedding"]
    except Exception:
        response = genai.embed_content(
            model="models/gemini-embedding-2-preview",
            content=clean_query,
            task_type="retrieval_query",
            output_dimensionality=output_dimensionality,
        )
        return response["embedding"]
