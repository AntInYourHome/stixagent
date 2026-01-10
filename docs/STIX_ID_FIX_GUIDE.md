# STIX ID 修复工具使用指南

## 问题描述

在 STIX 2.1 规范中，所有对象的 ID 必须遵循以下格式：
```
{object-type}--{uuid}
```

例如：
- `threat-actor--b1d4f6a8-9c2e-4d7b-8a1f-2e6d8f9b3c2d`
- `malware--6f0653cc-c8c0-4809-81c7-676b45c7b77d`

其中 UUID 部分必须是符合 RFC 4122 标准的 UUID v4，只能包含十六进制字符（0-9, a-f）和连字符。

## 工具列表

本项目提供了三个工具来处理 STIX ID 问题：

### 1. fix_stix_ids.py - ID 修复工具

自动修复 JSON 文件中的所有无效 STIX ID。

**使用方法：**
```bash
python tools/fix_stix_ids.py <输入文件> [输出文件]
```

**示例：**
```bash
# 修复 o1.json 并保存为 o1_fixed.json
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json

# 使用详细模式（显示ID映射）
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json -v
```

### 2. validate_stix_ids.py - ID 验证工具

验证 STIX JSON 文件中的所有 ID 是否符合规范。

**使用方法：**
```bash
python tools/validate_stix_ids.py <JSON文件>
```

**示例：**
```bash
# 验证修复后的文件
python tools/validate_stix_ids.py outputs/o1_fixed.json

# 验证原始文件（会显示错误）
python tools/validate_stix_ids.py outputs/o1.json
```

### 3. run_fix_ids.py - 快捷运行脚本

一键修复默认位置的文件。

**使用方法：**
```bash
python tools/run_fix_ids.py
```

自动处理 `outputs/o1.json` 并生成 `outputs/o1_fixed.json`。

## 快速开始

### 步骤 1: 验证原始文件

首先检查原始文件中有多少无效 ID：

```bash
python tools/validate_stix_ids.py outputs/o1.json
```

输出示例：
```
======================================================================
STIX ID Validation Report
======================================================================

Total objects: 116
Valid IDs: 19
Invalid IDs: 97

[ERROR] Found 158 errors:
  1. Invalid UUID in ID: intrusion-set--c2e5g7b9-a1f3-5e8c-9b2g-3f7e9a4d5f3e
  ...
======================================================================
[FAIL] Some IDs are invalid!
======================================================================
```

### 步骤 2: 修复 ID

使用修复工具自动修复所有无效 ID：

```bash
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json
```

输出示例：
```
[OK] Successfully fixed 97 invalid IDs
[OK] Output file: E:\coding\agents\stixagent\outputs/o1_fixed.json
```

### 步骤 3: 验证修复结果

验证修复后的文件：

```bash
python tools/validate_stix_ids.py outputs/o1_fixed.json
```

输出示例：
```
======================================================================
STIX ID Validation Report
======================================================================

Total objects: 116
Valid IDs: 116
Invalid IDs: 0

[OK] No errors found!

======================================================================
[PASS] All IDs are valid!
======================================================================
```

## 技术细节

### ID 格式要求

1. **基本格式**: `{type}--{uuid}`
2. **类型前缀**: 必须与对象的 `type` 字段匹配
3. **UUID 格式**: 标准 UUID v4 格式 (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
4. **字符限制**: UUID 部分只能包含 0-9, a-f 和连字符

### 无效 ID 示例

以下是一些常见的无效 ID：

```json
// 错误：包含非十六进制字符 (g, h, i, etc.)
"id": "malware--g6i9k1f3-e5j7-9i2g-df6k-7j1i3e8h9j7i"

// 错误：类型不匹配
{
  "type": "malware",
  "id": "threat-actor--12345678-1234-1234-1234-123456789abc"
}

// 错误：格式不正确
"id": "malware-12345"
```

### 有效 ID 示例

```json
{
  "type": "threat-actor",
  "id": "threat-actor--b1d4f6a8-9c2e-4d7b-8a1f-2e6d8f9b3c2d"
}

{
  "type": "malware",
  "id": "malware--6f0653cc-c8c0-4809-81c7-676b45c7b77d"
}

{
  "type": "relationship",
  "id": "relationship--fef23971-4df3-4fc0-95a2-1a4b7ede1863",
  "source_ref": "threat-actor--b1d4f6a8-9c2e-4d7b-8a1f-2e6d8f9b3c2d",
  "target_ref": "malware--6f0653cc-c8c0-4809-81c7-676b45c7b77d"
}
```

## 工作原理

### fix_stix_ids.py

1. **收集阶段**: 扫描所有对象，识别无效的 ID
2. **生成阶段**: 为每个无效 ID 生成新的有效 UUID
3. **映射阶段**: 建立旧 ID 到新 ID 的映射表
4. **替换阶段**: 递归替换所有 ID 引用（包括 relationship 中的 source_ref 和 target_ref）
5. **输出阶段**: 保存修复后的 JSON 文件

### validate_stix_ids.py

1. **解析 JSON**: 读取 STIX bundle 文件
2. **验证对象 ID**: 检查每个对象的 ID 格式
3. **验证引用**: 检查所有 ID 引用字段
4. **生成报告**: 统计有效/无效 ID 数量，列出所有错误

## 常见问题

### Q: 修复后的 ID 能否导入 OpenCTI？

A: 可以。修复工具生成的 UUID 完全符合 STIX 2.1 规范，可以正常导入 OpenCTI。

### Q: ID 修复后，对象之间的关系会保持吗？

A: 会。修复工具会自动更新所有引用字段（如 `source_ref`, `target_ref`, `sighting_of_ref` 等），确保关系完整性。

### Q: 可以覆盖原文件吗？

A: 可以，但不推荐。建议使用不同的输出文件名，保留原始文件作为备份。

```bash
# 不推荐
python tools/fix_stix_ids.py outputs/o1.json outputs/o1.json

# 推荐
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json
```

### Q: 如何查看详细的 ID 映射？

A: 使用 `-v` 或 `--verbose` 参数：

```bash
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json -v
```

这会显示每个旧 ID 到新 ID 的映射关系。

## 集成到项目

### Python API 使用

```python
from tools.fix_stix_ids import STIXIDFixer

# 创建修复器
fixer = STIXIDFixer()

# 修复文件
fixer.fix_file('input.json', 'output.json')

# 获取统计信息
print(f"修复了 {len(fixer.id_mapping)} 个无效 ID")

# 打印映射关系
fixer.print_mapping()
```

### 批量处理

```python
import glob
from tools.fix_stix_ids import STIXIDFixer

# 批量处理所有 JSON 文件
for input_file in glob.glob('outputs/*.json'):
    if '_fixed' not in input_file:
        output_file = input_file.replace('.json', '_fixed.json')
        fixer = STIXIDFixer()
        fixer.fix_file(input_file, output_file)
        print(f"处理完成: {input_file}")
```

## 参考资料

- [STIX 2.1 规范](https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html)
- [RFC 4122: UUID 格式](https://tools.ietf.org/html/rfc4122)
- [OpenCTI 文档](https://www.opencti.io/)

## 支持

如有问题，请查看 `tools/README.md` 获取更多详细信息。
