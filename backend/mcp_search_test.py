# M4 第 1 步测试：手写 MCP 客户端（第 7 课 mcp_client.py 的套路），连上 mcp_search_server.py，
# 先问菜单（应只有 search_kb 一个工具），再调一次 search_kb，看能不能查到块。
# 8002 必须先在跑（server 只是转调 8002，自己不存数据）。

import asyncio  # 跑异步主函数：MCP 客户端全是异步的
import os  # 拼 server 文件的绝对路径：按测试文件自己的位置找，不怕从哪个目录跑
import sys  # 退出码：工具没找到或调用失败就非零退出
from mcp import ClientSession, StdioServerParameters  # ClientSession：协议连接的一端；StdioServerParameters：怎么把 server 当子进程拉起来
from mcp.client.stdio import stdio_client  # stdio 传输的客户端：拉起子进程，用标准输入输出传话

# server 文件的绝对路径：跟这个测试文件在同一个 backend/ 目录下
SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_search_server.py")


async def main():
    # Host 的活：用命令把 server 当子进程启动——python 是 venv 里的（终端里 venv 开着）
    params = StdioServerParameters(command="python", args=[SERVER_PATH])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()  # 握手：对协议版本和能力
            tools = await session.list_tools()  # 问菜单
            names = [t.name for t in tools.tools]
            print("菜单：", names)
            if "search_kb" not in names:
                print("没找到 search_kb，server 不对。")
                sys.exit(1)
            if "delete_doc" in names:
                print("菜单里不该有 delete_doc！")
                sys.exit(1)
            result = await session.call_tool("search_kb", {"query": "联邦是干嘛的？"})
            print("调用结果：")
            for c in result.content:
                print(c.text)


if __name__ == "__main__":
    asyncio.run(main())
