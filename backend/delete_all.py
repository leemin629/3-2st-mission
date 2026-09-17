from firebase_config import db

# 모든 데이터 가져오기
docs = db.collection("data").stream()

count = 0
for doc in docs:
    doc.reference.delete()  # 하나씩 삭제!
    count += 1
    print(f"삭제: {doc.id}")

print(f"🗑️ 총 {count}개 삭제 완료!")