import os
import re
import shutil
import sys
import unicodedata


def load_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def chunk_text(text, size=200, overlap=50):
    """按字符切块，带重叠，避免一句话被拦腰切断后两边都查不到。"""
    chunks, start = [], 0
    step = size - overlap
    while start < len(text):
        chunks.append(text[start:start + size])
        start += step
    return chunks


def search(chunks, query):
    """关键词计分检索：命中词越多分越高，返回 (分数, 编号, 片段)。"""
    keywords = [w for w in re.split(r"\W+", query.lower()) if w]
    scored = []
    for i, chunk in enumerate(chunks):
        low = chunk.lower()
        score = sum(low.count(k) for k in keywords)
        if score > 0:
            scored.append((score, i, chunk))
    scored.sort(reverse=True)
    return scored


COLOR_ENABLED = (
    sys.stdout.isatty()
    and "NO_COLOR" not in os.environ
    and os.environ.get("TERM") != "dumb"
)
STYLES = {
    "bold": "1",
    "dim": "2",
    "red": "91",
    "green": "92",
    "yellow": "93",
    "blue": "94",
    "cyan": "96",
}


def paint(text, *styles):
    if not COLOR_ENABLED or not styles:
        return str(text)
    codes = ";".join(STYLES[style] for style in styles)
    return f"\033[{codes}m{text}\033[0m"


def display_width(char):
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1


def wrap_text(text, width):
    """按终端显示宽度换行，避免中文按一个字符计算导致再次挤在一起。"""
    lines = []
    for raw_line in text.expandtabs(4).splitlines() or [""]:
        line, columns = "", 0
        for char in raw_line:
            char_columns = display_width(char)
            if line and columns + char_columns > width:
                lines.append(line)
                line, columns = "", 0
            line += char
            columns += char_columns
        lines.append(line)
    return lines


def highlight_terms(text, query):
    terms = sorted({w for w in re.split(r"\W+", query, flags=re.UNICODE) if w}, key=len, reverse=True)
    if not terms:
        return text
    pattern = re.compile("(" + "|".join(re.escape(term) for term in terms) + ")", re.IGNORECASE)
    return pattern.sub(lambda match: paint(match.group(0), "bold", "yellow"), text)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.txt"
    query = sys.argv[2] if len(sys.argv) > 2 else "RAG"
    chunks = chunk_text(load_text(path))
    results = search(chunks, query)[:3]
    print(
        f"{paint('检索结果', 'bold', 'cyan')}  "
        f"切出 {paint(len(chunks), 'bold', 'green')} 块  "
        f"查询 {paint(query, 'bold', 'yellow')}  "
        f"命中 {paint(len(results), 'bold', 'green')} 条"
    )
    if not results:
        print(paint("● 没有找到匹配内容", "bold", "red"))
        raise SystemExit(0)

    columns = shutil.get_terminal_size(fallback=(80, 24)).columns
    body_width = max(20, columns - 6)
    results = search(chunks, query)
    if not results:
        print("没有命中，换个词试试")
    else:
        for score, i, chunk in results[:3]:
            print(f"\n--- 块 #{i}（命中 {score} 次）---")
            print(chunk.strip()[:300])

    # for rank, (score, i, chunk) in enumerate(results, 1):
    #     snippet = re.sub(r"[ \t]+", " ", chunk.strip())
    #     truncated = len(snippet) > 300
    #     snippet = snippet[:300]
    #     print()
    #     print(
    #         f"{paint('●', 'bold', 'cyan')} "
    #         f"{paint(f'结果 {rank}', 'bold', 'cyan')}  "
    #         f"{paint(f'块 #{i}', 'bold', 'blue')}  "
    #         f"{paint(f'命中 {score} 次', 'bold', 'green')}"
    #     )
    #     for line in wrap_text(snippet, body_width):
    #         print(f"  {paint('│', 'bold', 'blue')}  {highlight_terms(line, query)}")
    #     ending = "└─ 片段已截断" if truncated else "└─"
    #     print(f"  {paint(ending, 'dim', 'blue')}")
