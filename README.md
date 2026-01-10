# STIX Agent

一个基于 LangGraph 的 AI Agent 系统，用于将渗透测试案例转换为标准的 STIX 2.1 格式。

## 功能特性

- 🤖 基于 LangGraph 的智能 Agent 架构
- 🧠 **ReAct模式**：支持思考-行动-观察循环，逐段分析大文档
- 📄 支持多种文档格式：PDF、PPT、文本、HTML
- ✂️ **智能文本切分**：自动将大文档切分为可管理的段落
- 🔍 基于 LanceDB 的向量数据库，使用 STIX 2.1 规范文档作为参考
- ✅ 自动验证 STIX 格式合规性
- 🔄 **结果合并与一致性检查**：确保最终输出与原文一致
- 🔗 使用 OpenAI 兼容接口（支持 Qwen 等模型）

## 环境要求

- Python 3.8+
- Qwen API 密钥和端点

## 安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
创建 `.env` 文件：
```
QWEN_API=your_api_key_here
QWEN_URL=https://your-api-endpoint.com/v1
EMBEDDING_MODE=qwen            # 可选: "qwen" (默认) 或 "openai"
```

**Embedding 模式说明：**
- `qwen` (默认): 使用 QwenEmbeddings 直接调用 Qwen API（推荐，已修复参数格式问题）
- `openai`: 使用 OpenAIEmbeddings 兼容接口

## 使用方法

### 命令行使用

```bash
# 转换文档并输出到标准输出
python main.py input.pdf

# 转换文档并保存到文件
python main.py input.pdf -o output.json

# 转换并验证输出
python main.py input.pdf -o output.json --validate

# 使用ReAct模式处理大文档（自动启用，文档>3000字符时）
python main.py large_document.txt -o output.json --react

# 强制使用ReAct模式
python main.py input.pdf -o output.json --react --validate
```

### STIX ID 管理工具

生成的 STIX 文件可能包含无效的 ID 格式。使用以下工具修复和验证：

```bash
# 修复 STIX ID
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json

# 验证 STIX ID
python tools/validate_stix_ids.py outputs/o1_fixed.json

# 快捷修复（使用默认路径）
python tools/run_fix_ids.py
```

**工具说明：**
- `fix_stix_ids.py`: 自动修复无效的 STIX ID，将随机数替换为符合 RFC 4122 规范的 UUID
- `validate_stix_ids.py`: 验证所有 ID 是否符合 STIX 2.1 规范
- `run_fix_ids.py`: 一键修复工具，处理默认输出文件

### OpenCTI 兼容性工具

在导入 OpenCTI 之前，需要修复不兼容的关系类型：

```bash
# 修复 OpenCTI 兼容性问题
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json

# 完整工作流（ID修复 + OpenCTI兼容性）
python tools/fix_stix_ids.py outputs/o1.json outputs/o1_fixed.json
python tools/fix_opencti_compatibility.py outputs/o1_fixed.json outputs/o1_opencti.json
```

**工具说明：**
- `fix_opencti_compatibility.py`: 自动修复 OpenCTI 不支持的关系类型
  - 将 `malware --[attributed-to]--> threat-actor` 改为 `authored-by`
  - 将 `infrastructure --[consists-of]--> malware` 改为 `hosts`
  - 将 `attack-pattern --[exploits]--> vulnerability` 改为 `targets`
  - 等等...

**修复示例：**
```
[FIXED] 11 relationship(s) fixed:
  - malware --[attributed-to]--> threat-actor
    Changed to: malware --[authored-by]--> threat-actor
  - infrastructure --[consists-of]--> malware
    Changed to: infrastructure --[hosts]--> malware
```

详细使用说明请参考：
- [工具详细文档](tools/README.md)（英文）
- [ID 修复指南](docs/STIX_ID_FIX_GUIDE.md)（中文）
- [OpenCTI 兼容性指南](docs/OPENCTI_COMPATIBILITY_GUIDE.md)（中文）

### 支持的输入格式

- PDF (`.pdf`)
- PowerPoint (`.ppt`, `.pptx`)
- 文本文件 (`.txt`, `.md`)
- HTML (`.html`, `.htm`)

## 项目结构

```
stixagent/
├── main.py                 # 主入口文件
├── stixagent/
│   ├── agents/
│   │   ├── agent.py           # LangGraph Agent 实现（标准模式）
│   │   └── react_agent.py     # ReAct Agent 实现（大文档模式）
│   ├── loaders/
│   │   ├── document_loaders.py # 文档加载器
│   │   └── text_splitter.py    # 文本切分器
│   ├── embeddings/
│   │   └── qwen_embeddings.py  # Qwen Embeddings 实现
│   └── utils/
│       ├── vector_store.py     # LanceDB 向量数据库
│       └── stix_converter.py   # STIX 格式转换和验证
├── tools/                  # STIX ID 管理工具
│   ├── fix_stix_ids.py        # ID 修复工具
│   ├── validate_stix_ids.py   # ID 验证工具
│   ├── run_fix_ids.py         # 快捷运行脚本
│   └── README.md              # 工具详细文档
├── examples/               # 示例代码
│   └── stix_id_tools_examples.py  # 工具使用示例
├── docs/                   # 文档
│   ├── STIX_ID_FIX_GUIDE.md      # ID 修复指南（中文）
│   └── IMPLEMENTATION_SUMMARY.md  # 实现总结
├── outputs/                # 输出文件目录
│   ├── o1.json                # 原始输出（可能包含无效ID）
│   └── o1_fixed.json          # 修复后的输出
├── config.py               # 配置文件
├── requirements.txt        # 依赖列表
├── stix-v2.1-os.pdf       # STIX 2.1 参考文档
└── README.md              # 项目说明
```

## 工作原理

### 标准模式（小文档）
1. **文档加载**：从各种格式的文件中提取文本内容
2. **向量检索**：使用 LanceDB 向量数据库检索 STIX 2.1 规范文档中的相关内容
3. **AI 转换**：使用 LangGraph Agent 分析文档并生成 STIX 格式数据
4. **格式验证**：自动验证生成的 STIX JSON 是否符合标准

### ReAct模式（大文档，>3000字符）
1. **文档切分**：将大文档智能切分为多个段落（每段约2000字符）
2. **逐段处理**：使用ReAct（思考-行动-观察）循环逐段分析
   - **思考**：分析当前段落，识别需要提取的STIX对象
   - **行动**：使用工具（搜索STIX参考、验证输出）执行操作
   - **观察**：观察操作结果，决定下一步行动
3. **结果合并**：将所有段落的STIX对象合并为单个Bundle
4. **一致性验证**：检查合并后的结果是否完整捕获了原文的所有重要信息
5. **格式验证**：最终验证STIX JSON格式合规性

## 配置说明

在 `config.py` 中可以调整以下配置：

- `LLM_MODEL`: 使用的语言模型（默认：qwen-flash）
- `EMBEDDING_MODEL`: 向量模型（默认：text-embedding-v4）
- `VECTOR_DB_PATH`: 向量数据库路径
- `MAX_ITERATIONS`: Agent 最大迭代次数
- `TEMPERATURE`: 模型温度参数

## 注意事项

- 首次运行时会自动构建向量数据库，需要一些时间
- 确保 `stix-v2.1-os.pdf` 文件存在于项目根目录
- 生成的 STIX 输出会严格遵循 STIX 2.1 标准

## 许可证

MIT License

