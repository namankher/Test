"""
Database models for the Manufacturing RFQ Platform
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quotes = relationship("Quote", back_populates="created_by_user")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    company = Column(String)
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    quotes = relationship("Quote", back_populates="client")

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String, unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Quote Details
    project_name = Column(String)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, analyzing, quoted, approved, rejected
    
    # Pricing
    total_cost = Column(Float, default=0.0)
    client_price = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    
    # Processing Times
    estimated_delivery_days = Column(Integer)
    actual_delivery_days = Column(Integer)
    processing_time_minutes = Column(Float)
    
    # AI Analysis Results
    ai_confidence_score = Column(Float)
    complexity_level = Column(String)  # Low, Medium, High
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    quoted_at = Column(DateTime)
    approved_at = Column(DateTime)
    
    # Relationships
    client = relationship("Client", back_populates="quotes")
    created_by_user = relationship("User", back_populates="quotes")
    parts = relationship("Part", back_populates="quote")
    files = relationship("QuoteFile", back_populates="quote")

class Part(Base):
    __tablename__ = "parts"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    
    # Part Information
    name = Column(String, nullable=False)
    description = Column(Text)
    quantity = Column(Integer, default=1)
    material_type = Column(String)
    
    # Dimensions (extracted from CAD)
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    weight = Column(Float)
    volume = Column(Float)
    
    # Manufacturing Details
    machining_operations = Column(JSON)  # List of operations: turning, milling, etc.
    estimated_cycle_time = Column(Float)  # in minutes
    actual_cycle_time = Column(Float)
    
    # Costs
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # AI Analysis
    ai_extracted_features = Column(JSON)
    confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quote = relationship("Quote", back_populates="parts")

class QuoteFile(Base):
    __tablename__ = "quote_files"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    
    # File Information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer)
    
    # Processing Status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    
    # AI Analysis Results
    extracted_metadata = Column(JSON)
    analysis_results = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    quote = relationship("Quote", back_populates="files")

class QuoteTemplate(Base):
    __tablename__ = "quote_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Template Configuration
    labor_rate = Column(Float, default=75.0)
    material_markup = Column(Float, default=1.2)
    overhead_rate = Column(Float, default=0.15)
    
    # Template Content
    template_data = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metrics
    date = Column(DateTime, default=datetime.utcnow)
    quotes_generated = Column(Integer, default=0)
    quotes_approved = Column(Integer, default=0)
    quotes_rejected = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_processing_time = Column(Float, default=0.0)
    avg_accuracy_rate = Column(Float, default=0.0)
    
    # Additional metrics
    new_clients = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # cost_prediction, cycle_time, feature_extraction
    
    # Model Metadata
    model_path = Column(String, nullable=False)
    accuracy_score = Column(Float)
    training_data_size = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    trained_at = Column(DateTime)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer)
    details = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)