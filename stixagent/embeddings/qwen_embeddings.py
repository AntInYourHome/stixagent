"""OpenAI-like Embeddings using OpenAI compatible API."""
from typing import List, Optional
import requests
import json
from langchain_core.embeddings import Embeddings


class OPENAILIKEEmbeddings(Embeddings):
    """OpenAI-like embeddings using OpenAI compatible API with proper format."""
    
    def __init__(
        self,
        model: str = "text-embedding-v4",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize OpenAI-like embeddings using OpenAI compatible API.
        
        Args:
            model: The embedding model name
            api_key: API key for the embedding service
            base_url: Base URL for the OpenAI compatible API endpoint
        """
        if not api_key:
            raise ValueError("API key is required. Set it via api_key parameter.")
        
        if not base_url:
            raise ValueError("Base URL is required. Set it via base_url parameter.")
        
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.embedding_endpoint = f"{self.base_url}/embeddings"
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts using Qwen API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Qwen API expects input as a list of strings directly
        payload = {
            "model": self.model,
            "input": texts  # Direct list of strings, not wrapped in contents
        }
        
        try:
            response = requests.post(
                self.embedding_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract embeddings from response
            if "data" in result:
                # OpenAI-compatible format
                embeddings = [item["embedding"] for item in result["data"]]
            elif "output" in result and "embeddings" in result["output"]:
                # Qwen native format
                embeddings = [item["embedding"] for item in result["output"]["embeddings"]]
            else:
                raise ValueError(f"Unexpected API response format: {result}")
            
            return embeddings
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg} - {json.dumps(error_detail)}"
                except:
                    error_msg = f"{error_msg} - {e.response.text}"
            raise ValueError(f"Error calling embedding API: {error_msg}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Qwen API has a batch size limit, process in batches
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embed_documents([text])[0]

