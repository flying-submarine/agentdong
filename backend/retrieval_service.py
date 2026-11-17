# 第 9 课第 2 步：检索服务（端口 8002）——向量检索改连 Qdrant。
# 和第 1 步比只改了一处：/vector_search 不再算内存向量，改成问 Qdrant。
# Qdrant 里存的就是第 8 课写进去的那 4 块（collection 叫 docs，id 0-3），
# 所以 /vector_search 的返回形状、分数、chunk_id 都和第 1 步一模一样，验证的预期不变。
# 新入库的块由 worker 写进来，点的 id 是 uuid，chunk_id 和 doc_id 存在 payload 里——
# 所以这里 chunk_id 优先读 payload，读不到才回退到点的 id（老 4 块的 payload 里没有 chunk_id）。
# /search（关键词）这一步还没动，仍查内存里的 sample.txt——新入库的文档暂时查不到关键词结果，第 3 步再处理。
# 注意：启动前必须先起 Qdrant（docker compose up -d），起不来这个服务会在 import 时直接报错——这是故意的，错要错在明处。
import os  # 读环境变量：服务地址默认 localhost，Docker 里 compose 传服务名
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rag_core import embed, search, chunks, SIM_THRESHOLD

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 qdrant
COLLECTION = "docs"

qclient = QdrantClient(url=QDRANT_URL)

# 集合不存在就建一个（和第 8 课 qdrant_service_test.py 里建的一模一样：1024 维，余弦距离）。
if not qclient.collection_exists(COLLECTION):
    qclient.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VectorSearchIn(BaseModel):
    q: str = "RAG 是什么"
    top_k: int = 3

@app.post("/vector_search")
def do_vector_search(req: VectorSearchIn):
    qv = embed(req.q)
    hits = qclient.query_points(COLLECTION, query=qv, limit=req.top_k).points
    # 及格线还是第 1 步那个 0.4，过滤逻辑没变，只是从“自己算余弦”换成了“Qdrant 算好返回分数”。
    results = []
    for h in hits:
        if h.score < SIM_THRESHOLD:
            continue
        payload = h.payload or {}
        chunk_id = payload.get("chunk_id", h.id)
        results.append({
            "chunk_id": int(chunk_id),
            "doc_id": payload.get("doc_id", "sample"),
            "score": round(h.score, 4),
            "text": payload["text"].strip(),
        })
    return {"query": req.q, "results": results}

@app.get("/search")
def do_search(q: str = "RAG", top_k: int = 3):
    all_results = search(chunks, q)
    return {
        "query": q,
        "total": len(all_results),
        "results": [
            {"chunk_id": i, "score": s, "text": c.strip()[:300]}
            for s, i, c in all_results[:top_k]
        ],
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "retrieval-service"}
