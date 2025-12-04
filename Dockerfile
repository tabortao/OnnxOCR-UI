# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制精简依赖文件到工作目录
COPY ["requirements webui.txt", "requirements.txt"]

# 安装系统依赖与 Python 包
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 libgl1 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目目录中的所有文件到镜像中
COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 5005

# 启动 FastAPI Web 应用
CMD ["uvicorn", "webui:app", "--host", "0.0.0.0", "--port", "5005"]
