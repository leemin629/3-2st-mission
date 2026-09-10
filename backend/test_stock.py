import requests           # 인터넷에서 데이터 가져오는 도구
import os                 # 환경변수 읽는 도구
from dotenv import load_dotenv   # .env 파일 읽기

load_dotenv()  # .env 파일 불러오기
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")  # .env에 저장한 키 가져오기

# Alpha Vantage에 요청할 주소
url = "https://www.alphavantage.co/query"
params = {
    "function": "GLOBAL_QUOTE",  # 현재 주가 조회 기능
    "symbol": "AAPL",            # 애플 주식
    "apikey": API_KEY
}

# 데이터 요청!
response = requests.get(url, params=params)
data = response.json()  # JSON으로 변환

print(data)  # 결과 출력