# 存储当前所有连接的 WebSocket 客户端
from typing import List

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

clients: List[WebSocket] = []
router = APIRouter()


# 连接时，添加客户端
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # 接受 WebSocket 连接
    clients.append(websocket)  # 将连接的客户端添加到列表

    try:
        while True:
            # 接收消息
            message = await websocket.receive_text()

            # 向所有连接的客户端广播消息
            for client in clients:
                if client != websocket:  # 不发送给自己
                    await client.send_text(f"User says: {message}")
    except WebSocketDisconnect:
        # 客户端断开连接时，移除该客户端
        clients.remove(websocket)
