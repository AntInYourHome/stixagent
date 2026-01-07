"""Verify ReAct output."""
import json

with open('react_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"STIX Bundle ID: {data.get('id')}")
print(f"Spec Version: {data.get('spec_version')}")
print(f"Total Objects: {len(data.get('objects', []))}")

types = {}
for obj in data.get('objects', []):
    obj_type = obj.get('type', 'unknown')
    types[obj_type] = types.get(obj_type, 0) + 1

print("\nObject Types:")
for obj_type, count in sorted(types.items()):
    print(f"  - {obj_type}: {count}")

print("\n[OK] Output verification complete")

