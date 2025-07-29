"""
Quote management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.db.database import get_db
from app.db import models, schemas
from app.ml.cad_processor import CADProcessor, FeatureExtractor
from app.ml.cost_predictor import CostPredictor, CycleTimePredictor
from app.core.config import settings

router = APIRouter()

# Initialize ML components
cad_processor = CADProcessor()
cost_predictor = CostPredictor()
cycle_time_predictor = CycleTimePredictor()

@router.get("/", response_model=schemas.PaginatedResponse)
async def list_quotes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """List quotes with pagination and filtering"""
    try:
        # Build query
        query = db.query(models.Quote)
        
        # Apply filters
        if status:
            query = query.filter(models.Quote.status == status)
        if client_id:
            query = query.filter(models.Quote.client_id == client_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        quotes = query.offset(offset).limit(size).all()
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return schemas.PaginatedResponse(
            items=quotes,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=schemas.Quote)
async def create_quote(
    quote_data: schemas.QuoteCreate,
    db: Session = Depends(get_db)
):
    """Create a new quote"""
    try:
        # Generate unique quote number
        quote_number = f"RFQ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create quote
        db_quote = models.Quote(
            quote_number=quote_number,
            client_id=quote_data.client_id,
            created_by=1,  # TODO: Get from authentication
            project_name=quote_data.project_name,
            description=quote_data.description,
            status="pending"
        )
        
        db.add(db_quote)
        db.commit()
        db.refresh(db_quote)
        
        return db_quote
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quote_id}", response_model=schemas.Quote)
async def get_quote(quote_id: int, db: Session = Depends(get_db)):
    """Get a specific quote by ID"""
    quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.put("/{quote_id}", response_model=schemas.Quote)
async def update_quote(
    quote_id: int,
    quote_data: schemas.QuoteUpdate,
    db: Session = Depends(get_db)
):
    """Update a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Update fields
        update_data = quote_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quote, field, value)
        
        quote.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(quote)
        
        return quote
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{quote_id}")
async def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    """Delete a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        db.delete(quote)
        db.commit()
        
        return {"message": "Quote deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quote_id}/analyze", response_model=schemas.AIAnalysisResult)
async def analyze_quote(
    quote_id: int,
    analysis_request: schemas.AIAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run AI analysis on a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Update status to analyzing
        quote.status = "analyzing"
        db.commit()
        
        # Run analysis in background
        background_tasks.add_task(
            run_ai_analysis_task,
            quote_id,
            analysis_request.force_reprocess,
            db
        )
        
        return {
            "quote_id": quote_id,
            "confidence_score": 0.0,
            "complexity_level": "Medium",
            "estimated_costs": {},
            "machining_operations": [],
            "processing_time": 0.0,
            "part_features": [],
            "recommendations": ["Analysis started in background"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quote_id}/analysis", response_model=schemas.QuoteWithAnalysis)
async def get_quote_analysis(quote_id: int, db: Session = Depends(get_db)):
    """Get the AI analysis results for a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get related files and parts
        files = db.query(models.QuoteFile).filter(models.QuoteFile.quote_id == quote_id).all()
        parts = db.query(models.Part).filter(models.Part.quote_id == quote_id).all()
        
        # Compile analysis results
        ai_analysis = {
            "files_processed": len([f for f in files if f.is_processed]),
            "total_files": len(files),
            "parts_analyzed": len(parts),
            "overall_confidence": quote.ai_confidence_score or 0.0,
            "complexity_level": quote.complexity_level or "Medium",
            "processing_status": quote.status
        }
        
        processing_summary = {
            "total_cost": quote.total_cost,
            "client_price": quote.client_price,
            "margin": quote.margin,
            "estimated_delivery_days": quote.estimated_delivery_days,
            "processing_time_minutes": quote.processing_time_minutes
        }
        
        # Create response with analysis data
        quote_dict = schemas.Quote.from_orm(quote).dict()
        quote_dict["ai_analysis"] = ai_analysis
        quote_dict["processing_summary"] = processing_summary
        
        return quote_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quote_id}/approve")
async def approve_quote(quote_id: int, db: Session = Depends(get_db)):
    """Approve a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = "approved"
        quote.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Quote approved successfully", "quote_id": quote_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quote_id}/reject")
async def reject_quote(quote_id: int, db: Session = Depends(get_db)):
    """Reject a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote.status = "rejected"
        
        db.commit()
        
        return {"message": "Quote rejected", "quote_id": quote_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quote_id}/parts", response_model=List[schemas.Part])
async def get_quote_parts(quote_id: int, db: Session = Depends(get_db)):
    """Get all parts for a quote"""
    quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    parts = db.query(models.Part).filter(models.Part.quote_id == quote_id).all()
    return parts

