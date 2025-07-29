"""
Pydantic schemas for API request/response validation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator

# User Schemas
class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# Client Schemas
class ClientBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        orm_mode = True

# Part Schemas
class PartBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int = 1
    material_type: Optional[str] = None

class PartCreate(PartBase):
    quote_id: int

class PartUpdate(PartBase):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    machining_operations: Optional[List[str]] = None
    estimated_cycle_time: Optional[float] = None
    material_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    overhead_cost: Optional[float] = None

class Part(PartBase):
    id: int
    quote_id: int
    length: Optional[float]
    width: Optional[float]
    height: Optional[float]
    weight: Optional[float]
    volume: Optional[float]
    machining_operations: Optional[List[str]]
    estimated_cycle_time: Optional[float]
    actual_cycle_time: Optional[float]
    material_cost: float
    labor_cost: float
    overhead_cost: float
    total_cost: float
    ai_extracted_features: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    created_at: datetime
    
    class Config:
        orm_mode = True

# Quote File Schemas
class QuoteFileBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str

class QuoteFile(QuoteFileBase):
    id: int
    quote_id: int
    file_path: str
    file_size: int
    is_processed: bool
    processing_status: str
    extracted_metadata: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        orm_mode = True

# Quote Schemas
class QuoteBase(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None

class QuoteCreate(QuoteBase):
    client_id: int

class QuoteUpdate(QuoteBase):
    status: Optional[str] = None
    total_cost: Optional[float] = None
    client_price: Optional[float] = None
    margin: Optional[float] = None
    estimated_delivery_days: Optional[int] = None
    complexity_level: Optional[str] = None

class Quote(QuoteBase):
    id: int
    quote_number: str
    client_id: int
    created_by: int
    status: str
    total_cost: float
    client_price: float
    margin: float
    estimated_delivery_days: Optional[int]
    actual_delivery_days: Optional[int]
    processing_time_minutes: Optional[float]
    ai_confidence_score: Optional[float]
    complexity_level: Optional[str]
    created_at: datetime
    updated_at: datetime
    quoted_at: Optional[datetime]
    approved_at: Optional[datetime]
    
    # Relationships
    client: Client
    parts: List[Part] = []
    files: List[QuoteFile] = []
    
    class Config:
        orm_mode = True

class QuoteWithAnalysis(Quote):
    """Extended quote schema with AI analysis results"""
    ai_analysis: Optional[Dict[str, Any]] = None
    processing_summary: Optional[Dict[str, Any]] = None

# Dashboard Schemas
class DashboardMetrics(BaseModel):
    quotes_generated: int
    quotes_generated_change: float
    total_revenue: float
    total_revenue_change: float
    avg_processing_time: float
    avg_processing_time_change: float
    accuracy_rate: float
    accuracy_rate_change: float
    
    # Additional metrics
    quotes_pending: int
    quotes_approved: int
    quotes_rejected: int
    new_clients_this_month: int

class QuoteStatusDistribution(BaseModel):
    pending: int
    analyzing: int
    quoted: int
    approved: int
    rejected: int

class RevenueByMonth(BaseModel):
    month: str
    revenue: float
    quotes_count: int

# AI Analysis Schemas
class AIAnalysisRequest(BaseModel):
    quote_id: int
    file_ids: Optional[List[int]] = None
    force_reprocess: bool = False

class AIAnalysisResult(BaseModel):
    quote_id: int
    confidence_score: float
    complexity_level: str
    estimated_costs: Dict[str, float]
    machining_operations: List[str]
    processing_time: float
    part_features: List[Dict[str, Any]]
    recommendations: List[str]

# File Upload Schemas
class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    file_size: int
    upload_status: str
    message: str

class MultiFileUploadResponse(BaseModel):
    quote_id: int
    uploaded_files: List[FileUploadResponse]
    failed_files: List[Dict[str, str]]
    total_files: int
    successful_uploads: int

# Quote Template Schemas
class QuoteTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    labor_rate: float = 75.0
    material_markup: float = 1.2
    overhead_rate: float = 0.15

class QuoteTemplateCreate(QuoteTemplateBase):
    template_data: Optional[Dict[str, Any]] = None

class QuoteTemplate(QuoteTemplateBase):
    id: int
    template_data: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# Analytics Schemas
class AnalyticsData(BaseModel):
    date: datetime
    quotes_generated: int
    quotes_approved: int
    quotes_rejected: int
    total_revenue: float
    avg_processing_time: float
    avg_accuracy_rate: float
    new_clients: int
    files_processed: int

# Search and Filter Schemas
class QuoteFilter(BaseModel):
    status: Optional[str] = None
    client_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    complexity_level: Optional[str] = None

class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Page must be positive')
        return v
    
    @validator('size')
    def size_must_be_reasonable(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Size must be between 1 and 100')
        return v

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int