"""LangChain ReAct agent initialisation and execution."""

import logging

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from rag_manager import RAGManager

logger = logging.getLogger(__name__)

# System prompt injected into every agent invocation
SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on uploaded company documents.\n\n"
    "Use the search_documents tool to find relevant information from uploaded documents "
    "when answering questions. Always base your answers on the retrieved document content "
    "and provide clear, accurate responses."
)


class AgentManager:
    """Initialises and runs the LangGraph ReAct agent with RAG capabilities.

    The agent is given a single tool — search_documents — that performs
    similarity search against the in-memory vector store maintained by
    RAGManager.
    """

    def __init__(self, rag_manager: RAGManager, model: ChatOpenAI) -> None:
        self.rag_manager = rag_manager
        self.model = model
        self.agent = None
        self._setup_tools()
        self._initialize_agent()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """True when the agent has been successfully initialised."""
        return self.agent is not None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _setup_tools(self) -> None:
        """Define and register tools available to the agent."""

        # The @tool decorator must reference self via closure, so the
        # function is defined inside the method.
        @tool
        def search_documents(query: str) -> str:
            """Search through uploaded documents for relevant information."""
            documents = self.rag_manager.retrieve_data_from_vector_store(query)
            if not documents:
                return "No relevant documents found or no documents have been uploaded yet."

            results = []
            for i, doc in enumerate(documents, 1):
                source = doc.metadata.get("source", "Unknown source")
                # Truncate each chunk to keep the tool response concise
                content = doc.page_content.strip()[:500]
                results.append(f"Document {i} (Source: {source}):\n{content}...")

            return "\n\n".join(results)

        self.tools = [search_documents]
        logger.debug("Agent tools registered: %s", [t.name for t in self.tools])

    def _initialize_agent(self) -> None:
        """Create the LangGraph ReAct agent with the configured model and tools."""
        try:
            self.agent = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=SYSTEM_PROMPT,
            )
            logger.info("Agent initialised successfully")
        except Exception as exc:
            logger.exception("Failed to initialise agent: %s", exc)
            self.agent = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_stream(self, user_message: str) -> str:
        """Run the agent on *user_message* and return the final text response.

        Streams incremental updates from LangGraph and collects only the
        agent's final reply (ignoring intermediate tool-call messages).

        Args:
            user_message: The user's question or instruction.

        Returns:
            The agent's text response, or a fallback message if no content
            was produced.

        Raises:
            RuntimeError: If the agent is not initialised.
        """
        if not self.is_ready:
            raise RuntimeError("Agent is not initialised")

        response_parts: list[str] = []
        tool_calls_made: list[str] = []

        logger.info("Starting agent stream for message (length: %d)", len(user_message))
        print(f"\n[DEBUG agent] process_stream | message: {user_message!r}")

        for chunk in self.agent.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="updates",
        ):
            for step, data in chunk.items():

                if step == "agent" and "messages" in data:
                    last_msg = data["messages"][-1] if data["messages"] else None
                    if last_msg is None:
                        continue

                    has_tool_calls = bool(
                        getattr(last_msg, "tool_calls", None)
                    )

                    if has_tool_calls:
                        # Intermediate reasoning step — agent is invoking tools
                        tool_names = [
                            tc.get("name", "unknown") for tc in last_msg.tool_calls
                        ]
                        tool_calls_made.extend(tool_names)
                        logger.debug("Agent calling tools: %s", tool_names)
                        for tc in last_msg.tool_calls:
                            print(f"[DEBUG agent] tool_call | {tc.get('name')} | args: {tc.get('args')}")

                    elif getattr(last_msg, "content", None):
                        # Final response — no more tool calls pending
                        response_parts.append(last_msg.content)
                        logger.debug(
                            "Agent final response (length: %d)", len(last_msg.content)
                        )
                        print(f"[DEBUG agent] final_response_part | {last_msg.content[:300]!r}{'...' if len(last_msg.content) > 300 else ''}")

                elif step == "tools" and "messages" in data:
                    # Log tool execution results for observability
                    last_msg = data["messages"][-1] if data["messages"] else None
                    if last_msg and getattr(last_msg, "content", None):
                        content_str = str(last_msg.content)
                        logger.debug(
                            "Tool output received (%d chars)", len(content_str)
                        )
                        print(f"[DEBUG agent] tool_output | {len(content_str)} chars | {content_str[:400]!r}{'...' if len(content_str) > 400 else ''}")

        if response_parts:
            return "\n\n".join(response_parts)

        if tool_calls_made:
            logger.warning(
                "Agent called tools %s but produced no final response",
                set(tool_calls_made),
            )
            return (
                f"I searched your documents using: {', '.join(set(tool_calls_made))}. "
                "However, I couldn't generate a final response. "
                "Please try rephrasing your question."
            )

        logger.warning("Agent stream completed with no response and no tool calls")
        return "I processed your request but didn't generate a response. Please try asking in a different way."
