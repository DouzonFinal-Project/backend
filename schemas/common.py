"""
schemas/common.py

- 프로젝트 전반에서 재사용할 공용 스키마 모음
- Pydantic v2 기준
- 포함 내용:
  1) 에러 응답 표준: ErrorDetail, ErrorResponse
  2) 페이지네이션 메타: Pagination, MetaInfo, make_meta()
  3) (선택) 성공 응답 래퍼: SuccessEnvelope[T]
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict


# =========================================================
# 1) 에러 응답 표준
# =========================================================

class ErrorDetail(BaseModel):
    """에러 코드/메시지를 담는 최소 단위"""
    code: str = Field(..., description="에러 식별 코드 (예: INTERNAL_ERROR, LLM_TIMEOUT)")
    message: str = Field(..., description="사람이 읽을 수 있는 에러 메시지(한국어/영어 등)")

class ErrorResponse(BaseModel):
    """
    전역 에러 핸들러에서 내려주는 표준 에러 응답
    - middlewares/error_handler.py에서 이 스키마로 리턴하면 Swagger 문서화도 깔끔해짐
    """
    error: ErrorDetail
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="응답 생성 시각 (UTC)"
    )
    latency_ms: Optional[int] = Field(
        default=None, ge=0, description="요청 처리에 걸린 시간(ms). 타이밍 미들웨어와 연동 시 사용"
    )
    trace_id: Optional[str] = Field(
        default=None, description="요청 추적용 ID(X-Request-ID 등을 복사해 넣을 수 있음)"
    )

    model_config = ConfigDict(extra="ignore")


# =========================================================
# 2) 페이지네이션 요청/메타
# =========================================================

class Pagination(BaseModel):
    """
    목록 조회 시 공통으로 쓰는 페이징 파라미터
    - page: 1부터 시작
    - size: 1~200 사이 권장(서비스 정책에 맞게 변경)
    - sort: "created_at,desc" / "name,asc" 형식 등 자유 입력
    """
    page: int = Field(1, ge=1, description="현재 페이지(1부터 시작)")
    size: int = Field(20, ge=1, le=200, description="페이지당 항목 수")
    sort: Optional[str] = Field(default=None, description='정렬 키(예: "created_at,desc")')

    model_config = ConfigDict(extra="ignore")


class MetaInfo(BaseModel):
    """
    목록 응답에 포함시키는 메타 정보
    - total: 전체 개수
    - page/size: 현재 페이지와 크기
    - pages: 총 페이지 수
    - sort: 적용된 정렬 정보(선택)
    """
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    pages: int = Field(..., ge=1)
    sort: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


def make_meta(total: int, page: int, size: int, sort: Optional[str] = None) -> MetaInfo:
    """
    페이징 메타를 계산해서 생성
    - total 이 0이어도 pages는 최소 1로 보장(프론트 처리 단순화)
    """
    pages = max(1, ceil(total / max(1, size)))
    return MetaInfo(total=total, page=page, size=size, pages=pages, sort=sort)


# =========================================================
# 3) (선택) 성공 응답 래퍼
# =========================================================

T = TypeVar("T")

class SuccessEnvelope(BaseModel, Generic[T]):
    """
    성공 응답 표준 래퍼 (선택)
    - ok: 항상 True
    - data: 실제 데이터(payload)
    - meta: 목록 응답의 경우 메타 정보 포함 가능
    - trace_id: 요청 추적 ID(선택)
    """
    ok: bool = True
    data: T
    meta: Optional[MetaInfo] = None
    trace_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


# =========================================================
# 사용 예시 (참고용, 실제 라우터에서는 import만 해서 사용)
# =========================================================
# from fastapi import APIRouter
#
# router = APIRouter()
#
# @router.get("/students", response_model=SuccessEnvelope[list[StudentOut]])
# def list_students(p: Pagination = Depends()):
#     total, items = query_students(page=p.page, size=p.size, sort=p.sort)
#     return SuccessEnvelope(data=items, meta=make_meta(total, p.page, p.size, p.sort))
#
# 전역 에러 핸들러에서는 ErrorResponse를 반환 모델로 활용 가능.
