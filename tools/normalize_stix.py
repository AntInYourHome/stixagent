"""
STIX 2.1 规范化工具
确保生成的 STIX 对象完全符合 STIX 2.1 规范和 OpenCTI 要求
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class STIX21Normalizer:
    """STIX 2.1 对象规范化器"""

    # STIX 2.1 必需字段映射
    REQUIRED_FIELDS = {
        # SDO (STIX Domain Objects)
        'attack-pattern': ['type', 'spec_version', 'id', 'created', 'modified', 'name'],
        'campaign': ['type', 'spec_version', 'id', 'created', 'modified', 'name'],
        'course-of-action': ['type', 'spec_version', 'id', 'created', 'modified', 'name'],
        'identity': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'identity_class'],
        'indicator': ['type', 'spec_version', 'id', 'created', 'modified', 'pattern', 'pattern_type', 'valid_from'],
        'infrastructure': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'infrastructure_types'],
        'intrusion-set': ['type', 'spec_version', 'id', 'created', 'modified', 'name'],
        'location': ['type', 'spec_version', 'id', 'created', 'modified'],
        'malware': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'is_family'],
        'malware-analysis': ['type', 'spec_version', 'id', 'created', 'modified', 'product'],
        'note': ['type', 'spec_version', 'id', 'created', 'modified', 'content'],
        'observed-data': ['type', 'spec_version', 'id', 'created', 'modified', 'first_observed', 'last_observed', 'number_observed'],
        'opinion': ['type', 'spec_version', 'id', 'created', 'modified', 'opinion'],
        'report': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'published', 'object_refs'],
        'threat-actor': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'threat_actor_types'],
        'tool': ['type', 'spec_version', 'id', 'created', 'modified', 'name', 'tool_types'],
        'vulnerability': ['type', 'spec_version', 'id', 'created', 'modified', 'name'],

        # SRO (STIX Relationship Objects)
        'relationship': ['type', 'spec_version', 'id', 'created', 'modified', 'relationship_type', 'source_ref', 'target_ref'],
        'sighting': ['type', 'spec_version', 'id', 'created', 'modified', 'sighting_of_ref'],
    }

    # 字段默认值
    FIELD_DEFAULTS = {
        'spec_version': '2.1',
        'is_family': False,  # malware 默认值
        'identity_class': 'unknown',  # identity 默认值
        'number_observed': 1,  # observed-data 默认值
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes: List[str] = []

    def generate_valid_id(self, obj_type: str) -> str:
        """生成符合规范的 STIX ID"""
        return f"{obj_type}--{str(uuid.uuid4())}"

    def get_timestamp(self) -> str:
        """获取 STIX 格式的时间戳"""
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def normalize_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """规范化单个 STIX 对象"""
        if not isinstance(obj, dict):
            self.errors.append("Object is not a dictionary")
            return obj

        obj_type = obj.get('type')
        if not obj_type:
            self.errors.append("Object missing 'type' field")
            return obj

        # 获取必需字段列表
        required = self.REQUIRED_FIELDS.get(obj_type, [])

        # 1. 确保 spec_version 存在
        if 'spec_version' not in obj:
            obj['spec_version'] = '2.1'
            self.fixes.append(f"Added spec_version to {obj_type}")

        # 2. 确保 ID 存在且格式正确
        if 'id' not in obj:
            obj['id'] = self.generate_valid_id(obj_type)
            self.fixes.append(f"Generated ID for {obj_type}")
        else:
            # 验证 ID 格式
            obj_id = obj['id']
            if '--' not in obj_id or not obj_id.startswith(f"{obj_type}--"):
                old_id = obj_id
                obj['id'] = self.generate_valid_id(obj_type)
                self.fixes.append(f"Fixed invalid ID: {old_id} -> {obj['id']}")

        # 3. 确保时间戳存在
        timestamp = self.get_timestamp()
        if 'created' not in obj and 'created' in required:
            obj['created'] = timestamp
            self.fixes.append(f"Added created timestamp to {obj_type}")

        if 'modified' not in obj and 'modified' in required:
            obj['modified'] = timestamp
            self.fixes.append(f"Added modified timestamp to {obj_type}")

        # 4. 处理类型特定的必需字段
        if obj_type == 'malware':
            if 'is_family' not in obj:
                obj['is_family'] = True
                self.fixes.append(f"Added is_family to malware")

            # 确保 malware_types 存在
            if 'malware_types' not in obj:
                obj['malware_types'] = ['unknown']
                self.fixes.append(f"Added default malware_types")

        elif obj_type == 'threat-actor':
            if 'threat_actor_types' not in obj:
                obj['threat_actor_types'] = ['unknown']
                self.fixes.append(f"Added default threat_actor_types")

        elif obj_type == 'tool':
            if 'tool_types' not in obj:
                obj['tool_types'] = ['unknown']
                self.fixes.append(f"Added default tool_types")

        elif obj_type == 'infrastructure':
            if 'infrastructure_types' not in obj:
                obj['infrastructure_types'] = ['unknown']
                self.fixes.append(f"Added default infrastructure_types")

        elif obj_type == 'identity':
            if 'identity_class' not in obj:
                obj['identity_class'] = 'organization'
                self.fixes.append(f"Added default identity_class")

        elif obj_type == 'indicator':
            if 'pattern_type' not in obj:
                obj['pattern_type'] = 'stix'
                self.fixes.append(f"Added default pattern_type")

            if 'valid_from' not in obj:
                obj['valid_from'] = timestamp
                self.fixes.append(f"Added valid_from to indicator")

        elif obj_type == 'observed-data':
            if 'first_observed' not in obj:
                obj['first_observed'] = timestamp
                self.fixes.append(f"Added first_observed")

            if 'last_observed' not in obj:
                obj['last_observed'] = timestamp
                self.fixes.append(f"Added last_observed")

            if 'number_observed' not in obj:
                obj['number_observed'] = 1
                self.fixes.append(f"Added number_observed")

        elif obj_type == 'report':
            if 'published' not in obj:
                obj['published'] = timestamp
                self.fixes.append(f"Added published to report")

        # 5. 检查必需字段
        for field in required:
            if field not in obj:
                self.errors.append(f"Missing required field '{field}' in {obj_type} (ID: {obj.get('id')})")

        return obj

    def normalize_bundle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化整个 STIX bundle"""
        if data.get('type') != 'bundle':
            self.errors.append("Data is not a STIX bundle")
            return data

        # 确保 bundle 有 spec_version
        if 'spec_version' not in data:
            data['spec_version'] = '2.1'
            self.fixes.append("Added spec_version to bundle")

        # 确保 bundle 有 ID
        if 'id' not in data:
            data['id'] = self.generate_valid_id('bundle')
            self.fixes.append("Generated ID for bundle")

        # 规范化所有对象
        if 'objects' in data:
            normalized_objects = []
            for obj in data['objects']:
                normalized_obj = self.normalize_object(obj)
                normalized_objects.append(normalized_obj)

            data['objects'] = normalized_objects

        return data

    def normalize_file(self, input_path: str, output_path: str = None) -> None:
        """规范化 JSON 文件"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        normalized_data = self.normalize_bundle(data)

        if output_path is None:
            output_path = input_path.replace('.json', '_normalized.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] Normalization completed")
        print(f"[OK] Output file: {output_path}")

    def print_report(self) -> None:
        """打印规范化报告"""
        print("\n" + "=" * 70)
        print("STIX 2.1 Normalization Report")
        print("=" * 70)

        if self.fixes:
            print(f"\n[FIXED] {len(self.fixes)} issue(s) fixed:")
            for fix in self.fixes[:10]:
                print(f"  - {fix}")
            if len(self.fixes) > 10:
                print(f"  ... and {len(self.fixes) - 10} more")

        if self.warnings:
            print(f"\n[WARNING] {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n[ERROR] {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  - {error}")

        if not self.fixes and not self.warnings and not self.errors:
            print("\n[OK] All objects already compliant!")

        print("=" * 70)


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python normalize_stix.py <input_file> [output_file]")
        print("Example: python normalize_stix.py outputs/o1.json outputs/o1_normalized.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    normalizer = STIX21Normalizer()

    try:
        normalizer.normalize_file(input_file, output_file)
        normalizer.print_report()

    except FileNotFoundError:
        print(f"Error: File not found {input_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
