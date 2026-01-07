"""Example usage of STIX Agent."""
from document_loaders import DocumentLoader
from agent import STIXAgent
import json


def example_convert_text():
    """Example: Convert a text document to STIX."""
    # Create a sample penetration test case text
    sample_text = """
    Penetration Test Report
    
    Target: 192.168.1.100
    Vulnerability: SQL Injection in login form
    CVE: CVE-2024-12345
    Attack Pattern: SQL Injection (T1190)
    Indicator: Malicious SQL query detected
    """
    
    # Initialize agent
    agent = STIXAgent()
    
    # Convert to STIX
    stix_output = agent.convert_to_stix(sample_text)
    
    print("STIX Output:")
    print("=" * 80)
    print(stix_output)
    
    # Save to file
    with open("example_output.json", "w", encoding="utf-8") as f:
        f.write(stix_output)
    print("\nOutput saved to example_output.json")


if __name__ == "__main__":
    example_convert_text()

