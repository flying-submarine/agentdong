# 工作项目 M1：文档服务（端口 8001）——在第 9 课第 3 步的基础上加文件上传。
# 新增：POST /upload，接收前端传来的文件（PDF / Word / Markdown / 纯文本），
# 落盘 → 按格式解析成文本 → 和 /ingest 走同一条路（doc_id 按内容算、发 MQ、worker 入库）。
# worker 不用改：/upload 发的消息和 /ingest 一模一样（{task_id, doc_id, text}），
# 所以幂等、死信、SQLite 状态这些第 3 步的机制全都直接复用。
# 前端对照：antd Upload 组件发出去的就是 multipart/form-data 请求，
# 后端这边 UploadFile 就是接这个请求的；新东西在后端三步：接文件、落盘、解析。

# 引用的包（每个包是干嘛的）：
import hashlib        # 算哈希：给文本内容算一个固定指纹（doc_id），同样的文本算出来一样
import json           # 把 Python 字典转成 JSON 字符串，发给 RabbitMQ 时消息体必须是字符串
import os             # 路径操作：取文件名、拼上传目录、查文件大小
import shutil         # 流式复制文件：把上传的文件一点一点写到磁盘，不一次读进内存
import sqlite3        # Python 自带的轻量数据库：任务状态存在 tasks.db 文件里，重启不丢
import uuid           # 生成随机任务号 task_id（uuid4 是随机的，每次都不一样）
from datetime import datetime  # 取现在时间：任务创建时间存在 created_at 里，给前端列表显示用
import pdfplumber     # 解析 PDF：按页提取文字（pip install pdfplumber）
from docx import Document  # 解析 Word：读 .docx 的段落（pip install python-docx）
from fastapi import FastAPI, File, HTTPException, UploadFile  # FastAPI：搭 HTTP 服务；UploadFile/File：接上传的文件；HTTPException：返回 404 这类错误
from fastapi.middleware.cors import CORSMiddleware  # 跨域中间件：让浏览器里的前端能直接调这个服务
from pydantic import BaseModel  # 定义请求体的结构（/ingest 收什么字段、什么类型，FastAPI 自动校验）
import pika           # Python 连 RabbitMQ 的客户端库：发消息、声明队列都靠它
from qdrant_client import QdrantClient  # 连 Qdrant：删文档要按 doc_id 删点
from qdrant_client.models import FieldCondition, Filter, MatchValue  # 按 payload 条件删点：doc_id 等于谁就删谁的块
from rag_core import get_doc_stats, get_chunk_lengths, count_keyword  # 第 5 课的三个工具函数，复用

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 rabbitmq
QUEUE = "ingest_tasks"
DLX = "dlx"
DLQ = "ingest_tasks_dlq"
DB_PATH = "tasks.db"
UPLOAD_DIR = "uploads"  # 上传的原文件存在这里（留底 + 方便以后重新解析）
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 qdrant
COLLECTION = "docs"  # 和 8002 用同一个集合名
qclient = QdrantClient(url=QDRANT_URL)  # 模块层建一个连 Qdrant 的客户端（建的时候不真的连，调用时才连，Qdrant 没起也不炸导入）
MAX_FILE_SIZE = 20 * 1024 * 1024  # 单个文件上限 20MB，超过直接拒绝（消息和内存都吃不消大文件）
ALLOWED_EXTS = {".pdf", ".docx", ".md", ".txt"}  # 只收这四种格式，其他的报 400

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def db():
    # 打开 SQLite 连接，并保证 tasks 表存在（不存在就建一张）。
    # 每次操作都新开一个连接，用完就关——不跨请求共享连接，线程安全。
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks "
        "(task_id TEXT PRIMARY KEY, status TEXT, chars INTEGER, chunks INTEGER, error TEXT, filename TEXT, doc_id TEXT, created_at TEXT)"
    )
    # 老库补列：2026-11-21 加的 filename / doc_id / created_at 三列（给前端“已上传”列表用），
    # 服务器上的 tasks.db 是旧表结构，启动时自动补上，不用手动改库。
    # SQLite 的 ADD COLUMN 没有 IF NOT EXISTS，所以先查表结构再补。
    cols = [r[1] for r in conn.execute("PRAGMA table_info(tasks)")]
    if "filename" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN filename TEXT")
    if "doc_id" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN doc_id TEXT")
    if "created_at" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
    conn.commit()
    return conn

