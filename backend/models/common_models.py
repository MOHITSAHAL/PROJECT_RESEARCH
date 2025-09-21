"""Common Pydantic models used across the application."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')


class HealthCheck(BaseModel):
    """Model for health check responses."""
    status: str = "healthy"
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, bool] = {}
    uptime: Optional[float] = None  # seconds
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: Dict[str, Any]
    timestamp: datetime
    request_id: Optional[str] = None
    
    @classmethod
    def create(cls, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        return cls(
            error={
                "code": code,
                "message": message,
                "details": details or {}
            },
            timestamp=datetime.utcnow()
        )


class PaginationParams(BaseModel):
    """Model for pagination parameters."""
    limit: int = Field(50, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    
    @property
    def page(self) -> int:
        """Calculate page number from offset and limit."""
        return (self.offset // self.limit) + 1


class PageInfo(BaseModel):
    """Model for pagination information."""
    current_page: int
    total_pages: int
    page_size: int
    total_items: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic model for paginated responses."""
    items: List[T]
    page_info: PageInfo
    
    @classmethod
    def create(cls, items: List[T], total_count: int, pagination: PaginationParams):
        total_pages = (total_count + pagination.limit - 1) // pagination.limit
        current_page = pagination.page
        
        return cls(
            items=items,
            page_info=PageInfo(
                current_page=current_page,
                total_pages=total_pages,
                page_size=pagination.limit,
                total_items=total_count,
                has_next=current_page < total_pages,
                has_previous=current_page > 1
            )
        )


class SortParams(BaseModel):
    """Model for sorting parameters."""
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Model for filtering parameters."""
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")
    
    def get_filter(self, key: str, default: Any = None) -> Any:
        """Get filter value by key."""
        return self.filters.get(key, default)
    
    def has_filter(self, key: str) -> bool:
        """Check if filter exists."""
        return key in self.filters


class SearchParams(BaseModel):
    """Model for search parameters."""
    query: Optional[str] = Field(None, max_length=500, description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    fuzzy: bool = Field(False, description="Enable fuzzy search")
    highlight: bool = Field(False, description="Enable result highlighting")


class BulkOperation(BaseModel):
    """Model for bulk operations."""
    operation: str = Field(..., regex="^(create|update|delete)$")
    items: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    options: Optional[Dict[str, Any]] = None


class BulkOperationResult(BaseModel):
    """Model for bulk operation results."""
    operation: str
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[Dict[str, Any]] = []
    processing_time: float  # seconds
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.successful_items / self.total_items) * 100


class MetricsResponse(BaseModel):
    """Model for metrics responses."""
    metric_name: str
    value: float
    unit: Optional[str] = None
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None
    
    class Config:
        from_attributes = True


class SystemInfo(BaseModel):
    """Model for system information."""
    version: str
    environment: str
    build_date: Optional[datetime] = None
    commit_hash: Optional[str] = None
    python_version: str
    dependencies: Dict[str, str] = {}
    
    class Config:
        from_attributes = True


class RateLimitInfo(BaseModel):
    """Model for rate limit information."""
    limit: int
    remaining: int
    reset_time: datetime
    window_size: int  # seconds
    
    @property
    def is_exceeded(self) -> bool:
        """Check if rate limit is exceeded."""
        return self.remaining <= 0


class ValidationError(BaseModel):
    """Model for validation errors."""
    field: str
    message: str
    invalid_value: Optional[Any] = None


class BatchRequest(BaseModel):
    """Model for batch requests."""
    requests: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)
    parallel: bool = Field(False, description="Process requests in parallel")
    fail_fast: bool = Field(False, description="Stop on first error")


class BatchResponse(BaseModel):
    """Model for batch responses."""
    responses: List[Dict[str, Any]]
    total_requests: int
    successful_requests: int
    failed_requests: int
    processing_time: float  # seconds
    
    class Config:
        from_attributes = True


class CacheInfo(BaseModel):
    """Model for cache information."""
    key: str
    hit: bool
    ttl: Optional[int] = None  # seconds
    size: Optional[int] = None  # bytes
    
    class Config:
        from_attributes = True


class TaskStatus(BaseModel):
    """Model for background task status."""
    task_id: str
    status: str = Field(..., regex="^(pending|running|completed|failed|cancelled)$")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    """Model for WebSocket messages."""
    type: str = Field(..., regex="^(agent_response|paper_update|system_notification|error)$")
    data: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None
    
    class Config:
        from_attributes = True