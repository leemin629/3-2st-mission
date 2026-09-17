# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# 🔑 배포(Render)와 로컬 모두 지원
firebase_json = os.environ.get("FIREBASE_CREDENTIALS")

if firebase_json:
    # 🌐 배포 환경: 환경변수의 JSON 문자열로 인증
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
else:
    # 💻 로컬 환경: JSON 파일로 인증
    credential_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "nvda-catch-up-firebase-adminsdk-fbsvc-f2843fe2ab.json"
    )
    cred = credentials.Certificate(credential_path)

# Firebase 앱 초기화 (중복 방지)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 연결
db = firestore.client()