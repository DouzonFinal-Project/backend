from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/config", tags=["설정"])

# ==========================================================
# [1단계] 현재 학기 계산 함수
# ==========================================================
def get_current_year_semester():
    """
    현재 날짜를 기준으로 학년/학기 계산
    - 1~2월  → 전년도 2학기
    - 3~8월  → 당해년도 1학기
    - 9~12월 → 당해년도 2학기
    """
    now = datetime.now()
    year = now.year
    month = now.month

    if month in [1, 2]:
        return year - 1, 2
    elif 3 <= month <= 8:
        return year, 1
    else:
        return year, 2


# ==========================================================
# [2단계] Config 라우터
# ==========================================================

# ✅ [READ] 현재 학기 반환
@router.get("/academic")
def get_academic_config():
    """현재 학기(year, semester) 반환"""
    year, semester = get_current_year_semester()
    return {
        "success": True,
        "data": {
            "year": year,
            "semester": semester
        },
        "message": f"{year}년 {semester}학기 기준 설정 반환"
    }
