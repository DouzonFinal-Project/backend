from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...
    @abstractmethod
    def summarize(self, text: str, **kwargs) -> str: ...
    @abstractmethod
    def extract(self, text: str, schema: Dict[str, Any] | None = None) -> Dict[str, Any]: ...
