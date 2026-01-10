# STIX Agent - OpenCTI 集成完整指南

## 项目概述

STIX Agent 是一个基于 LangGraph 的 AI Agent 系统，用于将渗透测试案例转换为标准的 STIX 2.1 格式，并提供完整的 OpenCTI 集成工具链。

## 完整工作流

### 步骤 1: 生成 STIX 文件

使用 STIX Agent 将文档转换为 STIX 格式：

```bash
python main.py input.pdf -o outputs/o1.json --validate
```

### 步骤 2: 修复 STIX ID

修复 UUID 格式问题：

```bash
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json
```

**修复内容：**
- 将无效的随机数 ID 替换为符合 RFC 4122 规范的 UUID v4
- 自动更新所有引用关系
- 保持对象间关系完整性

**结果：**
- 原始: 97 个无效 ID (83.6%)
- 修复后: 0 个无效 ID (100% 合规)

### 步骤 3: 验证 ID 格式

确认所有 ID 符合规范：

```bash
python tools/validate_stix_ids.py outputs/o1_fixed.json
```

**输出示例：**
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

### 步骤 4: 修复 OpenCTI 兼容性

修复 OpenCTI 不支持的关系类型：

```bash
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json
```

**修复的关系类型：**

| 原关系 | 修复后 | 对象类型 |
|-------|--------|---------|
| `attributed-to` | `authored-by` | malware → threat-actor |
| `consists-of` | `hosts` | infrastructure → malware |
| `exploits` | `targets` | attack-pattern → vulnerability |
| `delivers` | `downloads` | malware → malware |
| `controls` | `uses` | malware → infrastructure |
| `communicates-with` | `uses` | malware → infrastructure |

**结果：**
```
[FIXED] 11 relationship(s) fixed
[REMOVED] 0 invalid relationship(s)
```

### 步骤 5: 最终验证

再次验证修复后的文件：

```bash
python tools/validate_stix_ids.py outputs/o1_opencti.json
```

### 步骤 6: 导入 OpenCTI

1. 登录 OpenCTI 平台
2. 进入 **Data → Entities → Import**
3. 上传 `outputs/o1_opencti.json`
4. 选择 **STIX 2.1** 导入器
5. 点击 **Import**
6. 等待处理完成

## 工具链总览

### 核心工具

1. **fix_stix_ids.py** - STIX ID 修复工具
   - 生成符合规范的 UUID
   - 更新所有引用
   - 97 个 ID 自动修复

2. **validate_stix_ids.py** - STIX ID 验证工具
   - 验证 UUID 格式
   - 检查类型一致性
   - 生成详细报告

3. **fix_opencti_compatibility.py** - OpenCTI 兼容性修复工具
   - 修复不支持的关系类型
   - 智能语义映射
   - 11 个关系自动修复

4. **run_fix_ids.py** - 快捷修复脚本
   - 一键运行
   - 默认路径处理

### 辅助工具

- **stix_id_tools_examples.py** - 使用示例代码
- 批量处理支持
- Python API

## 一键处理脚本

创建一个批处理脚本 `process_for_opencti.sh` (Linux/Mac) 或 `process_for_opencti.bat` (Windows):

```bash
#!/bin/bash
# process_for_opencti.sh

INPUT_FILE=$1
BASE_NAME=$(basename "$INPUT_FILE" .json)
OUTPUT_DIR="outputs"

echo "Processing $INPUT_FILE for OpenCTI..."

# 步骤 1: 修复 ID
echo "[1/3] Fixing STIX IDs..."
python tools/fix_stix_ids.py "$INPUT_FILE" "$OUTPUT_DIR/${BASE_NAME}_fixed.json"

# 步骤 2: 修复 OpenCTI 兼容性
echo "[2/3] Fixing OpenCTI compatibility..."
python tools/fix_opencti_compatibility.py "$OUTPUT_DIR/${BASE_NAME}_fixed.json" "$OUTPUT_DIR/${BASE_NAME}_opencti.json"

# 步骤 3: 验证
echo "[3/3] Validating..."
python tools/validate_stix_ids.py "$OUTPUT_DIR/${BASE_NAME}_opencti.json"

echo ""
echo "Done! Ready to import: $OUTPUT_DIR/${BASE_NAME}_opencti.json"
```

使用方法：
```bash
chmod +x process_for_opencti.sh
./process_for_opencti.sh outputs/o1.json
```

## 批量处理示例

Python 批量处理脚本：

