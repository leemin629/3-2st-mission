import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

symbol = "NVDA"  # ⭐ 엔비디아로 변경
url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

response = requests.get(url)
data = response.json()

# 필요한 값만 꺼내기
quote = data["Global Quote"]

price = quote["05. price"]          # 현재가
change = quote["09. change"]        # 변동액
change_percent = quote["10. change percent"]  # 변동률

# 보기 좋게 출력
print(f"종목: {symbol}")
print(f"현재가: {price}")
print(f"변동: {change} ({change_percent})")