import json
import random
import string
from datetime import timedelta
from typing import List, Dict
from aioredis import Redis
from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect
from .deps import get_redis_session
from datetime import datetime

clients: List[WebSocket] = []
client_map: Dict[str, Dict[str, str]] = {}  # {websocket_id: {"username": username, "ip": ip}}

router = APIRouter()


# 生成随机用户名
def generate_random_username() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


# 消息存储到 Redis
async def store_message_in_redis(message: str, username: str, ip: str, session: Redis):
    message_data = {
        "username": username,
        "ip": ip,
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    # 将消息数据以 JSON 字符串的形式存储到 Redis 列表
    await session.lpush("chat_history", json.dumps(message_data))
    # 设置消息过期时间为7天
    await session.expire("chat_history", timedelta(days=7))


# 获取历史消息
async def get_chat_history(session: Redis):
    messages = await session.lrange("chat_history", 0, 99)
    return [json.loads(msg) for msg in reversed(messages)]


# WebSocket 连接处理
@router.websocket("/ws/chat")
async def websocket_endpoint(
        websocket: WebSocket,
        rds_session: Redis = Depends(get_redis_session)
):
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
        await websocket.send_text(f"{message['timestamp']} - {message['username']} ({message['ip']}): {message['message']}")

    try:
        while True:
            # 接收客户端发送的消息
            message = await websocket.receive_text()

            # 获取客户端的用户名和 IP 地址
            client_username = client_map[websocket]["username"]
            client_real_ip = client_map[websocket]["ip"]

            # 将消息存储到 Redis
            await store_message_in_redis(message, client_username, client_real_ip, rds_session)

            # 向所有连接的客户端广播消息
            for client in clients:
                # 获取发送者的用户名
                sender_username = client_map[client]["username"]
                sender_ip = client_map[client]["ip"]
                # 发送时，附加用户名、IP 和时间戳
                await client.send_text(f"{datetime.now().isoformat()} - {sender_username} ({sender_ip}): {message}")

    except WebSocketDisconnect:
        # 断开连接时，清除客户端映射关系
        del client_map[websocket]
        clients.remove(websocket)
