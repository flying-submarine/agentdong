# frontend：Vue 3 RAG 平台前端（他真实做过的那套）

## 这里是什么

`src/` 是 Dong 在浙江省公众信息产业有限公司做过的 RAG 平台前端源码（137 个文件）：
Vue 3 + Vite + Pinia + TypeScript。模块：知识库、文档、RAG 对话、长文总结、写作助手、
ChatBI、评测、登录/注册/账号管理。RAG 对话走 `/gpt/psllm/retrieval/chat|completions`，
带 sessionId、历史记录、反馈、删除会话。

## 还缺什么（下一步补）

- **脚手架**：只有 src，没有 package.json / vite.config.ts / index.html——跑不起来。
  下一步按 src 里的 import 反推依赖，重建脚手架（vue、vite、pinia、axios、element-plus 等以实际 import 为准）。
- **接后端**：现在 src 里调的是老后端地址（/psllm/retrieval/*，他原公司的服务）。
  毕业设计的后端是本项目的三个服务（/search、/vector_search、/ask、/ask_tool、/ask_graph、
  /ingest、/upload），联调时把 service 里的 baseURL 指过来。
- **鉴权**：老项目用 Bearer token，401 跳登录；毕业设计 M4 做权限隔离时再对齐。

## 先别动

src 里的代码是他真实的工作成果，照原样放着。改只改联调需要的 baseURL 和接口路径，
不动业务逻辑。