def save_task(task_id, status, chars, chunks=0, error="", filename=None, doc_id=None, created_at=None):
    # 把一条任务状态写进 tasks.db。任务号已存在就覆盖（INSERT OR REPLACE），不存在就新建。
    # filename / doc_id 只在上传时给；没给就保留库里已有的——task_done 回告时不能把文件名冲掉。
    # created_at 同理：新任务记现在，更新时保留原来的。
    conn = db()
    try:
        old = conn.execute("SELECT filename, doc_id, created_at FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if filename is None and old:
            filename = old[0]
        if doc_id is None and old:
            doc_id = old[1]
        if created_at is None and old:
            created_at = old[2]
        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, status, chars, chunks, error, filename, doc_id, created_at),
        )
        conn.commit()
    finally:
        conn.close()

def load_task(task_id):
    # 按任务号从 tasks.db 查一条任务状态。查不到返回 None（调用方决定报 404 还是新建）。
    conn = db()
    try:
        row = conn.execute(
            "SELECT status, chars, chunks, error, filename, doc_id, created_at FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"status": row[0], "chars": row[1], "chunks": row[2], "error": row[3], "filename": row[4], "doc_id": row[5], "created_at": row[6]}

def publish_ingest(task_id: str, doc_id: str, text: str, roles=None):
    # roles：这篇文档能给哪些角色看，比如 ["运维"]；不给就是公开，谁都能查（老文档都这样）。
    # 把入库任务发进 RabbitMQ 队列。发之前先把死信拓扑声明好（交换机、死信队列、绑定、主队列），
    # 声明和 worker 那边必须一模一样，否则 RabbitMQ 报 406。
    # 每调一次就新开一个连接，用完就关——写法笨，本课够用。
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    try:
        channel = connection.channel()
        # 死信交换机 + 死信队列：先声明，队列才能引用它。
        channel.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)
        channel.queue_declare(queue=DLQ, durable=True)
        channel.queue_bind(queue=DLQ, exchange=DLX, routing_key=QUEUE)
        channel.queue_declare(
            queue=QUEUE,
            durable=True,
            arguments={"x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": QUEUE},
        )
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE,
            body=json.dumps({"task_id": task_id, "doc_id": doc_id, "text": text, "roles": roles}, ensure_ascii=False),
            # delivery_mode=2：消息持久化，RabbitMQ 重启也不丢。
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()

def parse_pdf(path: str) -> str:
    # 解析 PDF：按页提取文字，用换行拼成一段全文。扫描件（图片型 PDF）提不出文字，会返回空串。
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)

def parse_docx(path: str) -> str:
    # 解析 Word：把 .docx 里每个段落的文字取出来，用换行拼成一段全文。表格里的文字不在段落里，取不到。
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def parse_text_file(path: str) -> str:
    # 解析 Markdown / 纯文本：就是读文件。先按 UTF-8 读，失败再按 GBK 读（Windows 上存的中文文件常是 GBK）。
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="gbk") as f:
            return f.read()

def parse_file(path: str, filename: str) -> str:
    # 按文件后缀选解析器。不支持的格式抛 ValueError（调用方转成 400 返回给前端）。
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext == ".docx":
        return parse_docx(path)
    if ext in (".md", ".txt"):
        return parse_text_file(path)
    raise ValueError(f"不支持的文件格式：{ext}，只支持 pdf / docx / md / txt")

class IngestIn(BaseModel):
    # /ingest 的请求体：text 是要入库的文档全文；roles 是这篇能给哪些角色看（比如 ["运维"]），不给就是公开。
    text: str
    roles: list[str] | None = None

