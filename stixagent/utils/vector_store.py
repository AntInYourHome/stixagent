"""Vector store using LanceDB for STIX reference documents."""
import os
import lancedb
from langchain_community.vectorstores import LanceDB
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from ..loaders.document_loaders import DocumentLoader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import VECTOR_DB_PATH, STIX_REFERENCE_PDF, QWEN_API_KEY, EMBEDDING_MODEL

# Try to use QwenEmbeddings first, fall back to OpenAIEmbeddings
try:
    from ..embeddings.qwen_embeddings import QwenEmbeddings
    USE_QWEN_EMBEDDINGS = True
except ImportError:
    try:
        from langchain_openai import OpenAIEmbeddings
        USE_QWEN_EMBEDDINGS = False
    except ImportError:
        raise ImportError("Either dashscope (for QwenEmbeddings) or langchain-openai (for OpenAIEmbeddings) is required")


class STIXVectorStore:
    """Vector store for STIX reference documentation."""
    
    def __init__(self):
        """Initialize vector store."""
        self.db_path = VECTOR_DB_PATH
        self.table_name = "stix_reference"
        
        # Initialize embeddings - prefer QwenEmbeddings (dashscope SDK) over OpenAI compatible API
        if USE_QWEN_EMBEDDINGS:
            try:
                self.embeddings = QwenEmbeddings(
                    model=EMBEDDING_MODEL,
                    api_key=QWEN_API_KEY
                )
                print("[INFO] Using QwenEmbeddings (dashscope SDK)")
            except Exception as e:
                print(f"[WARN] Failed to initialize QwenEmbeddings: {e}")
                print("[INFO] Falling back to OpenAIEmbeddings")
                from langchain_openai import OpenAIEmbeddings
                from config import QWEN_BASE_URL
                try:
                    from config import EMBEDDING_URL
                    embedding_base_url = EMBEDDING_URL if EMBEDDING_URL else QWEN_BASE_URL
                except ImportError:
                    embedding_base_url = QWEN_BASE_URL
                self.embeddings = OpenAIEmbeddings(
                    model=EMBEDDING_MODEL,
                    openai_api_key=QWEN_API_KEY,
                    openai_api_base=embedding_base_url
                )
        else:
            from langchain_openai import OpenAIEmbeddings
            from config import QWEN_BASE_URL
            try:
                from config import EMBEDDING_URL
                embedding_base_url = EMBEDDING_URL if EMBEDDING_URL else QWEN_BASE_URL
            except ImportError:
                embedding_base_url = QWEN_BASE_URL
            self.embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=QWEN_API_KEY,
                openai_api_base=embedding_base_url
            )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store: Optional[LanceDB] = None
    
    def is_initialized(self) -> bool:
        """Check if the vector store is already initialized."""
        return self.vector_store is not None
    
    def _check_table_exists(self, db) -> bool:
        """Check if the table already exists in the database."""
        try:
            table_names = db.table_names()
            return self.table_name in table_names
        except Exception:
            return False
    
    def initialize(self, force_rebuild: bool = False):
        """Initialize vector store with STIX reference PDF.
        
        Args:
            force_rebuild: If True, rebuild the vector store even if it exists.
        """
        # If already initialized and not forcing rebuild, skip
        if self.is_initialized() and not force_rebuild:
            print("[INFO] Vector store already initialized, skipping...")
            return
        
        os.makedirs(self.db_path, exist_ok=True)
        
        # Connect to database
        db = lancedb.connect(self.db_path)
        
        # Check if table already exists
        table_exists = self._check_table_exists(db)
        
        if table_exists and not force_rebuild:
            # Load existing table
            try:
                # Use uri parameter instead of connection
                self.vector_store = LanceDB(
                    uri=self.db_path,
                    table_name=self.table_name,
                    embedding=self.embeddings
                )
                print(f"[OK] Loaded existing vector store from {self.db_path}")
                return
            except Exception as e:
                print(f"Warning: Failed to load existing table, will rebuild: {e}")
                # Fall through to rebuild
        
        # Build new vector store
        print(f"Building vector store from {STIX_REFERENCE_PDF}...")
        
        # Load STIX reference PDF
        if not os.path.exists(STIX_REFERENCE_PDF):
            raise FileNotFoundError(f"STIX reference PDF not found: {STIX_REFERENCE_PDF}")
        
        documents = DocumentLoader.load_pdf(STIX_REFERENCE_PDF)
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        if not chunks:
            raise ValueError("No document chunks to create vector store")
        
        # Create vector store using from_documents
        # Always use overwrite if table exists or force_rebuild is True
        try:
            self.vector_store = LanceDB.from_documents(
                chunks,
                self.embeddings,
                uri=self.db_path,
                table_name=self.table_name
            )
            print(f"[OK] Vector store initialized with {len(chunks)} chunks")
        except Exception as e:
            # If table already exists, delete it and recreate
            if "already exists" in str(e).lower() or "table" in str(e).lower():
                print(f"Table exists, deleting and recreating...")
                try:
                    db.drop_table(self.table_name)
                except:
                    pass
                self.vector_store = LanceDB.from_documents(
                    chunks,
                    self.embeddings,
                    uri=self.db_path,
                    table_name=self.table_name
                )
                print(f"[OK] Vector store initialized with {len(chunks)} chunks")
            else:
                raise
    
    def search(self, query: str, k: int = 5) -> List[dict]:
        """Search for relevant STIX documentation."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call initialize() first.")
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
    
    def get_relevant_context(self, query: str, k: int = 5) -> str:
        """Get relevant STIX context as formatted string."""
        results = self.search(query, k=k)
        context_parts = []
        
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Reference {i}]\n"
                f"Source: {result['metadata'].get('source', 'unknown')}\n"
                f"Page: {result['metadata'].get('page', 'N/A')}\n"
                f"Content:\n{result['content']}\n"
            )
        
        return "\n".join(context_parts)

