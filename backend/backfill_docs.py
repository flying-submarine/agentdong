# 一次性补录脚本：把 2026-11-21 之前上传的文件（当时代码没存文件名）补进 tasks.db，
# 这样前端的 Recent Records 列表能看到它们。跑一次就行，重复跑也不会重复写。
# 用法（服务器上，部署新代码并确认 /docs 能打开之后）：
#   cd /home/ubuntu/agentdong/backend && python3 backfill_docs.py
# 原理：uploads/ 里的文件叫 {task_id}_{原文件名}，按 task_id 找到任务行，
# 重新解析文件算 doc_id（和上传时同一个算法），把 filename / doc_id / createTime（文件修改时间）写回去。
# 注意：13 份语料当初就是走 /upload 传的，uploads/ 里有原文件，能补上；
# 如果哪篇是走 /ingest 纯文本入库的（uploads/ 里没文件），那篇就补不了——它是种子数据，不是上传，不在列表里也正常。

# 引用的包（每个包是干嘛的）：
import hashlib  # 算哈希：按内容算 doc_id，和上传时同一个算法
import os  # 读 uploads/ 目录、取文件修改时间
from datetime import datetime  # 把文件修改时间转成 "2026-11-19 20:00:00" 这种显示格式
from doc_service import UPLOAD_DIR, db, parse_file  # UPLOAD_DIR：原文件目录；db()：连 tasks.db（自动建表补列）；parse_file：按格式解析文件

def main():
    # db() 会保证表和新列都存在（老库自动补列），拿它返回的连接直接用。
    conn = db()
    fixed = 0
    skipped = 0
    for name in sorted(os.listdir(UPLOAD_DIR)):
        path = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(path):
            continue
        # 文件名是 {task_id}_{原文件名}，task_id 是 12 位十六进制，不含下划线，所以按第一个下划线切。
        task_id, _, safe_name = name.partition("_")
        if not task_id or not safe_name:
            skipped += 1
            continue
        row = conn.execute("SELECT filename FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        # 任务行不存在、或者已经有文件名了，都跳过（重复跑也不会重复写）。
        if row is None or row[0]:
            skipped += 1
            continue
        try:
            text = parse_file(path, safe_name)
        except Exception as e:
            print(f"跳过 {name}：解析失败 {e}")
            skipped += 1
            continue
        if not text.strip():
            print(f"跳过 {name}：解析出来是空的")
            skipped += 1
            continue
        doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        created_at = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE tasks SET filename = ?, doc_id = ?, created_at = ? WHERE task_id = ?",
            (safe_name, doc_id, created_at, task_id),
        )
        fixed += 1
        print(f"补上 {safe_name}（doc_id {doc_id}）")
    conn.commit()
    conn.close()
    print(f"完成：补了 {fixed} 个，跳过 {skipped} 个")

if __name__ == "__main__":
    main()
