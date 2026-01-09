# Tool Message 错误分析报告

## 错误现象

从日志分析（422-1028行），发现关键错误：

```
BadRequestError: Error code: 400
'message': 'messages with role "tool" must be a response to a preceeding message with "tool_calls".'
```

**发生时机**：
- 第一次迭代：成功，有工具调用和工具响应
- 第二次迭代：消息历史被压缩（从13条压缩到10条），然后调用LLM时出错

## 错误原因

### 问题根源：消息压缩破坏了消息对的完整性

**消息对的正确结构**：
```
SystemMessage
HumanMessage (chunk content)
AIMessage (with tool_calls)  ← 必须成对
ToolMessage (tool response)  ← 必须成对
AIMessage (with tool_calls)  ← 必须成对
ToolMessage (tool response)  ← 必须成对
...
```

**当前压缩逻辑**（第656-664行）：
```python
if len(messages) > MAX_MESSAGE_HISTORY:
    system_msg = messages[0] if messages and isinstance(messages[0], SystemMessage) else None
    recent_messages = messages[-(MAX_MESSAGE_HISTORY - 1):] if system_msg else messages[-MAX_MESSAGE_HISTORY:]
    if system_msg:
        messages = [system_msg] + recent_messages
```

**问题**：
- 简单地取最后N条消息
- 可能截断消息对：
  - 保留了 `ToolMessage`
  - 但丢失了前面的 `AIMessage (with tool_calls)`
- 结果：`ToolMessage` 前面没有对应的 `tool_calls`，导致API错误

### 具体场景

**压缩前**（13条消息）：
```
[0] SystemMessage
[1] HumanMessage
[2] AIMessage (tool_calls: [call1, call2, ...])  ← 第一次迭代
[3] ToolMessage (call1 response)
[4] ToolMessage (call2 response)
...
[12] ToolMessage (last call response)
```

**压缩后**（10条消息）：
```
[0] SystemMessage
[1] ToolMessage (call2 response)  ← 问题：前面没有对应的 AIMessage
[2] ToolMessage (call3 response)
...
[9] ToolMessage (last call response)
```

**结果**：第一个 `ToolMessage` 前面没有 `AIMessage (with tool_calls)`，导致API拒绝请求。

## 解决方案

### 方案1：智能消息压缩（推荐）

确保压缩时保持消息对的完整性：

```python
def _compress_messages(self, messages: List[BaseMessage], max_count: int) -> List[BaseMessage]:
    """压缩消息历史，保持消息对的完整性。
    
    规则：
    1. 保留 SystemMessage（如果有）
    2. 保留 HumanMessage（chunk content）
    3. 从后往前扫描，确保每个 ToolMessage 都有对应的 AIMessage (with tool_calls)
    """
    from langchain_core.messages import ToolMessage, AIMessage
    
    if len(messages) <= max_count:
        return messages
    
    # 保留 SystemMessage
    system_msg = messages[0] if messages and isinstance(messages[0], SystemMessage) else None
    remaining_count = max_count - (1 if system_msg else 0)
    
    # 从后往前扫描，确保消息对完整
    compressed = []
    i = len(messages) - 1
    
    while i >= 0 and len(compressed) < remaining_count:
        msg = messages[i]
        
        if isinstance(msg, ToolMessage):
            # ToolMessage 必须和前面的 AIMessage 配对
            compressed.insert(0, msg)
            # 检查前面是否有对应的 AIMessage
            if i > 0 and isinstance(messages[i-1], AIMessage) and hasattr(messages[i-1], 'tool_calls') and messages[i-1].tool_calls:
                compressed.insert(0, messages[i-1])
                i -= 2  # 跳过两个消息
            else:
                # 没有配对的 AIMessage，移除这个 ToolMessage
                compressed.pop(0)
                i -= 1
        else:
            compressed.insert(0, msg)
            i -= 1
    
    # 确保有 HumanMessage（chunk content）
    if system_msg:
        # 查找 HumanMessage
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg not in compressed:
                compressed.insert(1, msg)  # 插入到 SystemMessage 后面
                break
    
    if system_msg:
        return [system_msg] + compressed
    return compressed
```

### 方案2：移除孤立的 ToolMessage

在压缩时，如果发现 ToolMessage 前面没有对应的 AIMessage，则移除它：

```python
def _compress_messages_simple(self, messages: List[BaseMessage], max_count: int) -> List[BaseMessage]:
    """简单压缩：移除孤立的 ToolMessage"""
    from langchain_core.messages import ToolMessage, AIMessage
    
    if len(messages) <= max_count:
        return messages
    
    system_msg = messages[0] if messages and isinstance(messages[0], SystemMessage) else None
    recent_messages = messages[-(max_count - 1):] if system_msg else messages[-max_count:]
    
    # 移除孤立的 ToolMessage（前面没有 AIMessage with tool_calls）
    filtered = []
    for i, msg in enumerate(recent_messages):
        if isinstance(msg, ToolMessage):
            # 检查前面是否有对应的 AIMessage
            if i > 0 and isinstance(recent_messages[i-1], AIMessage) and \
               hasattr(recent_messages[i-1], 'tool_calls') and recent_messages[i-1].tool_calls:
                filtered.append(msg)
            # 否则跳过这个 ToolMessage
        else:
            filtered.append(msg)
    
    if system_msg:
        return [system_msg] + filtered
    return filtered
```

### 方案3：限制工具调用数量

在第一次迭代时就限制工具调用数量，避免消息历史过长：

```python
# 在工具调用时限制数量
if len(response.tool_calls) > 5:  # 限制最多5个工具调用
    response.tool_calls = response.tool_calls[:5]
    logger.warning(f"[CHUNK-{chunk_index + 1}] 工具调用过多，限制到5个")
```

## 推荐方案

**方案1（智能消息压缩）** 是最佳选择，因为：
1. 保持消息对的完整性
2. 最大化保留有用的上下文
3. 避免API错误

## 实施建议

1. **立即修复**：实施方案1，确保消息压缩时保持消息对完整
2. **长期优化**：考虑限制单次迭代的工具调用数量，减少消息历史增长
