from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.database import Quote, QuoteFile, Part, MachiningOperation, QuoteStatusEnum
from app.models.schemas import PartAnalysisResult, BaseResponse, QuoteProgressResponse, QuoteStatus
from app.services.ai_analysis import DrawingAnalyzer

router = APIRouter()

@router.post("/start/{quote_id}", response_model=BaseResponse)
async def start_analysis(
    quote_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start the AI analysis process for uploaded drawings"""
    
    # Verify quote exists and has files
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    files = db.query(QuoteFile).filter(QuoteFile.quote_id == quote_id).all()
    if not files:
        raise HTTPException(status_code=400, detail="No files found for analysis")
    
    # Check if already analyzing
    if quote.status == QuoteStatusEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    
    # Update quote status
    quote.status = QuoteStatusEnum.ANALYZING
    quote.updated_at = datetime.now()
    db.commit()
    
    # Start background analysis
    background_tasks.add_task(run_analysis, quote_id, db)
    
    return BaseResponse(
        success=True,
        message="Analysis started successfully"
    )

async def run_analysis(quote_id: str, db: Session):
    """Background task to run the AI analysis"""
    
    try:
        # Get all files for the quote
        files = db.query(QuoteFile).filter(QuoteFile.quote_id == quote_id).all()
        file_paths = [file.file_path for file in files]
        
        # Initialize analyzer
        analyzer = DrawingAnalyzer()
        
        # Run analysis
        analysis_results = await analyzer.analyze_files(file_paths, quote_id)
        
        # Save results to database
        for result in analysis_results:
            # Create Part record
            part = Part(
                id=result.part_id,
                quote_id=quote_id,
                part_name=result.part_name,
                length=result.dimensions.length,
                width=result.dimensions.width,
                height=result.dimensions.height,
                volume=result.dimensions.volume,
                surface_area=result.dimensions.surface_area,
                material_type=result.material.material_type,
                material_grade=result.material.grade,
                stock_size=result.material.stock_size,
                stock_thickness=result.material.stock_thickness,
                total_cycle_time=result.total_cycle_time,
                complexity_score=result.complexity_score,
                confidence_score=result.confidence_score
            )
            
            db.add(part)
            
            # Create MachiningOperation records
            for operation in result.operations:
                op_record = MachiningOperation(
                    part_id=result.part_id,
                    process_type=operation.process.value,
                    description=operation.description,
                    estimated_time=operation.estimated_time,
                    complexity_factor=operation.complexity_factor,
                    tool_requirements={"tools": [tool.dict() for tool in operation.tools_required]}
                )
                db.add(op_record)
        
        # Update quote status
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        quote.status = QuoteStatusEnum.READY_FOR_REVIEW
        quote.updated_at = datetime.now()
        
        db.commit()
        
    except Exception as e:
        print(f"Analysis failed for quote {quote_id}: {str(e)}")
        
        # Update quote status to show error
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            quote.status = QuoteStatusEnum.PENDING  # Reset to pending
            quote.updated_at = datetime.now()
            db.commit()

@router.get("/status/{quote_id}", response_model=QuoteProgressResponse)
async def get_analysis_status(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get the current analysis status for a quote"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Calculate progress based on status
    progress_mapping = {
        QuoteStatusEnum.PENDING: (0, "Waiting to start analysis"),
        QuoteStatusEnum.ANALYZING: (50, "Analyzing drawings and extracting data"),
        QuoteStatusEnum.READY_FOR_REVIEW: (100, "Analysis complete - ready for review")
    }
    
    progress, current_step = progress_mapping.get(quote.status, (0, "Unknown status"))
    
    return QuoteProgressResponse(
        success=True,
        message="Status retrieved successfully",
        quote_id=quote_id,
        status=QuoteStatus(quote.status.value),
        progress_percentage=progress,
        current_step=current_step,
        estimated_completion=None  # Could be calculated based on file count and complexity
    )

@router.get("/results/{quote_id}", response_model=List[PartAnalysisResult])
async def get_analysis_results(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get the analysis results for all parts in a quote"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status not in [QuoteStatusEnum.READY_FOR_REVIEW, QuoteStatusEnum.APPROVED]:
        raise HTTPException(status_code=400, detail="Analysis not yet complete")
    
    # Get all parts for the quote
    parts = db.query(Part).filter(Part.quote_id == quote_id).all()
    
    results = []
    for part in parts:
        # Get machining operations for the part
        operations = db.query(MachiningOperation).filter(MachiningOperation.part_id == part.id).all()
        
        # Convert to response format
        part_result = PartAnalysisResult(
            part_id=part.id,
            part_name=part.part_name,
            dimensions={
                "length": part.length,
                "width": part.width,
                "height": part.height,
                "volume": part.volume,
                "surface_area": part.surface_area
            },
            material={
                "material_type": part.material_type,
                "grade": part.material_grade,
                "stock_size": part.stock_size,
                "stock_thickness": part.stock_thickness
            },
            operations=[
                {
                    "process": op.process_type,
                    "description": op.description,
                    "estimated_time": op.estimated_time,
                    "complexity_factor": op.complexity_factor,
                    "tools_required": op.tool_requirements.get("tools", [])
                }
                for op in operations
            ],
            total_cycle_time=part.total_cycle_time,
            complexity_score=part.complexity_score,
            confidence_score=part.confidence_score
        )
        
        results.append(part_result)
    
    return results

@router.put("/results/{quote_id}/part/{part_id}", response_model=BaseResponse)
async def update_part_analysis(
    quote_id: str,
    part_id: str,
    updated_part: PartAnalysisResult,
    db: Session = Depends(get_db)
):
    """Update the analysis results for a specific part (manual review)"""
    
    # Verify quote and part exist
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    part = db.query(Part).filter(Part.id == part_id, Part.quote_id == quote_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    try:
        # Update part data
        part.part_name = updated_part.part_name
        part.length = updated_part.dimensions.length
        part.width = updated_part.dimensions.width
        part.height = updated_part.dimensions.height
        part.volume = updated_part.dimensions.volume
        part.surface_area = updated_part.dimensions.surface_area
        part.material_type = updated_part.material.material_type
        part.material_grade = updated_part.material.grade
        part.stock_size = updated_part.material.stock_size
        part.stock_thickness = updated_part.material.stock_thickness
        part.total_cycle_time = updated_part.total_cycle_time
        part.complexity_score = updated_part.complexity_score
        part.confidence_score = updated_part.confidence_score
        
        # Delete existing operations
        db.query(MachiningOperation).filter(MachiningOperation.part_id == part_id).delete()
        
        # Add updated operations
        for operation in updated_part.operations:
            op_record = MachiningOperation(
                part_id=part_id,
                process_type=operation.process.value,
                description=operation.description,
                estimated_time=operation.estimated_time,
                complexity_factor=operation.complexity_factor,
                tool_requirements={"tools": [tool.dict() for tool in operation.tools_required]}
            )
            db.add(op_record)
        
        db.commit()
        
        return BaseResponse(
            success=True,
            message="Part analysis updated successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update part analysis: {str(e)}")

@router.delete("/results/{quote_id}/part/{part_id}", response_model=BaseResponse)
async def delete_part_analysis(
    quote_id: str,
    part_id: str,
    db: Session = Depends(get_db)
):
    """Delete a part from the analysis results"""
    
    # Verify quote and part exist
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    part = db.query(Part).filter(Part.id == part_id, Part.quote_id == quote_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    try:
        # Delete operations first (due to foreign key constraint)
        db.query(MachiningOperation).filter(MachiningOperation.part_id == part_id).delete()
        
        # Delete part
        db.delete(part)
        db.commit()
        
        return BaseResponse(
            success=True,
            message="Part deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete part: {str(e)}")

@router.post("/reanalyze/{quote_id}", response_model=BaseResponse)
async def reanalyze_quote(
    quote_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Re-run analysis for a quote (useful after manual corrections)"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    try:
        # Clear existing analysis results
        parts = db.query(Part).filter(Part.quote_id == quote_id).all()
        for part in parts:
            db.query(MachiningOperation).filter(MachiningOperation.part_id == part.id).delete()
            db.delete(part)
        
        # Reset quote status
        quote.status = QuoteStatusEnum.PENDING
        quote.updated_at = datetime.now()
        db.commit()
        
        # Start new analysis
        background_tasks.add_task(run_analysis, quote_id, db)
        
        return BaseResponse(
            success=True,
            message="Re-analysis started successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start re-analysis: {str(e)}")