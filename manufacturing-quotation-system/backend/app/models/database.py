from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

# Enums
class QuoteStatusEnum(enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    SENT_TO_CLIENT = "sent_to_client"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class FileTypeEnum(enum.Enum):
    CAD_2D = "cad_2d"
    CAD_3D = "cad_3d"
    PDF = "pdf"
    IMAGE = "image"

# Database Models
class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    project_description = Column(Text)
    status = Column(Enum(QuoteStatusEnum), default=QuoteStatusEnum.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    valid_until = Column(DateTime)
    
    # Relationships
    files = relationship("QuoteFile", back_populates="quote", cascade="all, delete-orphan")
    parts = relationship("Part", back_populates="quote", cascade="all, delete-orphan")
    cost_breakdown = relationship("CostBreakdown", back_populates="quote", uselist=False)
    feedback = relationship("Feedback", back_populates="quote", cascade="all, delete-orphan")

class QuoteFile(Base):
    __tablename__ = "quote_files"
    
    id = Column(String, primary_key=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(Enum(FileTypeEnum), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, server_default=func.now())
    
    # Relationships
    quote = relationship("Quote", back_populates="files")

class Part(Base):
    __tablename__ = "parts"
    
    id = Column(String, primary_key=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    part_name = Column(String, nullable=False)
    
    # Dimensions
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    volume = Column(Float)
    surface_area = Column(Float)
    
    # Material
    material_type = Column(String)
    material_grade = Column(String)
    stock_size = Column(String)
    stock_thickness = Column(Float)
    
    # Analysis results
    total_cycle_time = Column(Float)  # minutes
    complexity_score = Column(Float)
    confidence_score = Column(Float)
    
    # Relationships
    quote = relationship("Quote", back_populates="parts")
    operations = relationship("MachiningOperation", back_populates="part", cascade="all, delete-orphan")

class MachiningOperation(Base):
    __tablename__ = "machining_operations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(String, ForeignKey("parts.id"), nullable=False)
    process_type = Column(String, nullable=False)
    description = Column(Text)
    estimated_time = Column(Float)  # minutes
    complexity_factor = Column(Float)
    tool_requirements = Column(JSON)  # Stored as JSON
    
    # Relationships
    part = relationship("Part", back_populates="operations")

class CostBreakdown(Base):
    __tablename__ = "cost_breakdowns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False, unique=True)
    
    # Cost components
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    machine_cost = Column(Float, default=0.0)
    tool_cost = Column(Float, default=0.0)
    setup_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    
    # Margin and pricing
    margin_percentage = Column(Float, default=0.0)
    margin_amount = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Quote specifics
    quantity = Column(Integer, default=1)
    delivery_days = Column(Integer)
    rush_order = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote = relationship("Quote", back_populates="cost_breakdown")

class ClientQuoteDelivery(Base):
    __tablename__ = "client_quote_deliveries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    quote_number = Column(String, unique=True, nullable=False)
    
    # Client information
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    
    # Quote content (stored as JSON for flexibility)
    quote_data = Column(JSON, nullable=False)
    
    # Delivery tracking
    sent_at = Column(DateTime)
    viewed_at = Column(DateTime)
    responded_at = Column(DateTime)
    client_response = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    
    # Actual production data
    actual_data = Column(JSON, nullable=False)  # Stores ActualProductionData
    overall_feedback = Column(Text)
    
    # Analysis comparison
    estimation_accuracy = Column(Float)  # Percentage accuracy
    lessons_learned = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    quote = relationship("Quote", back_populates="feedback")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    user_id = Column(String)  # For future user authentication
    details = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())