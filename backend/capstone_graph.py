# 毕业设计 M3 第 3 步修复版：结构化输出 + 拒答阈值 + 记忆（端口 8003 的 /ask_graph 用这张图）。
# 在第 2 步的图上只改了一处：
#   count_searches 只数【本轮】的 search_kb 调用，不数整个 thread 的累计次数。
#   旧版 bug：第一轮用了 2 轮，第二轮一开始 count 就已经是 2，模型节点直接改用不绑工具的模型，
#   第二轮根本不查，best_score 还是 0.0，收尾节点就拒答。
#   这就是 m3s3-clean 里 CNCF 追问被拒的根因：不是检索不行，是第二轮根本没查。
#   直接调 8002 验证过：显式问 0.9839、代词问 0.9612，都过 0.5 线；新会话显式问 1 轮就答对。
# 8001、8002 不动；不用装新包.

# 引用的包（每个包是干嘛的）：
import os  # 读环境变量：DeepSeek key 和检索服务地址
import re  # 正则：从工具结果里抠出"分数 0.9487"这样的数字
import httpx  # 发 HTTP 请求：调 8002 的 /vector_search
from typing import Annotated, TypedDict  # TypedDict：定义图的状态结构；Annotated：给 messages 加累加规则
from pydantic import BaseModel, ConfigDict, Field, field_validator  # 定义 RagAnswer 结构 + 进来先归一化的校验器
from langchain_openai import ChatOpenAI  # 调 DeepSeek 的 LangChain 客户端（第 6 课同款）
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage  # 消息类型：人问的、系统指令、模型回的、工具回的
from langchain_core.tools import tool as langchain_tool  # @tool 装饰器：把普通函数变成模型能调的工具
from langgraph.graph import StateGraph, START, END  # 建图：节点 + 边
from langgraph.graph.message import add_messages  # messages 字段的累加规则：新消息追加，不覆盖旧的
from langgraph.prebuilt import ToolNode, tools_condition  # ToolNode：执行工具的节点；tools_condition：模型调了工具就走 tools 节点，否则走收尾
from langgraph.checkpoint.memory import MemorySaver  # 内存存档：按 thread_id 存对话历史

RETRIEVAL_URL = os.environ.get("RETRIEVAL_URL", "http://127.0.0.1:8002")  # 环境变量优先：本地跑默认 8002，Docker 里 compose 传服务名
MAX_SEARCH_ROUNDS = 2  # 最多查几轮：超过就强制回答，不再查
TOP_K = 3  # 每轮查回几块
REFUSAL_THRESHOLD = 0.5  # 拒答线：精排最高分低于它就 refused（M2 评测用的同一条线）

# 系统指令（查的循环用）：每次调模型都在消息前面加上它（不存进历史，只当次生效）。
SYSTEM_PROMPT = (
    "你是企业运维知识库的问答助手。你只有一个工具 search_kb，用来查知识库。\n"
    "工作流程：先用 search_kb 查一次，看查回来的块够不够回答问题。\n"
    "不够就换个问法再查一轮（最多查 2 轮）；够了就等收尾节点出结构化答案。\n"
    "回答规则：只根据查到的块回答，块里没有答案也不要编造，交给收尾节点判 refused。"
)

# 收尾用的系统指令（结构化输出用）：只输出 JSON，不输出别的文字。
JSON_SYSTEM_PROMPT = (
    "你是一个 RAG 问答助手。只输出 JSON，字段只能是 answer（字符串）、"
    "sources（\"文档 id:块号\"组成的字符串数组，如 [\"bd1865bda758:7\"]）、"
    "confidence（0 到 1 的数字）、refused（true 或 false），不要输出其他字段和文字。"
    "资料里没有答案就 refused 填 true，其余字段空着就行。"
    "格式例子："
    '{"answer": "Prometheus 是一个系统监控和告警工具包。", '
    '"sources": ["d6fa599f2675:0"], "confidence": 0.9, "refused": false}'
)


def _to_confidence(v):
    """confidence 只认 0 到 1 的数字：null 当 0；"high/medium/low" 换成 0.9/0.5/0.2；数字字符串转数字。（第 8 课原样搬过来）"""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("high", "高"):
            return 0.9
        if s in ("medium", "中"):
            return 0.5
        if s in ("low", "低"):
            return 0.2
        try:
            return float(s)
        except ValueError:
            return 0.0
    return 0.0


def _to_source_id(v):
    """来源只认 "文档 id:块号"："bd1865bda758:7" 原样留；"块 7"、7 这种只有块号的也收下（第 8 课的老格式），
    但它分不清是哪个文档的——模型按提示词应该给带文档 id 的格式。"""
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        s = v.strip()
        if ":" in s:
            return s
        m = re.search(r"\d+", s)
        if m:
            return m.group()
    raise ValueError(f"解析不出来源：{v!r}")


class RagAnswer(BaseModel):
    """模型必须按这个结构回答案（第 8 课的 RagAnswer，改了一处：
    sources 从块号数字改成 "文档 id:块号" 字符串——第 8 课是单文档，块号就够；
    毕业设计 13 篇文档，只给块号会撞，分不清是哪篇的。
    answer/sources/confidence 都给了默认值——拒绝回答时它们本来就没意义；
    多余字段直接丢掉；confidence 和 sources 进来先归一化再校验。"""
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(default="", description="用检索到的资料回答问题")
    sources: list[str] = Field(default=[], description="答案依据的来源，只许填检索给你的块，格式是 文档 id:块号")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="0 到 1，对答案的把握")
    refused: bool = Field(default=False, description="资料里没有答案时填 true")

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_confidence(cls, v):
        return _to_confidence(v)

    @field_validator("sources", mode="before")
    @classmethod
    def _norm_sources(cls, v):
        if isinstance(v, list):
            return [_to_source_id(x) for x in v]
        return v


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
    # 图的状态：messages 是消息列表（新消息追加，旧的不覆盖——记忆就是这么来的）；
    # best_score 是本轮查到的最高精排分（只升不降），收尾节点拿它判拒答。
    messages: Annotated[list, add_messages]
    best_score: float


