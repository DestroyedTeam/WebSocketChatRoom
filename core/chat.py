import hashlib
import json
import os
import random
import shutil
import string
from datetime import datetime, timedelta

import starlette.datastructures
from aioredis import Redis
from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from loguru import logger

from .deps import get_redis_session

# 存储 WebSocket 连接和映射关系
clients: list[WebSocket] = []
client_map: dict[WebSocket, dict[str, str]] = {}

router = APIRouter()


# 生成随机用户名
def generate_random_username() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


# 消息存储到 Redis
async def store_message_in_redis(message: str | dict, username: str, ip: str, session: Redis):
    message_data = {
        "username": username,
        "ip": ip,
        "timestamp": datetime.now().isoformat(),
        "message": message,
    }
    # 将消息数据以 JSON 字符串的形式存储到 Redis 列表
    await session.lpush("chat_history", json.dumps(message_data))
    # 设置消息过期时间为7天
    await session.expire("chat_history", timedelta(days=7))


# 获取历史消息
async def get_chat_history(session: Redis):
    messages = await session.lrange("chat_history", 0, 99)
    return [json.loads(msg) for msg in reversed(messages)]


# 使用 SHA-256 对文件名进行加密
def encrypt_filename(filename: str) -> str:
    # 使用 SHA-256 对文件名进行哈希加密
    sha256_hash = hashlib.sha256()
    sha256_hash.update(filename.encode("utf-8"))  # 对文件名进行编码
    return sha256_hash.hexdigest()  # 返回加密后的文件名


# 上传文件处理，文件大小小于50MB时通过WebSocket直接传输，超过50MB时使用POST上传
async def handle_file_upload(file: UploadFile | bytes, file_name: str = None) -> str:
    # 获取文件的扩展名
    file_name, ext = os.path.splitext(file_name or file.filename)
    file_name = encrypt_filename(file_name) or encrypt_filename(file.filename)
    filename = f"{file_name}{ext}"
    file_location = f"/media/uploads/{filename}"

    # 保存文件到指定目录
    os.makedirs(os.path.dirname(file_location.lstrip("/")), exist_ok=True)
    with open(file_location.lstrip("/"), "wb") as f:
        shutil.copyfileobj(file.file, f) if isinstance(file, starlette.datastructures.UploadFile) else f.write(file)

    return file_location


# WebSocket 连接处理
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, rds_session: Redis = Depends(get_redis_session)):
    await websocket.accept()
    clients.append(websocket)

    # 获取客户端 IP 和生成随机用户名
    client_real_ip = str(websocket.client)
    username = generate_random_username()

    # 保存映射关系
    client_map[websocket] = {"username": username, "ip": client_real_ip}

    # 向客户端发送历史消息
    chat_history = await get_chat_history(rds_session)
    for message in chat_history:
        await websocket.send_json(message)

    try:
        while True:
            # 接收客户端发送的消息
            origin_message = await websocket.receive_json()
            if origin_message.get("type") == "file":
                if origin_message.get("filename") and origin_message.get("fileSize") < 50 * 1024 * 1024:
                    file_data = await websocket.receive_bytes()
                    print(encrypt_filename(origin_message.get("filename")))
                    if not os.path.exists(f"/media/uploads/{encrypt_filename(origin_message.get('filename'))}"):
                        # 接收文件二进制数据
                        if file_data:
                            file_location = await handle_file_upload(
                                file_data, file_name=origin_message.get("filename")
                            )
                            origin_message["url"] = file_location
                            logger.info(f"File saved: {file_location}")
                else:
                    logger.warning("File size exceeds 50MB, please use POST to upload.")
                    await websocket.send_json({"error": "File size exceeds 50MB, please use POST to upload."})

            # 获取客户端的用户名和 IP 地址
            client_username = client_map[websocket]["username"]
            client_real_ip = client_map[websocket]["ip"]

            # 将消息存储到 Redis
            await store_message_in_redis(origin_message, client_username, client_real_ip, rds_session)

            # 向所有连接的客户端广播消息
            for client in clients:
                await client.send_json(
                    {
                        "username": client_map[client]["username"],
                        "ip": client_map[client]["ip"],
                        "timestamp": datetime.now().isoformat(),
                        "message": origin_message,
                    }
                )

    except WebSocketDisconnect:
        # 断开连接时，清除客户端映射关系
        del client_map[websocket]
        clients.remove(websocket)


# 处理文件上传的HTTP POST请求
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 处理文件上传，并返回文件存储位置
        file_location = await handle_file_upload(file)

        # 返回文件的 URL
        return {"fileUrl": f"{file_location}"}

    except ValueError as e:
        return {"error": str(e)}
