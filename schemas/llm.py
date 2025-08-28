from pydantic import BaseModel
from typing import Optional, Dict, Any

class GenerateIn(BaseModel):
    prompt: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class GenerateOut(BaseModel):
    text: str
    usage: Optional[Dict[str, Any]] = None
