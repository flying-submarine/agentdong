# 工作项目 M2：检索服务（端口 8002）——/vector_search 改成混合检索 + 查询重写。
# 和 M1 比只改 /vector_search 这一路，其他接口（/search 关键词、/health）没动。
# 新流程：问题先过 DeepSeek 改写（补全省略、展开术语）→ 向量取 10 个 + BM25 取 10 个
# → RRF 按排名合并取前 5 → 精排取前 3 返回。
# 数字的道理：召回要宽（10，别漏）→ 精排贵，只排 5 个 → 最后给大模型的只要 3 块。
# 注意：BM25 是内存快照——每次查询都现从 Qdrant 拉全部块重建（289 块约半秒），
# 这样新上传的文档立刻能进 BM25，不会旧索引漏新文档；代价是每次查询多这半秒。
# 另外：这里不再按分数过滤（以前的 SIM_THRESHOLD 0.4 不用了）——只负责把最像的 3 块排好，
# 答不答、拒不拒是 M3 结构化输出的事；陷阱题的分数在评测里看，阈值到时再定。
# 精排挂了怎么办：不报错，退回 RRF 顺序返回，并在响应里标 reranked=false（看得见才不坑人）。
# 兜底（2026-11-19 加）：改写路最高分 < 0.5 时，再用原查询查一次，取分高的那路返回，
# 并在响应里标 fallback_used=true。改写对短关键词问法会丢分（cap-10：改写 0.0203，原句 0.7979），
# 兜底只在分数低时多查一次，大部分问题不触发，不多花钱。

