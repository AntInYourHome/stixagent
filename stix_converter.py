"""STIX format converter and validator."""
import json
from typing import Dict, Any, Optional, Tuple
import stix2
from stix2 import Bundle, Indicator, Malware, ThreatActor, AttackPattern, Vulnerability, Relationship
from datetime import datetime


class STIXConverter:
    """Convert penetration test cases to STIX 2.1 format."""
    
    @staticmethod
    def validate_stix_json(stix_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate STIX JSON structure."""
        try:
            # Try to parse as STIX bundle
            if isinstance(stix_data, dict):
                if "type" in stix_data and stix_data["type"] == "bundle":
                    # Validate bundle structure
                    if "objects" not in stix_data:
                        return False, "Bundle missing 'objects' field"
                    
                    # Validate each object
                    for obj in stix_data.get("objects", []):
                        if "type" not in obj:
                            return False, "STIX object missing 'type' field"
                        if "id" not in obj:
                            return False, "STIX object missing 'id' field"
                        if "created" not in obj:
                            return False, "STIX object missing 'created' field"
                        if "modified" not in obj:
                            return False, "STIX object missing 'modified' field"
                
                elif "type" in stix_data:
                    # Single STIX object
                    if "id" not in stix_data:
                        return False, "STIX object missing 'id' field"
                    if "created" not in stix_data:
                        return False, "STIX object missing 'created' field"
                    if "modified" not in stix_data:
                        return False, "STIX object missing 'modified' field"
            
            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def format_stix_output(stix_data: Dict[str, Any]) -> str:
        """Format STIX data as pretty JSON."""
        return json.dumps(stix_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_stix_schema_hints() -> str:
        """Get STIX 2.1 schema hints for the AI."""
        return """
STIX 2.1 Format Requirements:

1. Bundle Structure:
   - type: "bundle"
   - id: "bundle--<UUID>"
   - spec_version: "2.1"
   - objects: array of STIX objects

2. Common STIX Object Fields:
   - type: object type (e.g., "indicator", "malware", "attack-pattern")
   - id: "<type>--<UUID>"
   - created: ISO 8601 timestamp
   - modified: ISO 8601 timestamp
   - spec_version: "2.1"

3. Common Object Types:
   - indicator: Threat indicators (IPs, domains, hashes)
   - malware: Malware descriptions
   - attack-pattern: Attack techniques (MITRE ATT&CK)
   - threat-actor: Threat actors
   - vulnerability: Vulnerabilities (CVE)
   - relationship: Relationships between objects

4. Example Indicator:
   {
     "type": "indicator",
     "id": "indicator--<UUID>",
     "created": "2024-01-01T00:00:00.000Z",
     "modified": "2024-01-01T00:00:00.000Z",
     "spec_version": "2.1",
     "pattern": "[ipv4-addr:value = '192.168.1.1']",
     "pattern_type": "stix",
     "valid_from": "2024-01-01T00:00:00.000Z"
   }

5. Example Attack Pattern:
   {
     "type": "attack-pattern",
     "id": "attack-pattern--<UUID>",
     "created": "2024-01-01T00:00:00.000Z",
     "modified": "2024-01-01T00:00:00.000Z",
     "spec_version": "2.1",
     "name": "Attack Name",
     "description": "Attack description",
     "kill_chain_phases": [
       {
         "kill_chain_name": "mitre-attack",
         "phase_name": "initial-access"
       }
     ]
   }

6. Relationships:
   {
     "type": "relationship",
     "id": "relationship--<UUID>",
     "created": "2024-01-01T00:00:00.000Z",
     "modified": "2024-01-01T00:00:00.000Z",
     "spec_version": "2.1",
     "relationship_type": "uses",
     "source_ref": "malware--<UUID>",
     "target_ref": "attack-pattern--<UUID>"
   }

7. All timestamps must be ISO 8601 format: YYYY-MM-DDTHH:mm:ss.sssZ
8. All IDs must follow the pattern: <type>--<UUID v4>
"""

