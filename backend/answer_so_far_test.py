# _answer_so_far 自测（M5 第 3 步第 0 步）：从半截 JSON 里抠 answer，一个字符一个字符喂，模拟流式。
# 放 ~/Desktop/agentdong/backend/ 里跑（它要 import 同目录的 capstone_graph），能跑就删。
import json  # 拼测试用的完整 JSON
from dotenv import load_dotenv  # 先读 .env 再 import capstone_graph——它在模块层就建 ChatOpenAI，没 key 直接报错
load_dotenv()  # 从当前目录往上找 .env（在 backend/ 跑就读到 agentdong/.env）
from capstone_graph import _answer_so_far  # 从半截 JSON 里抠 answer 的小函数
full = json.dumps({"refused": False, "answer": "Prometheus 是监控工具。", "sources": ["d:0"], "confidence": 0.9}, ensure_ascii=False)
shown = ""
for cut in range(0, len(full) + 1):  # 一个字符一个字符喂，模拟流式（切点 48 是后引号刚到的位置）
    text = _answer_so_far(full[:cut])
    if len(text) > len(shown):  # 和 run_agent_stream 里同一条规则：只许往前长
        assert text.startswith(shown), (cut, text, shown)
        shown = text
assert shown == "Prometheus 是监控工具。", shown
print("OK:", shown)
