from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total_count: int
    stats: dict = {}

class PaginatedRunsResponse(BaseModel, Generic[T]):
    runs: List[T]
    total_count: int
    stats: dict = {}
