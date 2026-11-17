# -*- coding: utf-8 -*-
"""统一加载项目根目录 .env 里的密钥。

用法：在需要读环境变量的脚本最前面加一行 `import config`，
之后 os.environ["DEEPSEEK_API_KEY"] / os.environ["SILICONFLOW_API_KEY"] 就能直接取到。

优先级：终端里已 export 的变量 > .env 文件（load_dotenv 默认不覆盖已存在的变量）。
所以原来 `export XXX=... python app.py` 的临时覆盖方式依然有效，
但日常直接 `python app.py` 就行，不用再每次 export。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent / ".env"

# 文件不存在也不报错，只是加载不到（保持和以前一致：key 缺失时由调用方报错）
load_dotenv(dotenv_path=ENV_FILE, override=False)


def require(name: str) -> str:
    """取一个必填的密钥；缺失时给出明确的中文提示，而不是 KeyError。"""
    value = os.environ.get(name, "").strip()
    if not value or "填你的" in value:
        raise RuntimeError(
            f"缺少环境变量 {name}。请在 {ENV_FILE} 中填写，"
            f"或临时使用 export {name}=你的key 后再运行。"
        )
    return value
