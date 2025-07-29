from fastapi import HTTPException, UploadFile
import os
import magic
from typing import List

class FileValidator:
    def __init__(self):
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", 50)) * 1024 * 1024  # Convert MB to bytes
        self.allowed_extensions = [
            '.step', '.stp', '.stl', '.dwg', '.dxf', 
            '.pdf', '.png', '.jpg', '.jpeg', '.tiff'
        ]
        
        # MIME type mapping for additional validation
        self.mime_types = {
            '.pdf': ['application/pdf'],
            '.png': ['image/png'],
            '.jpg': ['image/jpeg'],
            '.jpeg': ['image/jpeg'],
            '.tiff': ['image/tiff'],
            '.step': ['application/octet-stream', 'model/step'],
            '.stp': ['application/octet-stream', 'model/step'],
            '.stl': ['application/octet-stream', 'model/stl'],
            '.dwg': ['application/acad', 'image/vnd.dwg'],
            '.dxf': ['application/dxf', 'image/vnd.dxf']
        }
    
    async def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file for security and format compliance"""
        
        # Check if filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Read file content for size and MIME type validation
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        # Check file size
        if len(content) > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum allowed size of {max_size_mb:.1f}MB"
            )
        
        # Check minimum file size (avoid empty files)
        if len(content) < 100:  # 100 bytes minimum
            raise HTTPException(status_code=400, detail="File appears to be empty or corrupted")
        
        # Validate MIME type (if python-magic is available)
        try:
            mime_type = magic.from_buffer(content, mime=True)
            expected_mimes = self.mime_types.get(file_extension, [])
            
            # For binary CAD files, we allow octet-stream as it's common
            if file_extension in ['.step', '.stp', '.stl', '.dwg'] and mime_type == 'application/octet-stream':
                pass  # This is acceptable for CAD files
            elif expected_mimes and mime_type not in expected_mimes:
                # For images and PDFs, be more strict
                if file_extension in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File MIME type {mime_type} doesn't match extension {file_extension}"
                    )
        except ImportError:
            # python-magic not available, skip MIME validation
            pass
        except Exception as e:
            # If MIME detection fails, log but don't block upload
            print(f"MIME detection failed for {file.filename}: {str(e)}")
        
        # Additional validation for specific file types
        await self._validate_specific_format(file_extension, content)
        
        return True
    
    async def _validate_specific_format(self, extension: str, content: bytes):
        """Perform specific validation based on file type"""
        
        if extension == '.pdf':
            # Check PDF magic number
            if not content.startswith(b'%PDF-'):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        elif extension in ['.png']:
            # Check PNG magic number
            if not content.startswith(b'\x89PNG\r\n\x1a\n'):
                raise HTTPException(status_code=400, detail="Invalid PNG file format")
        
        elif extension in ['.jpg', '.jpeg']:
            # Check JPEG magic number
            if not (content.startswith(b'\xff\xd8\xff')):
                raise HTTPException(status_code=400, detail="Invalid JPEG file format")
        
        elif extension == '.stl':
            # Check STL format (ASCII starts with 'solid', binary has 80-byte header)
            if content.startswith(b'solid '):
                # ASCII STL
                if b'endsolid' not in content:
                    raise HTTPException(status_code=400, detail="Invalid ASCII STL file format")
            else:
                # Binary STL should have at least 84 bytes (80-byte header + 4-byte triangle count)
                if len(content) < 84:
                    raise HTTPException(status_code=400, detail="Invalid binary STL file format")
        
        elif extension in ['.step', '.stp']:
            # STEP files should start with ISO-10303 identifier
            content_str = content[:200].decode('utf-8', errors='ignore').upper()
            if 'ISO-10303' not in content_str and 'STEP' not in content_str:
                raise HTTPException(status_code=400, detail="Invalid STEP file format")
    
    def validate_multiple_files(self, files: List[UploadFile]) -> bool:
        """Validate multiple files for batch upload"""
        
        if len(files) > 20:  # Max files per quote
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed per quote")
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one file is required")
        
        # Check for duplicate filenames
        filenames = [file.filename for file in files if file.filename]
        if len(filenames) != len(set(filenames)):
            raise HTTPException(status_code=400, detail="Duplicate filenames are not allowed")
        
        return True