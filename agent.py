"""LangGraph Agent for STIX conversion."""
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from vector_store import STIXVectorStore
from stix_converter import STIXConverter
from react_agent import ReActSTIXAgent
from config import QWEN_API_KEY, QWEN_BASE_URL, LLM_MODEL, TEMPERATURE, MAX_ITERATIONS


class AgentState(TypedDict):
    """State of the agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input_document: str
    stix_output: str
    iteration_count: int


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
    return vector_store.get_relevant_context(query, k=5)


@tool
def validate_stix_output(stix_json: str) -> str:
    """Validate STIX JSON output against STIX 2.1 standards.
    
    Args:
        stix_json: The STIX JSON string to validate.
    
    Returns:
        Validation result message.
    """
    try:
        import json
        stix_data = json.loads(stix_json)
        is_valid, error = STIXConverter.validate_stix_json(stix_data)
        if is_valid:
            return "STIX JSON is valid."
        else:
            return f"STIX JSON validation failed: {error}"
    except json.JSONDecodeError as e:
        return f"Invalid JSON format: {str(e)}"


class STIXAgent:
    """LangGraph Agent for converting penetration test cases to STIX format."""
    
    def __init__(self):
        """Initialize the agent."""
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
            temperature=TEMPERATURE,
        )
        self.tools = [search_stix_reference, validate_stix_output]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_agent)
        workflow.add_node("tools", self.tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow
    
    def _call_agent(self, state: AgentState) -> AgentState:
        """Call the agent with current state."""
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        iteration_count = state.get("iteration_count", 0) + 1
        return {
            "messages": [response],
            "iteration_count": iteration_count
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if the agent should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check iteration limit
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= MAX_ITERATIONS:
            return "end"
        
        # If the last message has tool calls, continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        return "end"
    
    def convert_to_stix(self, document_content: str, document_metadata: dict = None, use_react: bool = False) -> str:
        """Convert document content to STIX format.
        
        Args:
            document_content: The content of the penetration test case document.
            document_metadata: Optional metadata about the document.
            use_react: If True, use ReAct agent with text splitting for large documents.
        
        Returns:
            STIX JSON string.
        """
        # For large documents, use ReAct agent with text splitting
        if use_react or len(document_content) > 3000:
            print("[INFO] Using ReAct agent with text splitting for large document...")
            react_agent = ReActSTIXAgent()
            return react_agent.convert_to_stix(document_content, document_metadata)
        # Initialize vector store if needed
        try:
            vector_store.initialize()
        except Exception as e:
            print(f"Warning: Could not initialize vector store: {e}")
            # If vector store fails to initialize, try to continue without it
            # The agent can still work, just without STIX reference search capability
            import traceback
            traceback.print_exc()
        
        # Build system prompt
        system_prompt = f"""You are an expert STIX 2.1 format converter. Your task is to convert penetration test case information into strictly compliant STIX 2.1 JSON format.

{STIXConverter.get_stix_schema_hints()}

Instructions:
1. Analyze the provided penetration test case document
2. Extract relevant threat intelligence information (indicators, attack patterns, vulnerabilities, etc.)
3. Use the search_stix_reference tool to look up STIX format requirements when needed
4. Generate STIX 2.1 compliant JSON output
5. Use validate_stix_output tool to verify your output before finalizing
6. Output ONLY valid STIX 2.1 JSON, no additional text or explanations

The output must be a valid STIX 2.1 Bundle containing one or more STIX objects.
All timestamps must be in ISO 8601 format.
All IDs must follow STIX UUID format: <type>--<UUID v4>
"""

        # Build initial messages
        user_prompt = f"""Convert the following penetration test case into STIX 2.1 format:

{document_content}

{('Document metadata: ' + str(document_metadata)) if document_metadata else ''}

Please extract all relevant threat intelligence and create a STIX 2.1 Bundle with appropriate objects.
Remember to:
- Use proper STIX object types (indicator, attack-pattern, malware, etc.)
- Include all required fields (type, id, created, modified, spec_version)
- Use valid STIX patterns for indicators
- Create relationships between related objects
- Validate your output before returning
"""

        initial_state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ],
            "input_document": document_content,
            "stix_output": "",
            "iteration_count": 0
        }
        
        # Run the agent
        final_state = self.app.invoke(initial_state)
        
        # Extract STIX output from the final message
        messages = final_state["messages"]
        last_message = messages[-1]
        
        # Try to extract JSON from the response
        if isinstance(last_message, AIMessage):
            content = last_message.content
            # Try to find JSON in the content
            import json
            import re
            
            # Look for JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    stix_json = json_match.group(0)
                    # Validate it's proper JSON
                    json.loads(stix_json)
                    return STIXConverter.format_stix_output(json.loads(stix_json))
                except:
                    pass
            
            # If no JSON found, return the content as-is (might be in the message)
            return content
        
        return "Error: Could not extract STIX output from agent response."

