"""
STIX 2.1 ID修复工具
将随机生成的无效ID替换为符合STIX 2.1规范的UUID格式ID
"""

import json
import uuid
import re
from pathlib import Path
from typing import Dict, Any, Set


class STIXIDFixer:
    """修复STIX 2.1对象ID的工具类"""

    def __init__(self):
        self.id_mapping: Dict[str, str] = {}  # 旧ID -> 新ID的映射
        self.processed_objects: Set[str] = set()  # 已处理的对象ID

    def generate_valid_uuid(self) -> str:
        """生成符合STIX 2.1规范的UUID"""
        return str(uuid.uuid4())

    def extract_object_type(self, stix_id: str) -> str:
        """从STIX ID中提取对象类型

        Args:
            stix_id: STIX对象ID，格式为 {type}--{uuid}

        Returns:
            对象类型字符串
        """
        if '--' in stix_id:
            return stix_id.split('--')[0]
        return ''

    def create_new_id(self, old_id: str) -> str:
        """创建新的符合规范的STIX ID

        Args:
            old_id: 旧的STIX ID

        Returns:
            新的符合规范的STIX ID
        """
        object_type = self.extract_object_type(old_id)
        new_uuid = self.generate_valid_uuid()
        return f"{object_type}--{new_uuid}"

    def is_valid_uuid(self, uuid_str: str) -> bool:
        """检查UUID字符串是否有效

        Args:
            uuid_str: UUID字符串

        Returns:
            是否为有效的UUID格式
        """
        try:
            # UUID只能包含十六进制字符(0-9, a-f)和连字符
            uuid_pattern = re.compile(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                re.IGNORECASE
            )
            return bool(uuid_pattern.match(uuid_str))
        except Exception:
            return False

    def is_valid_stix_id(self, stix_id: str) -> bool:
        """检查STIX ID是否符合规范

        Args:
            stix_id: STIX对象ID

        Returns:
            是否符合STIX 2.1规范
        """
        if '--' not in stix_id:
            return False

        parts = stix_id.split('--')
        if len(parts) != 2:
            return False

        object_type, uuid_part = parts

        # 特殊处理bundle ID
        if object_type == 'bundle' and 'merged' in uuid_part:
            return True

        return self.is_valid_uuid(uuid_part)

    def collect_all_ids(self, data: Dict[str, Any]) -> None:
        """收集所有需要替换的ID并生成映射

        Args:
            data: STIX bundle数据
        """
        # 处理bundle ID
        if 'id' in data and not self.is_valid_stix_id(data['id']):
            old_id = data['id']
            if 'bundle' in old_id:
                # 保持bundle的特殊格式
                self.id_mapping[old_id] = f"bundle--{self.generate_valid_uuid()}"

        # 处理所有对象
        if 'objects' in data:
            for obj in data['objects']:
                if 'id' in obj and not self.is_valid_stix_id(obj['id']):
                    old_id = obj['id']
                    new_id = self.create_new_id(old_id)
                    self.id_mapping[old_id] = new_id

    def replace_id_in_value(self, value: Any) -> Any:
        """递归替换值中的所有旧ID

        Args:
            value: 要处理的值（可能是字符串、列表、字典等）

        Returns:
            替换后的值
        """
        if isinstance(value, str):
            # 检查是否是需要替换的ID
            if value in self.id_mapping:
                return self.id_mapping[value]
            return value
        elif isinstance(value, list):
            return [self.replace_id_in_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.replace_id_in_value(v) for k, v in value.items()}
        else:
            return value

    def fix_bundle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复整个STIX bundle的ID

        Args:
            data: STIX bundle数据

        Returns:
            修复后的STIX bundle数据
        """
        # 第一步：收集所有需要替换的ID
        self.collect_all_ids(data)

        # 第二步：替换所有ID引用
        fixed_data = self.replace_id_in_value(data)

        return fixed_data

    def fix_file(self, input_path: str, output_path: str = None) -> None:
        """修复JSON文件中的STIX ID

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（如果为None，则覆盖原文件）
        """
        # 读取文件
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 修复ID
        fixed_data = self.fix_bundle(data)

        # 确定输出路径
        if output_path is None:
            output_path = input_path

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] Successfully fixed {len(self.id_mapping)} invalid IDs")
        print(f"[OK] Output file: {output_path}")

    def print_mapping(self) -> None:
        """打印ID映射关系（用于调试）"""
        print("\n=== ID Mapping ===")
        for old_id, new_id in sorted(self.id_mapping.items()):
            print(f"{old_id}")
            print(f"  -> {new_id}")


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_stix_ids.py <input_file> [output_file]")
        print("Example: python fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    fixer = STIXIDFixer()

    try:
        fixer.fix_file(input_file, output_file)

        # Optional: print mapping
        if '--verbose' in sys.argv or '-v' in sys.argv:
            fixer.print_mapping()

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