@router.post("/{quote_id}/parts", response_model=schemas.Part)
async def create_part(
    quote_id: int,
    part_data: schemas.PartCreate,
    db: Session = Depends(get_db)
):
    """Create a new part for a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        db_part = models.Part(
            quote_id=quote_id,
            name=part_data.name,
            description=part_data.description,
            quantity=part_data.quantity,
            material_type=part_data.material_type
        )
        
        db.add(db_part)
        db.commit()
        db.refresh(db_part)
        
        return db_part
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def run_ai_analysis_task(quote_id: int, force_reprocess: bool, db: Session):
    """Background task to run AI analysis on a quote"""
    try:
        # Get quote and related data
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            return
        
        files = db.query(models.QuoteFile).filter(models.QuoteFile.quote_id == quote_id).all()
        
        # Process files if needed
        total_confidence = 0.0
        processed_files = 0
        all_features = []
        
        for file in files:
            if not file.is_processed or force_reprocess:
                # Process CAD file
                analysis_result = await cad_processor.process_file(
                    file.file_path, 
                    file.file_type
                )
                
                # Update file record
                file.is_processed = True
                file.processing_status = analysis_result['processing_status']
                file.extracted_metadata = analysis_result['file_info']
                file.analysis_results = analysis_result['extracted_features']
                file.processed_at = datetime.utcnow()
                
                if analysis_result['processing_status'] == 'completed':
                    total_confidence += analysis_result['confidence_score']
                    processed_files += 1
                    all_features.append(analysis_result['extracted_features'])
        
        # Calculate overall confidence
        if processed_files > 0:
            avg_confidence = total_confidence / processed_files
            quote.ai_confidence_score = avg_confidence
        
        # Determine complexity level
        if all_features:
            complexity_levels = [f.get('complexity_level', 'Medium') for f in all_features]
            if 'High' in complexity_levels:
                quote.complexity_level = 'High'
            elif 'Medium' in complexity_levels:
                quote.complexity_level = 'Medium'
            else:
                quote.complexity_level = 'Low'
        
        # Create or update parts based on analysis
        existing_parts = db.query(models.Part).filter(models.Part.quote_id == quote_id).all()
        
        if not existing_parts and all_features:
            # Create parts from analysis
            for i, features in enumerate(all_features):
                part_name = f"Part {i+1}"
                
                # Extract dimensions
                dimensions = FeatureExtractor.extract_dimensions(features)
                
                # Estimate machining time
                machining_time = FeatureExtractor.estimate_machining_time(features)
                
                # Create part
                part = models.Part(
                    quote_id=quote_id,
                    name=part_name,
                    description=f"Auto-generated from file analysis",
                    quantity=1,
                    material_type=features.get('material_recommendations', ['aluminum'])[0] if features.get('material_recommendations') else 'aluminum',
                    length=dimensions.get('length', 0.0),
                    width=dimensions.get('width', 0.0),
                    height=dimensions.get('height', 0.0),
                    volume=dimensions.get('volume', 0.0),
                    machining_operations=features.get('machining_operations', []),
                    estimated_cycle_time=machining_time,
                    ai_extracted_features=features,
                    confidence_score=features.get('confidence_score', 0.8)
                )
                
                db.add(part)
        
        # Calculate costs if we have parts
        parts = db.query(models.Part).filter(models.Part.quote_id == quote_id).all()
        if parts:
            # Prepare data for cost prediction
            parts_data = []
            for part in parts:
                part_dict = {
                    'length': part.length or 0.0,
                    'width': part.width or 0.0,
                    'height': part.height or 0.0,
                    'volume': part.volume or 0.0,
                    'material_type': part.material_type or 'aluminum',
                    'complexity_level': quote.complexity_level or 'Medium',
                    'machining_operations': part.machining_operations or [],
                    'quantity': part.quantity,
                    'confidence_score': part.confidence_score or 0.8
                }
                parts_data.append(part_dict)
            
            # Get cost predictions (use rule-based if model not trained)
            try:
                cost_results = cost_predictor.predict(parts_data)
                cost_breakdown = cost_results['cost_breakdown']
                
                # Update parts with cost information
                for i, part in enumerate(parts):
                    if i < len(cost_breakdown['material_costs']):
                        part.material_cost = cost_breakdown['material_costs'][i]
                        part.labor_cost = cost_breakdown['labor_costs'][i]
                        part.overhead_cost = cost_breakdown['overhead_costs'][i]
                        part.total_cost = cost_breakdown['total_costs'][i]
                
                # Update quote totals
                quote.total_cost = sum(cost_breakdown['total_costs'])
                quote.client_price = quote.total_cost * settings.DEFAULT_MATERIAL_MARKUP
                quote.margin = quote.client_price - quote.total_cost
                
            except Exception as e:
                # Fallback to rule-based costing
                total_cost = 0.0
                for part in parts:
                    # Simple cost calculation
                    base_cost = 50.0  # Base cost per part
                    complexity_mult = {'Low': 1.0, 'Medium': 2.0, 'High': 4.0}
                    part_cost = base_cost * complexity_mult.get(quote.complexity_level, 2.0) * part.quantity
                    
                    part.material_cost = part_cost * 0.4
                    part.labor_cost = part_cost * 0.4
                    part.overhead_cost = part_cost * 0.2
                    part.total_cost = part_cost
                    
                    total_cost += part_cost
                
                quote.total_cost = total_cost
                quote.client_price = total_cost * settings.DEFAULT_MATERIAL_MARKUP
                quote.margin = quote.client_price - quote.total_cost
        
        # Update quote status
        quote.status = "quoted"
        quote.quoted_at = datetime.utcnow()
        
        # Calculate estimated delivery
        if parts:
            max_cycle_time = max([p.estimated_cycle_time or 60.0 for p in parts])
            # Convert minutes to days (assuming 8-hour work days)
            delivery_days = max(1, int(max_cycle_time / (8 * 60)) + 2)  # Add 2 days buffer
            quote.estimated_delivery_days = delivery_days
        
        db.commit()
        
    except Exception as e:
        # Log error and update status
        quote.status = "failed"
        db.commit()
        print(f"Error in AI analysis: {str(e)}")