"""
OpenCTI 兼容性检查和修复工具
检查并修复 STIX 文件中 OpenCTI 不支持的关系类型
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set


class OpenCTICompatibilityFixer:
    """OpenCTI 兼容性修复器"""

    # OpenCTI 允许的关系类型映射
    # 来源: https://docs.opencti.io/latest/deployment/connectors/
    ALLOWED_RELATIONSHIPS = {
        'attack-pattern': {
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['malware', 'tool'],
            'mitigates': ['vulnerability'],
            'subtechnique-of': ['attack-pattern'],
        },
        'campaign': {
            'attributed-to': ['threat-actor', 'intrusion-set'],
            'compromises': ['infrastructure'],
            'originates-from': ['location'],
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['attack-pattern', 'infrastructure', 'malware', 'tool'],
        },
        'course-of-action': {
            'mitigates': ['attack-pattern', 'indicator', 'malware', 'tool', 'vulnerability'],
        },
        'identity': {
            'located-at': ['location'],
        },
        'indicator': {
            'based-on': ['observed-data'],
            'indicates': ['attack-pattern', 'campaign', 'infrastructure', 'intrusion-set', 'malware', 'threat-actor', 'tool'],
        },
        'infrastructure': {
            'communicates-with': ['infrastructure', 'ipv4-addr', 'ipv6-addr', 'domain-name', 'url'],
            'consists-of': ['infrastructure', 'observed-data'],
            'controls': ['infrastructure', 'malware'],
            'has': ['vulnerability'],
            'hosts': ['malware', 'tool'],
            'located-at': ['location'],
            'uses': ['infrastructure'],
        },
        'intrusion-set': {
            'attributed-to': ['threat-actor'],
            'compromises': ['infrastructure'],
            'hosts': ['infrastructure'],
            'originates-from': ['location'],
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['attack-pattern', 'infrastructure', 'malware', 'tool'],
        },
        'malware': {
            'authored-by': ['threat-actor', 'intrusion-set'],
            'beacons-to': ['infrastructure'],
            'communicates-with': ['ipv4-addr', 'ipv6-addr', 'domain-name', 'url'],
            'controls': ['malware'],
            'downloads': ['malware', 'tool', 'file'],
            'drops': ['malware', 'tool', 'file'],
            'exploits': ['vulnerability'],
            'originates-from': ['location'],
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['attack-pattern', 'infrastructure', 'tool'],
            'variant-of': ['malware'],
        },
        'threat-actor': {
            'attributed-to': ['identity'],
            'compromises': ['infrastructure'],
            'hosts': ['infrastructure'],
            'impersonates': ['identity'],
            'located-at': ['location'],
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['attack-pattern', 'infrastructure', 'malware', 'tool'],
        },
        'tool': {
            'delivers': ['malware'],
            'drops': ['malware'],
            'has': ['vulnerability'],
            'targets': ['identity', 'location', 'vulnerability'],
            'uses': ['infrastructure'],
        },
    }

    # 关系类型建议映射（当不允许的关系类型出现时的替代方案）
    RELATIONSHIP_SUGGESTIONS = {
        ('attack-pattern', 'exploits', 'vulnerability'): ('attack-pattern', 'targets', 'vulnerability'),
        ('infrastructure', 'consists-of', 'malware'): ('infrastructure', 'hosts', 'malware'),
        ('malware', 'delivers', 'infrastructure'): ('malware', 'uses', 'infrastructure'),
        ('malware', 'delivers', 'malware'): ('malware', 'downloads', 'malware'),  # delivers -> downloads
        ('malware', 'controls', 'infrastructure'): ('malware', 'uses', 'infrastructure'),  # controls -> uses
        ('malware', 'uses', 'malware'): ('malware', 'downloads', 'malware'),  # uses -> downloads (组件关系)
        ('malware', 'based-on', 'tool'): ('malware', 'uses', 'tool'),
        ('malware', 'communicates-with', 'infrastructure'): ('malware', 'uses', 'infrastructure'),
        ('malware', 'consists-of', 'infrastructure'): ('malware', 'uses', 'infrastructure'),
        ('malware', 'attributed-to', 'threat-actor'): ('malware', 'authored-by', 'threat-actor'),  # attributed-to -> authored-by
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes: List[Dict[str, str]] = []
        self.removed_relationships: List[Dict[str, Any]] = []

    def is_relationship_allowed(self, source_type: str, rel_type: str, target_type: str) -> bool:
        """检查关系类型是否被 OpenCTI 允许"""
        if source_type not in self.ALLOWED_RELATIONSHIPS:
            self.warnings.append(f"Unknown source type: {source_type}")
            return True  # 未知类型，允许通过

        allowed_rels = self.ALLOWED_RELATIONSHIPS.get(source_type, {})
        if rel_type not in allowed_rels:
            return False

        allowed_targets = allowed_rels[rel_type]
        return target_type in allowed_targets

    def get_relationship_suggestion(self, source_type: str, rel_type: str, target_type: str) -> str:
        """获取关系类型的建议替代方案"""
        key = (source_type, rel_type, target_type)
        if key in self.RELATIONSHIP_SUGGESTIONS:
            _, suggested_rel, _ = self.RELATIONSHIP_SUGGESTIONS[key]
            return suggested_rel
        return None

    def fix_relationship(self, rel: Dict[str, Any], objects_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """修复单个关系对象"""
        if rel.get('type') != 'relationship':
            return rel

        source_id = rel.get('source_ref')
        target_id = rel.get('target_ref')
        rel_type = rel.get('relationship_type')

        if not all([source_id, target_id, rel_type]):
            self.errors.append(f"Relationship missing required fields: {rel.get('id')}")
            return rel

        source_obj = objects_map.get(source_id)
        target_obj = objects_map.get(target_id)

        if not source_obj or not target_obj:
            self.errors.append(f"Cannot find source or target object for relationship: {rel.get('id')}")
            return rel

        source_type = source_obj.get('type')
        target_type = target_obj.get('type')

        if not self.is_relationship_allowed(source_type, rel_type, target_type):
            # 尝试获取建议的关系类型
            suggested_rel = self.get_relationship_suggestion(source_type, rel_type, target_type)

            if suggested_rel:
                self.fixes.append({
                    'id': rel.get('id'),
                    'source': source_type,
                    'old_rel': rel_type,
                    'new_rel': suggested_rel,
                    'target': target_type,
                })
                rel['relationship_type'] = suggested_rel
            else:
                # 没有建议的替代方案，标记为删除
                self.errors.append(
                    f"Invalid relationship: {source_type} --[{rel_type}]--> {target_type} "
                    f"(ID: {rel.get('id')}). No suggestion available, will be removed."
                )
                return None

        return rel

    def fix_bundle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复整个 STIX bundle"""
        if 'objects' not in data:
            self.errors.append("No 'objects' field in bundle")
            return data

        # 创建对象映射
        objects_map = {}
        for obj in data['objects']:
            if 'id' in obj:
                objects_map[obj['id']] = obj

        # 修复所有关系对象
        fixed_objects = []
        for obj in data['objects']:
            if obj.get('type') == 'relationship':
                fixed_obj = self.fix_relationship(obj, objects_map)
                if fixed_obj is not None:
                    fixed_objects.append(fixed_obj)
                else:
                    self.removed_relationships.append(obj)
            else:
                fixed_objects.append(obj)

        data['objects'] = fixed_objects
        return data

    def fix_file(self, input_path: str, output_path: str = None) -> None:
        """修复 JSON 文件中的 OpenCTI 兼容性问题"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        fixed_data = self.fix_bundle(data)

        if output_path is None:
            output_path = input_path

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] OpenCTI compatibility check completed")
        print(f"[OK] Output file: {output_path}")

    def print_report(self) -> None:
        """打印修复报告"""
        print("\n" + "=" * 70)
        print("OpenCTI Compatibility Report")
        print("=" * 70)

        if self.fixes:
            print(f"\n[FIXED] {len(self.fixes)} relationship(s) fixed:")
            for fix in self.fixes:
                print(f"  - {fix['id']}")
                print(f"    {fix['source']} --[{fix['old_rel']}]--> {fix['target']}")
                print(f"    Changed to: {fix['source']} --[{fix['new_rel']}]--> {fix['target']}")

        if self.removed_relationships:
            print(f"\n[REMOVED] {len(self.removed_relationships)} invalid relationship(s):")
            for rel in self.removed_relationships:
                print(f"  - {rel.get('id')}")
                print(f"    Type: {rel.get('relationship_type')}")

        if self.errors:
            print(f"\n[ERROR] {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n[WARNING] {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.fixes and not self.removed_relationships and not self.errors:
            print("\n[OK] No compatibility issues found!")

        print("=" * 70)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python fix_opencti_compatibility.py <input_file> [output_file]")
        print("Example: python fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_opencti.json')

    fixer = OpenCTICompatibilityFixer()

    try:
        fixer.fix_file(input_file, output_file)
        fixer.print_report()

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