# 引用的包（每个包是干嘛的）：
import os  # 读环境变量：服务地址默认 localhost，Docker 里 compose 传服务名
import httpx  # 发 HTTP 请求：调 SiliconFlow 的 reranker 接口
import jieba  # 中文分词：BM25 是词袋模型，中文要先切词才能算词频
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Filter, FieldCondition, MatchAny, VectorParams  # Filter/FieldCondition/MatchAny：按 payload 条件过滤（权限隔离用）
from rank_bm25 import BM25Okapi  # BM25 关键词检索：按词频 + 逆文档频率给块打分
from rag_core import client, embed, search, chunks  # client：第 4 课的 DeepSeek 客户端（查询重写用）；embed：问题变向量；search/chunks：/search 关键词接口复用

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 qdrant
COLLECTION = "docs"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
VECTOR_TOP_K = 10  # 向量一路取几个候选
BM25_TOP_K = 10  # BM25 一路取几个候选
RRF_TOP_N = 5  # RRF 合并后取几个进精排
FINAL_TOP_K = 3  # 最终返回几块
FALLBACK_THRESHOLD = 0.5  # 兜底线：改写路最高分低于它，才用原查询再查一次；和 M3 的拒答线 0.5 取同一个数，低于这条线 Agent 本来就会拒答，所以值得再试一次

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
    allow_origins=["https://agentdong.com", "https://www.agentdong.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def rrf(rank, k=60):
    # RRF（倒数排名融合）：把排名变成分数，1/(k+rank)。k=60 是缓冲常数，
    # 让第 1 名和第 10 名的差距别太大；只用排名不用原始分数，所以向量分（0~1）和 BM25 分（没上限）能合并。
    # 注意 rank 从 0 起：第 1 名是 1/(60+0)=1/60。
    return 1 / (k + rank)

def visible_filter(role: str | None):
    # 权限过滤器：看得见的块 = 没打标签的老文档（公开）+ 标签里有这个角色的。
    # role 没给（None）= 只看公开的——默认拒绝，不是不设防；MCP 和老接口不传角色时也只看到公开文档。
    # is_empty 指 payload 里没这个字段（老文档都没打标签）；MatchAny 指标签列表里有这个角色。
    if role is None:
        return Filter(must=[FieldCondition(key="allowed_roles", is_empty=True)])
    return Filter(should=[
        FieldCondition(key="allowed_roles", match=MatchAny(any=[role])),
        FieldCondition(key="allowed_roles", is_empty=True),
    ])


def load_all_chunks(role: str | None = None):
    # 从 Qdrant 把这个角色看得见的块拉回来（只要 payload，不要向量——1024 个数没用还占流量）。
    # 返回 [{'point_id', 'doc_id', 'chunk_id', 'text'}]，顺序就是 BM25 和 RRF 共用的下标。
    # 过滤在 Qdrant 那层做（scroll_filter），BM25 建索引时就只有看得见的块。
    points, _ = qclient.scroll(COLLECTION, limit=1000, with_payload=True, with_vectors=False, scroll_filter=visible_filter(role))
    out = []
    for p in points:
        payload = p.payload or {}
        out.append({
            "point_id": str(p.id),
            "doc_id": payload.get("doc_id", "sample"),
            "chunk_id": payload.get("chunk_id", 0),
            "text": payload.get("text", ""),
        })
    return out

def rewrite_query(q: str) -> str:
    # 查询重写：把用户的问题交给 DeepSeek 改写成更适合检索的查询——补全省略的主语、展开同义词和专业术语。
    # 改写失败（没 key、超时、接口报错）就原样返回原问题，不让检索挂掉。
    try:
        resp = client.chat.completions.create(
            model="deepseek-flash",
            temperature=0,
            messages=[
                {"role": "system", "content": "你是一个检索查询改写器。把用户的问题改写成一个更适合在运维知识库里检索的查询：补全省略的主语，展开同义词和专业术语，保留原意。只输出改写后的查询，不要解释。"},
                {"role": "user", "content": q},
            ],
        )
        rewritten = resp.choices[0].message.content.strip()
        return rewritten or q
    except Exception:
        return q

def rerank(query, candidate_idx, chunk_list, top_n=3):
    # 精排：把候选块和问题成对交给 cross-encoder 打分（bge-reranker-v2-m3），按分从高到低返回 [(块下标, 分数)]。
    # 注意：返回的 index 是 documents 里的位置（从 0 起），要映射回候选下标——第 8 课踩过的坑，别拿位置当块号。
    # 接口挂了返回 None，调用方退回 RRF 顺序。
    try:
        resp = httpx.post(
            RERANK_URL,
            headers={"Authorization": f"Bearer {os.environ['SILICONFLOW_API_KEY']}"},
            json={"model": RERANK_MODEL, "query": query, "documents": [chunk_list[i]["text"] for i in candidate_idx], "top_n": top_n},
            timeout=30.0,
        ).json()
        if "results" not in resp:
            return None
        ranked = sorted(resp["results"], key=lambda r: r["relevance_score"], reverse=True)
        return [(candidate_idx[r["index"]], round(r["relevance_score"], 4)) for r in ranked]
    except Exception:
        return None

def hybrid_retrieve(effective_q, chunk_list, role: str | None = None):
    # 混合检索核心：向量一路 + BM25 一路 → RRF 合并 → 精排。
    # 返回 (results, reranked)：results 是 [(块下标, 分数)]，reranked 说精排有没有成功跑起来。
    # role 传进来后，向量那路也在 Qdrant 层加过滤（query_filter），只返回看得见的点；
    # BM25 那路不用再滤——chunk_list 本来就是按角色拉回来的。
    id_to_idx = {c["point_id"]: i for i, c in enumerate(chunk_list)}
    # 向量一路：问题变向量，问 Qdrant 要最像的 10 个，映射成块下标。
    qv = embed(effective_q)
    vec_idx = []
    for h in qclient.query_points(COLLECTION, query=qv, limit=VECTOR_TOP_K, query_filter=visible_filter(role)).points:
        if str(h.id) in id_to_idx:
            vec_idx.append(id_to_idx[str(h.id)])
    # BM25 一路：全文先 jieba 切词建索引，问题也切词，取分数最高的 10 个块下标。
    tokenized = [list(jieba.cut(c["text"])) for c in chunk_list]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(list(jieba.cut(effective_q)))
    bm25_idx = sorted(range(len(chunk_list)), key=lambda i: bm25_scores[i], reverse=True)[:BM25_TOP_K]
    # RRF 合并：两路的排名各算一份分，加起来，取前 5 进精排。
    scores = {}
    for rank, i in enumerate(vec_idx):
        scores[i] = scores.get(i, 0) + rrf(rank)
    for rank, i in enumerate(bm25_idx):
        scores[i] = scores.get(i, 0) + rrf(rank)
    candidates = sorted(scores, key=scores.get, reverse=True)[:RRF_TOP_N]
    # 精排：成功就按精排分排，失败就退回 RRF 顺序（分数用 RRF 分），并标 reranked=false。
    ranked = rerank(effective_q, candidates, chunk_list, top_n=FINAL_TOP_K)
    if ranked is not None:
        return ranked, True
    return [(i, round(scores[i], 4)) for i in candidates[:FINAL_TOP_K]], False

class VectorSearchIn(BaseModel):
    q: str = "RAG 是什么"
    top_k: int = 3
    rewrite: bool = True  # 要不要先查询重写；评测对比时可以关掉它，只比混合检索本身
    role: str | None = None  # 调用方角色（比如 "运维"）：只返回这个角色看得见的块；不给就只看公开的

@app.post("/vector_search")
def do_vector_search(req: VectorSearchIn):
    # 新版 /vector_search：先改写问题（可关），再混合检索，返回前 3 块；改写路分数低时用原查询兜底一次。
    # 响应里同时给原问题、改写后的问题、精排是否成功、兜底有没有用上——调问题时看得见每一步。
    rewritten = rewrite_query(req.q) if req.rewrite else req.q
    chunk_list = load_all_chunks(req.role)
    if not chunk_list:
        return {"query": req.q, "rewritten_query": rewritten, "reranked": False, "fallback_used": False, "role": req.role, "results": []}
    ranked, reranked = hybrid_retrieve(rewritten, chunk_list, req.role)
    fallback_used = False
    # 兜底：只有同时满足这四个条件才多查一次——
    # [1] 开了改写（req.rewrite），[2] 改写真的改动了问题（rewritten != 原问题，否则再查一次是重复劳动），
    # [3] 精排成功跑起来了（reranked；精排挂了退回的是 RRF 分，量纲和 0.5 不是一回事，没法比），
    # [4] 改写路最高分低于兜底线（这路再往下走 Agent 也会拒答）。
    # 满足就用原查询再跑一次混合检索，两路比最高分，分高的赢；原句路赢了才换结果、标 fallback_used=true。
    # 块列表 chunk_list 两路共用一次，不用重新拉；多花的只是一次向量化 + 一次精排。
    if req.rewrite and rewritten != req.q and reranked and ranked and ranked[0][1] < FALLBACK_THRESHOLD:
        ranked_orig, reranked_orig = hybrid_retrieve(req.q, chunk_list, req.role)
        if reranked_orig and ranked_orig and ranked_orig[0][1] > ranked[0][1]:
            ranked, reranked = ranked_orig, reranked_orig
            fallback_used = True
    results = []
    for i, score in ranked[:req.top_k]:
        c = chunk_list[i]
        results.append({
            "chunk_id": int(c["chunk_id"]),
            "doc_id": c["doc_id"],
            "score": score,
            "text": c["text"].strip(),
        })
    return {"query": req.q, "rewritten_query": rewritten, "reranked": reranked, "fallback_used": fallback_used, "role": req.role, "results": results}

@app.get("/search")
def do_search(q: str = "RAG", top_k: int = 3):
    # 关键词搜索（老接口，没动）：仍查内存里的 sample.txt——新入库的文档暂时查不到关键词结果。
    # 混合检索的正路是 /vector_search，这个接口留着给第 5 课的工具调用和对比。
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
    return {"status": "ok", "service": "retrieval-service", "mode": "hybrid"}
