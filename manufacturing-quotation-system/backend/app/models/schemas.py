from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QuoteStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    SENT_TO_CLIENT = "sent_to_client"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class FileType(str, Enum):
    CAD_2D = "cad_2d"
    CAD_3D = "cad_3d"
    PDF = "pdf"
    IMAGE = "image"

class MachiningProcess(str, Enum):
    MILLING = "milling"
    TURNING = "turning"
    DRILLING = "drilling"
    GRINDING = "grinding"
    EDM = "edm"
    LASER_CUTTING = "laser_cutting"
    WATERJET = "waterjet"

# File Upload Schemas
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_timestamp: datetime

class MultipleFileUploadRequest(BaseModel):
    quote_id: Optional[str] = None
    client_name: str
    client_email: str
    project_description: Optional[str] = None

# Part Analysis Schemas
class PartDimensions(BaseModel):
    length: float
    width: float
    height: float
    volume: Optional[float] = None
    surface_area: Optional[float] = None

class MaterialSpecification(BaseModel):
    material_type: str
    grade: Optional[str] = None
    stock_size: str
    stock_thickness: Optional[float] = None

class ToolRequirement(BaseModel):
    tool_type: str
    tool_size: str
    quantity: int
    estimated_cost: float

class MachiningOperation(BaseModel):
    process: MachiningProcess
    description: str
    estimated_time: float  # minutes
    complexity_factor: float
    tools_required: List[ToolRequirement]

class PartAnalysisResult(BaseModel):
    part_id: str
    part_name: str
    dimensions: PartDimensions
    material: MaterialSpecification
    operations: List[MachiningOperation]
    total_cycle_time: float  # minutes
    complexity_score: float
    confidence_score: float

# Cost Calculation Schemas
class CostBreakdown(BaseModel):
    material_cost: float
    labor_cost: float
    machine_cost: float
    tool_cost: float
    setup_cost: float
    overhead_cost: float
    subtotal: float
    margin: float
    total_cost: float

class QuotationInput(BaseModel):
    overhead_percentage: float = Field(ge=0, le=100)
    margin_percentage: float = Field(ge=0, le=100)
    quantity: int = Field(ge=1)
    delivery_days: int = Field(ge=1)
    rush_order: bool = False
    additional_notes: Optional[str] = None

# Quote Generation Schemas
class ClientQuoteItem(BaseModel):
    part_name: str
    quantity: int
    unit_price: float
    total_price: float
    delivery_time: str

class ClientQuote(BaseModel):
    quote_number: str
    client_name: str
    client_email: str
    quote_date: datetime
    valid_until: datetime
    items: List[ClientQuoteItem]
    subtotal: float
    tax: Optional[float] = None
    shipping: Optional[float] = None
    total: float
    terms_and_conditions: str
    notes: Optional[str] = None

class InternalQuoteRecord(BaseModel):
    quote_id: str
    client_quote: ClientQuote
    internal_costs: CostBreakdown
    margin_amount: float
    margin_percentage: float
    profitability_analysis: Dict[str, Any]

# Feedback Schemas
class ActualProductionData(BaseModel):
    quote_id: str
    part_id: str
    actual_cycle_time: float
    actual_material_cost: float
    actual_labor_hours: float
    quality_issues: Optional[str] = None
    notes: Optional[str] = None

class FeedbackSubmission(BaseModel):
    quote_id: str
    production_data: List[ActualProductionData]
    overall_feedback: Optional[str] = None

# Base Response Schemas
class BaseResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class QuoteProgressResponse(BaseResponse):
    quote_id: str
    status: QuoteStatus
    progress_percentage: int
    current_step: str
    estimated_completion: Optional[datetime] = None