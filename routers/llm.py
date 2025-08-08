from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import csv
import os

router = APIRouter(prefix="/llm", tags=["LLM 요약 기능"])

# ✅ 요약 응답을 위한 JSON 포맷
class LLMResponse(BaseModel):
    id: int  # 기존 str → int로 변경
    title: str
    student_query: str
    counselor_answer: str
    date: str
    student_name: str
    worry_tags: List[str]

# ✅ 학생 이름 매핑을 위한 student_id → name dict 구성
STUDENT_NAME_MAP = {}
STUDENT_CSV_PATH = "data/students.csv"
if os.path.exists(STUDENT_CSV_PATH):
    with open(STUDENT_CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            STUDENT_NAME_MAP[row["id"]] = row["student_name"]

# ✅ reports.csv 경로
REPORTS_CSV_PATH = "data/reports.csv"

# ✅ /llm/summary 전체 요약 목록
@router.get("/summary", response_model=List[LLMResponse])
def get_llm_summary():
    if not os.path.exists(REPORTS_CSV_PATH):
        raise HTTPException(status_code=404, detail="reports.csv 파일을 찾을 수 없습니다.")

    result = []
    with open(REPORTS_CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            student_id = row["student_id"]
            student_name = STUDENT_NAME_MAP.get(student_id, "이름 없음")
            summary_text = row.get("summary") or "요약 정보 없음"

            item = {
                "id": int(row["id"]),
                "title": f"상담 유형 - {row['type']}",
                "student_query": row.get("content_raw", "내용 없음"),
                "counselor_answer": summary_text,
                "date": row.get("date", "날짜 없음"),
                "student_name": student_name,
                "worry_tags": extract_tags(summary_text)
            }
            result.append(item)

    return result

# ✅ /llm/summary/{report_id} 단건 조회
@router.get("/summary/{report_id}", response_model=LLMResponse)
def get_llm_summary_by_id(report_id: int):
    if not os.path.exists(REPORTS_CSV_PATH):
        raise HTTPException(status_code=404, detail="reports.csv 파일을 찾을 수 없습니다.")

    with open(REPORTS_CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["id"]) == report_id:
                student_id = row["student_id"]
                student_name = STUDENT_NAME_MAP.get(student_id, "이름 없음")
                summary_text = row.get("summary") or "요약 정보 없음"

                return {
                    "id": int(row["id"]),
                    "title": f"상담 유형 - {row['type']}",
                    "student_query": row.get("content_raw", "내용 없음"),
                    "counselor_answer": summary_text,
                    "date": row.get("date", "날짜 없음"),
                    "student_name": student_name,
                    "worry_tags": extract_tags(summary_text)
                }

    raise HTTPException(status_code=404, detail=f"id가 {report_id}인 데이터를 찾을 수 없습니다.")

# ✅ 간단한 키워드 태깅 함수
KEYWORDS = ["진로", "불안", "자신감", "성격", "관계", "학업", "건강"]
def extract_tags(text: str) -> List[str]:
    tags = []
    for kw in KEYWORDS:
        if kw in text:
            tags.append(kw)
    return tags or ["기타"]