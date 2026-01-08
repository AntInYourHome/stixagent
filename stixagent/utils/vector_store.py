"""Vector store using LanceDB for STIX reference documents."""
import os
import lancedb
try:
    from langchain_community.vectorstores import LanceDB
except ImportError:
    try:
        from langchain_lance import LanceDB
    except ImportError:
        LanceDB = None
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from ..loaders.document_loaders import DocumentLoader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import VECTOR_DB_PATH, STIX_REFERENCE_PDF, QWEN_API_KEY, EMBEDDING_MODEL, EMBEDDING_URL, QWEN_BASE_URL, EMBEDDING_MODE

# Import embedding classes
try:
    from ..embeddings.qwen_embeddings import QwenEmbeddings
    QWEN_EMBEDDINGS_AVAILABLE = True
except ImportError:
    QWEN_EMBEDDINGS_AVAILABLE = False

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDINGS_AVAILABLE = False


class STIXVectorStore:
    """Vector store for STIX reference documentation."""
    
    def __init__(self):
        """Initialize vector store."""
        self.db_path = VECTOR_DB_PATH
        self.table_name = "stix_reference"
        
        # Initialize embeddings based on configuration
        embedding_base_url = EMBEDDING_URL if EMBEDDING_URL else QWEN_BASE_URL
        
        if EMBEDDING_MODE == "qwen":
            # Use QwenEmbeddings (direct Qwen API call)
            if not QWEN_EMBEDDINGS_AVAILABLE:
                raise ImportError(
                    "QwenEmbeddings not available. Install required dependencies or set EMBEDDING_MODE=openai"
                )
            try:
                self.embeddings = QwenEmbeddings(
                    model=EMBEDDING_MODEL,
                    api_key=QWEN_API_KEY,
                    base_url=embedding_base_url
                )
                print("[INFO] Using QwenEmbeddings (Qwen API direct call)")
            except Exception as e:
                print(f"[WARN] Failed to initialize QwenEmbeddings: {e}")
                if OPENAI_EMBEDDINGS_AVAILABLE:
                    print("[INFO] Falling back to OpenAIEmbeddings")
                    self.embeddings = OpenAIEmbeddings(
                        model=EMBEDDING_MODEL,
                        openai_api_key=QWEN_API_KEY,
                        openai_api_base=embedding_base_url
                    )
                    print("[INFO] Using OpenAIEmbeddings (OpenAI compatible API)")
                else:
                    raise
        elif EMBEDDING_MODE == "openai":
            # Use OpenAIEmbeddings (OpenAI compatible interface)
            if not OPENAI_EMBEDDINGS_AVAILABLE:
                raise ImportError(
                    "OpenAIEmbeddings not available. Install langchain-openai or set EMBEDDING_MODE=qwen"
                )
            self.embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=QWEN_API_KEY,
                openai_api_base=embedding_base_url
            )
            print("[INFO] Using OpenAIEmbeddings (OpenAI compatible API)")
        else:
            raise ValueError(
                f"Invalid EMBEDDING_MODE: {EMBEDDING_MODE}. Must be 'qwen' or 'openai'"
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
            # Check if vector store exists but not loaded
            if not self.is_initialized():
                import logging
                logger = logging.getLogger("stixagent")
                logger.warning("Vector store not initialized. Attempting to load existing vector store...")
                try:
                    self.initialize()
                    # Re-check if initialized successfully
                    if self.vector_store is None:
                        logger.warning("Vector store initialization returned None. Search will return empty results.")
                        return []
                except Exception as e:
                    logger.warning(f"Failed to initialize vector store: {e}")
                    return []
            else:
                # Try to load existing vector store
                try:
                    db = lancedb.connect(self.db_path)
                    if self._check_table_exists(db) and LanceDB is not None:
                        self.vector_store = LanceDB(
                            uri=self.db_path,
                            table_name=self.table_name,
                            embedding=self.embeddings
                        )
                    else:
                        import logging
                        logger = logging.getLogger("stixagent")
                        if LanceDB is None:
                            logger.warning("LanceDB not available. Search will return empty results.")
                        else:
                            logger.warning("Vector store table does not exist. Search will return empty results.")
                        return []
                except Exception as e:
                    import logging
                    logger = logging.getLogger("stixagent")
                    logger.warning(f"Failed to load vector store: {e}")
                    return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]
        except Exception as e:
            # If embedding API fails, return empty results with warning
            import logging
            logger = logging.getLogger("stixagent")
            logger.warning(f"Vector search failed (embedding API error): {e}")
            logger.warning("Returning empty search results. Agent will continue without STIX reference context.")
            # Check if it's an embedding API error specifically
            error_str = str(e).lower()
            if "embedding" in error_str or "api" in error_str or "connection" in error_str:
                logger.warning("This appears to be an embedding API issue. Vector store search will be disabled.")
            return []
    
    def get_relevant_context(self, query: str, k: int = 5, max_length: int = None) -> str:
        """Get relevant STIX context as formatted string.
        
        Args:
            query: Search query
            k: Number of results to return
            max_length: Maximum length of returned context (characters). If None, no limit.
        """
        try:
            results = self.search(query, k=k)
            if not results:
                return "无法从 STIX 参考文档中检索到相关信息（embedding API 调用失败）。请根据系统提示中的 STIX 格式要求生成输出。"
            
            context_parts = []
            current_length = 0
            
            for i, result in enumerate(results, 1):
                content = result['content']
                # 如果设置了最大长度，截断内容
                if max_length and current_length + len(content) > max_length:
                    remaining = max_length - current_length - 100  # 留100字符给格式
                    if remaining > 0:
                        content = content[:remaining] + "...[截断]"
                    else:
                        break
                
                context_parts.append(
                    f"[Reference {i}]\n"
                    f"Source: {result['metadata'].get('source', 'unknown')}\n"
                    f"Page: {result['metadata'].get('page', 'N/A')}\n"
                    f"Content:\n{content}\n"
                )
                current_length += len(context_parts[-1])
            
            return "\n".join(context_parts)
        except Exception as e:
            import logging
            logger = logging.getLogger("stixagent")
            logger.warning(f"Failed to get relevant context: {e}")
            return "无法从 STIX 参考文档中检索到相关信息。请根据系统提示中的 STIX 格式要求生成输出。"

