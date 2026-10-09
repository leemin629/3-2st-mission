from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from firebase_config import db
from firebase_admin import firestore

router = APIRouter()

class Conversation(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    reply: str = Field(min_length=1)
    model: str = ""
    symbol: str = "NVDA"

def read_records():
    # 과거 conversations 기록도 유지하고 새 채팅과 동일하게 조회합니다.
    records = []
    for collection in ("chat_history", "conversations"):
        for doc in db.collection(collection).stream():
            records.append({**doc.to_dict(), "id": f"{collection}:{doc.id}"})
    records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return records

def record_ref(conv_id):
    collection, sep, identifier = conv_id.partition(":")
    if not sep:
        collection, identifier = "conversations", conv_id
    if collection not in ("chat_history", "conversations") or not identifier:
        raise HTTPException(400, "잘못된 대화 ID입니다.")
    return db.collection(collection).document(identifier)

@router.post("")
def create_conversation(item: Conversation):
    ref = db.collection("chat_history").add({
        **item.model_dump(), "created_at": firestore.SERVER_TIMESTAMP
    })
    return {"id": f"chat_history:{ref[1].id}", **item.model_dump()}

@router.get("")
def list_conversations():
    return read_records()

@router.get("/{conv_id}")
def get_conversation(conv_id: str):
    doc = record_ref(conv_id).get()
    if not doc.exists:
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return {**doc.to_dict(), "id": conv_id}

@router.delete("/{conv_id}")
def delete_conversation(conv_id: str):
    ref = record_ref(conv_id)
    if not ref.get().exists:
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    ref.delete()
    return {"message": "삭제 완료", "id": conv_id}
