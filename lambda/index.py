# app.py

import json
import urllib.request
import urllib.error
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# CORS 設定（必要に応じて調整）
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["OPTIONS", "POST"],
    allow_headers=["*"],
)

# ngrok 経由の外部 FastAPI エンドポイント
EXTERNAL_GENERATE_URL = "https://0d2d-34-125-252-73.ngrok-free.app/generate"

# リクエスト／レスポンスのスキーマ定義
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversationHistory: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    success: bool
    response: str
    conversationHistory: List[Message]


@app.post("/generate", response_model=ChatResponse)
async def generate(req: ChatRequest):
    """
    受け取ったメッセージ＋履歴をそのまま ngrok 経由の FastAPI に POST し、
    返ってきた JSON をそのまま返却します。
    """
    # 1) リクエストボディを JSON にエンコード
    payload = req.dict()
    body_bytes = json.dumps(payload).encode("utf-8")

    # 2) urllib.request で POST
    request = urllib.request.Request(
        url=EXTERNAL_GENERATE_URL,
        data=body_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            resp_text = resp.read().decode("utf-8")
            result = json.loads(resp_text)
    except urllib.error.HTTPError as e:
        # 外部 API の 4xx/5xx エラーをそのまま返却
        error_body = e.read().decode("utf-8")
        raise HTTPException(status_code=e.code, detail=error_body)
    except urllib.error.URLError as e:
        # 接続タイムアウトやDNSエラー
        raise HTTPException(status_code=500, detail=str(e.reason))

    # 3) 外部 API のレスポンスをそのまま返却
    return result
