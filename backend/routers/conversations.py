# routers/conversations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_config import db
from firebase_admin import firestore

router = APIRouter()

# 대화 저장용 모델
class Conversation(BaseModel):
    message: str
    reply: str
    model: str = ""

# 1️⃣ POST - 대화 저장
@router.post("")
async def create_conversation(item: Conversation):
    ref = db.collection("conversations").add({
        **item.dict(),
        "created_at": firestore.SERVER_TIMESTAMP
    })
    return {"id": ref[1].id, **item.dict()}

# 2️⃣ GET - 목록 조회
@router.get("")
async def list_conversations():
    docs = db.collection("conversations")\
        .order_by("created_at", direction=firestore.Query.DESCENDING)\
        .stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

# 3️⃣ GET - 개별 조회
@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    doc = db.collection("conversations").document(conv_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    return {"id": doc.id, **doc.to_dict()}

# 4️⃣ DELETE - 삭제
@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    doc_ref = db.collection("conversations").document(conv_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")
    doc_ref.delete()
    return {"message": "삭제 완료", "id": conv_id}