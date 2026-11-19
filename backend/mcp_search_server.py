# M4 第 1 步：MCP server——把知识库检索 search_kb 暴露成 MCP 工具（stdio 传输，不占端口）。
# 第 7 课是“我的图调别人的 MCP 工具”，这次反过来：“我的 search_kb 变成 MCP 工具给别人调”。
# 只暴露查（search_kb），不暴露删（delete_doc）：改库的操作不对外，这是 M4 的安全边界。
# 注意：stdio 传输下 stdout 是协议专用管道，绝对不能往 stdout 打日志（print 默认走 stdout），
# 所以这个文件里没有任何 print；真要记日志走 sys.stderr。

import os  # 读环境变量：8002 的地址可以改，不写死
import httpx  # 发 HTTP 请求：调 8002 的 /vector_search（现成的混合检索 + 改写 + 重排 + 兜底）
from mcp.server.fastmcp import FastMCP  # MCP 的 server 框架（第 7 课同款；版本钉在 mcp<2，2.x 改名了）

# server 的名字：客户端连上来在菜单里看到的就是它
mcp = FastMCP("agentdong-kb")

# 8002 的地址：默认本机 8002；compose 部署时用环境变量改成服务名
RETRIEVAL_URL = os.environ.get("RETRIEVAL_URL", "http://127.0.0.1:8002/vector_search")


@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> str:
    """在企业运维知识库里查问题，返回最相关的文档块（带分数）。
    参数 query 是用户原问题（中文），top_k 是要几块（默认 3）。
    只读，不改库；删文档不在这儿，MCP 对外不提供删除。"""
    try:
        # trust_env=False：不读终端的代理环境变量——8002 是本机服务，走代理会 502（第 9 课的坑）
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            resp = client.post(RETRIEVAL_URL, json={"q": query, "top_k": top_k, "rewrite": True})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        # 8002 没起、超时、报错：不炸 server，把原因当结果文本回给客户端
        return f"检索服务不可用（8002）：{type(e).__name__} {e}。先确认 retrieval_service.py 在跑。"
    results = data.get("results", [])
    if not results:
        return "知识库里没有相关内容。"
    head = f"检索到 {len(results)} 块（改写后查询：{data.get('rewritten_query', query)}）"
    if data.get("fallback_used"):
        head += "（改写效果差，已用原问题兜底）"
    lines = [head + "："]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('doc_id')}:{r.get('chunk_id')}（分数 {r.get('score')}）")
        lines.append(r.get("text", ""))
    return "\n".join(lines)


if __name__ == "__main__":
    # 默认 stdio 传输：server 当子进程被客户端拉起，零网络配置（第 7 课同款）
    mcp.run()
