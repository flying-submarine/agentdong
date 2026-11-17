"""第 8 课第 3 步：用评测集对比 纯向量 vs 混合+精排。

跑法（在 ~/Desktop/day1 里，venv 已激活、key 已 export）：
    python3 eval_compare.py

读 08-eval-set.json（20 道题），每道题跑两路：
  A 路 纯向量：Qdrant top 3
  B 路 混合+精排：向量 top 3 + BM25 全榜 → RRF 合并取前 3 → reranker 精排
指标：答得出的题算命中率（期望块进没进 top 3）；陷阱题看精排最高分，
超过 TRAP_SCORE_THRESHOLD（可调）视为"会硬答"。

注意：本文件在你 Mac 上没跑过，第一次跑先看有没有报错再看分数。
"""
import json
import os

import jieba
import requests
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient, models

from chunk_search import load_text, chunk_text
from app import embed

SILICONFLOW_API_KEY = os.environ["SILICONFLOW_API_KEY"]
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
TRAP_SCORE_THRESHOLD = 0.5  # 可调：精排最高分超过它，视为"会硬答"


def rrf(rank, k=60):
    return 1 / (k + rank)


def build_index(chunks):
    """Qdrant 内存库 + BM25 各建一次，所有题共用。"""
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="docs",
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )
    vecs = [embed(c) for c in chunks]
    client.upsert(
        collection_name="docs",
        points=[
            models.PointStruct(id=i, vector=v, payload={"text": c, "chunk_id": i})
            for i, (v, c) in enumerate(zip(vecs, chunks))
        ],
    )
    tokenized = [list(jieba.cut(c)) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    return client, bm25


def vector_search(client, query, top_k=3):
    """A 路：纯向量，返回块号列表。"""
    hits = client.query_points(
        collection_name="docs",
        query=embed(query),
        limit=top_k,
    ).points
    return [h.payload["chunk_id"] for h in hits]


def rerank(query, candidates, chunks, top_n=3):
    """精排：返回 [(块号, 分数)]，按分数从高到低。"""
    resp = requests.post(
        RERANK_URL,
        headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
        json={
            "model": RERANK_MODEL,
            "query": query,
            "documents": [chunks[i] for i in candidates],
            "top_n": top_n,
        },
    ).json()
    if "results" not in resp:
        print("精排接口返回异常：", resp)
        return []
    ranked = sorted(resp["results"], key=lambda r: r["relevance_score"], reverse=True)
    # index 是 documents 里的位置（从 0 起），要映射回块号
    return [(candidates[r["index"]], r["relevance_score"]) for r in ranked]


def hybrid_search(client, bm25, query, chunks, top_k=3):
    """B 路：向量 top 3 + BM25 全榜 → RRF 合并取前 3 → 精排。"""
    vec_order = vector_search(client, query, top_k)
    bm25_scores = bm25.get_scores(list(jieba.cut(query)))
    bm25_order = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
    scores = {}
    for rank, cid in enumerate(vec_order):
        scores[cid] = scores.get(cid, 0) + rrf(rank)
    for rank, cid in enumerate(bm25_order):
        scores[cid] = scores.get(cid, 0) + rrf(rank)
    candidates = sorted(scores, key=scores.get, reverse=True)[:top_k]
    ranked = rerank(query, candidates, chunks, top_n=top_k)
    return [cid for cid, _ in ranked], ranked


def main():
    with open("08-eval-set.json", encoding="utf-8") as f:
        items = json.load(f)
    text = load_text("sample.txt")
    chunks = chunk_text(text, 200, 50)
    client, bm25 = build_index(chunks)

    n_answerable = 0
    vec_hits = 0
    hyb_hits = 0
    vec_hit1 = 0
    hyb_hit1 = 0
    vec_mrr = 0.0
    hyb_mrr = 0.0
    n_trap = 0
    trap_would_answer = 0

    for item in items:
        q = item["question"]
        gt = item["expected_chunks"]
        if item["type"] == "trap":
            n_trap += 1
            _, ranked = hybrid_search(client, bm25, q, chunks)
            top_score = ranked[0][1] if ranked else 0.0
            flag = "会硬答!" if top_score >= TRAP_SCORE_THRESHOLD else "ok"
            if top_score >= TRAP_SCORE_THRESHOLD:
                trap_would_answer += 1
            print(f"[{item['id']}] TRAP {q} | 精排最高分 {top_score:.3f} {flag}")
            continue
        n_answerable += 1
        vec_order = vector_search(client, q)
        hyb_order, _ = hybrid_search(client, bm25, q, chunks)
        v_hit = any(c in vec_order for c in gt)
        h_hit = any(c in hyb_order for c in gt)
        vec_hits += v_hit
        hyb_hits += h_hit
        # 命中@1：期望块排第一才算；MRR：第一个期望块的名次倒数
        vec_hit1 += vec_order[0] in gt
        hyb_hit1 += hyb_order[0] in gt
        vec_mrr += 1.0 / (next(i for i, c in enumerate(vec_order) if c in gt) + 1)
        hyb_mrr += 1.0 / (next(i for i, c in enumerate(hyb_order) if c in gt) + 1)
        print(
            f"[{item['id']}] {q} | 期望 {gt} | "
            f"向量 {vec_order} {'命中' if v_hit else '未命中'} | "
            f"混合 {hyb_order} {'命中' if h_hit else '未命中'}"
        )

    print(f"\n答得出的题 {n_answerable} 道：")
    print(f"  命中@3：纯向量 {vec_hits}/{n_answerable} ({vec_hits / n_answerable:.0%})，"
          f"混合+精排 {hyb_hits}/{n_answerable} ({hyb_hits / n_answerable:.0%})")
    print(f"  命中@1：纯向量 {vec_hit1}/{n_answerable}，混合+精排 {hyb_hit1}/{n_answerable}")
    print(f"  MRR@3：纯向量 {vec_mrr / n_answerable:.3f}，混合+精排 {hyb_mrr / n_answerable:.3f}")
    print(f"陷阱题 {n_trap} 道：会硬答 {trap_would_answer} 道（阈值 {TRAP_SCORE_THRESHOLD}，可调）")


if __name__ == "__main__":
    main()
