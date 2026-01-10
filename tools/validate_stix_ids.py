"""
STIX ID验证工具
验证STIX 2.1 JSON文件中的所有ID是否符合规范
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class STIXIDValidator:
    """STIX ID验证器"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.total_objects = 0
        self.valid_ids = 0
        self.invalid_ids = 0

    def is_valid_uuid(self, uuid_str: str) -> bool:
        """检查UUID字符串是否有效"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_str))

    def is_valid_stix_id(self, stix_id: str, object_type: str = None) -> bool:
        """检查STIX ID是否符合规范"""
        if '--' not in stix_id:
            self.errors.append(f"Invalid ID format (missing '--'): {stix_id}")
            return False

        parts = stix_id.split('--')
        if len(parts) != 2:
            self.errors.append(f"Invalid ID format (wrong number of parts): {stix_id}")
            return False

        id_type, uuid_part = parts

        # 验证对象类型是否匹配
        if object_type and id_type != object_type:
            self.errors.append(
                f"ID type mismatch: expected '{object_type}', got '{id_type}' in ID: {stix_id}"
            )
            return False

        # 特殊处理bundle ID
        if id_type == 'bundle':
            return True

        # 验证UUID部分
        if not self.is_valid_uuid(uuid_part):
            self.errors.append(f"Invalid UUID in ID: {stix_id}")
            return False

        return True

    def validate_object(self, obj: Dict[str, Any]) -> None:
        """验证单个STIX对象"""
        self.total_objects += 1

        if 'id' not in obj:
            self.errors.append(f"Object missing 'id' field: {obj.get('type', 'unknown')}")
            self.invalid_ids += 1
            return

        obj_id = obj['id']
        obj_type = obj.get('type')

        if self.is_valid_stix_id(obj_id, obj_type):
            self.valid_ids += 1
        else:
            self.invalid_ids += 1

    def validate_references(self, obj: Dict[str, Any]) -> None:
        """验证对象中的ID引用"""
        # 检查常见的引用字段
        ref_fields = [
            'source_ref', 'target_ref', 'created_by_ref',
            'sighting_of_ref', 'where_sighted_refs', 'observed_data_refs',
            'object_marking_refs', 'object_refs'
        ]

        for field in ref_fields:
            if field in obj:
                value = obj[field]
                if isinstance(value, str):
                    # 单个引用
                    if not self.is_valid_stix_id(value):
                        self.warnings.append(
                            f"Invalid reference in '{field}': {value}"
                        )
                elif isinstance(value, list):
                    # 引用列表
                    for ref in value:
                        if isinstance(ref, str) and not self.is_valid_stix_id(ref):
                            self.warnings.append(
                                f"Invalid reference in '{field}': {ref}"
                            )

    def validate_bundle(self, data: Dict[str, Any]) -> bool:
        """验证整个STIX bundle"""
        # 验证bundle本身的ID
        if 'id' in data:
            self.is_valid_stix_id(data['id'], 'bundle')

        # 验证所有对象
        if 'objects' in data:
            for obj in data['objects']:
                self.validate_object(obj)
                self.validate_references(obj)

        return self.invalid_ids == 0 and len(self.errors) == 0

    def validate_file(self, file_path: str) -> bool:
        """验证JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.validate_bundle(data)

    def print_report(self) -> None:
        """打印验证报告"""
        print("\n" + "=" * 70)
        print("STIX ID Validation Report")
        print("=" * 70)

        print(f"\nTotal objects: {self.total_objects}")
        print(f"Valid IDs: {self.valid_ids}")
        print(f"Invalid IDs: {self.invalid_ids}")

        if self.errors:
            print(f"\n[ERROR] Found {len(self.errors)} errors:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n[OK] No errors found!")

        if self.warnings:
            print(f"\n[WARNING] Found {len(self.warnings)} warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        print("\n" + "=" * 70)
        if self.invalid_ids == 0 and len(self.errors) == 0:
            print("[PASS] All IDs are valid!")
        else:
            print("[FAIL] Some IDs are invalid!")
        print("=" * 70)


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_stix_ids.py <json_file>")
        print("Example: python validate_stix_ids.py outputs/o1_fixed.json")
        sys.exit(1)

    file_path = sys.argv[1]

    validator = STIXIDValidator()

    try:
        is_valid = validator.validate_file(file_path)
        validator.print_report()

        sys.exit(0 if is_valid else 1)

    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
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
