# agentdong — 企业知识库 Agent（毕业设计）

> Dong 的 AI 转行作品：上传企业文档 → 自动切块入库 → 员工提问，Agent 查库、带引用回答、
> 答不出就拒绝、高危操作先请示，全程可评测、可追踪、可部署。
> 对应简历项目 2：生产运行中心智能问答系统（RAG）——机制全部做实，数字全部实测。

## 目录结构

```
agentdong/
├── README.md                 # 本文件
├── .env.example              # 复制成 .env，填两个 API key（不要进 git）
├── .gitignore
├── docker-compose.yml        # 一键起全部服务（M5 收尾，现在先起 Qdrant + RabbitMQ）
├── backend/                  # Python + FastAPI：三个服务 + 一个 worker
│   ├── Dockerfile            # 三个服务共用一个镜像，compose 里用 command 区分启动命令
│   ├── requirements.txt
│   ├── rag_core.py           # 共享代码：向量、客户端、三个工具函数、SIM_THRESHOLD 0.4
│   ├── chunk_search.py       # 第 1 课的切块（200/50）——见 NEED-FROM-DAY1.md，从 day1 拷过来
│   ├── agent_graph.py        # 第 6 课的 LangGraph（run_agent）——同上
│   ├── sample.txt            # 演示文档 496 字——同上
│   ├── doc_service.py        # :8001 文档服务：/ingest、/upload（PDF/Word/MD/纯文本）、任务状态（SQLite）
│   ├── retrieval_service.py  # :8002 检索服务：/vector_search（Qdrant）、/search（关键词）
│   ├── agent_service.py      # :8003 Agent 服务：/ask、/ask_stream、/ask_tool、/ask_graph
│   ├── ingest_worker.py      # 入库 worker：消费 MQ → 切块 → 向量 → Qdrant（幂等 + 补偿 + 死信）
│   └── uploads/              # 上传的原文件留底（git 忽略内容）
├── frontend/                 # Vue 3 RAG 平台前端（他真实做过的那套源码）
│   └── src/                  # 137 个文件；脚手架（package.json 等）下一步补，见 frontend/README.md
├── corpus/                   # 12 份真实公开中文文档（Prometheus 手册 11 篇 + K8s 加固指南 PDF）
├── eval/                     # 评测集（21 题）+ 对比脚本
└── docs/                     # 毕业设计计划 + 简历对照表
```

## 本地跑（现在的跑法：4 个进程）

```bash
cd agentdong/backend
cp ../.env.example ../.env   # 填 DEEPSEEK_API_KEY 和 SILICONFLOW_API_KEY（别贴到聊天里）
pip install -r requirements.txt
# Qdrant + RabbitMQ 先起起来
docker compose -f ../docker-compose.yml up -d qdrant rabbitmq
# 四个终端：
uvicorn doc_service:app --port 8001
uvicorn retrieval_service:app --port 8002
uvicorn agent_service:app --port 8003
python3 ingest_worker.py
```

验证：`curl http://127.0.0.1:8001/stats` → `{"total_chars":496,"num_chunks":4}`。

## Docker 跑（M5 收尾）

服务地址已经改成环境变量（本地默认 localhost，Docker 里 compose 传服务名），
`docker-compose.yml` 里三个服务的定义已写好，M5 时一次点亮。

## 里程碑

- **M1 文档入库链路**：/upload（多格式解析）→ MQ → embedding → Qdrant；能查回原文。进行中。
- **M2 检索 + 评测**：混合检索 + 精排接进检索服务；评测集扩到 corpus 的真实文档，hit@1 / MRR 有数可报。
- **M3 Agent**：LangGraph 工具循环 + 记忆 + 人工确认 + RagAnswer 结构化输出（答不出就 refused）。
- **M4 对外 + 安全**：MCP 暴露工具；Prompt Injection 防御；权限隔离；限流。
- **M5 部署 + 演示**：compose 一键起；演示脚本；项目讲稿；前端接通。

## 诚实口径（面试时这么说）

- 语料是 12 份真实公开文档、约 800 块，不说"2000+ 份"。
- 召回率、准确率这些数字以 eval/ 里的实测为准，不抄简历上的 25%、90%。
- 向量库用的是 Qdrant（简历上写的 Milvus 是同类产品，机制一样，措辞按实际写）。
- LoRA 微调、Qwen-32B 本地部署、SQL Agent 是后续，不在这次主链路里。
