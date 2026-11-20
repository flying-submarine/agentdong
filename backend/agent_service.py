# 第 9 课第 1 步搭的 Agent 服务（端口 8003）——拥有大模型调用。
# 检索不再是本地函数调用，改成 HTTP 问检索服务（8002）；
# /ask_tool 里的三个工具也不再是本地函数，改成 HTTP 问文档服务（8001）。
# M3 第 1 步：/ask_graph 改走工作项目的 capstone_graph.py（第 6 课那张图的 M3 版：
# 工具只剩 1 个 search_kb，调 8002 的 /vector_search；最多查 2 轮）。
# M3 第 2 步：/ask_graph 返回结构化答案（refused / sources / confidence / answer），
# 拒答由图里的 finalize 节点按分数硬拦（最高分 < 0.5 就 refused）。
# /ask、/ask_stream、/ask_tool 都没动。
# M4 第 4 步：/ask_graph 加限流（每个 session 每分钟最多 10 次，超了 429）。
import json
import os  # 读环境变量：服务地址默认 localhost，Docker 里 compose 传服务名
import threading  # 锁（Lock）：多线程同时改限流计数时不打架
import time  # 取现在几点：算限流窗口开了多久
import httpx
from fastapi import FastAPI, HTTPException  # HTTPException：抛出去 FastAPI 自动变成对应状态码的 JSON 响应（429 就靠它）
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag_core import client, tools
from capstone_graph import run_agent, resume_agent, run_agent_stream  # M3 第 1 步：/ask_graph 走工作项目的图（原来是第 6 课的 agent_graph.py）；M3 第 4 步：resume_agent 续上被确认关卡冻住的图；M5 第 3 步：run_agent_stream 流式跑图

RETRIEVAL_URL = os.environ.get("RETRIEVAL_URL", "http://127.0.0.1:8002")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 retrieval-service
DOC_URL = os.environ.get("DOC_URL", "http://127.0.0.1:8001")  # 同上，Docker 里是 doc-service:8001

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    q: str = "RAG 是什么"

class ToolAskIn(BaseModel):
    question: str

class GraphAskIn(BaseModel):
    question: str
    session_id: str = "default"
    role: str | None = None  # 调用方角色（比如 "运维"）：只返回这个角色看得见的块；不给就只看公开的

class GraphConfirmIn(BaseModel):
    # M3 第 4 步：人确认删不删。session_id 必须和当时问的那次一样（图是按 thread_id 冻住的），
    # approved=True 放行去删，False 取消，文档还在。
    session_id: str = "default"
    approved: bool

# M4 第 4 步：限流（rate limiting，固定窗口计数 fixed window counter）。
# 每个 session 每分钟最多 RATE_LIMIT_N 次 /ask_graph，超了返回 429。
# 内存版：计数存在字典里，8003 重启就清零；单机有效。生产要持久化得用 Redis（你 11 月 16 日定的不用 Redis，这里先做内存版）。
# 两个老实边界：① 固定窗口在边界能 burst（第 59 秒刷满 10 次 + 下一分钟第 1 秒再刷 10 次），
# 生产升级用令牌桶（token bucket）或滑动窗口（sliding window）；② session_id 是调用方自己报的，换个 session 就绕过去——
# 这是按 session 公平，不是按用户鉴权；生产按登录用户 / API key 限。
RATE_LIMIT_N = 10  # 每个 session 每分钟最多几次
RATE_LIMIT_WINDOW = 60  # 窗口长度（秒）
_rate_counts = {}  # session_id -> [窗口开始时间, 这窗口里已用了几次]
_rate_lock = threading.Lock()  # 锁：同一时间只有一个线程能改 _rate_counts

def _check_rate_limit(session_id: str):
    # 查一次限流：返回 None = 放行；返回数字 = 超了，还要等几秒。
    # 每问一次就调一次，计数在放行时才加 1——超了的请求不占名额。
    now = time.time()
    with _rate_lock:
        window_start, count = _rate_counts.get(session_id, (now, 0))
        if now - window_start >= RATE_LIMIT_WINDOW:
            # 进了新的一分钟：窗口重开，计数清零，这次算第 1 次
            _rate_counts[session_id] = [now, 1]
            return None
        if count >= RATE_LIMIT_N:
            # 这窗口里已经用满了：告诉调用方还要等几秒（窗口剩多久 + 1，免得卡在边界上）
            return int(RATE_LIMIT_WINDOW - (now - window_start)) + 1
        _rate_counts[session_id] = [window_start, count + 1]
        return None

