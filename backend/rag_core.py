# 第 9 课第 1 步：三个服务共用的核心代码。
# 从你 11-10 的 app.py 里原样抽出来，只改了一处：向量改成第一次用时才算（懒加载），
# 不然三个服务启动时各算 4 次 embedding，白白烧 3 倍 token。
import os, math
from openai import OpenAI
from chunk_search import load_text, chunk_text, search  # search 是转给检索服务用的

text = load_text("sample.txt")
chunks = chunk_text(text)

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

embed_client = OpenAI(
    api_key=os.environ.get("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

def embed(text):
    resp = embed_client.embeddings.create(model="BAAI/bge-m3", input=text)
    return resp.data[0].embedding

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)

def get_doc_stats():
    return {"total_chars": len(text), "num_chunks": len(chunks)}

def get_chunk_lengths():
    return {"lengths": [len(c) for c in chunks]}

def count_keyword(keyword):
    return {"keyword": keyword, "count": text.count(keyword)}

_chunk_vecs = None

def get_chunk_vecs():
    global _chunk_vecs
    if _chunk_vecs is None:
        _chunk_vecs = [embed(c) for c in chunks]
    return _chunk_vecs

SIM_THRESHOLD = 0.4  # 及格线，等火星的分数出来再定

def vector_search(q, top_k=3):
    qv = embed(q)
    chunk_vecs = get_chunk_vecs()
    scored = sorted(
        ((cosine(qv, v), i) for i, v in enumerate(chunk_vecs)),
        reverse=True,
    )
    return [(s, i, chunks[i]) for s, i in scored[:top_k] if s >= SIM_THRESHOLD]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_doc_stats",
            "description": "查询当前文档的总字数和切块数量",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chunk_lengths",
            "description": "查询文档每一块各自的字符长度",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_keyword",
            "description": "统计某个关键词在文档中出现的次数",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string", "description": "要统计的词"}},
                "required": ["keyword"],
            },
        },
    },
]
