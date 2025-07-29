from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import os

from app.core.database import get_db
from app.models.database import Quote, Part, CostBreakdown, ClientQuoteDelivery, QuoteStatusEnum
from app.models.schemas import (
    QuotationInput, CostBreakdown as CostBreakdownSchema, 
    ClientQuote, InternalQuoteRecord, BaseResponse
)
from app.services.cost_calculator import CostCalculator
from app.services.quote_generator import QuoteGenerator

router = APIRouter()

@router.post("/calculate/{quote_id}", response_model=CostBreakdownSchema)
async def calculate_costs(
    quote_id: str,
    quotation_input: QuotationInput,
    db: Session = Depends(get_db)
):
    """Calculate costs for all parts in a quote"""
    
    # Verify quote exists and analysis is complete
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status != QuoteStatusEnum.READY_FOR_REVIEW:
        raise HTTPException(status_code=400, detail="Quote analysis must be complete before cost calculation")
    
    # Get all parts for the quote
    parts = db.query(Part).filter(Part.quote_id == quote_id).all()
    if not parts:
        raise HTTPException(status_code=400, detail="No parts found for quote")
    
    try:
        # Initialize cost calculator
        calculator = CostCalculator()
        
        # Calculate costs for all parts
        total_costs = await calculator.calculate_quote_costs(
            parts=parts,
            quantity=quotation_input.quantity,
            overhead_percentage=quotation_input.overhead_percentage,
            margin_percentage=quotation_input.margin_percentage,
            delivery_days=quotation_input.delivery_days,
            rush_order=quotation_input.rush_order
        )
        
        # Save cost breakdown to database
        existing_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote_id).first()
        if existing_breakdown:
            # Update existing
            for key, value in total_costs.dict().items():
                if key != 'quote_id':
                    setattr(existing_breakdown, key, value)
            existing_breakdown.quantity = quotation_input.quantity
            existing_breakdown.delivery_days = quotation_input.delivery_days
            existing_breakdown.rush_order = quotation_input.rush_order
            existing_breakdown.updated_at = datetime.now()
            cost_breakdown = existing_breakdown
        else:
            # Create new
            cost_breakdown = CostBreakdown(
                quote_id=quote_id,
                material_cost=total_costs.material_cost,
                labor_cost=total_costs.labor_cost,
                machine_cost=total_costs.machine_cost,
                tool_cost=total_costs.tool_cost,
                setup_cost=total_costs.setup_cost,
                overhead_cost=total_costs.overhead_cost,
                subtotal=total_costs.subtotal,
                margin_percentage=total_costs.margin_percentage,
                margin_amount=total_costs.margin,
                total_cost=total_costs.total_cost,
                quantity=quotation_input.quantity,
                delivery_days=quotation_input.delivery_days,
                rush_order=quotation_input.rush_order
            )
            db.add(cost_breakdown)
        
        db.commit()
        db.refresh(cost_breakdown)
        
        return CostBreakdownSchema(
            material_cost=cost_breakdown.material_cost,
            labor_cost=cost_breakdown.labor_cost,
            machine_cost=cost_breakdown.machine_cost,
            tool_cost=cost_breakdown.tool_cost,
            setup_cost=cost_breakdown.setup_cost,
            overhead_cost=cost_breakdown.overhead_cost,
            subtotal=cost_breakdown.subtotal,
            margin=cost_breakdown.margin_amount,
            total_cost=cost_breakdown.total_cost
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost calculation failed: {str(e)}")

@router.get("/costs/{quote_id}", response_model=CostBreakdownSchema)
async def get_cost_breakdown(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get the current cost breakdown for a quote"""
    
    cost_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote_id).first()
    if not cost_breakdown:
        raise HTTPException(status_code=404, detail="Cost breakdown not found")
    
    return CostBreakdownSchema(
        material_cost=cost_breakdown.material_cost,
        labor_cost=cost_breakdown.labor_cost,
        machine_cost=cost_breakdown.machine_cost,
        tool_cost=cost_breakdown.tool_cost,
        setup_cost=cost_breakdown.setup_cost,
        overhead_cost=cost_breakdown.overhead_cost,
        subtotal=cost_breakdown.subtotal,
        margin=cost_breakdown.margin_amount,
        total_cost=cost_breakdown.total_cost
    )

@router.post("/approve/{quote_id}", response_model=BaseResponse)
async def approve_quote(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Approve a quote for client delivery"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Verify cost breakdown exists
    cost_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote_id).first()
    if not cost_breakdown:
        raise HTTPException(status_code=400, detail="Cost calculation required before approval")
    
    try:
        # Update quote status
        quote.status = QuoteStatusEnum.APPROVED
        quote.updated_at = datetime.now()
        db.commit()
        
        return BaseResponse(
            success=True,
            message="Quote approved successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Quote approval failed: {str(e)}")

@router.post("/generate-client-quote/{quote_id}", response_model=ClientQuote)
async def generate_client_quote(
    quote_id: str,
    include_breakdown: bool = False,
    db: Session = Depends(get_db)
):
    """Generate a professional client-facing quote"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status != QuoteStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="Quote must be approved before client delivery")
    
    # Get cost breakdown
    cost_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote_id).first()
    if not cost_breakdown:
        raise HTTPException(status_code=400, detail="Cost breakdown not found")
    
    # Get parts
    parts = db.query(Part).filter(Part.quote_id == quote_id).all()
    
    try:
        # Initialize quote generator
        generator = QuoteGenerator()
        
        # Generate client quote
        client_quote = await generator.generate_client_quote(
            quote=quote,
            parts=parts,
            cost_breakdown=cost_breakdown,
            include_cost_breakdown=include_breakdown
        )
        
        # Save client quote delivery record
        quote_delivery = ClientQuoteDelivery(
            quote_id=quote_id,
            quote_number=client_quote.quote_number,
            client_name=client_quote.client_name,
            client_email=client_quote.client_email,
            quote_data=client_quote.dict()
        )
        db.add(quote_delivery)
        db.commit()
        
        return client_quote
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote generation failed: {str(e)}")

@router.post("/send-to-client/{quote_id}", response_model=BaseResponse)
async def send_quote_to_client(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Send the generated quote to the client via email"""
    
    # Get quote delivery record
    quote_delivery = db.query(ClientQuoteDelivery).filter(
        ClientQuoteDelivery.quote_id == quote_id
    ).first()
    
    if not quote_delivery:
        raise HTTPException(status_code=404, detail="Client quote not generated yet")
    
    if quote_delivery.sent_at:
        raise HTTPException(status_code=400, detail="Quote already sent to client")
    
    try:
        # In production, this would send an actual email
        # For now, we'll just mark it as sent
        quote_delivery.sent_at = datetime.now()
        
        # Update quote status
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        quote.status = QuoteStatusEnum.SENT_TO_CLIENT
        quote.updated_at = datetime.now()
        
        db.commit()
        
        return BaseResponse(
            success=True,
            message="Quote sent to client successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send quote: {str(e)}")

@router.get("/internal-record/{quote_id}", response_model=InternalQuoteRecord)
async def get_internal_quote_record(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get the complete internal quote record with margins and profitability"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    cost_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote_id).first()
    if not cost_breakdown:
        raise HTTPException(status_code=404, detail="Cost breakdown not found")
    
    quote_delivery = db.query(ClientQuoteDelivery).filter(
        ClientQuoteDelivery.quote_id == quote_id
    ).first()
    if not quote_delivery:
        raise HTTPException(status_code=404, detail="Client quote not generated")
    
    # Calculate profitability analysis
    profitability_analysis = {
        "gross_profit": cost_breakdown.margin_amount,
        "gross_margin_percentage": cost_breakdown.margin_percentage,
        "cost_per_unit": cost_breakdown.subtotal / cost_breakdown.quantity,
        "selling_price_per_unit": cost_breakdown.total_cost / cost_breakdown.quantity,
        "break_even_quantity": max(1, int(cost_breakdown.overhead_cost / (cost_breakdown.total_cost / cost_breakdown.quantity - cost_breakdown.subtotal / cost_breakdown.quantity))),
        "estimated_delivery_date": (datetime.now() + timedelta(days=cost_breakdown.delivery_days)).isoformat()
    }
    
    return InternalQuoteRecord(
        quote_id=quote_id,
        client_quote=ClientQuote(**quote_delivery.quote_data),
        internal_costs=CostBreakdownSchema(
            material_cost=cost_breakdown.material_cost,
            labor_cost=cost_breakdown.labor_cost,
            machine_cost=cost_breakdown.machine_cost,
            tool_cost=cost_breakdown.tool_cost,
            setup_cost=cost_breakdown.setup_cost,
            overhead_cost=cost_breakdown.overhead_cost,
            subtotal=cost_breakdown.subtotal,
            margin=cost_breakdown.margin_amount,
            total_cost=cost_breakdown.total_cost
        ),
        margin_amount=cost_breakdown.margin_amount,
        margin_percentage=cost_breakdown.margin_percentage,
        profitability_analysis=profitability_analysis
    )

@router.get("/quotes/dashboard")
async def get_quotes_dashboard(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get dashboard view of all quotes with summary information"""
    
    query = db.query(Quote)
    
    if status:
        try:
            status_enum = QuoteStatusEnum(status)
            query = query.filter(Quote.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    quotes = query.offset(offset).limit(limit).all()
    
    dashboard_data = []
    for quote in quotes:
        cost_breakdown = db.query(CostBreakdown).filter(CostBreakdown.quote_id == quote.id).first()
        parts_count = db.query(Part).filter(Part.quote_id == quote.id).count()
        
        quote_summary = {
            "quote_id": quote.id,
            "client_name": quote.client_name,
            "client_email": quote.client_email,
            "status": quote.status.value,
            "created_at": quote.created_at,
            "updated_at": quote.updated_at,
            "parts_count": parts_count,
            "total_value": cost_breakdown.total_cost if cost_breakdown else None,
            "margin_amount": cost_breakdown.margin_amount if cost_breakdown else None,
            "delivery_days": cost_breakdown.delivery_days if cost_breakdown else None
        }
        dashboard_data.append(quote_summary)
    
    return {
        "quotes": dashboard_data,
        "total_count": db.query(Quote).count(),
        "filtered_count": query.count()
    }

@router.delete("/quote/{quote_id}", response_model=BaseResponse)
async def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Delete a quote and all associated data"""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    try:
        # Delete associated records (cascading should handle most of this)
        db.delete(quote)
        db.commit()
        
        return BaseResponse(
            success=True,
            message="Quote deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete quote: {str(e)}")