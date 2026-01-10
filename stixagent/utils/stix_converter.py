"""STIX format converter and validator."""
import json
from typing import Dict, Any, Optional, Tuple
import stix2
from stix2 import Bundle, Indicator, Malware, ThreatActor, AttackPattern, Vulnerability, Relationship
from datetime import datetime
import time

# #region agent log
DEBUG_LOG_PATH = r"e:\coding\agents\.cursor\debug.log"
def _debug_log(location, message, data, hypothesis_id):
    try:
        log_entry = {
            "id": f"log_{int(time.time() * 1000)}",
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


class STIXConverter:
    """Convert penetration test cases to STIX 2.1 format."""
    
    @staticmethod
    def validate_stix_json(stix_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate STIX JSON structure."""
        try:
            # STIX Cyber Observable Objects (SCOs) that don't require created/modified fields
            SCO_TYPES = {
                'artifact', 'autonomous-system', 'directory', 'domain-name', 'email-addr',
                'email-message', 'file', 'ipv4-addr', 'ipv6-addr', 'mac-addr', 'mutex',
                'network-traffic', 'process', 'software', 'url', 'user-account',
                'windows-registry-key', 'x509-certificate'
            }

            # Try to parse as STIX bundle
            if isinstance(stix_data, dict):
                if "type" in stix_data and stix_data["type"] == "bundle":
                    # Validate bundle structure
                    if "objects" not in stix_data:
                        return False, "Bundle missing 'objects' field"

                    # Validate each object
                    for idx, obj in enumerate(stix_data.get("objects", [])):
                        # #region agent log
                        _debug_log("stix_converter.py:24", "Validating STIX object", {
                            "index": idx,
                            "type": obj.get("type"),
                            "id": obj.get("id"),
                            "has_created": "created" in obj,
                            "has_modified": "modified" in obj,
                            "all_keys": list(obj.keys())[:10]
                        }, "C")
                        # #endregion
                        if "type" not in obj:
                            return False, "STIX object missing 'type' field"
                        if "id" not in obj:
                            return False, "STIX object missing 'id' field"

                        # SCOs don't require created/modified fields
                        obj_type = obj.get("type", "")
                        if obj_type not in SCO_TYPES:
                            # SDOs and SROs require created/modified
                            if "created" not in obj:
                                # #region agent log
                                _debug_log("stix_converter.py:29", "Object missing created field", {
                                    "object_type": obj.get("type"),
                                    "object_id": obj.get("id"),
                                    "all_keys": list(obj.keys())
                                }, "C")
                                # #endregion
                                return False, f"STIX object missing 'created' field (type: {obj.get('type')}, id: {obj.get('id')})"
                            if "modified" not in obj:
                                # #region agent log
                                _debug_log("stix_converter.py:31", "Object missing modified field", {
                                    "object_type": obj.get("type"),
                                    "object_id": obj.get("id"),
                                    "all_keys": list(obj.keys())
                                }, "C")
                                # #endregion
                                return False, f"STIX object missing 'modified' field (type: {obj.get('type')}, id: {obj.get('id')})"

                elif "type" in stix_data:
                    # Single STIX object
                    if "id" not in stix_data:
                        return False, "STIX object missing 'id' field"

                    # SCOs don't require created/modified fields
                    obj_type = stix_data.get("type", "")
                    if obj_type not in SCO_TYPES:
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

3. STIX 2.1 Object Types (MUST extract ALL types when present in document):

   STIX Domain Objects (SDOs) - 18 types:
   - attack-pattern: Attack techniques (MITRE ATT&CK), exploitation methods
   - campaign: Grouping of adversarial behaviors over time
   - course-of-action: Recommendations for response actions
   - grouping: Objects with shared context
   - identity: Individuals, organizations, or groups
   - indicator: Threat indicators (IPs, domains, hashes, URLs)
   - infrastructure: Systems, software services, C2 servers
   - intrusion-set: Grouped adversarial behaviors by single organization
   - location: Geographic locations
   - malware: Malware descriptions, tools, web shells
   - malware-analysis: Metadata and results of malware analysis
   - note: Additional context and analysis
   - observed-data: Cyber security entities (files, systems, networks)
   - opinion: Assessment of correctness of information
   - report: Collections of threat intelligence on topics
   - threat-actor: Threat actors, attacker groups
   - tool: Legitimate software used by threat actors
   - vulnerability: Vulnerabilities (CVE), security weaknesses
   
   STIX Relationship Objects (SROs) - 2 types:
   - relationship: Links between SDOs or SCOs (uses, targets, indicates, etc.)
   - sighting: Belief that something in CTI was seen
   
   IMPORTANT: Do not only extract indicators. If the document mentions:
   - Attack techniques → create attack-pattern objects
   - Malware/tools → create malware or tool objects  
   - Vulnerabilities/CVE → create vulnerability objects
   - Attackers → create threat-actor objects
   - Campaigns → create campaign objects
   - Infrastructure → create infrastructure objects
   - Connections between entities → create relationship objects
   - Sightings → create sighting objects

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
     ],
     "external_references": [
       {
         "source_name": "mitre-attack",
         "external_id": "T1190"
       }
     ]
   }

6. Example Malware:
   {
     "type": "malware",
     "id": "malware--<UUID>",
     "created": "2024-01-01T00:00:00.000Z",
     "modified": "2024-01-01T00:00:00.000Z",
     "spec_version": "2.1",
     "name": "Malware Name",
     "description": "Malware description",
     "malware_types": ["web-shell", "trojan"]
   }

7. Example Vulnerability:
   {
     "type": "vulnerability",
     "id": "vulnerability--<UUID>",
     "created": "2024-01-01T00:00:00.000Z",
     "modified": "2024-01-01T00:00:00.000Z",
     "spec_version": "2.1",
     "name": "Vulnerability Name",
     "description": "Vulnerability description",
     "external_references": [
       {
         "source_name": "cve",
         "external_id": "CVE-2024-12345"
       }
     ]
   }

8. Relationships:
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

9. All timestamps must be ISO 8601 format: YYYY-MM-DDTHH:mm:ss.sssZ
10. All IDs must follow the pattern: <type>--<UUID v4>
"""

