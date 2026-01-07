"""Test ReAct agent and text splitting functionality."""
from text_splitter import STIXDocumentSplitter
from react_agent import ReActSTIXAgent
import json

def test_text_splitting():
    """Test text splitting functionality."""
    print("=" * 80)
    print("Test 1: Text Splitting")
    print("=" * 80)
    
    splitter = STIXDocumentSplitter(chunk_size=2000, chunk_overlap=200)
    
    with open('test_large_document.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Original document length: {len(content)} characters")
    
    chunks = splitter.split_document(content)
    print(f"Split into {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}:")
        print(f"  Length: {len(chunk.page_content)} characters")
        print(f"  Metadata: {chunk.metadata}")
        print(f"  Preview: {chunk.page_content[:100]}...")
        print()
    
    return chunks

def test_react_agent():
    """Test ReAct agent with large document."""
    print("=" * 80)
    print("Test 2: ReAct Agent Conversion")
    print("=" * 80)
    
    try:
        agent = ReActSTIXAgent()
        print("[OK] ReAct agent initialized")
    except Exception as e:
        print(f"[FAIL] Failed to initialize ReAct agent: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    with open('test_large_document.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Document length: {len(content)} characters")
    print("Starting conversion...\n")
    
    try:
        stix_output = agent.convert_to_stix(content)
        print("\n[OK] Conversion completed")
        return stix_output
    except Exception as e:
        print(f"\n[FAIL] Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_output(stix_output):
    """Validate STIX output."""
    print("=" * 80)
    print("Test 3: Output Validation")
    print("=" * 80)
    
    if not stix_output:
        print("[FAIL] No output to validate")
        return False
    
    try:
        stix_data = json.loads(stix_output)
        print(f"[OK] Valid JSON")
        print(f"  Type: {stix_data.get('type')}")
        print(f"  Spec version: {stix_data.get('spec_version')}")
        print(f"  Objects count: {len(stix_data.get('objects', []))}")
        
        # Count object types
        object_types = {}
        for obj in stix_data.get('objects', []):
            obj_type = obj.get('type', 'unknown')
            object_types[obj_type] = object_types.get(obj_type, 0) + 1
        
        print(f"  Object types:")
        for obj_type, count in object_types.items():
            print(f"    - {obj_type}: {count}")
        
        # Validate STIX format
        from stix_converter import STIXConverter
        is_valid, error = STIXConverter.validate_stix_json(stix_data)
        if is_valid:
            print(f"\n[OK] STIX format is valid")
            return True
        else:
            print(f"\n[FAIL] STIX validation failed: {error}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ReAct Agent and Text Splitting Test Suite")
    print("=" * 80 + "\n")
    
    # Test 1: Text splitting
    chunks = test_text_splitting()
    
    # Test 2: ReAct agent (only if text splitting works)
    if chunks:
        print("\n")
        stix_output = test_react_agent()
        
        # Test 3: Validate output
        if stix_output:
            print("\n")
            is_valid = validate_output(stix_output)
            
            # Save output
            if is_valid:
                with open('test_react_output.json', 'w', encoding='utf-8') as f:
                    f.write(stix_output)
                print(f"\n[OK] Output saved to test_react_output.json")
    
    print("\n" + "=" * 80)
    print("Test Suite Completed")
    print("=" * 80)

