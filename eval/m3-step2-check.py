# M3 第 2 步验收脚本：把 23 道评测题逐题发给 8003 的 /ask_graph，数拒答。
# 验收线（M3 提案第 2 步）：4 道陷阱题全 refused；19 道能答的题里 refused 不超过 1 道。重点盯 cap-20。
# 用法：先启动 8003（新版 capstone_graph.py + agent_service.py），再跑：
#   python3 m3-step2-check.py
# 每题约 10–30 秒（最多 2 轮检索 + 结构化输出），23 题大概 5–10 分钟，跑完直接给结论。
# 评测集文件在同目录或 ../eval/ 下都能找到（跟 M2 的评测脚本一个找法）。

# 引用的包（每个包是干嘛的）：
import json  # 读评测集 JSON、拼请求体
import sys  # 失败时给非零退出码，方便一眼看出没过
from pathlib import Path  # 找评测集文件（同目录或 ../eval/）
import httpx  # 发 HTTP 请求：调 8003 的 /ask_graph

GRAPH_URL = "http://127.0.0.1:8003/ask_graph"  # 8003 的 /ask_graph，本地跑默认这个地址
TIMEOUT = 180.0  # 每题最多等 3 分钟：两轮检索（改写调 DeepSeek）+ 结构化输出，慢题也够


def find_eval_set():
    """找评测集文件：先看脚本同目录，再看 ../eval/（脚本放 backend/ 里跑也能找到）。"""
    here = Path(__file__).resolve().parent
    for cand in (here / "capstone-eval-set.json", here.parent / "eval" / "capstone-eval-set.json"):
        if cand.exists():
            return cand
    raise FileNotFoundError("找不到 capstone-eval-set.json（同目录和 ../eval/ 都看了）")


def main():
    items = json.loads(find_eval_set().read_text(encoding="utf-8"))
    traps = [it for it in items if it["type"] == "trap"]  # 4 道陷阱题：必须全 refused
    answerable = [it for it in items if it["type"] != "trap"]  # 19 道能答的题：refused 不超过 1 道
    trap_missed = []  # 该拒没拒的陷阱题
    ans_refused = []  # 被误拒的能答题

    with httpx.Client(timeout=TIMEOUT) as client:
        for it in items:
            qid = it["id"]
            try:
                r = client.post(GRAPH_URL, json={"question": it["question"], "session_id": f"m3s2-{qid}"})
                r.raise_for_status()
                data = r.json()
            except Exception as e:  # 这题没跑通：记成误拒（能答题）或漏拒（陷阱题），最后结论里看得见
                print(f"{qid} 请求失败：{type(e).__name__} {e}")
                (trap_missed if it["type"] == "trap" else ans_refused).append(qid + "（请求失败）")
                continue
            refused = data.get("refused", False)
            print(f"{qid} refused={refused} rounds={data.get('search_rounds')} confidence={data.get('confidence')}")
            if it["type"] == "trap" and not refused:
                trap_missed.append(qid)
            if it["type"] != "trap" and refused:
                ans_refused.append(qid)

    print(f"\n陷阱题：{len(traps) - len(trap_missed)}/{len(traps)} 已拒答" + (f"，漏拒：{trap_missed}" if trap_missed else ""))
    print(f"能答题：{len(ans_refused)}/{len(answerable)} 被误拒" + (f"，误拒的题：{ans_refused}" if ans_refused else ""))
    ok = not trap_missed and len(ans_refused) <= 1
    print("结论：通过" if ok else "结论：没通过")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
