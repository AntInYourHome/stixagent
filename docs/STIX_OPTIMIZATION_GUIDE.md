# STIX Agent 优化指南 - OpenCTI 完全兼容

## 概述

本文档介绍如何优化 STIX Agent 的输出，使其完全符合 STIX 2.1 规范和 OpenCTI 要求。

## 主要改进

### 1. STIX 2.1 规范化 (Normalization)

**问题**: 生成的 STIX 对象可能缺少必需字段

**解决方案**: 自动添加所有必需字段

#### 必需字段检查

| 对象类型 | 必需字段 |
|---------|---------|
| **malware** | type, spec_version, id, created, modified, name, `is_family` |
| **threat-actor** | type, spec_version, id, created, modified, name, `threat_actor_types` |
| **tool** | type, spec_version, id, created, modified, name, `tool_types` |
| **infrastructure** | type, spec_version, id, created, modified, name, `infrastructure_types` |
| **indicator** | type, spec_version, id, created, modified, pattern, `pattern_type`, `valid_from` |
| **identity** | type, spec_version, id, created, modified, name, `identity_class` |

#### 示例修复

**修复前:**
```json
{
  "type": "malware",
  "id": "malware--123",
  "name": "Back_Eleven"
}
```

**修复后:**
```json
{
  "type": "malware",
  "spec_version": "2.1",
  "id": "malware--6f0653cc-c8c0-4809-81c7-676b45c7b77d",
  "created": "2024-01-11T00:00:00.000Z",
  "modified": "2024-01-11T00:00:00.000Z",
  "name": "Back_Eleven",
  "is_family": true,
  "malware_types": ["trojan"]
}
```

### 2. UUID 格式修复

**问题**: 使用随机数代替标准 UUID

**解决方案**: 生成符合 RFC 4122 的 UUID v4

#### UUID 格式要求

- 格式: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- 只能包含: 0-9, a-f 和连字符
- 总长度: 36 个字符（包括 4 个连字符）

### 3. OpenCTI 关系类型兼容性

**问题**: 使用了 OpenCTI 不支持的关系类型

**解决方案**: 自动映射到兼容的关系类型

#### 关系类型映射表

| 原关系 | 目标 | 修复后 | 说明 |
|-------|-----|--------|------|
| malware → threat-actor | `attributed-to` | `authored-by` | 作者关系 |
| infrastructure → malware | `consists-of` | `hosts` | 托管关系 |
| attack-pattern → vulnerability | `exploits` | `targets` | 目标关系 |
| malware → malware | `delivers` | `downloads` | 下载关系 |
| malware → infrastructure | `controls` | `uses` | 使用关系 |
| malware → infrastructure | `communicates-with` | `uses` | 使用关系 |

## 完整处理流程

### 方法 1: 一键处理（推荐）

使用完整流程工具，自动完成所有步骤：

```bash
python tools/full_pipeline.py outputs/o1.json outputs/ready.json
```

**处理步骤:**
1. ✅ 规范化 STIX 对象（添加必需字段）
2. ✅ 修复 STIX ID（生成有效 UUID）
3. ✅ 修复 OpenCTI 兼容性（修复关系类型）
4. ✅ 最终验证（确保合规）

**输出示例:**
```
======================================================================
Complete STIX 2.1 Processing Pipeline
======================================================================

[Step 1/4] Normalizing STIX objects...
[OK] Fixed 5 normalization issue(s)

[Step 2/4] Fixing STIX IDs...
[OK] Fixed 97 invalid ID(s)

[Step 3/4] Fixing OpenCTI compatibility...
[OK] Fixed 11 relationship(s)

[Step 4/4] Final validation...
[OK] Validation passed
  - Total objects: 116
  - Valid IDs: 116
  - Invalid IDs: 0

======================================================================
[SUCCESS] Processing complete!
======================================================================

Pipeline Summary:
  - Normalization fixes: 5
  - IDs fixed: 97
  - Relationships fixed: 11
  - Total objects: 116
  - Validation status: PASS

Ready to import into OpenCTI!
```

### 方法 2: 分步处理

如果需要更精细的控制，可以分步执行：

```bash
# 步骤 1: 规范化
python tools/normalize_stix.py outputs/o1.json outputs/o1_normalized.json

# 步骤 2: 修复 ID
python tools/fix_stix_ids.py outputs/o1_normalized.json outputs/o1_fixed.json

# 步骤 3: 修复 OpenCTI 兼容性
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_ready.json

# 步骤 4: 验证
python tools/validate_stix_ids.py outputs/o1_ready.json
```

## 工具详解

### normalize_stix.py - STIX 2.1 规范化工具

**功能:**
- 自动添加缺失的必需字段
- 生成正确的时间戳
- 设置类型特定的默认值

**使用:**
```bash
python tools/normalize_stix.py <input> [output]
```

**示例:**
```bash
python tools/normalize_stix.py outputs/o1.json outputs/o1_norm.json
```

### fix_stix_ids.py - ID 修复工具

