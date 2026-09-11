# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore

# 🔑 다운받은 JSON 파일 이름 (.json 꼭 붙이기!)
credential_path = "nvda-catch-up-firebase-adminsdk-fbsvc-ee033dc64f.json"

# Firebase 앱 초기화
cred = credentials.Certificate(credential_path)
firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 연결
db = firestore.client()