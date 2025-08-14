from pydantic import BaseModel
from typing import Optional

class ExampleFrontRequest(BaseModel):
    user_id: int
    query: str
    limit: Optional[int] = 10