def retrieve(q, top_k=3):
    r = httpx.post(
        f"{RETRIEVAL_URL}/vector_search",
        json={"q": q, "top_k": top_k},
        timeout=30.0,
    )
    r.raise_for_status()
    data = r.json()
    return [(item["score"], item["chunk_id"], item["text"]) for item in data["results"]]

def _get_doc_stats():
    return httpx.get(f"{DOC_URL}/stats", timeout=10.0).json()

def _get_chunk_lengths():
    return httpx.get(f"{DOC_URL}/chunk_lengths", timeout=10.0).json()

def _count_keyword(keyword):
    return httpx.get(f"{DOC_URL}/count_keyword", params={"keyword": keyword}, timeout=10.0).json()

funcs = {
    "get_doc_stats": _get_doc_stats,
    "get_chunk_lengths": _get_chunk_lengths,
    "count_keyword": _count_keyword,
}

@app.get("/health")
def health():
    # 健康检查：服务活着就返回 ok，给部署和监控用（演示页的状态行也调它）。
    return {"status": "ok", "service": "agent-service"}

@app.post("/ask")
def do_ask(req: AskRequest):
    try:
        results = retrieve(req.q)
        if not results:
            return {"query": req.q, "answer": "资料里没找到相关内容，换个词试试", "sources": []}
        context = "\n\n".join(
            f"[块 {i}]\n{c.strip()[:500]}" for _, i, c in results
        )
        resp = client.chat.completions.create(
            model="deepseek-flash",
            messages=[
                {
                    "role": "system",
                    "content": "只根据下面提供的资料回答问题。资料里没有答案就直说不知道，不要编造。",
                },
                {"role": "user", "content": f"资料：\n{context}\n\n问题：{req.q}"},
            ],
        )
        return {
            "query": req.q,
            "answer": resp.choices[0].message.content,
            "sources": [i for _, i, _ in results],
        }
    except Exception as e:
        print("ask 调用失败:", type(e).__name__, e)
        return {"query": req.q, "answer": "外部服务暂时不可用，请稍后重试", "sources": []}

@app.post("/ask_stream")
def do_ask_stream(req: AskRequest):
    try:
        results = retrieve(req.q)
    except Exception as e:
        print("ask_stream 检索失败:", type(e).__name__, e)
        return {"query": req.q, "answer": "外部服务暂时不可用，请稍后重试", "sources": []}
    if not results:
        return {"query": req.q, "answer": "资料里没找到相关内容，换个词试试", "sources": []}

    context = "\n\n".join(
        f"[块 {i}]\n{c.strip()[:500]}" for _, i, c in results
    )
    sources = [i for _, i, _ in results]

    def gen():
        stream = client.chat.completions.create(
            model="deepseek-flash",
            messages=[
                {
                    "role": "system",
                    "content": "只根据下面提供的资料回答问题。资料里没有答案就直说不知道，不要编造。",
                },
                {"role": "user", "content": f"资料：\n{context}\n\n问题：{req.q}"},
            ],
            stream=True,
        )
        for chunk in stream:
            piece = chunk.choices[0].delta.content
            if piece:
                yield piece
        yield f"\n\n[来源块] {sources}"

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")

@app.post("/ask_tool")
def ask_tool(req: ToolAskIn):
    messages = [{"role": "user", "content": req.question}]
    for round_no in range(1, 6):
        resp = client.chat.completions.create(model="deepseek-flash", messages=messages, tools=tools)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {"answer": msg.content, "rounds": round_no}
        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = funcs[call.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})
    return {"answer": "工具调用轮数超限，换个问法试试", "rounds": 5}

