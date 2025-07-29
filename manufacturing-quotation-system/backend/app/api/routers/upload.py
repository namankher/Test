from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import aiofiles
from datetime import datetime

from app.core.database import get_db
from app.models.database import Quote, QuoteFile, QuoteStatusEnum, FileTypeEnum
from app.models.schemas import FileUploadResponse, MultipleFileUploadRequest, BaseResponse
from app.services.file_handler import FileHandler
from app.services.validation import FileValidator

router = APIRouter()

# File type mapping
FILE_TYPE_MAPPING = {
    '.step': FileTypeEnum.CAD_3D,
    '.stp': FileTypeEnum.CAD_3D,
    '.stl': FileTypeEnum.CAD_3D,
    '.dwg': FileTypeEnum.CAD_2D,
    '.dxf': FileTypeEnum.CAD_2D,
    '.pdf': FileTypeEnum.PDF,
    '.png': FileTypeEnum.IMAGE,
    '.jpg': FileTypeEnum.IMAGE,
    '.jpeg': FileTypeEnum.IMAGE,
    '.tiff': FileTypeEnum.IMAGE,
}

@router.post("/create-quote", response_model=BaseResponse)
async def create_new_quote(
    client_name: str = Form(...),
    client_email: str = Form(...),
    project_description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new quote for file uploads"""
    try:
        quote_id = str(uuid.uuid4())
        
        new_quote = Quote(
            id=quote_id,
            client_name=client_name,
            client_email=client_email,
            project_description=project_description,
            status=QuoteStatusEnum.PENDING
        )
        
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        
        return BaseResponse(
            success=True,
            message=f"Quote created successfully with ID: {quote_id}",
            quote_id=quote_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create quote: {str(e)}")

@router.post("/files/{quote_id}", response_model=List[FileUploadResponse])
async def upload_files(
    quote_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple files for a specific quote"""
    
    # Verify quote exists
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    file_validator = FileValidator()
    file_handler = FileHandler()
    uploaded_files = []
    
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        quote_upload_dir = os.path.join(upload_dir, quote_id)
        os.makedirs(quote_upload_dir, exist_ok=True)
        
        for file in files:
            # Validate file
            await file_validator.validate_file(file)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(quote_upload_dir, unique_filename)
            
            # Determine file type
            file_type = FILE_TYPE_MAPPING.get(file_extension, FileTypeEnum.IMAGE)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create database record
            quote_file = QuoteFile(
                id=file_id,
                quote_id=quote_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_type=file_type,
                file_size=len(content)
            )
            
            db.add(quote_file)
            
            # Add to response list
            uploaded_files.append(FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                file_type=file_type,
                file_size=len(content),
                upload_timestamp=datetime.now()
            ))
        
        # Update quote status to start analysis
        quote.status = QuoteStatusEnum.ANALYZING
        quote.updated_at = datetime.now()
        
        db.commit()
        
        # Trigger analysis process (async)
        # This would be handled by a background task in production
        # analysis_service.start_analysis(quote_id)
        
        return uploaded_files
        
    except Exception as e:
        db.rollback()
        # Clean up any uploaded files
        for uploaded_file in uploaded_files:
            try:
                if os.path.exists(uploaded_file.file_path):
                    os.remove(uploaded_file.file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/quote/{quote_id}/files", response_model=List[FileUploadResponse])
async def get_quote_files(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get all files for a specific quote"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    files = db.query(QuoteFile).filter(QuoteFile.quote_id == quote_id).all()
    
    return [
        FileUploadResponse(
            file_id=file.id,
            filename=file.original_filename,
            file_type=file.file_type,
            file_size=file.file_size,
            upload_timestamp=file.upload_timestamp
        )
        for file in files
    ]

@router.delete("/files/{file_id}", response_model=BaseResponse)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Delete a specific file"""
    
    file_record = db.query(QuoteFile).filter(QuoteFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Delete physical file
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # Delete database record
        db.delete(file_record)
        db.commit()
        
        return BaseResponse(
            success=True,
            message="File deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": {
            "cad_3d": [".step", ".stp", ".stl"],
            "cad_2d": [".dwg", ".dxf"],
            "documents": [".pdf"],
            "images": [".png", ".jpg", ".jpeg", ".tiff"]
        },
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE", 50)),
        "max_files_per_quote": 20
    }