from pydantic import BaseModel
from typing import List

class ExampleFrontResponse(BaseModel):
    results: List[dict]
    total: int
