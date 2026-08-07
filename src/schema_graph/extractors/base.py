from abc import ABC, abstractmethod
from ..context import CreateTableContext

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, contexts: list[CreateTableContext]) -> None:
        """Extract information from the given contexts."""
        