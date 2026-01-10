"""
测试和运行STIX ID修复工具
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.fix_stix_ids import STIXIDFixer


def main():
    """运行ID修复工具"""
    input_file = "outputs/o1.json"
    output_file = "outputs/o1_fixed.json"

    # 转换为绝对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, input_file)
    output_path = os.path.join(base_dir, output_file)

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print("-" * 60)

    fixer = STIXIDFixer()

    try:
        fixer.fix_file(input_path, output_path)
        print("\n" + "=" * 60)
        print("ID Fix Statistics:")
        print(f"  - Total fixed: {len(fixer.id_mapping)} IDs")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
