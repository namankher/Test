"""
Client management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Client])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    db: Session = Depends(get_db)
):
    """List all clients with optional search"""
    try:
        query = db.query(models.Client).filter(models.Client.is_active == True)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (models.Client.name.ilike(search_term)) |
                (models.Client.email.ilike(search_term)) |
                (models.Client.company.ilike(search_term))
            )
        
        clients = query.offset(skip).limit(limit).all()
        return clients
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=schemas.Client)
async def create_client(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    """Create a new client"""
    try:
        # Check if email already exists
        existing_client = db.query(models.Client).filter(
            models.Client.email == client_data.email
        ).first()
        
        if existing_client:
            raise HTTPException(
                status_code=400, 
                detail="Client with this email already exists"
            )
        
        # Create new client
        db_client = models.Client(
            name=client_data.name,
            email=client_data.email,
            phone=client_data.phone,
            company=client_data.company,
            address=client_data.address
        )
        
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        
        return db_client
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}", response_model=schemas.Client)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """Get a specific client by ID"""
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.is_active == True
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client

@router.put("/{client_id}", response_model=schemas.Client)
async def update_client(
    client_id: int,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update a client"""
    try:
        client = db.query(models.Client).filter(
            models.Client.id == client_id,
            models.Client.is_active == True
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if email is being changed and if it conflicts
        if client_data.email and client_data.email != client.email:
            existing_client = db.query(models.Client).filter(
                models.Client.email == client_data.email,
                models.Client.id != client_id
            ).first()
            
            if existing_client:
                raise HTTPException(
                    status_code=400,
                    detail="Another client with this email already exists"
                )
        
        # Update fields
        update_data = client_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        
        db.commit()
        db.refresh(client)
        
        return client
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Soft delete a client (mark as inactive)"""
    try:
        client = db.query(models.Client).filter(
            models.Client.id == client_id,
            models.Client.is_active == True
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if client has active quotes
        active_quotes = db.query(models.Quote).filter(
            models.Quote.client_id == client_id,
            models.Quote.status.in_(['pending', 'analyzing', 'quoted'])
        ).count()
        
        if active_quotes > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete client with {active_quotes} active quotes"
            )
        
        # Soft delete (mark as inactive)
        client.is_active = False
        db.commit()
        
        return {"message": "Client deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/quotes", response_model=List[schemas.Quote])
async def get_client_quotes(
    client_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all quotes for a specific client"""
    try:
        # Verify client exists
        client = db.query(models.Client).filter(
            models.Client.id == client_id,
            models.Client.is_active == True
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Build quote query
        query = db.query(models.Quote).filter(models.Quote.client_id == client_id)
        
        # Apply status filter if provided
        if status:
            query = query.filter(models.Quote.status == status)
        
        quotes = query.order_by(models.Quote.created_at.desc()).limit(limit).all()
        return quotes
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/stats")
async def get_client_stats(client_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific client"""
    try:
        # Verify client exists
        client = db.query(models.Client).filter(
            models.Client.id == client_id,
            models.Client.is_active == True
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get all quotes for this client
        quotes = db.query(models.Quote).filter(models.Quote.client_id == client_id).all()
        
        # Calculate statistics
        total_quotes = len(quotes)
        approved_quotes = len([q for q in quotes if q.status == 'approved'])
        pending_quotes = len([q for q in quotes if q.status in ['pending', 'analyzing', 'quoted']])
        rejected_quotes = len([q for q in quotes if q.status == 'rejected'])
        
        total_revenue = sum([q.client_price for q in quotes if q.status == 'approved' and q.client_price])
        
        # Calculate average values
        approved_quote_values = [q.client_price for q in quotes if q.status == 'approved' and q.client_price]
        avg_quote_value = sum(approved_quote_values) / len(approved_quote_values) if approved_quote_values else 0.0
        
        # Processing times
        processing_times = [q.processing_time_minutes for q in quotes if q.processing_time_minutes]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        return {
            "client_id": client_id,
            "client_name": client.name,
            "company": client.company,
            "statistics": {
                "total_quotes": total_quotes,
                "approved_quotes": approved_quotes,
                "pending_quotes": pending_quotes,
                "rejected_quotes": rejected_quotes,
                "total_revenue": total_revenue,
                "average_quote_value": avg_quote_value,
                "average_processing_time_minutes": avg_processing_time,
                "approval_rate": (approved_quotes / total_quotes * 100) if total_quotes > 0 else 0.0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))