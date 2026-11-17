# 毕业设计语料：生产运行中心知识库（真实公开文档）

> 用途：毕业设计（简历项目 2：生产运行中心智能问答系统）的真实语料，
> 替代 sample.txt 的 4 块演示数据。仅供学习演示使用。
> 诚实口径：这是 12 份真实公开文档，不是简历上写的"2000+ 份运维手册"——
> 机制是真的，规模写实测数；面试时说"12 份真实文档、约 800 块"，不说 2000+。

## 文件清单（12 个）

| 文件 | 来源 | 内容 |
|---|---|---|
| prometheus-overview.md | daichangya/prometheus.io | Prometheus 简介：是什么、为什么用 pull |
| prometheus-data_model.md | 同上 | 数据模型：metric、label、时序 |
| prometheus-metric_types.md | 同上 | 指标类型：Counter / Gauge / Histogram / Summary |
| prometheus-basics.md | 同上 | 基础概念：作业、实例、抓取 |
| prometheus-installation.md | 同上 | 安装部署 |
| prometheus-gettingstarted.md | 同上 | 上手：第一个监控目标 |
| prometheus-functions.md | 同上 | PromQL 函数手册（最长一篇） |
| prometheus-operators.md | 同上 | 查询操作符 |
| prometheus-storage.md | 同上 | 存储：TSDB、WAL、压缩 |
| prometheus-federation.md | 同上 | 联邦集群 |
| prometheus-examples.md | 同上 | 常用查询示例 |
| prometheus-api.md | 同上 | HTTP API |
| k8s-hardening-guide-zh.pdf（51 页，约 38,900 字） | CISA《Kubernetes Hardening Guidance》中文版（Jimmy Song 译） | K8s 加固：认证、授权、网络策略、审计——故障排查与安全场景 |

## 规模

- Markdown 11 篇，合计 92,185 字符；PDF 1 份，提取约 38,900 字符。
- 合计约 131,000 字符；按 200 字/块、50 字重叠切分，约 800+ 块（入库后以 Qdrant points_count 为准）。
- 场景覆盖：监控告警（Prometheus）、容器加固与故障排查（K8s）——正是运维知识库的核心问题域。

## 来源

- Prometheus 中文文档：https://github.com/daichangya/prometheus.io（Prometheus 官方文档的中文翻译 + 实践总结）
- Kubernetes 加固指南中文版：https://assets.jimmysong.io/books/kubernetes-hardening-guidance-zh.pdf（CISA 官方指南，Jimmy Song 个人翻译，仅供交流学习）

## 注意

- 语料里没有 .docx：公开的真实运维 .docx 很少；M1 的 .docx 解析照常做，用测试文件验证。
- 评测集（M2）从这 12 份文档出题：每篇出 2–3 道 + 改述版 + 陷阱题，做法沿用第 8 课第 3 步。
