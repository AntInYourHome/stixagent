"""ReAct-based Agent for STIX conversion with text splitting and consistency checking."""
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from ..utils.vector_store import STIXVectorStore
from ..utils.stix_converter import STIXConverter
from ..loaders.text_splitter import STIXDocumentSplitter
from ..utils.logger import get_logger, log_agent_step, log_tool_call, log_react_cycle, log_chunk_processing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import QWEN_API_KEY, QWEN_BASE_URL, LLM_MODEL, TEMPERATURE, MAX_ITERATIONS

logger = get_logger()


class ReActState(TypedDict):
    """State for ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    original_document: str
    document_chunks: List[str]
    current_chunk_index: int
    processed_chunks: List[Dict[str, Any]]
    merged_stix: Dict[str, Any]
    iteration_count: int
    reasoning: str
    action: str
    observation: str


# Initialize vector store
vector_store = STIXVectorStore()


@tool
def search_stix_reference(query: str) -> str:
    """Search STIX 2.1 reference documentation for format requirements.
    
    Args:
        query: The question or topic to search for in STIX documentation.
    
    Returns:
        Relevant STIX documentation context.
    """
    log_tool_call("search_stix_reference", {"query": query})
    result = vector_store.get_relevant_context(query, k=5)
    log_tool_call("search_stix_reference", {"query": query}, result[:200] if result else None)
    return result


@tool
def validate_stix_output(stix_json: str) -> str:
    """Validate STIX JSON output against STIX 2.1 standards.
    
    Args:
        stix_json: The STIX JSON string to validate.
    
    Returns:
        Validation result message.
    """
    log_tool_call("validate_stix_output", {"stix_json_length": len(stix_json)})
    try:
        stix_data = json.loads(stix_json)
        is_valid, error = STIXConverter.validate_stix_json(stix_data)
        if is_valid:
            result = "STIX JSON is valid."
        else:
            result = f"STIX JSON validation failed: {error}"
        log_tool_call("validate_stix_output", None, result)
        return result
    except json.JSONDecodeError as e:
        result = f"Invalid JSON format: {str(e)}"
        log_tool_call("validate_stix_output", None, result)
        return result


@tool
def compare_with_original(extracted_info: str, original_text: str) -> str:
    """Compare extracted STIX information with original document to check consistency.
    
    Args:
        extracted_info: The extracted STIX information summary
        original_text: The original document text to compare against
    
    Returns:
        Comparison result and consistency check
    """
    # This will be used by the LLM to verify consistency
    return f"Original text length: {len(original_text)} characters. Extracted info: {extracted_info[:200]}..."


class ReActSTIXAgent:
    """ReAct-based Agent for converting large documents to STIX format."""
    
    def __init__(self):
        """Initialize the ReAct agent."""
        log_agent_step("Initializing ReActSTIXAgent", {"model": LLM_MODEL})
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
            temperature=TEMPERATURE,
        )
        self.tools = [search_stix_reference, validate_stix_output, compare_with_original]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)
        self.splitter = STIXDocumentSplitter(chunk_size=2000, chunk_overlap=200)
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        log_agent_step("ReActSTIXAgent initialized", {"tools_count": len(self.tools)})
    
    def _build_graph(self) -> StateGraph:
        """Build the ReAct workflow graph."""
        workflow = StateGraph(ReActState)
        
        # Add nodes
        workflow.add_node("think", self._think)
        workflow.add_node("act", self._act)
        workflow.add_node("observe", self._observe)
        workflow.add_node("process_chunk", self._process_chunk)
        workflow.add_node("merge_results", self._merge_results)
        workflow.add_node("verify_consistency", self._verify_consistency)
        
        # Set entry point
        workflow.set_entry_point("think")
        
        # Add edges
        workflow.add_edge("think", "act")
        workflow.add_edge("act", "observe")
        workflow.add_conditional_edges(
            "observe",
            self._should_continue_react,
            {
                "continue_react": "think",
                "process_chunk": "process_chunk",
                "merge": "merge_results",
                "verify": "verify_consistency",
                "end": END
            }
        )
        workflow.add_edge("process_chunk", "think")
        workflow.add_edge("merge_results", "verify_consistency")
        workflow.add_edge("verify_consistency", END)
        
        return workflow
    
    def _think(self, state: ReActState) -> ReActState:
        """ReAct: Think step - analyze current situation and plan next action."""
        messages = state["messages"]
        reasoning = state.get("reasoning", "")
        
        # Build thinking prompt
        think_prompt = f"""Think about the current situation:

