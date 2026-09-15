from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from src.agent_tools import (
    query_telemetry_db,
    fetch_corridor_conditions,
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


tools = [
    query_telemetry_db,
    fetch_corridor_conditions,
]


def build_graph(llm):
    """
    Build the Cold-Chain Logistics AI workflow.

    Flow:

        START
          ↓
       Reasoner
          ↓
      Tool needed?
       ↙       ↘
    Tools       END
       ↓
     Reasoner
       ↓
      END
    """

    llm_with_tools = llm.bind_tools(tools)

    def reasoner(state: AgentState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("reasoner", reasoner)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "reasoner")

    graph_builder.add_conditional_edges(
        "reasoner",
        tools_condition,
    )

    graph_builder.add_edge("tools", "reasoner")

    graph_builder.add_edge("reasoner", END)

    return graph_builder.compile()