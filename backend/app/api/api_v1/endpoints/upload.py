"""
File upload API endpoints for CAD files
"""
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path

from app.db.database import get_db
from app.db import models, schemas
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=schemas.MultiFileUploadResponse)
async def upload_files(
    quote_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple CAD files for a quote"""
    try:
        # Verify quote exists
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                # Validate file
                file_validation = validate_file(file)
                if not file_validation["valid"]:
                    failed_files.append({
                        "filename": file.filename,
                        "error": file_validation["error"]
                    })
                    continue
                
                # Save file
                file_record = await save_uploaded_file(file, quote_id, db)
                
                uploaded_files.append(schemas.FileUploadResponse(
                    file_id=file_record.id,
                    filename=file_record.filename,
                    file_size=file_record.file_size,
                    upload_status="success",
                    message="File uploaded successfully"
                ))
                
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return schemas.MultiFileUploadResponse(
            quote_id=quote_id,
            uploaded_files=uploaded_files,
            failed_files=failed_files,
            total_files=len(files),
            successful_uploads=len(uploaded_files)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/single", response_model=schemas.FileUploadResponse)
async def upload_single_file(
    quote_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a single CAD file"""
    try:
        # Verify quote exists
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Validate file
        file_validation = validate_file(file)
        if not file_validation["valid"]:
            raise HTTPException(status_code=400, detail=file_validation["error"])
        
        # Save file
        file_record = await save_uploaded_file(file, quote_id, db)
        
        return schemas.FileUploadResponse(
            file_id=file_record.id,
            filename=file_record.filename,
            file_size=file_record.file_size,
            upload_status="success",
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quote_id}/files", response_model=List[schemas.QuoteFile])
async def get_quote_files(quote_id: int, db: Session = Depends(get_db)):
    """Get all files for a quote"""
    quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    files = db.query(models.QuoteFile).filter(models.QuoteFile.quote_id == quote_id).all()
    return files

@router.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete an uploaded file"""
    try:
        file_record = db.query(models.QuoteFile).filter(models.QuoteFile.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete physical file
        try:
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
        except Exception as e:
            print(f"Warning: Could not delete physical file: {str(e)}")
        
        # Delete database record
        db.delete(file_record)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """Download an uploaded file"""
    file_record = db.query(models.QuoteFile).filter(models.QuoteFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type='application/octet-stream'
    )

def validate_file(file: UploadFile) -> dict:
    """Validate uploaded file"""
    try:
        # Check file size
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            }
        
        # Check file extension
        if not file.filename:
            return {"valid": False, "error": "No filename provided"}
        
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            return {
                "valid": False,
                "error": f"File type '{file_extension}' not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            }
        
        # Additional file content validation could go here
        # For example, checking file headers, magic numbers, etc.
        
        return {"valid": True}
        
    except Exception as e:
        return {"valid": False, "error": f"File validation error: {str(e)}"}

async def save_uploaded_file(file: UploadFile, quote_id: int, db: Session) -> models.QuoteFile:
    """Save uploaded file to disk and database"""
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create upload directory for this quote
        quote_upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, f"quote_{quote_id}")
        os.makedirs(quote_upload_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(quote_upload_dir, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        file_record = models.QuoteFile(
            quote_id=quote_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=Path(file.filename).suffix.lower().lstrip('.'),
            file_size=file_size,
            is_processed=False,
            processing_status="uploaded"
        )
        
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        return file_record
        
    except Exception as e:
        db.rollback()
        # Clean up file if database operation failed
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        raise e

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": settings.ALLOWED_FILE_TYPES,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "descriptions": {
            "dwg": "AutoCAD Drawing files",
            "step": "STEP 3D CAD files",
            "stp": "STEP 3D CAD files (alternative extension)",
            "iges": "IGES 3D CAD files",
            "igs": "IGES 3D CAD files (alternative extension)",
            "pdf": "PDF technical drawings",
            "png": "PNG image files",
            "jpg": "JPEG image files",
            "jpeg": "JPEG image files"
        }
    }

@router.post("/{quote_id}/process-files")
async def process_uploaded_files(
    quote_id: int,
    force_reprocess: bool = False,
    db: Session = Depends(get_db)
):
    """Trigger processing of uploaded files for a quote"""
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        files = db.query(models.QuoteFile).filter(models.QuoteFile.quote_id == quote_id).all()
        if not files:
            raise HTTPException(status_code=400, detail="No files found for this quote")
        
        # Trigger AI analysis (this would typically be done as a background task)
        from app.api.api_v1.endpoints.quotes import run_ai_analysis_task
        
        # In a real implementation, this should be run as a background task
        # For now, we'll just update the quote status
        quote.status = "analyzing"
        db.commit()
        
        return {
            "message": "File processing initiated",
            "quote_id": quote_id,
            "files_to_process": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))