**功能:**
- 生成符合规范的 UUID v4
- 自动更新所有引用关系
- 保持关系完整性

**使用:**
```bash
python tools/fix_stix_ids.py <input> [output]
```

### fix_opencti_compatibility.py - OpenCTI 兼容性工具

**功能:**
- 修复不支持的关系类型
- 智能语义映射
- 详细的修复报告

**使用:**
```bash
python tools/fix_opencti_compatibility.py <input> [output]
```

### validate_stix_ids.py - 验证工具

**功能:**
- 验证 UUID 格式
- 检查类型一致性
- 生成详细报告

**使用:**
```bash
python tools/validate_stix_ids.py <file>
```

### full_pipeline.py - 完整流程工具

**功能:**
- 集成所有工具
- 自动化处理
- 一次性完成所有修复

**使用:**
```bash
python tools/full_pipeline.py <input> [output]
```

## 集成到 STIX Agent 主流程

### 方案 1: 后处理（推荐）

在 STIX Agent 生成文件后，运行处理流程：

```bash
# 生成 STIX 文件
python main.py input.pdf -o outputs/raw.json

# 处理为 OpenCTI 就绪
python tools/full_pipeline.py outputs/raw.json outputs/ready.json

# 导入 OpenCTI
# 上传 outputs/ready.json 到 OpenCTI
```

### 方案 2: 集成到代码

修改 `main.py` 以自动调用处理流程：

```python
from tools.full_pipeline import full_stix_pipeline

# 生成 STIX 文件
output_file = agent.process(input_file)

# 自动处理
ready_file = full_stix_pipeline(output_file)

print(f"OpenCTI-ready file: {ready_file}")
```

## 最佳实践

### 1. 始终使用完整流程

```bash
# 好 ✓
python tools/full_pipeline.py outputs/o1.json

# 避免跳过步骤 ✗
python tools/fix_stix_ids.py outputs/o1.json
# (缺少规范化和兼容性修复)
```

### 2. 验证最终输出

```bash
# 在导入 OpenCTI 之前，总是验证
python tools/validate_stix_ids.py outputs/ready.json
```

### 3. 保留中间文件用于调试

```bash
# 使用不同的文件名保存每个阶段
python tools/normalize_stix.py o1.json o1_step1.json
python tools/fix_stix_ids.py o1_step1.json o1_step2.json
python tools/fix_opencti_compatibility.py o1_step2.json o1_final.json
```

### 4. 批量处理

```python
import glob
from tools.full_pipeline import full_stix_pipeline

for input_file in glob.glob('outputs/*.json'):
    if not any(x in input_file for x in ['_ready', '_final', '_temp']):
        try:
            output = full_stix_pipeline(input_file)
            print(f"✓ Processed: {output}")
        except Exception as e:
            print(f"✗ Failed: {input_file} - {e}")
```

## 故障排除

### 问题 1: "Missing required field"

**原因**: 对象缺少 STIX 2.1 必需字段

**解决**: 运行规范化工具
```bash
python tools/normalize_stix.py <file>
```

### 问题 2: "UUID not valid"

**原因**: ID 包含无效字符或格式错误

**解决**: 运行 ID 修复工具
```bash
python tools/fix_stix_ids.py <file>
```

### 问题 3: "Relationship type not allowed"

**原因**: 使用了 OpenCTI 不支持的关系类型

**解决**: 运行兼容性修复工具
```bash
python tools/fix_opencti_compatibility.py <file>
```

### 问题 4: 多个问题同时存在

**解决**: 使用完整流程工具
```bash
python tools/full_pipeline.py <file>
```

## Python API 使用

```python
from tools.normalize_stix import STIX21Normalizer
from tools.fix_stix_ids import STIXIDFixer
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer
from tools.full_pipeline import full_stix_pipeline

# 方法 1: 使用完整流程（推荐）
output = full_stix_pipeline('input.json', 'output.json')

# 方法 2: 分步处理
normalizer = STIX21Normalizer()
normalizer.normalize_file('input.json', 'temp1.json')

id_fixer = STIXIDFixer()
id_fixer.fix_file('temp1.json', 'temp2.json')

compat_fixer = OpenCTICompatibilityFixer()
compat_fixer.fix_file('temp2.json', 'output.json')
```

## 性能指标

基于 116 个 STIX 对象的测试：

| 步骤 | 处理时间 | 修复项 |
|-----|---------|--------|
| 规范化 | <1秒 | 5项 |
| ID修复 | <1秒 | 97项 |
| 兼容性修复 | <1秒 | 11项 |
| 验证 | <1秒 | 116个对象 |
| **总计** | **<3秒** | **113项修复** |

## 总结

使用优化后的 STIX Agent 工具链，您可以：

1. ✅ 自动规范化 STIX 对象
2. ✅ 自动生成有效的 UUID
3. ✅ 自动修复 OpenCTI 兼容性
4. ✅ 验证数据完整性
5. ✅ 无缝导入 OpenCTI

**完全自动化，零手动干预！**
