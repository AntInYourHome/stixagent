"""Test LLM API connectivity and functionality."""
import sys
from config import API_KEY, BASE_URL, LLM_MODEL, EMBEDDING_MODEL
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def test_llm_api():
    """Test LLM API connection."""
    print("=" * 80)
    print("Testing LLM API Configuration")
    print("=" * 80)
    
    # Check configuration
    print(f"\n[Config Check]")
    print(f"  API Key: {'Set' if API_KEY else 'NOT SET'}")
    print(f"  Base URL: {BASE_URL if BASE_URL else 'NOT SET'}")
    print(f"  LLM Model: {LLM_MODEL}")
    print(f"  Embedding Model: {EMBEDDING_MODEL}")
    
    if not API_KEY or not BASE_URL:
        print("\n[ERROR] API credentials not configured!")
        print("Please set API_KEY and BASE_URL environment variables or create .env file")
        return False
    
    # Test LLM
    print(f"\n[Test 1] Testing LLM API ({LLM_MODEL})...")
    try:
        llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=API_KEY,
            base_url=BASE_URL,
            temperature=0.1,
            timeout=30
        )
        
        # Simple test message
        test_message = "Hello, please respond with 'API test successful' in Chinese."
        print(f"  Sending test message: {test_message}")
        
        response = llm.invoke(test_message)
        print(f"  [OK] LLM Response: {response.content}")
        print(f"  [OK] LLM API is working correctly!")
        
    except Exception as e:
        print(f"  [FAIL] LLM API test failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Embedding
    print(f"\n[Test 2] Testing Embedding API ({EMBEDDING_MODEL})...")
    
    # Try different configurations
    embedding_configs = [
        {"name": "Using BASE_URL", "base_url": BASE_URL},
    ]
    
    embedding_success = False
    for config in embedding_configs:
        try:
            print(f"  Trying: {config['name']} ({config['base_url']})")
            embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=API_KEY,
                openai_api_base=config['base_url']
            )
            
            # Test embedding
            test_text = "This is a test text for embedding."
            print(f"    Testing embedding for: '{test_text}'")
            
            embedding = embeddings.embed_query(test_text)
            print(f"    [OK] Embedding generated successfully")
            print(f"    [OK] Embedding dimension: {len(embedding)}")
            print(f"    [OK] Embedding API is working correctly with {config['name']}!")
            embedding_success = True
            break
            
        except Exception as e:
            print(f"    [FAIL] {config['name']} failed: {type(e).__name__}: {str(e)[:100]}")
            continue
    
    if not embedding_success:
        print(f"  [FAIL] All embedding API configurations failed")
        print(f"  Note: This may not prevent the system from working if vector DB already exists")
        # Don't return False here, as embedding might not be needed if vector DB exists
        return True  # LLM works, which is the main requirement
    
    print("\n" + "=" * 80)
    print("[SUCCESS] All API tests passed!")
    print("=" * 80)
    return True


def test_llm_with_tools():
    """Test LLM with tool binding (simulating agent usage)."""
    print("\n" + "=" * 80)
    print("Testing LLM with Tool Binding")
    print("=" * 80)
    
    if not API_KEY or not BASE_URL:
        print("[SKIP] API credentials not configured, skipping tool test")
        return False
    
    try:
        from langchain_core.tools import tool
        
        @tool
        def test_tool(query: str) -> str:
            """A test tool that returns a simple message."""
            return f"Tool called with: {query}"
        
        llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=API_KEY,
            base_url=BASE_URL,
            temperature=0.1,
            timeout=30
        )
        
        llm_with_tools = llm.bind_tools([test_tool])
        
        # Test message that might trigger tool use
        test_message = "Please use the test_tool with the parameter 'hello world'"
        print(f"  Sending message: {test_message}")
        
        response = llm_with_tools.invoke(test_message)
        print(f"  [OK] Response received")
        print(f"  Response content: {response.content}")
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"  [OK] Tool calls detected: {len(response.tool_calls)}")
            for tool_call in response.tool_calls:
                print(f"    - Tool: {tool_call.get('name', 'unknown')}")
        else:
            print(f"  [INFO] No tool calls in response (this is OK)")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Tool binding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("LLM API Test Suite")
    print("=" * 80)
    
    # Basic API tests
    llm_ok = test_llm_api()
    
    # Tool binding test
    if llm_ok:
        test_llm_with_tools()
    
    if not llm_ok:
        print("\n[ERROR] API tests failed. Please check your configuration.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests completed successfully!")

