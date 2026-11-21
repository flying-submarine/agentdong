agentdong — 企业级 Agentic RAG 知识库问答平台
Dong 的 AI 转行作品：上传企业文档 → 自动切块入库 → 员工提问，Agent 查库、带引用回答、
答不出就拒绝、高危操作先请示，全程可评测、可追踪、可部署。
>
在线演示：https://agentdong.com
>
对应简历项目 2：生产运行中心智能问答系统（RAG）。
在线演示
https://agentdong.com —— 提问、传文档、陷阱题拒答都能直接试。演示站没有登录；
删文档、确认删库、Qdrant 写操作不对公众开放。
它是怎么工作的
入库：上传 PDF / Word / Markdown / 纯文本 → 切块（200 字，50 字重叠）→ SiliconFlow bge-m3 向量化 →
   Qdrant。入库走 RabbitMQ 异步（async），点 ID 由内容哈希决定，重复传同一份不会多出块；
   失败进死信（dead-letter），可补偿重试。
检索：向量检索 + BM25 关键词检索，RRF 融合，再过 bge-reranker-v2-m3 精排（rerank）。
   先用 DeepSeek 改写查询，改写后分数低就回退到原查询再查一次。
Agent：LangGraph 图（graph），最多查 2 轮，第 1 轮按原问题逐字查，第 2 轮才改写；
   每轮取精排最高分，低于 0.5 直接拒答，不调用回答模型；高于 0.5 才生成结构化回答
   （RagAnswer：answer / sources / confidence / refused）。会话记忆（MemorySaver）按 session 分。
高危操作先请示：删文档这类改库操作，图在确认关卡冻住（interrupt），等人点头才继续；只读操作直接跑。
对外：MCP 服务（FastMCP，stdio）只暴露一个工具 search_kb；演示站只放行读接口和上传。
验证过的数字（都是实测，不是简历上的数）
语料：13 份真实公开中文文档（Prometheus 中文手册 12 篇 + K8s 加固指南 PDF），648 块。
评测集：23 题（19 道能答 + 4 道陷阱），题目自 2026-11-17 起没改过，只改系统。
检索（M2）：MRR 0.579（纯向量）/ 0.649（混合）/ 0.658（混合 + 改写）；hit@1 9 / 10 / 9。
Agent 回归（M3/M4）：陷阱题 4/4 拒答，能答题 0/19 误拒，连续 6 次干净通过。
权限隔离（M4）：运维角色问运维值班手册，相关块 0.9899 排第一，答对了；财务角色问同一句，看不到那块，直接拒答。
注入防御（M4）：两份带毒文档（短语注入、删库指令）都被顶到检索前排，模型照常作答，注入没执行。
限流（M4）：每 session 每分钟 10 次，刷满返回 429 + Retry-After（实测 19 秒）；换 session 不受影响；窗口过后恢复 200。
目录结构
agentdong/
├── README.md                 # 本文件
├── .env.example              # 复制成 .env，填两个 API key（不要进 git）
├── .gitignore
├── docker-compose.yml        # 一键起全部服务：Qdrant + RabbitMQ + 3 个服务 + worker
├── backend/                  # Python + FastAPI：三个服务 + 一个 worker + Agent 图 + MCP 服务
│   ├── Dockerfile            # 三个服务共用一个镜像，compose 里用 command 区分启动命令
│   ├── requirements.txt
│   ├── rag_core.py           # 共享代码：向量、客户端、切块、embedding
│   ├── chunk_search.py       # 第 1 课的切块（200/50）——见 NEED-FROM-DAY1.md，从 day1 拷过来
│   ├── agent_graph.py        # 第 6 课的 LangGraph（run_agent）——同上
│   ├── sample.txt            # 演示文档 496 字——同上
│   ├── doc_service.py        # :8001 文档服务：/ingest、/upload（PDF/Word/MD/纯文本）、任务状态（SQLite）、DELETE /doc/{id}
│   ├── retrieval_service.py  # :8002 检索服务：/vector_search（混合检索 + 精排 + 回退）
│   ├── agent_service.py      # :8003 Agent 服务：/ask、/ask_graph、/ask_graph/confirm、限流 10 次/分钟
│   ├── capstone_graph.py     # LangGraph 图：查库循环 + 评分 + 结构化回答 + 人工确认关卡
│   ├── ingest_worker.py      # 入库 worker：消费 MQ → 切块 → 向量 → Qdrant（幂等 + 补偿 + 死信）
│   ├── mcp_search_server.py  # MCP 服务：只暴露 search_kb（stdio）
│   └── uploads/              # 上传的原文件留底（git 忽略内容）
├── frontend/                 # Vue 3 RAG 平台前端（真实做过的那套源码）
│   ├── package.json / vite.config.ts / index.html   # 脚手架（Vite）
│   └── src/                  # 平台源码（137 个文件）
├── corpus/                   # 13 份真实公开中文文档
├── eval/                     # 评测集（23 题）+ 对比脚本 + M3 验收脚本
└── docs/                     # 课程计划 + 简历对照表
本地跑（4 个进程）
cd agentdong/backend
cp ../.env.example ../.env   # 填 DEEPSEEK_API_KEY 和 SILICONFLOW_API_KEY（别贴到聊天里，也别进 git）
pip install -r requirements.txt
# Qdrant + RabbitMQ 先起起来
docker compose -f ../docker-compose.yml up -d qdrant rabbitmq
# 四个终端：
uvicorn doc_service:app --port 8001
uvicorn retrieval_service:app --port 8002
uvicorn agent_service:app --port 8003
python3 ingest_worker.py
验证：curl http://127.0.0.1:8001/stats → {"total_chars":496,"num_chunks":4}。
Docker 跑（已上线）
docker compose up -d --build   # 6 个容器：qdrant、rabbitmq、doc、retrieval、agent、worker
首次运行先 docker volume create qdrant_storage（compose 里标了 external）。
线上在腾讯云香港轻量（2 核 4G），Nginx + certbot，https://agentdong.com，Qdrant 点数 648。
里程碑
M1 文档入库链路 ✅：/upload（多格式解析）→ MQ → embedding → Qdrant；能查回原文。
M2 检索 + 评测 ✅：混合检索 + 精排；23 题评测集，MRR 0.579 / 0.649 / 0.658。
M3 Agent ✅：LangGraph 工具循环 + 记忆 + 人工确认 + RagAnswer 结构化输出；陷阱 4/4、误拒 0/19。
M4 对外 + 安全 ✅：MCP（search_kb）；注入防御；权限隔离；限流 10 次/分钟。
M5 部署 + 演示：第 1 步已上线（agentdong.com）；第 2 步 Vue 接线进行中；第 3 步演示脚本。
诚实口径（面试时这么说）
语料是 13 份真实公开文档、648 块，不说"2000+ 份"。
召回率、准确率这些数字以 eval/ 里的实测为准，不抄简历上的 25%、90%。
向量库用的是 Qdrant（简历上写的 Milvus 是同类产品，机制一样，措辞按实际写）。
LoRA 微调、Qwen 本地部署、SQL Agent 是后续，不在这次主链路里。
演示站没加登录鉴权；删库和确认删库没暴露，Qdrant 写操作没暴露。