Current chunk: {state.get('current_chunk_index', 0)} / {len(state.get('document_chunks', []))}
Processed chunks: {len(state.get('processed_chunks', []))}
Reasoning so far: {reasoning}

What should I do next?
1. If processing a chunk, analyze it and extract STIX objects
2. If all chunks processed, merge the results
3. If merged, verify consistency with original document

Think step by step and decide the next action."""
        
        response = self.llm.invoke([HumanMessage(content=think_prompt)])
        new_reasoning = reasoning + "\n" + response.content if reasoning else response.content
        
        return {
            "reasoning": new_reasoning,
            "messages": [response]
        }
    
    def _act(self, state: ReActState) -> ReActState:
        """ReAct: Act step - execute actions using tools."""
        messages = state["messages"]
        reasoning = state.get("reasoning", "")
        
        # Determine action based on state
        current_index = state.get("current_chunk_index", 0)
        chunks = state.get("document_chunks", [])
        processed = state.get("processed_chunks", [])
        
        if current_index < len(chunks):
            # Process current chunk
            action = "process_chunk"
            action_prompt = f"""Act: Process chunk {current_index + 1} of {len(chunks)}.

Chunk content:
{chunks[current_index]}

Extract all STIX objects from this chunk. Use search_stix_reference if needed for format guidance.
Output valid STIX JSON for this chunk."""
        elif len(processed) == len(chunks) and not state.get("merged_stix"):
            # Merge results
            action = "merge"
            action_prompt = f"""Act: Merge {len(processed)} chunk results into a single STIX Bundle.

Processed chunks contain {sum(len(p.get('objects', [])) for p in processed)} STIX objects total.
Merge them into one cohesive STIX 2.1 Bundle."""
        else:
            # Verify consistency
            action = "verify"
            action_prompt = f"""Act: Verify the merged STIX output is consistent with the original document.

Original document length: {len(state.get('original_document', ''))} characters
Merged STIX contains {len(state.get('merged_stix', {}).get('objects', []))} objects

