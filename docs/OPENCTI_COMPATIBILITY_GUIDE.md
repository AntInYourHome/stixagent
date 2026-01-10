# OpenCTI 兼容性修复工具使用指南

## 问题背景

当将 STIX 文件导入 OpenCTI 时，可能会遇到以下错误：

1. **无效的关系类型**: `The relationship type X is not allowed between TypeA and TypeB`
2. **格式错误**: `Indicator of type stix is not correctly formatted`
3. **UUID 验证失败**: `Provided value X is not a valid STIX ID (UUID not valid)`
4. **缺失引用**: `Element(s) not found`

## 解决方案

我们提供了一个完整的工具链来修复这些问题：

### 步骤 1: 修复 STIX ID

首先确保所有 ID 符合 STIX 2.1 规范：

```bash
# 修复无效的 UUID
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json

# 验证修复结果
python tools/validate_stix_ids.py outputs/o1_fixed.json
```

### 步骤 2: 修复 OpenCTI 兼容性

修复不被 OpenCTI 支持的关系类型：

```bash
# 修复关系类型
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json
```

### 步骤 3: 导入到 OpenCTI

现在可以将修复后的文件导入 OpenCTI：

1. 登录 OpenCTI 平台
2. 进入 Data → Entities → Import
3. 上传 `o1_opencti.json`
4. 选择 STIX 2.1 导入器
5. 点击 Import

## 工具详解

### fix_opencti_compatibility.py

自动检查和修复 OpenCTI 不支持的关系类型。

**功能特性：**

1. **关系类型映射**: 根据 OpenCTI 文档的允许列表检查关系
2. **智能建议**: 自动将不支持的关系类型替换为语义相近的支持类型
3. **详细报告**: 显示所有修复和移除的关系

**修复示例：**

| 原关系 | 目标类型 | 修复后 | 说明 |
|-------|---------|--------|------|
| `malware --[delivers]--> malware` | malware → malware | `malware --[downloads]--> malware` | 组件下载关系 |
| `malware --[attributed-to]--> threat-actor` | malware → threat-actor | `malware --[authored-by]--> threat-actor` | 作者关系 |
| `malware --[controls]--> infrastructure` | malware → infrastructure | `malware --[uses]--> infrastructure` | 使用关系 |
| `infrastructure --[consists-of]--> malware` | infrastructure → malware | `infrastructure --[hosts]--> malware` | 托管关系 |
| `attack-pattern --[exploits]--> vulnerability` | attack-pattern → vulnerability | `attack-pattern --[targets]--> vulnerability` | 目标关系 |

## 完整工作流

```bash
# 1. 生成 STIX 文件（使用 stix-agent）
python main.py input.pdf -o outputs/o1.json

# 2. 修复 ID 格式
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json

# 3. 验证 ID
python tools/validate_stix_ids.py outputs/o1_fixed.json

# 4. 修复 OpenCTI 兼容性
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json

# 5. 最终验证
python tools/validate_stix_ids.py outputs/o1_opencti.json

# 6. 导入到 OpenCTI
# 上传 outputs/o1_opencti.json
```

## 修复统计示例

```
======================================================================
OpenCTI Compatibility Report
======================================================================

[FIXED] 11 relationship(s) fixed:
  - relationship--de6d3c86-4455-4001-915d-ed715fd3e80c
    attack-pattern --[exploits]--> vulnerability
    Changed to: attack-pattern --[targets]--> vulnerability

  - relationship--d6e7f8a9-b0c1-d2e3-f4a5-b6c7d8e9f0a1
    malware --[attributed-to]--> threat-actor
    Changed to: malware --[authored-by]--> threat-actor

  ... (9 more relationships)

======================================================================
```

## OpenCTI 允许的关系类型参考

### Attack Pattern

- `targets`: identity, location, vulnerability
- `uses`: malware, tool
- `mitigates`: vulnerability
- `subtechnique-of`: attack-pattern

### Malware

- `authored-by`: threat-actor, intrusion-set
- `beacons-to`: infrastructure
- `communicates-with`: ipv4-addr, ipv6-addr, domain-name, url
- `controls`: malware
- `downloads`: malware, tool, file
- `drops`: malware, tool, file
- `exploits`: vulnerability
- `originates-from`: location
- `targets`: identity, location, vulnerability
- `uses`: attack-pattern, infrastructure, tool
- `variant-of`: malware

### Infrastructure

- `communicates-with`: infrastructure, ipv4-addr, ipv6-addr, domain-name, url
- `consists-of`: infrastructure, observed-data
- `controls`: infrastructure, malware
- `has`: vulnerability
- `hosts`: malware, tool
- `located-at`: location
- `uses`: infrastructure

### Threat Actor

- `attributed-to`: identity
- `compromises`: infrastructure
- `hosts`: infrastructure
- `impersonates`: identity
- `located-at`: location
- `targets`: identity, location, vulnerability
- `uses`: attack-pattern, infrastructure, malware, tool

完整列表请参考 [OpenCTI 文档](https://docs.opencti.io/latest/deployment/connectors/)。

## 常见错误和解决方案

### 错误 1: "Indicator of type stix is not correctly formatted"

**原因**: Indicator 对象的 pattern 字段格式不正确

**解决方案**: 检查并修复 indicator 对象的 pattern 字段

### 错误 2: "UUID not valid"

**原因**: ID 中的 UUID 部分包含非十六进制字符或格式不正确

**解决方案**: 使用 `fix_stix_ids.py` 自动修复

### 错误 3: "The relationship type X is not allowed between TypeA and TypeB"

**原因**: 使用了 OpenCTI 不支持的关系类型

**解决方案**: 使用 `fix_opencti_compatibility.py` 自动修复

### 错误 4: "Element(s) not found"

**原因**: 关系引用的对象在 bundle 中不存在

**解决方案**: 检查并确保所有被引用的对象都存在于 bundle 中

## Python API 使用

```python
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer

# 创建修复器
fixer = OpenCTICompatibilityFixer()

# 修复文件
fixer.fix_file('input.json', 'output.json')

# 打印报告
fixer.print_report()

# 获取修复统计
print(f"Fixed: {len(fixer.fixes)} relationships")
print(f"Removed: {len(fixer.removed_relationships)} relationships")
```

## 批量处理

```python
import glob
from tools.fix_stix_ids import STIXIDFixer
from tools.fix_opencti_compatibility import OpenCTICompatibilityFixer

for input_file in glob.glob('outputs/*.json'):
    if '_opencti' not in input_file:
        # 步骤 1: 修复 ID
        id_fixer = STIXIDFixer()
        temp_file = input_file.replace('.json', '_fixed.json')
        id_fixer.fix_file(input_file, temp_file)

        # 步骤 2: 修复 OpenCTI 兼容性
        opencti_fixer = OpenCTICompatibilityFixer()
        output_file = input_file.replace('.json', '_opencti.json')
        opencti_fixer.fix_file(temp_file, output_file)

        print(f"Processed: {input_file} -> {output_file}")
```

## 总结

使用这个工具链，您可以：

1. ✓ 自动修复无效的 STIX ID
2. ✓ 自动修复不兼容的关系类型
3. ✓ 生成详细的修复报告
4. ✓ 确保文件可以成功导入 OpenCTI

这大大简化了 STIX 数据准备和 OpenCTI 集成的流程。
