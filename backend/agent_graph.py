import config  # noqa: F401 —— 自动加载 .env 里的密钥（见 config.py）
import os
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from chunk_search import chunk_text

text = open("sample.txt", encoding="utf-8").read()
chunks = chunk_text(text)

@tool
def get_doc_stats() -> dict:
    """返回文档的总字数和切块数量"""
    return {"total_chars": len(text), "num_chunks": len(chunks)}

@tool
def get_chunk_lengths() -> dict:
    """返回每个文本块的长度列表"""
    return {"lengths": [len(c) for c in chunks]}

@tool
def count_keyword(keyword: str) -> dict:
    """统计某个关键词在文档中出现的次数"""
    return {"keyword": keyword, "count": text.count(keyword)}

tools = [get_doc_stats, get_chunk_lengths, count_keyword]

llm = ChatOpenAI(model="deepseek-flash", base_url="https://api.deepseek.com",
                 api_key=os.environ["DEEPSEEK_API_KEY"], temperature=0)
llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def model_node(state: State):
    reply = llm_with_tools.invoke(state["messages"])
    return {"messages": [reply]}

graph = StateGraph(State)
graph.add_node("model", model_node)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "model")
graph.add_conditional_edges("model", tools_condition)
graph.add_edge("tools", "model")
agent = graph.compile(checkpointer=MemorySaver())

def run_agent(question: str, session_id: str = "default") -> str:
    config = {"configurable": {"thread_id": session_id}, "recursion_limit": 10}
    result = agent.invoke({"messages": [HumanMessage(question)]}, config)
    return result["messages"][-1].content



