"""Configuration settings for STIX Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
QWEN_API_KEY = os.getenv("QWEN_API", "")
QWEN_BASE_URL = os.getenv("QWEN_URL", "")

# Model Configuration
LLM_MODEL = "qwen-flash"
EMBEDDING_MODEL = "text-embedding-v4"
EMBEDDING_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# Vector Database Configuration
VECTOR_DB_PATH = "./vector_db"
STIX_REFERENCE_PDF = "stix-v2.1-os.pdf"

# Agent Configuration
MAX_ITERATIONS = 50
TEMPERATURE = 0.1  # Lower temperature for more consistent STIX format output

# STIX Configuration
STIX_VERSION = "2.1"