```python
#!/usr/bin/env python
"""批量处理所有 STIX 文件以准备导入 OpenCTI"""

import glob
from pathlib import Path
from tools.fix_stix_ids import STIXIDFixer
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer

def process_file(input_file):
    """处理单个文件"""
    print(f"\n{'='*70}")
    print(f"Processing: {input_file}")
    print('='*70)

    # 生成输出文件名
    path = Path(input_file)
    fixed_file = path.parent / f"{path.stem}_fixed.json"
    opencti_file = path.parent / f"{path.stem}_opencti.json"

    # 步骤 1: 修复 ID
    print("\n[1/2] Fixing STIX IDs...")
    id_fixer = STIXIDFixer()
    id_fixer.fix_file(str(input_file), str(fixed_file))
    print(f"  Fixed {len(id_fixer.id_mapping)} IDs")

    # 步骤 2: 修复 OpenCTI 兼容性
    print("\n[2/2] Fixing OpenCTI compatibility...")
    compat_fixer = OpenCTICompatibilityFixer()
    compat_fixer.fix_file(str(fixed_file), str(opencti_file))
    print(f"  Fixed {len(compat_fixer.fixes)} relationships")

    return opencti_file

# 处理所有 JSON 文件
input_files = glob.glob('outputs/*.json')
input_files = [f for f in input_files if not any(x in f for x in ['_fixed', '_opencti'])]

print(f"Found {len(input_files)} file(s) to process")

for input_file in input_files:
    try:
        output_file = process_file(input_file)
        print(f"\n✓ Success: {output_file}")
    except Exception as e:
        print(f"\n✗ Error processing {input_file}: {e}")

print(f"\n{'='*70}")
print("Batch processing complete!")
print('='*70)
```

## 错误处理

### 常见错误及解决方案

#### 1. UUID 格式错误

**错误信息：**
```
Provided value malware--b8c90d2e1-... is not a valid STIX ID (UUID not valid)
```

**解决方案：**
```bash
python tools/fix_stix_ids.py outputs/problem.json outputs/fixed.json
```

#### 2. 关系类型不支持

**错误信息：**
```
The relationship type attributed-to is not allowed between Malware and Threat-Actor
```

**解决方案：**
```bash
python tools/fix_opencti_compatibility.py outputs/fixed.json outputs/opencti.json
```

#### 3. 缺失引用

**错误信息：**
```
Element(s) not found
```

**解决方案：**
检查并确保所有被引用的对象都存在于 bundle 中。

## 性能统计

基于实际测试的 116 个 STIX 对象：

| 阶段 | 处理时间 | 修复项目 |
|------|---------|---------|
| ID 修复 | <1 秒 | 97 个 ID |
| 兼容性修复 | <1 秒 | 11 个关系 |
| 验证 | <1 秒 | 116 个对象 |
| **总计** | **<3 秒** | **108 项修复** |

## 文档索引

### 用户指南
- [README.md](../README.md) - 项目总览
- [STIX_ID_FIX_GUIDE.md](STIX_ID_FIX_GUIDE.md) - ID 修复详细指南
- [OPENCTI_COMPATIBILITY_GUIDE.md](OPENCTI_COMPATIBILITY_GUIDE.md) - OpenCTI 兼容性详细指南

### 技术文档
- [tools/README.md](../tools/README.md) - 工具 API 文档
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - 实现总结

### 示例代码
- [examples/stix_id_tools_examples.py](../examples/stix_id_tools_examples.py) - 使用示例

## 集成到 CI/CD

GitHub Actions 示例：

```yaml
name: Process STIX for OpenCTI

on:
  push:
    paths:
      - 'outputs/*.json'

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Process STIX files
        run: |
          for file in outputs/*.json; do
            if [[ ! "$file" =~ (_fixed|_opencti) ]]; then
              python tools/fix_stix_ids.py "$file" "${file%.json}_fixed.json"
              python tools/fix_opencti_compatibility.py "${file%.json}_fixed.json" "${file%.json}_opencti.json"
            fi
          done

      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: opencti-ready-files
          path: outputs/*_opencti.json
```

## 总结

使用 STIX Agent 工具链，您可以：

1. ✓ 自动生成 STIX 2.1 格式威胁情报
2. ✓ 自动修复所有 ID 格式问题
3. ✓ 自动修复 OpenCTI 兼容性问题
4. ✓ 验证数据完整性和合规性
5. ✓ 无缝导入 OpenCTI 平台

**从文档到 OpenCTI，只需要 6 个步骤，全程自动化！**
