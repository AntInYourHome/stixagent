"""
STIX ID 工具使用示例
演示如何在实际工作流中使用 fix_stix_ids 和 validate_stix_ids
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.fix_stix_ids import STIXIDFixer
from tools.validate_stix_ids import STIXIDValidator


def example_1_basic_fix():
    """示例 1: 基本的 ID 修复"""
    print("\n" + "="*70)
    print("示例 1: 基本的 ID 修复")
    print("="*70)

    input_file = project_root / "outputs" / "o1.json"
    output_file = project_root / "outputs" / "o1_fixed_example.json"

    fixer = STIXIDFixer()
    fixer.fix_file(str(input_file), str(output_file))

    print(f"\n总结:")
    print(f"  - 修复的 ID 数量: {len(fixer.id_mapping)}")
    print(f"  - 输出文件: {output_file}")


def example_2_validate_before_after():
    """示例 2: 修复前后对比验证"""
    print("\n" + "="*70)
    print("示例 2: 修复前后对比验证")
    print("="*70)

    original_file = project_root / "outputs" / "o1.json"
    fixed_file = project_root / "outputs" / "o1_fixed.json"

    # 验证原始文件
    print("\n[1] 验证原始文件...")
    validator_original = STIXIDValidator()
    validator_original.validate_file(str(original_file))

    # 验证修复后的文件
    print("\n[2] 验证修复后的文件...")
    validator_fixed = STIXIDValidator()
    validator_fixed.validate_file(str(fixed_file))

    # 对比结果
    print("\n" + "-"*70)
    print("对比结果:")
    print("-"*70)
    print(f"{'文件':<30} {'有效ID':<15} {'无效ID':<15} {'状态':<10}")
    print("-"*70)
    status_orig = 'FAIL' if validator_original.invalid_ids > 0 else 'PASS'
    status_fixed = 'FAIL' if validator_fixed.invalid_ids > 0 else 'PASS'
    print(f"{'原始文件 (o1.json)':<30} "
          f"{validator_original.valid_ids:<15} "
          f"{validator_original.invalid_ids:<15} "
          f"{status_orig:<10}")
    print(f"{'修复后 (o1_fixed.json)':<30} "
          f"{validator_fixed.valid_ids:<15} "
          f"{validator_fixed.invalid_ids:<15} "
          f"{status_fixed:<10}")
    print("-"*70)


def example_3_show_id_mapping():
    """示例 3: 显示 ID 映射关系"""
    print("\n" + "="*70)
    print("示例 3: 显示部分 ID 映射关系")
    print("="*70)

    input_file = project_root / "outputs" / "o1.json"
    output_file = project_root / "outputs" / "o1_temp.json"

    fixer = STIXIDFixer()
    fixer.fix_file(str(input_file), str(output_file))

    # 显示前 5 个映射
    print("\n前 5 个 ID 映射:")
    print("-"*70)
    for i, (old_id, new_id) in enumerate(list(fixer.id_mapping.items())[:5], 1):
        print(f"\n{i}. 旧 ID:")
        print(f"   {old_id}")
        print(f"   新 ID:")
        print(f"   {new_id}")

    # 清理临时文件
    if output_file.exists():
        output_file.unlink()


def example_4_batch_processing():
    """示例 4: 批量处理多个文件"""
    print("\n" + "="*70)
    print("示例 4: 批量处理示例（演示用）")
    print("="*70)

    # 这里只是演示代码结构，实际不运行批量处理
    print("\n批量处理代码示例:")
    print("-"*70)

    code_example = '''
import glob
from tools.fix_stix_ids import STIXIDFixer

# 处理所有 JSON 文件
for input_file in glob.glob('outputs/*.json'):
    if '_fixed' not in input_file:
        output_file = input_file.replace('.json', '_fixed.json')

        print(f"处理: {input_file}")
        fixer = STIXIDFixer()
        fixer.fix_file(input_file, output_file)
        print(f"完成: 修复了 {len(fixer.id_mapping)} 个 ID")
'''

    print(code_example)


def example_5_integration_workflow():
    """示例 5: 完整的集成工作流"""
    print("\n" + "="*70)
    print("示例 5: 完整的 STIX 数据处理工作流")
    print("="*70)

    input_file = project_root / "outputs" / "o1.json"
    output_file = project_root / "outputs" / "o1_workflow_output.json"

    print("\n步骤 1: 验证输入文件")
    print("-"*70)
    validator_input = STIXIDValidator()
    is_valid_input = validator_input.validate_file(str(input_file))

    if not is_valid_input:
        print(f"发现 {validator_input.invalid_ids} 个无效 ID，需要修复")

        print("\n步骤 2: 修复 ID")
        print("-"*70)
        fixer = STIXIDFixer()
        fixer.fix_file(str(input_file), str(output_file))

        print("\n步骤 3: 验证输出文件")
        print("-"*70)
        validator_output = STIXIDValidator()
        is_valid_output = validator_output.validate_file(str(output_file))

        if is_valid_output:
            print("\n[OK] 工作流完成！文件已准备好导入 OpenCTI")
            print(f"[OK] 输出文件: {output_file}")
        else:
            print("\n[ERROR] 验证失败，请检查错误")

        # 清理临时文件
        if output_file.exists():
            output_file.unlink()
    else:
        print("[OK] 输入文件已经有效，无需修复")


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("STIX ID 工具使用示例集")
    print("="*70)

    try:
        # 运行所有示例
        example_1_basic_fix()
        example_2_validate_before_after()
        example_3_show_id_mapping()
        example_4_batch_processing()
        example_5_integration_workflow()

        print("\n" + "="*70)
        print("所有示例运行完成！")
        print("="*70)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
