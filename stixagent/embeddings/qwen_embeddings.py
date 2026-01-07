"""Custom Qwen Embeddings using OpenAI compatible API."""
from typing import List, Optional
from langchain_core.embeddings import Embeddings
try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDINGS_AVAILABLE = False
    OpenAIEmbeddings = None


class QwenEmbeddings(Embeddings):
    """Qwen embeddings using OpenAI compatible API."""
    
    def __init__(
        self,
        model: str = "text-embedding-v4",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize Qwen embeddings using OpenAI compatible API.
        
        Args:
            model: The embedding model name
            api_key: API key for the embedding service
            base_url: Base URL for the OpenAI compatible API endpoint
        """
        if not OPENAI_EMBEDDINGS_AVAILABLE:
            raise ImportError(
                "langchain-openai package is required. Install it with: pip install langchain-openai"
            )
        
        if not api_key:
            raise ValueError("API key is required. Set it via api_key parameter.")
        
        if not base_url:
            raise ValueError("Base URL is required. Set it via base_url parameter.")
        
        # Use OpenAIEmbeddings with custom base URL for OpenAI compatible API
        self.embeddings = OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)

