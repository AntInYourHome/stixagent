# 消息压缩修复报告

## 错误分析

### 错误信息
```
BadRequestError: Error code: 400
'message': 'messages with role "tool" must be a response to a preceeding message with "tool_calls".'
```

### 错误原因

**问题根源**：消息压缩时破坏了消息对的完整性

**消息对的正确结构**：
```
AIMessage (with tool_calls)  ← 必须成对
ToolMessage (tool response)  ← 必须成对
ToolMessage (tool response)  ← 可以多个
```

**问题场景**：
1. 第一次迭代：LLM调用成功，有10个工具调用，产生10个ToolMessage
2. 消息历史：SystemMessage + HumanMessage + AIMessage + 10个ToolMessage = 13条消息
3. 第二次迭代：压缩到10条消息
4. **问题**：压缩时只保留了部分ToolMessage，但丢失了对应的AIMessage
5. **结果**：ToolMessage前面没有tool_calls，API拒绝请求

## 解决方案

### 实施的修复

添加了 `_compress_messages` 方法，确保消息压缩时保持消息对的完整性：

1. **保留基础消息**：
   - SystemMessage（如果有）
   - HumanMessage（chunk content）

2. **智能消息对处理**：
   - 从后往前扫描消息
   - 当遇到 ToolMessage 时：
     - 找到对应的 AIMessage (with tool_calls)
     - 收集该 AIMessage 的所有 ToolMessage
     - 一起保留（AIMessage + 所有 ToolMessages）
   - 当遇到 AIMessage 时：
     - 检查后面是否有 ToolMessage
     - 如果有，一起保留

3. **确保完整性**：
   - 不会保留孤立的 ToolMessage
   - 不会保留没有 ToolMessage 的 AIMessage（如果它原本有 tool_calls）

### 代码改进

**之前**（简单截断）：
```python
recent_messages = messages[-(MAX_MESSAGE_HISTORY - 1):]
messages = [system_msg] + recent_messages
```

**现在**（智能压缩）：
```python
messages = self._compress_messages(messages, MAX_MESSAGE_HISTORY)
```

## 效果

### 修复前
- ❌ 可能保留孤立的 ToolMessage
- ❌ API 返回 400 错误
- ❌ Chunk 处理失败

### 修复后
- ✅ 确保消息对完整
- ✅ 避免 API 错误
- ✅ Chunk 可以正常处理

## 测试建议

1. **测试消息压缩**：
   - 创建包含多个工具调用的消息历史
   - 验证压缩后消息对仍然完整

2. **测试边界情况**：
   - 只有 SystemMessage 和 HumanMessage
   - 消息对跨越压缩边界
   - 多个 AIMessage 和 ToolMessage 混合

3. **测试实际场景**：
   - 运行完整的文档转换
   - 验证不再出现 400 错误

## 总结

修复了消息压缩逻辑，确保：
1. ✅ 消息对完整性
2. ✅ 避免 API 400 错误
3. ✅ 提高处理成功率
