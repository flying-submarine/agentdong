# 冒烟测试：DeepSeek 的 json_object + 流式（streaming）支不支持（M5 第 3 步第 0 步）。
# 放 ~/Desktop/day1 里跑，能跑就删。只测模型，不碰图和后端。
import asyncio  # 跑 async 函数用
import os  # 读环境变量里的 key
from dotenv import load_dotenv  # 读 .env：把 key 读进环境变量（day1 自带 python-dotenv）
load_dotenv()  # 从当前目录往上找 .env（在 ~/Desktop/day1 跑就读到 day1/.env）
from langchain_openai import ChatOpenAI  # 调 DeepSeek 的 LangChain 客户端
from langchain_core.messages import HumanMessage  # 人发的问题

llm_json = ChatOpenAI(model="deepseek-flash", base_url="https://api.deepseek.com",
                      api_key=os.environ.get("DEEPSEEK_API_KEY"), temperature=0,
                      response_format={"type": "json_object"})

async def main():
    # 只回一段小 JSON，看是不是一块一块吐出来
    async for c in llm_json.astream([HumanMessage('只回 JSON：{"a": "你好"}')]):
        print(repr(c.content), end=" ", flush=True)
    print()  # 换行收尾

asyncio.run(main())