llm = ChatOpenAI(
    model="deepseek-flash",
    base_url="https://api.deepseek.com",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    temperature=0,
)
llm_with_tools = llm.bind_tools([search_kb])  # 绑上工具的模型：能决定调不调 search_kb
llm_json = ChatOpenAI(
    model="deepseek-flash",
    base_url="https://api.deepseek.com",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    temperature=0,
    response_format={"type": "json_object"},  # 只出 JSON：DeepSeek 只保证是合法 JSON，字段类型由下面的 RagAnswer 校验
)


def count_searches(messages):
    """数一数【本轮】已经调了几次 search_kb（看 AI 消息里的 tool_calls）。
    只数最后一条 HumanMessage（本轮问题）之后的调用，不数以前轮次的。
    旧版数的是整个 thread 的累计次数：第一轮用了 2 轮，第二轮一开始就以为已经查满 2 轮，
    模型节点直接改用不绑工具的模型，第二轮根本不查，best_score 还是 0.0，收尾节点就拒答。
    这就是 m3s3-clean 里 CNCF 追问被拒的根因。"""
    start = 0
    for i in range(len(messages) - 1, -1, -1):  # 从后往前找最后一条 HumanMessage（本轮问题）
        if isinstance(messages[i], HumanMessage):
            start = i
            break
    n = 0
    for m in messages[start:]:  # 只数本轮问题之后的 AI 消息
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            n += sum(1 for tc in m.tool_calls if tc.get("name") == "search_kb")
    return n


def model_node(state: GraphState):
    """模型节点：本轮查满 2 轮就改用不绑工具的模型（只能等收尾，不能再查），否则用绑了工具的模型。
    系统指令每次都加在最前面，但不存进历史。"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    if count_searches(state["messages"]) >= MAX_SEARCH_ROUNDS:
        reply = llm.invoke(messages)
    else:
        reply = llm_with_tools.invoke(messages)
    return {"messages": [reply]}


def score_node(state: GraphState):
    """读分节点：从最后一条工具消息里读本轮最高分，记进 best_score（只升不降）。
    工具返回的结果按分数从高到低排，第一个"分数"就是最高分；没查到或服务不可用就记 0。"""
    top = 0.0
    for m in reversed(state["messages"]):
        if isinstance(m, ToolMessage):
            found = re.findall(r"分数 ([0-9]*\.?[0-9]+)", m.content)
            if found:
                top = float(found[0])
            break
    return {"best_score": max(state.get("best_score", 0.0), top)}


def finalize_node(state: GraphState):
    """收尾节点：先按分数硬拦——最高分低于拒答线，直接出 refused，不用模型猜；
    分数够了才调模型，用 RagAnswer 结构出答案（模型自己觉得块不够也可以填 refused=true）。
    校验失败不炸服务：把模型原样打到日志里，回一个 refused，请人去日志里看原样。"""
    best = state.get("best_score", 0.0)
    if best < REFUSAL_THRESHOLD:
        ans = RagAnswer(refused=True, answer="知识库里没有相关内容，换个问法试试。", sources=[], confidence=0.0)
        return {"messages": [AIMessage(content=ans.model_dump_json())]}
    resp = llm_json.invoke([SystemMessage(content=JSON_SYSTEM_PROMPT)] + state["messages"])
    raw = resp.content
    try:
        ans = RagAnswer.model_validate_json(raw)
    except Exception as e:
        print("结构化输出校验失败:", type(e).__name__, e, "| 模型原样：", raw)
        ans = RagAnswer(refused=True, answer="回答生成失败，请重试。", sources=[], confidence=0.0)
    return {"messages": [AIMessage(content=ans.model_dump_json())]}


builder = StateGraph(GraphState)
builder.add_node("model", model_node)
builder.add_node("tools", ToolNode([search_kb]))
builder.add_node("score", score_node)
builder.add_node("finalize", finalize_node)
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition, {"tools": "tools", "__end__": "finalize"})  # 模型调了工具 → tools；没调 → 收尾
builder.add_edge("tools", "score")
builder.add_edge("score", "model")
builder.add_edge("finalize", END)
# 只编译一次，放在模块层：每次请求都重新 compile 会连 MemorySaver 一起重建，记忆就丢了（第 6 课的坑）。
graph_app = builder.compile(checkpointer=MemorySaver())


def run_agent(question: str, thread_id: str = "default"):
    """跑一轮问答：返回 (RagAnswer, 本轮查了几轮)。thread_id 相同就是同一轮对话，记得住上文。
    best_score 每问一次重新算（invoke 里传 0.0 盖掉上一轮的），不然上一轮的高分会让这轮的陷阱题蒙混过关。
    查了几轮现在也是本轮的数（count_searches 只数最后一条 HumanMessage 之后），不是整个 thread 的累计。"""
    result = graph_app.invoke(
        {"messages": [HumanMessage(question)], "best_score": 0.0},
        {"configurable": {"thread_id": thread_id}, "recursion_limit": 10},
    )
    rounds = count_searches(result["messages"])
    ans = RagAnswer.model_validate_json(result["messages"][-1].content)
    return ans, rounds
