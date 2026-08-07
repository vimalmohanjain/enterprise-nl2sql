from abc import ABC, abstractmethod
from ..context import CreateTableContext
from collections.abc import Iterable

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, contexts: Iterable[CreateTableContext]) -> None:
        """Extract information from the given contexts."""
        