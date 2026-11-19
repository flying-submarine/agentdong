# 第 9 课第 3 步：入库消费者 worker——三个变化。
# 1. 幂等：点的 id 不再按“集合里现有块数”往后排，改用 uuid5（doc_id + 块号）算出来——
#    同样的文档、同样的块，算出来的 id 永远一样，Qdrant 的 upsert 按 id 覆盖，重复入库不会累加。
# 2. 补偿（Saga 的最小例子）：处理失败时，先把本次已写入的点按 doc_id 删掉，再回告 failed、
#    再 nack 不重回队列——失败的任务不留一半数据。
# 3. 死信：队列声明加上死信交换机，nack(requeue=False) 的消息进死信队列 ingest_tasks_dlq，
#    在管理界面能看到，而不是直接丢掉。注意：队列参数和 doc_service 那边必须一模一样，
#    否则 RabbitMQ 报 406；改参数前要先删掉第 2 步建的旧队列。

# 引用的包（每个包是干嘛的）：
import json           # 解析 RabbitMQ 消息体（JSON 字符串转回 Python 字典）
import os             # 读环境变量：服务地址默认 localhost，Docker 里 compose 传服务名
import uuid           # uuid5：按“文档 id + 块号”算出确定性的点 id，同样的输入永远同一个 id
import httpx          # 发 HTTP 请求：回告 doc 服务任务完成 / 失败
import pika           # Python 连 RabbitMQ 的客户端库：收消息、签收、声明队列都靠它
from qdrant_client import QdrantClient  # 连 Qdrant 的客户端：查集合、写点、删点
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, MatchValue
#   Distance：向量距离算法（COSINE 余弦相似度）；PointStruct：一个向量点（id + 向量 + payload）；
#   VectorParams：建集合时的参数（维度 1024、距离算法）；Filter / FieldCondition / MatchValue：
#   补偿删除时用的查询条件（按 doc_id 匹配要删的点）
from chunk_search import chunk_text  # 第 1 课的切块函数：200 字一块，重叠 50 字
from rag_core import embed_client    # 第 4 课的 SiliconFlow 客户端：调 BAAI/bge-m3 算向量

QUEUE = "ingest_tasks"
DLX = "dlx"
DLQ = "ingest_tasks_dlq"
COLLECTION = "docs"
DOC_URL = os.environ.get("DOC_URL", "http://127.0.0.1:8001")  # 环境变量优先：本地跑默认 localhost，Docker 里 compose 传服务名 doc-service
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")  # 同上，Docker 里是 qdrant:6333
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")  # 同上，Docker 里是 rabbitmq

# 连 Qdrant，集合不存在就建一个（1024 维、余弦相似度，和第 8 课的参数一样）。
qclient = QdrantClient(url=QDRANT_URL)
if not qclient.collection_exists(COLLECTION):
    qclient.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

def embed_batch(texts):
    # 批量算向量：一次请求算所有块的向量（和第 8 课 qdrant_service_test.py 里一样的做法）。
    resp = embed_client.embeddings.create(model="BAAI/bge-m3", input=texts)
    return [d.embedding for d in resp.data]

def point_id(doc_id: str, chunk_index: int):
    # 按“文档 id + 块号”算出点的 id。uuid5 是确定性的：同样的输入永远算出同样的 UUID——这就是幂等的关键。
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk_index}"))

def handle(doc_id, text, roles=None):
    # 处理一条入库任务：切块 → 批量算向量 → 写进 Qdrant。返回入库了几块。
    # roles 写进 payload 的 allowed_roles：有标签只给标签里的角色看；没给就不写这个字段，老文档默认公开。
    chunks = chunk_text(text)
    vectors = embed_batch(chunks)
    payloads = []
    for i in range(len(chunks)):
        payload = {"doc_id": doc_id, "chunk_id": i, "text": chunks[i]}
        if roles:
            payload["allowed_roles"] = list(roles)
        payloads.append(payload)
    points = [
        PointStruct(id=point_id(doc_id, i), vector=vectors[i], payload=payloads[i])
        for i in range(len(chunks))
    ]
    qclient.upsert(COLLECTION, points)
    print(f"已入库 {len(chunks)} 块，doc_id {doc_id}")
    return len(chunks)

def compensate(doc_id):
    # 补偿：按 doc_id 删掉本次任务已写入的点。失败的任务不留一半数据。
    qclient.delete(
        collection_name=COLLECTION,
        points_selector=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
    )
    print(f"已补偿删除 doc_id {doc_id} 的点")

def report_done(task_id, n_chunks):
    # 回告 doc 服务任务完成了，前端轮询 /task/{task_id} 就能看到 done。
    # 回告失败也不影响数据——数据已经在 Qdrant 里了，只是前端会一直看到 processing。
    try:
        httpx.post(f"{DOC_URL}/task/{task_id}/done", json={"chunks": n_chunks}, timeout=5.0)
    except Exception as e:
        print("回告 doc 服务失败（数据已入库，状态没同步）:", type(e).__name__, e)

def report_failed(task_id, error):
    # 回告 doc 服务任务失败了，并把错误信息带过去，任务状态改成 failed。
    try:
        httpx.post(f"{DOC_URL}/task/{task_id}/failed", json={"error": error}, timeout=5.0)
    except Exception as e:
        print("回告 failed 失败:", type(e).__name__, e)

def callback(ch, method, properties, body):
    # RabbitMQ 每推一条消息就调一次这个函数。body 是消息体（JSON 字符串）。
    # 成功：处理 → 回告 done → ack 签收，消息从队列删除。
    # 失败：补偿删除 → 回告 failed → nack 不重回队列，消息进死信队列。
    try:
        task = json.loads(body.decode("utf-8"))
    except Exception as e:
        print("消息不是合法 JSON，直接进死信：", type(e).__name__, e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    task_id = task.get("task_id", "unknown")
    doc_id = task.get("doc_id", task_id)
    try:
        n = handle(doc_id, task["text"], task.get("roles"))
        report_done(task_id, n)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print("任务处理失败，开始补偿：", type(e).__name__, e)
        try:
            compensate(doc_id)
        except Exception as ce:
            print("补偿删除失败（需要人工处理）：", type(ce).__name__, ce)
        report_failed(task_id, f"{type(e).__name__}: {e}")
        # requeue=False：不再重试，消息进死信队列。
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# 启动时连 RabbitMQ，声明死信拓扑，然后开始消费。声明必须和 doc_service 那边一模一样，否则报 406。
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)
channel.queue_declare(queue=DLQ, durable=True)
channel.queue_bind(queue=DLQ, exchange=DLX, routing_key=QUEUE)
channel.queue_declare(
    queue=QUEUE,
    durable=True,
    arguments={"x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": QUEUE},
)
channel.basic_consume(queue=QUEUE, on_message_callback=callback, auto_ack=False)
print("worker 已启动，等 ingest 任务……（Ctrl+C 停）")
channel.start_consuming()
