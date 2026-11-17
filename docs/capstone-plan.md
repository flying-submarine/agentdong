# 毕业设计：企业知识库 Agent（Agentic RAG 平台）

> 选题决定：2026-11-14，Dong 选 A。依据：2026 年就业市场——AI Agent 岗位上半年 1.2 万 → 6.7 万，约 80% 大厂技术岗 JD 写着「Agent 开发经验优先」，硬要求是「至少 1 个完整 AI Agent 项目落地经验」；JD 技能收敛于 Python / LangChain / LangGraph / RAG / 向量库 / Function Calling / MCP / 部署 / 评测。行业共识：先 workflow，后 agent；先 eval，后自治；先治理边界，后放权。
>
> 一句话：上传企业文档 → 自动切块入库 → 员工提问，Agent 查库、带引用回答、答不出就拒绝、高危操作先请示，全程可评测、可追踪、可部署。

## 架构（从你 1–8 课长出来的）

```
前端（Vue 3 RAG 平台，你真实做过的那套：知识库、会话、评测模块）
  │  CORS
  ▼
FastAPI 网关（app.py 演进：/search /stats /ask /ask_tool /ask_graph 再加新接口）
  ├── 文档服务：上传 → 解析（PDF/Word/Markdown）→ 切块（200/50）
  ├── 入库：RabbitMQ 异步 embedding → Qdrant（混合检索 + reranker）
  ├── Agent 服务：LangGraph（工具 + 记忆 + 人工确认 + 结构化输出）
  ├── MCP 服务：工具对外暴露（第 7 课的 mcp_server.py 演进）
  ├── 评测：eval set + hit@k / MRR + 陷阱题（第 8 课第 3 步的打法）
  └── 可观测：AgentOps（trace / token / 延迟 / 成本）
部署：docker-compose.yml（第 8 课第 5 步已通）
```

## 里程碑

- **M1 文档入库链路**：上传 → 解析 → 切块 → MQ → embedding → Qdrant；能查回原文。
- **M2 检索 + 评测**：混合检索 + 精排接进服务；评测集扩到真实文档，hit@1 / MRR 有数可报。
- **M3 Agent**：LangGraph 工具循环 + 记忆（同 thread 记得住，换 thread 记不住）+ 人工确认 + RagAnswer 结构化输出（答不出就 refused）。
- **M4 对外 + 安全**：MCP 暴露工具；Prompt Injection 防御；只读边界。
- **M5 部署 + 演示**：compose 一键起；演示脚本：上传 → 提问 → 陷阱题被拒 → 高危操作先请示；项目讲稿。

## 第 9 / 10 / 11 课怎么喂给它

- **第 9 课（微服务与分布式）**：把 app.py 拆成文档 / 检索 / Agent 三个服务 + RabbitMQ 异步入库；幂等、最终一致性；最小 Spring Cloud demo 只做面试对照。
- **第 10 课（模型工程）**：一次真实 LoRA（Qwen2.5-1.5B + vLLM）；毕业设计里可选：查询改写小模型；不强制进主链路。
- **第 11 课（进阶专题）**：ChatBI / SQL Agent 只读安全边界、AgentOps、Prompt Injection 攻防——直接长在 M4 上。

## 面试讲稿锚点（到时展开）

- 评测数：hit@1 / MRR 从第 8 课的 16/17、0.971 起步，扩集后再报。
- 陷阱题：trap-01 精排 0.521 敢答，结构化输出 refused 才拦住。
- 部署数：镜像构建 867 秒（1ms.run 镜像源），compose 一条命令起两个服务。
- 故障故事：Hub 超时、chunk_search 漏拷、CORS、空卷 external: true——每个都有日志和修复。
