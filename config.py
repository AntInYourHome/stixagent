"""Configuration settings for STIX Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
QWEN_API_KEY = os.getenv("QWEN_API", "")
QWEN_BASE_URL = os.getenv("QWEN_URL", "")

# Model Configuration
LLM_MODEL = "qwen3-max"
EMBEDDING_MODEL = "text-embedding-v4"
EMBEDDING_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# Embedding Mode Configuration
# Options: "qwen" (使用 QwenEmbeddings 直接调用 Qwen API) or "openai" (使用 OpenAIEmbeddings 兼容接口)
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "qwen").lower()  # Default to "qwen"

# Vector Database Configuration
VECTOR_DB_PATH = "./vector_db"
STIX_REFERENCE_PDF = "stix-v2.1-os.pdf"

# Agent Configuration
MAX_ITERATIONS = 50
CHUNK_MAX_ITERATIONS = int(os.getenv("CHUNK_MAX_ITERATIONS", "3"))  # 每个chunk的最大迭代次数，默认3
TEMPERATURE = 0.1  # Lower temperature for more consistent STIX format output
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))  # LLM API超时时间（秒），默认120秒（增加到2分钟）
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))  # LLM API最大重试次数，默认2次
TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "30"))  # 工具调用超时时间（秒），默认30秒
VECTOR_SEARCH_TIMEOUT = int(os.getenv("VECTOR_SEARCH_TIMEOUT", "20"))  # 向量搜索超时时间（秒），默认20秒
MAX_TOOL_RESULT_LENGTH = int(os.getenv("MAX_TOOL_RESULT_LENGTH", "2000"))  # 工具返回结果最大长度（字符），默认2000
MAX_MESSAGE_HISTORY = int(os.getenv("MAX_MESSAGE_HISTORY", "10"))  # 最大消息历史数量，默认10（只保留最近的交互）

# STIX Configuration
STIX_VERSION = "2.1"

# Logging Configuration
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "./logs/stixagent.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

