# 后端镜像：三个服务（doc/retrieval/agent）+ worker 共用这一个镜像，
# 启动时用不同的命令区分（见 docker-compose.yml 的 command）。
FROM python:3.12-slim
WORKDIR /app
# 先拷 requirements，利用 Docker 缓存：依赖不变就不重新 pip install
COPY requirements.txt .
# 清华 pip 源（国内快）；--no-cache-dir 不留缓存，镜像小一点
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# 再拷代码和演示文档（*.py + sample.txt；sample.txt 从 day1 拷进 backend/ 后才有）
COPY *.py sample.txt ./
EXPOSE 8001 8002 8003
# 默认起文档服务；compose 里每个服务会用自己的 command 覆盖这一行
CMD ["uvicorn", "doc_service:app", "--host", "0.0.0.0", "--port", "8001"]
