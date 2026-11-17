"""M2 评测对比脚本：同一套题，三条路并排跑

三条路：
  A 路：纯向量 —— 问题向量化后直接查 Qdrant，取前 3 块（第 8 课的做法）
  B 路：混合，不改写 —— 调 8002 的 /vector_search，rewrite=false
  C 路：混合 + 改写 —— 调 8002 的 /vector_search，rewrite=true（默认）

评测集：capstone-eval-set.json（23 题：13 直接 + 6 改述 + 4 陷阱）
指标（只算能回答的 19 题）：hit@1、hit@3、MRR@3
陷阱题（4 题）：看 C 路第 1 名的精排分数，>= 0.5 算"会硬答"，< 0.5 算"会拒答"

用法（先启动 Qdrant 和 8002 检索服务）：
  这个脚本放在 backend/ 或 eval/ 里都能跑，评测集 JSON 也一样：
  cd ~/Desktop/agentdong/backend
  python3 capstone-eval-compare.py
"""

# [块 1] 导入：json 读评测集；os/sys 定路径；httpx 调 8002 的 HTTP 接口
import json
import os
import sys

import httpx  # 调 8002 的 /vector_search（B 路和 C 路走 HTTP，像真实客户端一样）
from qdrant_client import QdrantClient  # 连 Qdrant 的客户端：A 路直接查库用

# [块 2] 路径：脚本放在 backend/ 还是 eval/ 里都能跑。
# 先在脚本自己所在的文件夹找文件，找不到再去隔壁文件夹找。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_file(name):
    """找一个文件：先看脚本旁边，再看 ../eval/，再看当前目录。找不到就返回脚本旁边的路径（报错时会显示它）。"""
    for cand in (
        os.path.join(SCRIPT_DIR, name),
        os.path.join(SCRIPT_DIR, "..", "eval", name),
        os.path.join(os.getcwd(), name),
    ):
        if os.path.exists(cand):
            return cand
    return os.path.join(SCRIPT_DIR, name)


# backend 在哪：脚本旁边有 rag_core.py 就是 backend/，否则去 ../backend/
BACKEND_DIR = SCRIPT_DIR if os.path.exists(os.path.join(SCRIPT_DIR, "rag_core.py")) else os.path.join(SCRIPT_DIR, "..", "backend")
sys.path.insert(0, BACKEND_DIR)

from rag_core import embed  # embed：把问题转成 1024 维向量（rag_core 里的函数就叫 embed）

# [块 3] 常量：评测集路径、Qdrant 地址、8002 地址、陷阱判定阈值（第 8 课沿用的 0.5）
EVAL_SET_PATH = find_file("capstone-eval-set.json")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 qdrant
qclient = QdrantClient(url=QDRANT_URL)
RETRIEVAL_URL = "http://127.0.0.1:8002/vector_search"
TRAP_THRESHOLD = 0.5  # 陷阱题：C 路第 1 名精排分数达到这个值，就认为系统会硬着头皮回答


def load_eval_set():
    """读评测集 JSON，返回题目列表"""
    with open(EVAL_SET_PATH, encoding="utf-8") as f:
        return json.load(f)


def route_a_pure_vector(question):
    """A 路：纯向量。问题向量化 → Qdrant 取前 3 块，返回 (doc_id, chunk_id) 列表"""
    vec = embed(question)  # 把问题变成 1024 维向量
    hits = qclient.query_points(collection_name="docs", query=vec, limit=3).points
    return [(p.payload["doc_id"], p.payload["chunk_id"]) for p in hits]


def route_bc_hybrid(question, rewrite):
    """B/C 路：调 8002 的 /vector_search。

    rewrite=False 是 B 路（混合，不改写）；rewrite=True 是 C 路（混合 + 改写）。
    返回 (结果列表, 第 1 名分数, 改写后的问题)；服务不通时返回 (None, None, None)。
    """
    try:
        resp = httpx.post(
            RETRIEVAL_URL,
            json={"q": question, "top_k": 3, "rewrite": rewrite},
            timeout=120.0,  # 改写要调一次 DeepSeek，留足时间
        )
        resp.raise_for_status()
    except Exception as e:  # 服务没起、超时、报错：不让整个评测崩掉，返回空，让主流程标注
        print(f"  [警告] 调 8002 失败（rewrite={rewrite}）：{e}")
        return None, None, None
    data = resp.json()
    results = [(r["doc_id"], r["chunk_id"]) for r in data["results"]]
    top_score = data["results"][0]["score"] if data["results"] else 0.0
    return results, top_score, data.get("rewritten_query", question)


