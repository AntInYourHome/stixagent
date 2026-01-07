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
TEMPERATURE = 0.1  # Lower temperature for more consistent STIX format output

# STIX Configuration
STIX_VERSION = "2.1"

# Logging Configuration
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "./logs/stixagent.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

