from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["인증"])

# ✅ 요청 형식 정의
class LoginRequest(BaseModel):
    id: str
    password: str

# ✅ 응답 형식 정의
class LoginResponse(BaseModel):
    name: str
    role: str
    token: str

# ✅ [LOGIN] 로그인 API
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    if request.id == "teacher01" and request.password == "1234":
        return {
            "name": "김선생",
            "role": "교사",
            "token": "abc.def.ghi"  # 형식만 맞춘 더미 토큰
        }
    raise HTTPException(status_code=401, detail="잘못된 아이디 또는 비밀번호입니다.")
