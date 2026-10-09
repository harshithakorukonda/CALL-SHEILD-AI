class WebSocketManager:
    def __init__(self):
        self.connections = set()

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.connections.discard(connection)