class TaskDoneIn(BaseModel):
    # /task/{task_id}/done 的请求体：worker 做完后回告入库了几块。
    chunks: int

class TaskFailedIn(BaseModel):
    # /task/{task_id}/failed 的请求体：worker 失败时回告错误信息，默认空字符串。
    error: str = ""

@app.post("/ingest")
def ingest(req: IngestIn):
    # 接收一段文本，生成任务号和文档号，记状态、发消息、立刻返回。
    # doc_id 按内容算：同样的文本每次都一样，重复入库时 worker 生成的点 id 也一样，upsert 就是覆盖。
    task_id = uuid.uuid4().hex[:12]
    doc_id = hashlib.sha256(req.text.encode("utf-8")).hexdigest()[:12]
    save_task(task_id, "processing", len(req.text))
    publish_ingest(task_id, doc_id, req.text, req.roles)
    return {"task_id": task_id, "doc_id": doc_id, "status": "processing", "message": "已收到，正在后台处理", "chars": len(req.text)}

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    # 接收前端上传的文件（multipart/form-data），落盘 → 解析 → 和 /ingest 走同一条入库路。
    # 顺序：1. 校验格式；2. 流式落盘（不一次读进内存）；3. 查大小；4. 按格式解析；
    # 5. 文本为空就报 400；6. 按内容算 doc_id；7. 记状态、发 MQ、立刻返回任务号。
    # 注意：文件名只取最后一部分（防 ../../ 这种路径穿越）；原文件留在 uploads/ 里，文件名带任务号，方便追溯。
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{ext}，只支持 pdf / docx / md / txt")
    task_id = uuid.uuid4().hex[:12]
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = os.path.basename(file.filename or "upload")
    saved_path = os.path.join(UPLOAD_DIR, f"{task_id}_{safe_name}")
    # 流式落盘：一次只读 1MB 写磁盘，大文件也不会把内存撑爆。
    with open(saved_path, "wb") as out:
        shutil.copyfileobj(file.file, out, length=1024 * 1024)
    if os.path.getsize(saved_path) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 20MB 上限")
    try:
        text = parse_file(saved_path, safe_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败：{e}")
    if not text.strip():
        raise HTTPException(status_code=400, detail="解析出来是空的：文件里没有可提取的文字（可能是扫描件）")
    doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    save_task(task_id, "processing", len(text), filename=safe_name, doc_id=doc_id)
    publish_ingest(task_id, doc_id, text)
    return {"task_id": task_id, "doc_id": doc_id, "filename": safe_name, "status": "processing", "message": "已收到，正在后台处理", "chars": len(text)}

@app.get("/task/{task_id}")
def get_task(task_id: str):
    # 按任务号查状态（前端轮询就调这个）。任务号不存在报 404。
    task = load_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务号不存在")
    return {"task_id": task_id, **task}

@app.post("/task/{task_id}/done")
def task_done(task_id: str, req: TaskDoneIn):
    # worker 做完后回告：把任务状态改成 done，并记下入库了几块。任务号不存在报 404。
    task = load_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务号不存在")
    save_task(task_id, "done", task["chars"], req.chunks)
    return {"task_id": task_id, **load_task(task_id)}

@app.post("/task/{task_id}/failed")
def task_failed(task_id: str, req: TaskFailedIn):
    # worker 失败时回告：把任务状态改成 failed，并存下错误信息。
    # 失败回告可能来自没经过 /ingest 的坏消息，任务号在库里没有——这时直接建一条 failed 记录，而不是 404。
    task = load_task(task_id)
    chars = task["chars"] if task else 0
    save_task(task_id, "failed", chars, 0, req.error[:200])
    return {"task_id": task_id, **load_task(task_id)}

@app.delete("/doc/{doc_id}")
def delete_doc_endpoint(doc_id: str):
    # M3 第 4 步加的：按文档号删掉这篇文档在 Qdrant 里的所有块。先数后删，返回删了几块；
    # 一篇都没有也返回 0，不报错。注意：只删向量库里的点，uploads/ 里的原文件和 tasks.db 里的任务记录不动（留底备查）。
    filt = Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])
    try:
        n = qclient.count(COLLECTION, count_filter=filt).count
    except Exception:
        n = 0
    qclient.delete(collection_name=COLLECTION, points_selector=filt)
    return {"doc_id": doc_id, "deleted": n}

