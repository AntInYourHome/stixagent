# 项目结构说明

## 目录结构

```
stixagent/
├── stixagent/                    # 核心代码包
│   ├── __init__.py              # 包初始化
│   ├── agents/                   # Agent实现
│   │   ├── __init__.py
│   │   ├── agent.py             # 标准Agent
│   │   └── react_agent.py       # ReAct Agent
│   ├── loaders/                  # 文档加载器
│   │   ├── __init__.py
│   │   ├── document_loaders.py  # 多格式文档加载
│   │   └── text_splitter.py     # 文本切分器
│   ├── embeddings/               # Embedding实现
│   │   ├── __init__.py
│   │   └── qwen_embeddings.py   # Qwen Embeddings
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       ├── logger.py             # 日志系统
│       ├── vector_store.py       # 向量数据库
│       └── stix_converter.py    # STIX转换器
│
├── tests/                        # 测试文件
│   ├── test_*.py                # 各种测试脚本
│   ├── test_*.txt               # 测试文档
│   └── verify_output.py         # 输出验证
│
├── docs/                         # 文档
│   ├── *.md                     # 各种文档
│
├── outputs/                      # 输出文件
│   └── *.json                   # STIX输出文件
│
├── data/                         # 数据文件
│   └── stix-v2.1-os.pdf         # STIX参考文档
│
├── logs/                         # 日志文件（自动创建）
│   └── stixagent.log            # 应用日志
│
├── vector_db/                    # 向量数据库（自动创建）
│
├── main.py                       # 主入口
├── config.py                     # 配置文件
├── requirements.txt              # 依赖列表
├── README.md                     # 项目说明
└── .gitignore                    # Git忽略文件
```

## 模块说明

### stixagent.agents
- **agent.py**: 标准LangGraph Agent，用于处理小文档
- **react_agent.py**: ReAct模式Agent，用于处理大文档，支持文本切分和逐段分析

### stixagent.loaders
- **document_loaders.py**: 支持PDF、PPT、文本、HTML格式的文档加载
- **text_splitter.py**: 智能文本切分，将大文档切分为可管理的段落

### stixagent.embeddings
- **qwen_embeddings.py**: Qwen Embeddings实现，使用dashscope SDK

### stixagent.utils
- **logger.py**: 统一的日志系统，支持debug模式
- **vector_store.py**: LanceDB向量数据库封装
- **stix_converter.py**: STIX格式转换和验证

## 日志系统

### 日志级别
- **INFO**: 常规操作信息
- **DEBUG**: 详细调试信息（需要--debug参数）
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 日志打点
- `[AGENT]`: Agent操作步骤
- `[REACT-*]`: ReAct循环信息（THINK, ACT, OBSERVE）
- `[TOOL]`: 工具调用信息
- `[CHUNK]`: 文档块处理信息

### 使用方式

```bash
# 普通模式
python main.py input.txt -o output.json

# Debug模式（详细日志）
python main.py input.txt -o output.json --debug

# Debug模式 + 日志文件
python main.py input.txt -o output.json --debug --log-file ./logs/app.log
```

## 环境变量

在`.env`文件中配置：
```
QWEN_API=your_api_key
QWEN_URL=https://your-api-endpoint.com/v1
EMBEDDING_MODE=qwen            # Embedding模式: "qwen" 或 "openai"
                                # - "qwen": 使用 QwenEmbeddings 直接调用 Qwen API（推荐，已修复参数格式问题）
                                # - "openai": 使用 OpenAIEmbeddings 兼容接口
DEBUG=false                    # 是否启用debug模式
LOG_FILE=./logs/stixagent.log # 日志文件路径
LOG_LEVEL=INFO                 # 日志级别
```

### Embedding 模式说明

- **qwen** (默认): 使用 `QwenEmbeddings` 类直接调用 Qwen API，已修复参数格式问题，推荐使用
- **openai**: 使用 `OpenAIEmbeddings` 通过 OpenAI 兼容接口调用，如果遇到参数格式问题可以尝试此模式


