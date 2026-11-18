# 第 9 课第 1 步搭的 Agent 服务（端口 8003）——拥有大模型调用。
# 检索不再是本地函数调用，改成 HTTP 问检索服务（8002）；
# /ask_tool 里的三个工具也不再是本地函数，改成 HTTP 问文档服务（8001）。
# M3 第 1 步：/ask_graph 改走毕业设计的 capstone_graph.py（第 6 课那张图的 M3 版：
# 工具只剩 1 个 search_kb，调 8002 的 /vector_search；最多查 2 轮）。
# /ask、/ask_stream、/ask_tool 都没动。
import json
import os  # 读环境变量：服务地址默认 localhost，Docker 里 compose 传服务名
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag_core import client, tools
from capstone_graph import run_agent  # M3 第 1 步：/ask_graph 走毕业设计的图（原来是第 6 课的 agent_graph.py）

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
def ask_graph(req: GraphAskIn):
    try:
        answer, search_rounds = run_agent(req.question, req.session_id)
        return {"question": req.question, "session_id": req.session_id, "answer": answer, "search_rounds": search_rounds}
    except Exception as e:
        print("ask_graph 调用失败:", type(e).__name__, e)
        return {"question": req.question, "session_id": req.session_id, "answer": "外部服务暂时不可用，请稍后重试", "search_rounds": 0}
