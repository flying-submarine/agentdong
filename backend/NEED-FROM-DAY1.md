# 还差 3 个文件：只在你 Mac 的 day1 里有，不在我这边

这三个文件没法从我这边给你，你从 `~/Desktop/day1/` 拷进 `backend/`：

```bash
cd ~/Desktop/day1
cp chunk_search.py agent_graph.py sample.txt ~/Desktop/agentdong/backend/
```

| 文件 | 是什么 | 谁在用 |
|---|---|---|
| `chunk_search.py` | 第 1 课的切块函数（200 字一块，重叠 50 字） | `rag_core.py`、`ingest_worker.py` |
| `agent_graph.py` | 第 6 课的 LangGraph（`run_agent`） | `agent_service.py`（/ask_graph） |
| `sample.txt` | 演示文档 496 字 | `rag_core.py`（/stats、/search 的数据源） |

拷完检查一下：

```bash
ls ~/Desktop/agentdong/backend/
# 应该看到：8 个 .py 文件 + sample.txt + Dockerfile + requirements.txt + uploads/
```

注意：`agent_graph.py` 里的 `run_agent(question, session_id)` 签名以你 day1 里那份为准，
不要用我猜的——第 9 课第 1 步留过这个口子。
