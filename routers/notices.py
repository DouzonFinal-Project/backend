from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.notices import Notice as NoticeModel
from schemas.notices import NoticeCreate

router = APIRouter(prefix="/notices", tags=["공지사항"])

# ==========================================================
# DB 세션 연결
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 공지사항 추가
@router.post("/")
def create_notice(notice: NoticeCreate, db: Session = Depends(get_db)):
    db_notice = NoticeModel(**notice.model_dump())
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return {
        "success": True,
        "data": {
            "id": db_notice.id,
            "title": db_notice.title,
            "content": db_notice.content,
            "date": str(db_notice.date),
            "is_important": db_notice.is_important
        },
        "message": "공지사항이 성공적으로 등록되었습니다"
    }


# ✅ [READ] 전체 공지사항 조회
@router.get("/")
def read_notices(db: Session = Depends(get_db)):
    records = db.query(NoticeModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "date": str(r.date),
                "is_important": r.is_important
            }
            for r in records
        ],
        "message": "전체 공지사항 조회 완료"
    }


# ==========================================================
# [2단계] 확장 라우터 (필터/조회)
# ==========================================================

# ✅ [FILTER] 중요 공지만 조회
@router.get("/important")
def read_important_notices(db: Session = Depends(get_db)):
    records = db.query(NoticeModel).filter(NoticeModel.is_important == True).all()
    if not records:
        return {
            "success": False,
            "error": {"code": 404, "message": "중요 공지사항이 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "date": str(r.date),
                "is_important": r.is_important
            }
            for r in records
        ],
        "message": "중요 공지사항 조회 성공"
    }


# ✅ [RECENT] 최신 공지 조회
@router.get("/recent")
def read_recent_notices(limit: int = 5, db: Session = Depends(get_db)):
    records = db.query(NoticeModel).order_by(NoticeModel.date.desc()).limit(limit).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "date": str(r.date),
                "is_important": r.is_important
            }
            for r in records
        ],
        "message": f"최신 {limit}개의 공지사항 조회 성공"
    }


# ==========================================================
# [3단계] 상세/수정/삭제 라우터
# ==========================================================

# ✅ [READ] 공지사항 상세 조회
@router.get("/{notice_id}")
def read_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "공지사항을 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "date": str(notice.date),
            "is_important": notice.is_important
        },
        "message": "공지사항 상세 조회 성공"
    }


# ✅ [UPDATE] 공지사항 수정
@router.put("/{notice_id}")
def update_notice(notice_id: int, updated: NoticeCreate, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "공지사항을 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(notice, key, value)

    db.commit()
    db.refresh(notice)
    return {
        "success": True,
        "data": {
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "date": str(notice.date),
            "is_important": notice.is_important
        },
        "message": "공지사항이 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 공지사항 삭제
@router.delete("/{notice_id}")
def delete_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "공지사항을 찾을 수 없습니다"}
        }

    db.delete(notice)
    db.commit()
    return {
        "success": True,
        "data": {"notice_id": notice_id},
        "message": "공지사항이 성공적으로 삭제되었습니다"
    }
