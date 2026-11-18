# 毕业设计 M3 第 1 步：Agent 循环接进 8003（端口 8003 的 /ask_graph 用这张图）。
# 这张图就是你第 6 课那张图的毕业设计版，只改了两处：
#   1. 工具从 3 个本地小工具变成 1 个：search_kb，调 8002 现成的 /vector_search
#      （混合检索 + 查询重写，不用再写检索逻辑）。
#   2. 模型节点会数查了几轮：查满 2 轮就改用不绑工具的模型，只能回答不能再查——
#      循环就停了，不会无限查下去。
# 记忆（MemorySaver + thread_id）沿用第 6 课的做法：同一 thread 记得住，换 thread 记不住。
# 服务重启后记忆清空（内存存档），和第 6 课一样。
# 8001、8002 不动；不用装新包。

# 引用的包（每个包是干嘛的）：
import os  # 读环境变量：DeepSeek key 和检索服务地址
import httpx  # 发 HTTP 请求：调 8002 的 /vector_search
from typing import Annotated, TypedDict  # TypedDict：定义图的状态结构；Annotated：给 messages 加累加规则
from langchain_openai import ChatOpenAI  # 调 DeepSeek 的 LangChain 客户端（第 6 课同款）
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  # 消息类型：人问的、系统指令、模型回的
from langchain_core.tools import tool as langchain_tool  # @tool 装饰器：把普通函数变成模型能调的工具
from langgraph.graph import StateGraph, START  # 建图：节点 + 边
from langgraph.graph.message import add_messages  # messages 字段的累加规则：新消息追加，不覆盖旧的
from langgraph.prebuilt import ToolNode, tools_condition  # ToolNode：执行工具的节点；tools_condition：模型调了工具就走 tools 节点，否则结束
from langgraph.checkpoint.memory import MemorySaver  # 内存存档：按 thread_id 存对话历史

RETRIEVAL_URL = os.environ.get("RETRIEVAL_URL", "http://127.0.0.1:8002")  # 环境变量优先：本地跑默认 8002，Docker 里 compose 传服务名
MAX_SEARCH_ROUNDS = 2  # 最多查几轮：超过就强制回答，不再查
TOP_K = 3  # 每轮查回几块

# 系统指令：每次调模型都在消息前面加上它（不存进历史，只当次生效）。
# 告诉模型三件事：只能根据查到的块回答、答之前先判够不够、答的时候标出来源。
SYSTEM_PROMPT = (
    "你是企业运维知识库的问答助手。你只有一个工具 search_kb，用来查知识库。\n"
    "工作流程：先用 search_kb 查一次，看查回来的块够不够回答问题。\n"
    "不够就换个问法再查一轮（最多查 2 轮）；够了就根据块写答案。\n"
    "回答规则：只根据查到的块回答，块里没有答案就直说不知道，不要编造；"
    "答案里标出来源，格式是 [文档 doc_id 块 chunk_id]。"
)


@langchain_tool
def search_kb(query: str) -> str:
    """在运维知识库里检索相关内容。输入一个查询问题，返回最相关的 3 个文档块。
    如果返回的块答不上用户的问题，换个问法再调一次这个工具（最多 2 轮）。"""
    try:
        resp = httpx.post(
            RETRIEVAL_URL + "/vector_search",
            json={"q": query, "top_k": TOP_K, "rewrite": True},
            timeout=120.0,  # 改写要调一次 DeepSeek，留足时间
        )
        resp.raise_for_status()
    except Exception as e:  # 检索服务没起、超时、报错：不抛异常，返回一句话，让模型自己决定是再试还是认不知道
        return f"检索服务暂时不可用（{type(e).__name__}），请稍后再试。"
    data = resp.json()
    if not data["results"]:
        return "没查到相关块，换个问法再试一次。"
    lines = [f"改写后问题：{data.get('rewritten_query', query)}"]
    for i, r in enumerate(data["results"]):
        lines.append(
            f"[来源 {i}] 文档 {r['doc_id']} 块 {r['chunk_id']}（分数 {r['score']}）\n"
            f"{r['text'].strip()[:500]}"
        )
    return "\n\n".join(lines)


class GraphState(TypedDict):
    # 图的状态：只有消息列表。新消息靠 add_messages 追加，旧的不会被覆盖——记忆就是这么来的。
    messages: Annotated[list, add_messages]


llm = ChatOpenAI(
    model="deepseek-flash",
    base_url="https://api.deepseek.com",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    temperature=0,
)
llm_with_tools = llm.bind_tools([search_kb])  # 绑上工具的模型：能决定调不调 search_kb


def count_searches(messages):
    """数一数这轮对话里已经调了几次 search_kb（看 AI 消息里的 tool_calls）。"""
    n = 0
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            n += sum(1 for tc in m.tool_calls if tc.get("name") == "search_kb")
    return n


def model_node(state: GraphState):
    """模型节点：查满 2 轮就改用不绑工具的模型（只能回答，不能再查），否则用绑了工具的模型。
    系统指令每次都加在最前面，但不存进历史。"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    if count_searches(state["messages"]) >= MAX_SEARCH_ROUNDS:
        reply = llm.invoke(messages)
    else:
        reply = llm_with_tools.invoke(messages)
    return {"messages": [reply]}


builder = StateGraph(GraphState)
builder.add_node("model", model_node)
builder.add_node("tools", ToolNode([search_kb]))
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition)  # 模型调了工具 → tools 节点；没调 → 结束
builder.add_edge("tools", "model")
# 只编译一次，放在模块层：每次请求都重新 compile 会连 MemorySaver 一起重建，记忆就丢了（第 6 课的坑）。
graph_app = builder.compile(checkpointer=MemorySaver())


def run_agent(question: str, thread_id: str = "default"):
    """跑一轮问答：返回 (答案, 查了几轮)。thread_id 相同就是同一轮对话，记得住上文。"""
    result = graph_app.invoke(
        {"messages": [HumanMessage(question)]},
        {"configurable": {"thread_id": thread_id}, "recursion_limit": 10},
    )
    rounds = count_searches(result["messages"])
    return result["messages"][-1].content, rounds