@app.post("/ask_graph")
async def ask_graph(req: GraphAskIn):
    # M4 第 4 步：先查限流再调模型——超了的请求不花模型钱，直接 429。
    # M5 第 3 步改 async：run_agent 改 async 后，接口也得 async + await。
    wait = _check_rate_limit(req.session_id)
    if wait is not None:
        raise HTTPException(status_code=429, detail=f"请求太频繁，{wait} 秒后再试", headers={"Retry-After": str(wait)})
    try:
        ans, search_rounds, waiting = await run_agent(req.question, req.session_id, req.role)
        if waiting is not None:
            # 图冻在确认关卡了：还没答案，先把要删的文档号告诉人，等 /ask_graph/confirm 回话。
            return {"question": req.question, "session_id": req.session_id, "status": "waiting_confirm", "confirm": waiting, "answer": "", "refused": False, "sources": [], "confidence": 0.0, "search_rounds": search_rounds, "role": req.role}
        return {"question": req.question, "session_id": req.session_id, "status": "done", "answer": ans.answer, "refused": ans.refused, "sources": ans.sources, "confidence": ans.confidence, "search_rounds": search_rounds, "role": req.role}
    except Exception as e:
        print("ask_graph 调用失败:", type(e).__name__, e)
        return {"question": req.question, "session_id": req.session_id, "status": "done", "answer": "外部服务暂时不可用，请稍后重试", "refused": False, "sources": [], "confidence": 0.0, "search_rounds": 0}

@app.post("/ask_graph_stream")
async def ask_graph_stream(req: GraphAskIn):
    # M5 第 3 步：流式问答（SSE）。和 /ask_graph 同一条图、同一套限流，只是答案一个 token 一个 token 往外吐。
    # 限流先查——超了直接 429，不进流；流开始后再想拦就晚了。
    wait = _check_rate_limit(req.session_id)
    if wait is not None:
        raise HTTPException(status_code=429, detail=f"请求太频繁，{wait} 秒后再试", headers={"Retry-After": str(wait)})
    async def gen():
        # 第一行先告诉前端"正在检索"：第一个 token 之前还要跑改写+检索+精排，别让页面干等。
        yield 'data: {"type": "status", "text": "正在检索…"}\n\n'
        try:
            async for ev in run_agent_stream(req.question, req.session_id, req.role):
                yield "data: " + json.dumps(ev, ensure_ascii=False) + "\n\n"
        except Exception as e:
            print("ask_graph_stream 调用失败:", type(e).__name__, e)
            yield 'data: {"type": "error", "text": "外部服务暂时不可用，请稍后重试"}\n\n'
    # X-Accel-Buffering: no 是告诉 Nginx 别缓冲这条流（Nginx 配置里也要加 proxy_buffering off，双保险）。
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/ask_graph/confirm")
async def confirm_graph(req: GraphConfirmIn):
    # M3 第 4 步：续上冻住的图。approved=True 放行去删，False 取消。
    # 每次 curl 都是一个新连接，所以"隔一会儿再确认"本身就是断开再续上的验证——冻住的状态存在 MemorySaver 里，8003 不重启就一直在。
    # 不限流：确认不调模型，冻住的图等不起——限了确认，删一半的流程会被卡住。
    # M5 第 3 步改 async：resume_agent 改 async 后，接口也得 async + await。
    try:
        ans, search_rounds, waiting = await resume_agent(req.session_id, req.approved)
        if waiting is not None:
            return {"session_id": req.session_id, "status": "waiting_confirm", "confirm": waiting, "answer": "", "refused": False, "sources": [], "confidence": 0.0, "search_rounds": search_rounds}
        if ans is None:
            return {"session_id": req.session_id, "status": "done", "answer": "确认流程异常，请重试", "refused": False, "sources": [], "confidence": 0.0, "search_rounds": search_rounds}
        return {"session_id": req.session_id, "status": "done", "answer": ans.answer, "refused": ans.refused, "sources": ans.sources, "confidence": ans.confidence, "search_rounds": search_rounds}
    except Exception as e:
        print("ask_graph/confirm 调用失败:", type(e).__name__, e)
        return {"session_id": req.session_id, "status": "done", "answer": "外部服务暂时不可用，请稍后重试", "refused": False, "sources": [], "confidence": 0.0, "search_rounds": 0}
