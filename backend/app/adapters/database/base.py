from abc import ABC, abstractmethod
from typing import Any

from app.schemas.db_schema import DatabaseSchema


class DatabaseConnectionAdapter(ABC):
    @abstractmethod
    def test_connection(self, config: dict[str, Any]) -> tuple[bool, str]:
        pass

    @abstractmethod
    def inspect_schema(self, config: dict[str, Any], project_id: int) -> DatabaseSchema:
        pass
