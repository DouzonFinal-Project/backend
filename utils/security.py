from fastapi import Header, HTTPException

# TODO: 나중에 settings로 옮겨서 .env에서 읽어오기
EXPECTED_TOKEN = "dev-llm-token"

def require_llm_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if token != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"client": "llm"}