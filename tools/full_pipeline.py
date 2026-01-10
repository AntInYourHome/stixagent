"""
完整的 STIX 2.1 处理流程 - 从生成到 OpenCTI 就绪
集成所有规范化、修复和验证工具
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.normalize_stix import STIX21Normalizer
from tools.fix_stix_ids import STIXIDFixer
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer
from tools.validate_stix_ids import STIXIDValidator


def full_stix_pipeline(input_file: str, output_file: str = None) -> str:
    """
    完整的 STIX 处理流程

    步骤:
    1. 规范化 - 确保所有必需字段存在
    2. 修复 ID - 生成符合规范的 UUID
    3. 修复 OpenCTI 兼容性 - 修复不支持的关系类型
    4. 最终验证 - 确保所有内容符合规范

    Args:
        input_file: 输入的 STIX JSON 文件路径
        output_file: 输出文件路径（可选）

    Returns:
        最终输出文件路径
    """
    input_path = Path(input_file)

    # 确定输出文件路径
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_ready.json"
    else:
        output_file = Path(output_file)

    # 临时文件
    temp_normalized = input_path.parent / f"{input_path.stem}_temp1_normalized.json"
    temp_fixed_ids = input_path.parent / f"{input_path.stem}_temp2_fixed_ids.json"

    print("\n" + "=" * 70)
    print("Complete STIX 2.1 Processing Pipeline")
    print("=" * 70)
    print(f"Input:  {input_path}")
    print(f"Output: {output_file}")
    print("=" * 70)

    try:
        # ===== 步骤 1: 规范化 STIX 对象 =====
        print("\n[Step 1/4] Normalizing STIX objects...")
        print("-" * 70)
        normalizer = STIX21Normalizer()
        normalizer.normalize_file(str(input_path), str(temp_normalized))

        if normalizer.fixes:
            print(f"[OK] Fixed {len(normalizer.fixes)} normalization issue(s)")
            # 显示前5个修复
            for fix in normalizer.fixes[:5]:
                print(f"  - {fix}")
            if len(normalizer.fixes) > 5:
                print(f"  ... and {len(normalizer.fixes) - 5} more")
        else:
            print("[OK] All objects already normalized")

        if normalizer.errors:
            print(f"[WARNING] Found {len(normalizer.errors)} error(s)")
            for error in normalizer.errors[:3]:
                print(f"  - {error}")

        # ===== 步骤 2: 修复 STIX ID =====
        print("\n[Step 2/4] Fixing STIX IDs...")
        print("-" * 70)
        id_fixer = STIXIDFixer()
        id_fixer.fix_file(str(temp_normalized), str(temp_fixed_ids))

        if id_fixer.id_mapping:
            print(f"[OK] Fixed {len(id_fixer.id_mapping)} invalid ID(s)")
        else:
            print("[OK] All IDs already valid")

        # ===== 步骤 3: 修复 OpenCTI 兼容性 =====
        print("\n[Step 3/4] Fixing OpenCTI compatibility...")
        print("-" * 70)
        compat_fixer = OpenCTICompatibilityFixer()
        compat_fixer.fix_file(str(temp_fixed_ids), str(output_file))

        if compat_fixer.fixes:
            print(f"[OK] Fixed {len(compat_fixer.fixes)} relationship(s)")
            # 显示前3个修复
            for fix in compat_fixer.fixes[:3]:
                print(f"  - {fix['source']} --[{fix['old_rel']}]--> {fix['target']}")
                print(f"    -> {fix['source']} --[{fix['new_rel']}]--> {fix['target']}")
            if len(compat_fixer.fixes) > 3:
                print(f"  ... and {len(compat_fixer.fixes) - 3} more")
        else:
            print("[OK] All relationships already compatible")

        if compat_fixer.removed_relationships:
            print(f"[WARNING] Removed {len(compat_fixer.removed_relationships)} invalid relationship(s)")

        # ===== 步骤 4: 最终验证 =====
        print("\n[Step 4/4] Final validation...")
        print("-" * 70)
        validator = STIXIDValidator()
        is_valid = validator.validate_file(str(output_file))

        if is_valid and validator.invalid_ids == 0:
            print(f"[OK] Validation passed")
            print(f"  - Total objects: {validator.total_objects}")
            print(f"  - Valid IDs: {validator.valid_ids}")
            print(f"  - Invalid IDs: {validator.invalid_ids}")
        else:
            print(f"[WARNING] Validation issues found")
            print(f"  - Total objects: {validator.total_objects}")
            print(f"  - Valid IDs: {validator.valid_ids}")
            print(f"  - Invalid IDs: {validator.invalid_ids}")

        # 清理临时文件
        for temp_file in [temp_normalized, temp_fixed_ids]:
            if temp_file.exists():
                temp_file.unlink()

        # ===== 输出结果 =====
        print("\n" + "=" * 70)
        print("[SUCCESS] Processing complete!")
        print("=" * 70)
        print(f"\nPipeline Summary:")
        print(f"  - Normalization fixes: {len(normalizer.fixes)}")
        print(f"  - IDs fixed: {len(id_fixer.id_mapping)}")
        print(f"  - Relationships fixed: {len(compat_fixer.fixes)}")
        print(f"  - Total objects: {validator.total_objects}")
        print(f"  - Validation status: {'PASS' if is_valid else 'FAIL'}")
        print(f"\nOutput file: {output_file}")
        print("\n" + "=" * 70)
        print("Ready to import into OpenCTI!")
        print("=" * 70)

        return str(output_file)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

        # 清理临时文件
        for temp_file in [temp_normalized, temp_fixed_ids]:
            if temp_file.exists():
                temp_file.unlink()

        raise


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python full_pipeline.py <input_file> [output_file]")
        print("\nDescription:")
        print("  Complete STIX 2.1 processing pipeline for OpenCTI import")
        print("\nSteps:")
        print("  1. Normalize STIX objects (add required fields)")
        print("  2. Fix STIX IDs (generate valid UUIDs)")
        print("  3. Fix OpenCTI compatibility (fix relationships)")
        print("  4. Final validation")
        print("\nExamples:")
        print("  python full_pipeline.py outputs/o1.json")
        print("  python full_pipeline.py outputs/o1.json outputs/ready.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = full_stix_pipeline(input_file, output_file)
        print(f"\n[SUCCESS] Pipeline completed!")
        print(f"[INFO] Output: {result}")
        sys.exit(0)

    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
