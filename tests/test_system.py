"""Test script to verify system components."""
import sys
import os
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test all imports."""
    print("=" * 80)
    print("Testing Imports...")
    print("=" * 80)
    try:
        from stixagent.loaders import DocumentLoader
        print("[OK] DocumentLoader imported successfully")
    except Exception as e:
        print(f"[FAIL] DocumentLoader import failed: {e}")
        return False
    
    try:
        from stixagent.utils import STIXVectorStore
        print("[OK] STIXVectorStore imported successfully")
    except Exception as e:
        print(f"[FAIL] STIXVectorStore import failed: {e}")
        return False
    
    try:
        from stixagent.utils import STIXConverter
        print("[OK] STIXConverter imported successfully")
    except Exception as e:
        print(f"[FAIL] STIXConverter import failed: {e}")
        return False
    
    try:
        import config
        print("[OK] Config imported successfully")
    except Exception as e:
        print(f"[FAIL] Config import failed: {e}")
        return False
    
    try:
        from stixagent.agents import STIXAgent
        print("[OK] STIXAgent imported successfully")
    except Exception as e:
        print(f"[FAIL] STIXAgent import failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_document_loader():
    """Test document loading."""
    print("\n" + "=" * 80)
    print("Testing Document Loader...")
    print("=" * 80)
    try:
        from stixagent.loaders import DocumentLoader
        import os
        test_file = os.path.join(os.path.dirname(__file__), "test_input.txt")
        docs = DocumentLoader.load_document(test_file)
        print(f"[OK] Loaded {len(docs)} document(s) from test_input.txt")
        print(f"  Content length: {len(docs[0].page_content)} characters")
        print(f"  Metadata: {docs[0].metadata}")
        return True
    except Exception as e:
        print(f"[FAIL] Document loading failed: {e}")
        traceback.print_exc()
        return False

def test_stix_converter():
    """Test STIX converter."""
    print("\n" + "=" * 80)
    print("Testing STIX Converter...")
    print("=" * 80)
    try:
        from stixagent.utils import STIXConverter
        
        # Test schema hints
        hints = STIXConverter.get_stix_schema_hints()
        print(f"[OK] Schema hints retrieved ({len(hints)} characters)")
        
        # Test validation with valid STIX
        valid_stix = {
            "type": "bundle",
            "id": "bundle--test",
            "spec_version": "2.1",
            "objects": [
                {
                    "type": "indicator",
                    "id": "indicator--test",
                    "created": "2024-01-01T00:00:00.000Z",
                    "modified": "2024-01-01T00:00:00.000Z",
                    "spec_version": "2.1"
                }
            ]
        }
        is_valid, error = STIXConverter.validate_stix_json(valid_stix)
        if is_valid:
            print("[OK] STIX validation works correctly")
        else:
            print(f"[FAIL] STIX validation failed: {error}")
            return False
        
        # Test validation with invalid STIX
        invalid_stix = {"type": "bundle"}  # Missing required fields
        is_valid, error = STIXConverter.validate_stix_json(invalid_stix)
        if not is_valid:
            print("[OK] Invalid STIX correctly rejected")
        else:
            print("[FAIL] Invalid STIX was accepted")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] STIX converter test failed: {e}")
        traceback.print_exc()
        return False

def test_agent_initialization():
    """Test agent initialization (may fail if API not configured)."""
    print("\n" + "=" * 80)
    print("Testing Agent Initialization...")
    print("=" * 80)
    try:
        from stixagent.agents import STIXAgent
        from config import API_KEY, BASE_URL
        
        if not API_KEY or not BASE_URL:
            print("[WARN] API credentials not configured (API_KEY, BASE_URL)")
            print("  Agent initialization will fail, but this is expected.")
            print("  Please set environment variables or create .env file:")
            print("    QWEN_API=your_api_key")
            print("    QWEN_URL=https://your-api-endpoint.com/v1")
            return True  # Not a failure, just missing config
        
        agent = STIXAgent()
        print("[OK] STIXAgent initialized successfully")
        return True
    except Exception as e:
        if "QWEN_API" in str(e) or "api_key" in str(e).lower() or "base_url" in str(e).lower():
            print("[WARN] Agent initialization failed due to missing API configuration")
            print("  This is expected if QWEN_API and QWEN_URL are not set")
            return True  # Expected failure
        else:
            print(f"[FAIL] Agent initialization failed: {e}")
            traceback.print_exc()
            return False

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("STIX Agent System Test")
    print("=" * 80)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Document Loader", test_document_loader()))
    results.append(("STIX Converter", test_stix_converter()))
    results.append(("Agent Initialization", test_agent_initialization()))
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n[OK] All tests passed!")
        print("\nNext steps:")
        print("1. Set QWEN_API and QWEN_URL environment variables or create .env file")
        print("2. Run: python main.py test_input.txt -o output.json")
    else:
        print("\n[FAIL] Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

