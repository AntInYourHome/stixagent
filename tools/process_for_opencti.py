"""
一键处理脚本 - 准备 STIX 文件以导入 OpenCTI
自动完成 ID 修复和兼容性修复
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.fix_stix_ids import STIXIDFixer
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer
from tools.validate_stix_ids import STIXIDValidator


def process_file_for_opencti(input_file: str, output_file: str = None) -> str:
    """
    一键处理 STIX 文件以准备导入 OpenCTI

    Args:
        input_file: 输入的 STIX JSON 文件路径
        output_file: 输出文件路径（可选，默认为 <input>_opencti.json）

    Returns:
        输出文件路径
    """
    input_path = Path(input_file)

    # 确定输出文件路径
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_opencti.json"
    else:
        output_file = Path(output_file)

    # 临时文件（用于中间步骤）
    temp_file = input_path.parent / f"{input_path.stem}_temp_fixed.json"

    print("\n" + "=" * 70)
    print("Processing STIX file for OpenCTI import")
    print("=" * 70)
    print(f"Input:  {input_path}")
    print(f"Output: {output_file}")
    print("=" * 70)

    try:
        # 步骤 1: 修复 STIX ID
        print("\n[Step 1/3] Fixing STIX IDs...")
        print("-" * 70)
        id_fixer = STIXIDFixer()
        id_fixer.fix_file(str(input_path), str(temp_file))

        if id_fixer.id_mapping:
            print(f"[OK] Fixed {len(id_fixer.id_mapping)} invalid IDs")
        else:
            print("[OK] All IDs are already valid")

        # 步骤 2: 修复 OpenCTI 兼容性
        print("\n[Step 2/3] Fixing OpenCTI compatibility...")
        print("-" * 70)
        compat_fixer = OpenCTICompatibilityFixer()
        compat_fixer.fix_file(str(temp_file), str(output_file))

        if compat_fixer.fixes:
            print(f"[OK] Fixed {len(compat_fixer.fixes)} relationship(s)")
            for fix in compat_fixer.fixes[:3]:  # 显示前3个修复
                print(f"  - {fix['source']} --[{fix['old_rel']}]--> {fix['target']}")
                print(f"    -> {fix['source']} --[{fix['new_rel']}]--> {fix['target']}")
            if len(compat_fixer.fixes) > 3:
                print(f"  ... and {len(compat_fixer.fixes) - 3} more")
        else:
            print("[OK] All relationships are already compatible")

        if compat_fixer.removed_relationships:
            print(f"[WARNING] Removed {len(compat_fixer.removed_relationships)} invalid relationship(s)")

        # 步骤 3: 最终验证
        print("\n[Step 3/3] Final validation...")
        print("-" * 70)
        validator = STIXIDValidator()
        is_valid = validator.validate_file(str(output_file))

        if is_valid:
            print(f"[OK] Validation passed: {validator.total_objects} objects, {validator.valid_ids} valid IDs")
        else:
            print(f"[WARNING] Validation issues: {validator.invalid_ids} invalid IDs found")

        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()

        # 输出结果
        print("\n" + "=" * 70)
        print("[SUCCESS] Processing complete!")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  - IDs fixed: {len(id_fixer.id_mapping)}")
        print(f"  - Relationships fixed: {len(compat_fixer.fixes)}")
        print(f"  - Total objects: {validator.total_objects}")
        print(f"\nOutput file: {output_file}")
        print("\nReady to import into OpenCTI!")
        print("=" * 70)

        return str(output_file)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()

        raise


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python process_for_opencti.py <input_file> [output_file]")
        print("\nExample:")
        print("  python process_for_opencti.py outputs/o1.json")
        print("  python process_for_opencti.py outputs/o1.json outputs/final.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = process_file_for_opencti(input_file, output_file)
        print(f"\n[SUCCESS]!")
        sys.exit(0)

    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
