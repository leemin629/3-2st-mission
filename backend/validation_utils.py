# backend/validation_utils.py

import re
import html
from fastapi import HTTPException

ALLOWED_SYMBOLS = {"NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"}


def clean_text(value: str, max_length: int, field_name: str) -> str:
    """
    문자열 입력값을 정리하고 길이를 제한합니다.
    - 앞뒤 공백 제거
    - 제어문자 제거
    - HTML 특수문자 이스케이프
    - 최대 길이 검사
    """

    if value is None:
        return ""

    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"{field_name}은 문자열이어야 합니다.")

    value = value.strip()

    # 제어 문자 제거
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)

    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}은 최대 {max_length}자까지 입력할 수 있습니다."
        )

    # XSS 방지를 위한 HTML 이스케이프
    return html.escape(value, quote=True)


def validate_symbol(symbol: str) -> str:
    """
    허용된 종목 코드만 통과시킵니다.
    """

    if not symbol:
        raise HTTPException(status_code=400, detail="종목 코드는 필수입니다.")

    symbol = symbol.strip().upper()

    if symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(status_code=400, detail="허용되지 않은 종목 코드입니다.")

    return symbol


def validate_price(price) -> float:
    """
    가격 입력값 검증
    """

    try:
        price = float(price)
    except ValueError:
        raise HTTPException(status_code=400, detail="가격은 숫자여야 합니다.")

    if price <= 0:
        raise HTTPException(status_code=400, detail="가격은 0보다 커야 합니다.")

    if price > 100000:
        raise HTTPException(status_code=400, detail="가격이 너무 큽니다.")

    return price


def validate_date(date: str) -> str:
    """
    YYYY-MM-DD 형식만 허용합니다.
    """

    if not isinstance(date, str):
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.")

    date = date.strip()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(status_code=400, detail="날짜는 YYYY-MM-DD 형식이어야 합니다.")

    return date