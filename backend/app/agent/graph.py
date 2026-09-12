from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from app.agent.tools import get_unread_emails, get_todays_schedule

tools = [get_unread_emails, get_todays_schedule]
tool_node = ToolNode(tools)

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: MessagesState):
    system_prompt = SystemMessage(
        content="You are Jerry, a highly capable executive assistant. "
                "When calling tools, always pass the user_id provided in the execution context/metadata."
    )
    return {"messages": [llm_with_tools.invoke([system_prompt] + state["messages"])]}

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(MessagesState)
workflow.add_node("chatbot", chatbot)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "chatbot")
workflow.add_conditional_edges("chatbot", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "chatbot")

agent_app = workflow.compile()
