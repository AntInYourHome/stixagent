"""Custom Qwen Embeddings using dashscope SDK."""
from typing import List, Optional
from langchain_core.embeddings import Embeddings
try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    dashscope = None


class QwenEmbeddings(Embeddings):
    """Qwen embeddings using dashscope SDK."""
    
    def __init__(
        self,
        model: str = "text-embedding-v4",
        api_key: Optional[str] = None,
    ):
        """Initialize Qwen embeddings.
        
        Args:
            model: The embedding model name
            api_key: Dashscope API key
        """
        if not DASHSCOPE_AVAILABLE:
            raise ImportError(
                "dashscope package is required. Install it with: pip install dashscope"
            )
        
        self.model = model
        if api_key:
            dashscope.api_key = api_key
        elif not dashscope.api_key:
            raise ValueError("API key is required. Set it via api_key parameter or DASHSCOPE_API_KEY environment variable.")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Dashscope API has a batch size limit of 10
        # Ensure we never exceed this limit
        batch_size = 10
        all_embeddings = []
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Double-check batch size (should never exceed 10)
            if len(batch) > batch_size:
                # If somehow batch is larger, split it further
                for j in range(0, len(batch), batch_size):
                    sub_batch = batch[j:j + batch_size]
                    all_embeddings.extend(self._embed_batch(sub_batch))
            else:
                all_embeddings.extend(self._embed_batch(batch))
        
        return all_embeddings
    
    def _embed_batch(self, batch: List[str]) -> List[List[float]]:
        """Embed a single batch of texts (max 10 items).
        
        Args:
            batch: List of texts to embed (must be <= 10 items)
            
        Returns:
            List of embedding vectors
        """
        if len(batch) > 10:
            raise ValueError(f"Batch size {len(batch)} exceeds maximum of 10")
        
        try:
            response = dashscope.TextEmbedding.call(
                model=self.model,
                input=batch
            )
            
            if response.status_code == 200:
                embeddings = [item['embedding'] for item in response.output['embeddings']]
                return embeddings
            else:
                raise ValueError(f"Dashscope API error: {response.message}")
        except Exception as e:
            raise ValueError(f"Error calling dashscope API: {str(e)}")
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embed_documents([text])[0]