Check if all important information from the original document is captured in the STIX output."""
        
        response = self.llm_with_tools.invoke([
            SystemMessage(content=f"Current reasoning: {reasoning}"),
            HumanMessage(content=action_prompt)
        ])
        
        return {
            "action": action,
            "messages": [response]
        }
    
    def _observe(self, state: ReActState) -> ReActState:
        """ReAct: Observe step - observe the results of actions."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Execute tool calls if any
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Use tool node to execute tools
            tool_results = self.tool_node.invoke({"messages": [last_message]})
            tool_messages = tool_results.get("messages", [])
            observation = f"Tool executed: {len(tool_messages)} tool result(s)"
            return {
                "observation": observation,
                "messages": tool_messages
            }
        else:
            observation = "Action completed: " + (last_message.content[:200] if hasattr(last_message, "content") else str(last_message))
            return {
                "observation": observation,
                "messages": []
            }
    
    def _should_continue_react(self, state: ReActState) -> str:
        """Determine next step in ReAct loop."""
        current_index = state.get("current_chunk_index", 0)
        chunks = state.get("document_chunks", [])
        processed = state.get("processed_chunks", [])
        merged = state.get("merged_stix")
        
        # Check iteration limit
        if state.get("iteration_count", 0) >= MAX_ITERATIONS:
            return "end"
        
        # If still processing chunks
        if current_index < len(chunks):
            # Check if current chunk is done
            if len(processed) > current_index:
                # Move to next chunk
                return "process_chunk"
            else:
                # Continue ReAct loop for current chunk
                return "continue_react"
        
        # If all chunks processed but not merged
        if len(processed) == len(chunks) and not merged:
            return "merge"
        
        # If merged but not verified
        if merged and not state.get("verified", False):
            return "verify"
        
        return "end"
    
    def _process_chunk(self, state: ReActState) -> ReActState:
        """Process a single chunk and extract STIX objects."""
        current_index = state.get("current_chunk_index", 0)
        chunks = state.get("document_chunks", [])
        processed = state.get("processed_chunks", []).copy()
        
        if current_index >= len(chunks):
            return state
        
        chunk_text = chunks[current_index]
        print(f"Processing chunk {current_index + 1}/{len(chunks)}...")
        
        # Extract STIX from chunk
        chunk_prompt = f"""从以下文档块中提取 STIX 2.1 对象：

{chunk_text}

请按步骤思考，必须提取所有类型的威胁情报：

1. **指标 (Indicator)**: IP地址、域名、文件哈希、URL等可观察指标
2. **攻击模式 (Attack-Pattern)**: 攻击技术、MITRE ATT&CK技术（如T1190、T1059等）
3. **恶意软件 (Malware)**: 恶意软件名称、类型、功能描述
4. **漏洞 (Vulnerability)**: CVE编号、漏洞描述、严重程度
5. **威胁行为者 (Threat-Actor)**: 攻击者信息、组织、动机
6. **关系 (Relationship)**: 对象之间的关联关系（uses、targets、indicates等）

重要要求：
- 不要只提取 indicator，必须识别并提取所有相关类型的对象
- 如果文档提到攻击技术（如SQL注入、XSS、文件上传等），必须创建 attack-pattern 对象
- 如果文档提到恶意软件或工具，必须创建 malware 对象
- 如果文档提到漏洞或CVE，必须创建 vulnerability 对象
- 所有描述性字段（name、description 等）必须使用中文
- 创建对象之间的关系（relationship）以连接相关对象

输出有效的 STIX 2.1 Bundle。如需要格式指导，可使用 search_stix_reference 工具。
仅输出有效的 JSON，不要包含其他文本。"""
        
        # Use LLM with tools to process chunk
        # Add Chinese output requirement to system message
        system_hints = STIXConverter.get_stix_schema_hints()
        system_message_content = f"""{system_hints}

重要提示：
- **必须提取所有类型的 STIX 对象**：indicator、attack-pattern、malware、vulnerability、threat-actor、relationship
- 不要只提取 indicator，必须全面分析文档中的所有威胁情报元素
- 所有描述性字段（name、description、labels 等）必须使用中文
- STIX 对象的结构和字段名保持英文（符合 STIX 标准）
- 但字段值中的描述性内容应使用中文
- 对于攻击技术，必须创建 attack-pattern 对象并包含 MITRE ATT&CK 引用（如果适用）
- 对于恶意软件，必须创建 malware 对象
- 对于漏洞，必须创建 vulnerability 对象并包含 CVE 引用（如果适用）
"""
        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=chunk_prompt)
        ]
        
        # Run a few iterations to allow tool usage
        max_iterations = 5
        for _ in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)
            
            if hasattr(response, "tool_calls") and response.tool_calls:
                # Execute tools
                tool_results = self.tool_node.invoke({"messages": [response]})
                messages.extend(tool_results.get("messages", []))
            else:
                # Got final response
                break
        
        # Extract STIX JSON from final response
        stix_json = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                stix_json = self._extract_stix_json(msg.content)
                if stix_json:
                    break
        
        if stix_json:
            try:
                chunk_result = json.loads(stix_json)
                processed.append({
                    "chunk_index": current_index,
                    "stix_data": chunk_result,
                    "objects": chunk_result.get("objects", [])
                })
                print(f"  Extracted {len(chunk_result.get('objects', []))} STIX objects from chunk {current_index + 1}")
            except Exception as e:
                print(f"  Warning: Failed to parse STIX JSON from chunk {current_index + 1}: {e}")
        else:
            print(f"  Warning: No STIX JSON found in chunk {current_index + 1} response")
        
        return {
            "current_chunk_index": current_index + 1,
            "processed_chunks": processed
        }
    
    def _merge_results(self, state: ReActState) -> ReActState:
        """Merge all chunk results into a single STIX Bundle."""
        processed = state.get("processed_chunks", [])
        
        if not processed:
            return state
        
        # Collect all objects
        all_objects = []
        for chunk_result in processed:
            objects = chunk_result.get("objects", [])
            all_objects.extend(objects)
        
        # Create merged bundle
        merged_bundle = {
            "type": "bundle",
            "id": f"bundle--merged-{len(all_objects)}-objects",
            "spec_version": "2.1",
            "objects": all_objects
        }
        
        return {
            "merged_stix": merged_bundle
        }
    
    def _verify_consistency(self, state: ReActState) -> ReActState:
        """Verify merged STIX is consistent with original document."""
        original = state.get("original_document", "")
        merged = state.get("merged_stix", {})
        
        verify_prompt = f"""Verify that the merged STIX output captures all important information from the original document.

Original document ({len(original)} characters):
{original[:1000]}...

Merged STIX Bundle contains {len(merged.get('objects', []))} objects.

Check:
1. Are all vulnerabilities mentioned in the original captured?
2. Are all attack patterns identified?
3. Are all indicators (IPs, domains, hashes) included?
4. Are relationships between objects properly established?

If anything is missing, note it. Otherwise, confirm consistency."""
        
        response = self.llm.invoke([HumanMessage(content=verify_prompt)])
        
        return {
            "verified": True,
            "verification_result": response.content
        }
    
    def _extract_stix_json(self, text: str) -> str:
        """Extract STIX JSON from text."""
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group(0))
                return json_match.group(0)
            except:
                pass
        return ""
    
    def convert_to_stix(self, document_content: str, document_metadata: dict = None) -> str:
        """Convert large document to STIX format using ReAct approach.
        
        Args:
            document_content: The full document content
            document_metadata: Optional metadata
            
        Returns:
            STIX JSON string
        """
        # Initialize vector store
        log_agent_step("Initializing vector store")
        try:
            vector_store.initialize()
            log_agent_step("Vector store initialized")
        except Exception as e:
            logger.warning(f"Could not initialize vector store: {e}")
        
        # Split document into chunks
        log_agent_step("Splitting document into chunks", {"content_length": len(document_content)})
        chunks = self.splitter.split_document(document_content, document_metadata)
        chunk_texts = [chunk.page_content for chunk in chunks]
        logger.info(f"Document split into {len(chunk_texts)} chunks")
        
        # Process each chunk
        processed_chunks = []
        for i, chunk_text in enumerate(chunk_texts):
            log_chunk_processing(i+1, len(chunk_texts), "Starting")
            logger.debug(f"Chunk {i+1} content length: {len(chunk_text)} characters")
            
            # Process chunk with ReAct approach
            chunk_result = self._process_chunk_simple(chunk_text, i)
            if chunk_result:
                processed_chunks.append(chunk_result)
                objects_count = len(chunk_result.get("objects", []))
                log_chunk_processing(i+1, len(chunk_texts), f"Completed - {objects_count} objects extracted")
            else:
                log_chunk_processing(i+1, len(chunk_texts), "Failed")
        
        # Merge all results
        log_agent_step("Merging chunk results", {"chunks_count": len(processed_chunks)})
        merged_stix = self._merge_chunk_results(processed_chunks)
        logger.info(f"Merged STIX Bundle contains {len(merged_stix.get('objects', []))} objects")
        
        # Verify consistency
        log_agent_step("Verifying consistency with original document")
        verification = self._verify_consistency_simple(document_content, merged_stix)
        logger.debug(f"Verification result: {verification[:200]}...")
        
        return STIXConverter.format_stix_output(merged_stix)
    
    def _process_chunk_simple(self, chunk_text: str, chunk_index: int) -> dict:
        """Process a single chunk using simplified ReAct approach."""
        chunk_prompt = f"""从以下文档块中提取 STIX 2.1 对象：

{chunk_text}

请按步骤思考，必须提取所有类型的威胁情报：

1. **指标 (Indicator)**: IP地址、域名、文件哈希、URL等可观察指标
2. **攻击模式 (Attack-Pattern)**: 攻击技术、MITRE ATT&CK技术（如T1190、T1059等）
3. **恶意软件 (Malware)**: 恶意软件名称、类型、功能描述
4. **漏洞 (Vulnerability)**: CVE编号、漏洞描述、严重程度
5. **威胁行为者 (Threat-Actor)**: 攻击者信息、组织、动机
6. **关系 (Relationship)**: 对象之间的关联关系（uses、targets、indicates等）

重要要求：
- 不要只提取 indicator，必须识别并提取所有相关类型的对象
- 如果文档提到攻击技术（如SQL注入、XSS、文件上传等），必须创建 attack-pattern 对象
- 如果文档提到恶意软件或工具，必须创建 malware 对象
- 如果文档提到漏洞或CVE，必须创建 vulnerability 对象
- 所有描述性字段（name、description 等）必须使用中文
- 创建对象之间的关系（relationship）以连接相关对象

输出有效的 STIX 2.1 Bundle。如需要格式指导，可使用 search_stix_reference 工具。
仅输出有效的 JSON，不要包含其他文本。"""
        
        # Add Chinese output requirement to system message
        system_hints = STIXConverter.get_stix_schema_hints()
        system_message_content = f"""{system_hints}

重要提示：
- **必须提取所有类型的 STIX 对象**：indicator、attack-pattern、malware、vulnerability、threat-actor、relationship
- 不要只提取 indicator，必须全面分析文档中的所有威胁情报元素
- 所有描述性字段（name、description、labels 等）必须使用中文
- STIX 对象的结构和字段名保持英文（符合 STIX 标准）
- 但字段值中的描述性内容应使用中文
- 对于攻击技术，必须创建 attack-pattern 对象并包含 MITRE ATT&CK 引用（如果适用）
- 对于恶意软件，必须创建 malware 对象
- 对于漏洞，必须创建 vulnerability 对象并包含 CVE 引用（如果适用）
"""
        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=chunk_prompt)
        ]
        
        # Run with tool support
        max_iterations = 5
        logger.debug(f"Processing chunk {chunk_index + 1}, max iterations: {max_iterations}")
        for iteration in range(max_iterations):
            logger.debug(f"Chunk {chunk_index + 1} iteration {iteration + 1}/{max_iterations}")
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)
            
            if hasattr(response, "tool_calls") and response.tool_calls:
                logger.debug(f"Tool calls detected: {len(response.tool_calls)}")
                # Execute tools manually
                tool_messages = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    log_tool_call(tool_name, tool_args)
                    
                    # Find and execute the tool
                    for tool in self.tools:
                        if tool.name == tool_name:
                            try:
                                result = tool.invoke(tool_args)
                                log_tool_call(tool_name, tool_args, str(result)[:200])
                                from langchain_core.messages import ToolMessage
                                tool_messages.append(ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_call.get("id", "")
                                ))
                            except Exception as e:
                                logger.error(f"Tool {tool_name} execution failed: {e}")
                                from langchain_core.messages import ToolMessage
                                tool_messages.append(ToolMessage(
                                    content=f"Error: {str(e)}",
                                    tool_call_id=tool_call.get("id", "")
                                ))
                            break
                
                messages.extend(tool_messages)
            else:
                # Got final response
                logger.debug(f"Chunk {chunk_index + 1} processing completed")
                break
        
        # Extract STIX JSON
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                stix_json = self._extract_stix_json(msg.content)
                if stix_json:
                    try:
                        return json.loads(stix_json)
                    except:
                        pass
        
        return None
    
    def _merge_chunk_results(self, processed_chunks: List[dict]) -> dict:
        """Merge chunk results into single STIX Bundle."""
        all_objects = []
        seen_ids = set()
        
        for chunk_result in processed_chunks:
            if isinstance(chunk_result, dict):
                objects = chunk_result.get("objects", [])
                for obj in objects:
                    obj_id = obj.get("id")
                    if obj_id and obj_id not in seen_ids:
                        all_objects.append(obj)
                        seen_ids.add(obj_id)
        
        return {
            "type": "bundle",
            "id": f"bundle--merged-{len(all_objects)}-objects",
            "spec_version": "2.1",
            "objects": all_objects
        }
    
    def _verify_consistency_simple(self, original: str, merged_stix: dict) -> str:
        """Verify merged STIX is consistent with original."""
        verify_prompt = f"""Verify that the merged STIX output captures all important information from the original document.

Original document ({len(original)} characters):
{original[:2000]}...

Merged STIX Bundle contains {len(merged_stix.get('objects', []))} objects:
{json.dumps(merged_stix, indent=2)[:1000]}...

Check if all important information is captured. Respond with a brief summary."""
        
        response = self.llm.invoke([HumanMessage(content=verify_prompt)])
        return response.content if hasattr(response, "content") else str(response)