def first_expected_rank(results, expected):
    """找期望答案在结果列表里的最早名次（从 0 数起）；没出现返回 None。

    有的题期望答案有两块（比如 cap-03 的 Counter 和 Gauge 各一块），命中任意一块就算。
    """
    expected_set = {(d, c) for d, c in expected}
    for rank, pair in enumerate(results):
        if pair in expected_set:
            return rank
    return None


def main():
    """主流程：逐题跑三条路，打印逐题结果，最后汇总三张表的指标"""
    items = load_eval_set()
    answerable = [it for it in items if it["expected"]]  # 能回答的题（陷阱题 expected 为空，不算进 hit/MRR）
    traps = [it for it in items if not it["expected"]]

    # 每条路的累计：hit@1 次数、hit@3 次数、MRR 总和、跑通的题数
    totals = {
        "A 纯向量": {"h1": 0, "h3": 0, "mrr": 0.0, "n": 0},
        "B 混合不改写": {"h1": 0, "h3": 0, "mrr": 0.0, "n": 0},
        "C 混合+改写": {"h1": 0, "h3": 0, "mrr": 0.0, "n": 0},
    }
    trap_verdicts = []  # 每道陷阱题：(题号, B 路第 1 名分数, C 路第 1 名分数, 结论)

    for it in items:
        q, expected = it["question"], it["expected"]
        print(f"\n{it['id']} [{it['type']}] {q}")

        # 三条路各跑一次
        a_results = route_a_pure_vector(q)
        b_results, b_top, _ = route_bc_hybrid(q, rewrite=False)
        c_results, c_top, rewritten = route_bc_hybrid(q, rewrite=True)
        if rewritten and rewritten != q:
            print(f"  改写后：{rewritten}")

        routes = [("A 纯向量", a_results), ("B 混合不改写", b_results), ("C 混合+改写", c_results)]
        for name, results in routes:
            if results is None:  # 这条路没跑通（比如 8002 没起），跳过，不计入分母
                print(f"  {name}：未跑通")
                continue
            print(f"  {name}：{results}")
            if expected:  # 能回答的题才计分
                rank = first_expected_rank(results, expected)
                t = totals[name]
                t["n"] += 1
                if rank is not None:
                    t["h3"] += 1
                    t["mrr"] += 1.0 / (rank + 1)
                    if rank == 0:
                        t["h1"] += 1
            else:  # 陷阱题：只记分数，不计 hit
                if name == "C 混合+改写":
                    verdict = "会硬答" if c_top >= TRAP_THRESHOLD else "会拒答"
                    trap_verdicts.append((it["id"], b_top, c_top, verdict))

    # [块 4] 汇总：三条路的 hit@1、hit@3、MRR@3（分母是每条路实际跑通的题数）
    print("\n========== 汇总（能回答的 19 题）==========")
    print(f"{'路线':<12}{'hit@1':>8}{'hit@3':>8}{'MRR@3':>8}")
    for name, t in totals.items():
        n = t["n"] or 1  # 防止除零（某条路全没跑通时分母按 1 算，显示 0）
        print(f"{name:<12}{t['h1']}/{t['n']:<7}{t['h3']}/{t['n']:<7}{t['mrr'] / n:.3f}")

    # [块 5] 陷阱题汇总：B 路和 C 路第 1 名的分数对比
    print("\n========== 陷阱题（4 题，分数越低越好）==========")
    for item_id, b_top, c_top, verdict in trap_verdicts:
        print(f"{item_id}：B 路第 1 名 {b_top}，C 路第 1 名 {c_top} → {verdict}")


if __name__ == "__main__":
    main()
