"""Agent Manager for LangChain agent initialization and management"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from rag_manager import RAGManager


class AgentManager:
    """
    Manages LangChain agent initialization and tool definitions
    Handles agent creation with RAG capabilities
    """
    
    def __init__(self, rag_manager: RAGManager, model: ChatOpenAI):
        """
        Initialize the agent manager
        
        Args:
            rag_manager: RAGManager instance for document retrieval
            model: ChatOpenAI model instance
        """
        self.rag_manager = rag_manager
        self.model = model
        self.agent = None
        self._setup_tools()
        self.initialize()
    
    def _setup_tools(self):
        """Setup tools for the agent"""
        @tool
        def search_documents(query: str) -> str:
            """Search through uploaded documents for relevant information."""
            documents = self.rag_manager.retrieve_data_from_vector_store(query, k=3)
            if not documents:
                return "No relevant documents found or no documents have been uploaded yet."
            
            # Format the results
            results = []
            for i, doc in enumerate(documents, 1):
                source = doc.metadata.get('source', 'Unknown source')
                content = doc.page_content.strip()[:500]  # Limit content length
                results.append(f"Document {i} (Source: {source}):\n{content}...")
            
            return "\n\n".join(results)
        
        self.tools = [search_documents]
    
    def initialize(self):
        """Initialize the agent with tools and model"""
        try:
            # Create the agent with the new API
            system_prompt = """You are a helpful assistant that can search through uploaded documents to answer questions.
            
Use the search_documents tool to find relevant information from uploaded documents when answering questions.
Always provide clear and helpful answers based on the documents available."""
            
            self.agent = create_agent(
                model=self.model,
                tools=self.tools,
                system_prompt=system_prompt
            )
            print("Agent initialized successfully")
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")
            self.agent = None
    
    def get_agent(self):
        """Get the initialized agent"""
        return self.agent
    
    def process_stream(self, user_message: str) -> str:
        """
        Process agent streaming response
        
        Args:
            user_message: User's input message
        
        Returns:
            Agent's response text
        """
        response_parts = []
        tool_calls_info = []
        
        # Stream the agent response directly from agent
        for chunk in self.agent.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="updates",
        ):
            for step, data in chunk.items():
                print(f"step: {step}")
                
                # Process agent messages
                if step == "agent" and "messages" in data:
                    messages = data["messages"]
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content') and last_message.content:
                            response_parts.append(last_message.content)
                            print(f"Agent: {last_message.content}")
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            tool_names = [tc.get('name', 'unknown') for tc in last_message.tool_calls]
                            tool_calls_info.extend(tool_names)
                            print(f"Calling tools: {tool_names}")
                
                # Handle tool execution output
                elif step == "tools" and "messages" in data:
                    messages = data["messages"]
                    if messages:
                        tool_output = str(messages[-1].content) if hasattr(messages[-1], 'content') else ""
                        print(f"Tool output received: {len(tool_output)} characters")
        
        # Combine response parts
        if response_parts:
            return " ".join(response_parts)
        elif tool_calls_info:
            return f"I searched through your documents using tools: {', '.join(set(tool_calls_info))}. However, I didn't generate a final response. Please try rephrasing your question."
        else:
            return "I processed your request but didn't generate a response. Please try asking your question in a different way."