@app.get("/stats")
def stats():
    # 返回 sample.txt 的总字数和块数（第 2 课的 get_doc_stats）。
    return get_doc_stats()

@app.get("/count")
def count_docs():
    # 数知识库里有几份文档、几块：Qdrant 没有直接数去重值的接口，
    # 所以 scroll（翻页读）全部点，按 doc_id 去重。648 个点这个量级一次够了，分页循环是为了以后上万了也不炸。
    # 返回 {"docs": 份数, "points": 块数}，前端拿 docs 显示。
    try:
        doc_ids = set()
        offset = None
        while True:
            points, offset = qclient.scroll(
                COLLECTION,
                limit=1000,
                offset=offset,
                with_payload=["doc_id"],
                with_vectors=False,
            )
            for p in points:
                if p.payload and p.payload.get("doc_id"):
                    doc_ids.add(p.payload["doc_id"])
            if offset is None:
                break
        total = qclient.count(COLLECTION).count
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量库连不上：{e}")
    return {"docs": len(doc_ids), "points": total}

@app.get("/list")
def list_docs():
    # 文档列表（给前端 Recent Records 用）：只取 filename 不为空的任务
    # （/ingest 的纯文本任务没有文件名，不列）。按入库顺序倒序，最新在前。
    # 返回 {data: [...]}，字段是前端要的驼峰名：docId / fileName / createTime / chars / chunks / status。
    # 注意：路由不能叫 /docs——FastAPI 的 /docs 被内置 Swagger 页面占了，自己写的 /docs 永远抢不过它。
    # 对外还是 /api/doc/docs（前端契约不变），Nginx 那边把 /api/doc/docs 重写到 /list。
    conn = db()
    try:
        rows = conn.execute(
            "SELECT doc_id, filename, created_at, chars, chunks, status FROM tasks "
            "WHERE filename IS NOT NULL ORDER BY rowid DESC"
        ).fetchall()
    finally:
        conn.close()
    return {"data": [{"docId": r[0], "fileName": r[1], "createTime": r[2], "chars": r[3], "chunks": r[4], "status": r[5]} for r in rows]}

@app.get("/docs/{doc_id}/content")
def get_doc_content(doc_id: str):
    # 按文档号取全文预览：从 Qdrant 里把这篇的所有块按 chunk_id 排好拼起来。
    # 注意：块是 200 字、步长 150 的滑动窗口，相邻块有 50 字重叠，拼起来会有重复——预览够用，不是原文件。
    filt = Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])
    points, _ = qclient.scroll(
        COLLECTION,
        limit=1000,
        with_payload=["doc_id", "chunk_id", "text"],
        with_vectors=False,
        scroll_filter=filt,
    )
    if not points:
        raise HTTPException(status_code=404, detail="文档不存在")
    chunks = sorted(points, key=lambda p: (p.payload.get("chunk_id") if p.payload else 0) or 0)
    text = "\n\n".join((p.payload.get("text") or "") for p in chunks)
    return {"data": {"text": text}}

@app.get("/chunk_lengths")
def chunk_lengths():
    # 返回每块的长度（第 5 课的 get_chunk_lengths）。
    return get_chunk_lengths()

@app.get("/count_keyword")
def count_keyword_endpoint(keyword: str):
    # 返回某个关键词在文档里出现了几次（第 5 课的 count_keyword）。
    return count_keyword(keyword)

@app.get("/health")
def health():
    # 健康检查：服务活着就返回 ok，给部署和监控用。
    return {"status": "ok", "service": "doc-service"}
