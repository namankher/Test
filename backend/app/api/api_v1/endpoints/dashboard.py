"""
Dashboard and Analytics API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import calendar

from app.db.database import get_db
from app.db import models, schemas

router = APIRouter()

@router.get("/metrics", response_model=schemas.DashboardMetrics)
async def get_dashboard_metrics(
    days: int = Query(30, description="Number of days to calculate metrics for"),
    db: Session = Depends(get_db)
):
    """Get main dashboard KPI metrics"""
    try:
        # Calculate date ranges
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)
        
        # Current period metrics
        current_quotes = db.query(models.Quote).filter(
            and_(
                models.Quote.created_at >= start_date,
                models.Quote.created_at <= end_date
            )
        ).all()
        
        # Previous period metrics for comparison
        prev_quotes = db.query(models.Quote).filter(
            and_(
                models.Quote.created_at >= prev_start_date,
                models.Quote.created_at < start_date
            )
        ).all()
        
        # Calculate current period stats
        quotes_generated = len(current_quotes)
        quotes_approved = len([q for q in current_quotes if q.status == 'approved'])
        quotes_rejected = len([q for q in current_quotes if q.status == 'rejected'])
        quotes_pending = len([q for q in current_quotes if q.status in ['pending', 'analyzing', 'quoted']])
        
        total_revenue = sum([q.client_price for q in current_quotes if q.status == 'approved' and q.client_price])
        
        # Calculate processing times
        processing_times = [q.processing_time_minutes for q in current_quotes 
                          if q.processing_time_minutes and q.processing_time_minutes > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Calculate accuracy rate (based on AI confidence scores)
        confidence_scores = [q.ai_confidence_score for q in current_quotes 
                           if q.ai_confidence_score is not None]
        accuracy_rate = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Previous period stats for change calculation
        prev_quotes_generated = len(prev_quotes)
        prev_total_revenue = sum([q.client_price for q in prev_quotes if q.status == 'approved' and q.client_price])
        
        prev_processing_times = [q.processing_time_minutes for q in prev_quotes 
                               if q.processing_time_minutes and q.processing_time_minutes > 0]
        prev_avg_processing_time = sum(prev_processing_times) / len(prev_processing_times) if prev_processing_times else 0.0
        
        prev_confidence_scores = [q.ai_confidence_score for q in prev_quotes 
                                if q.ai_confidence_score is not None]
        prev_accuracy_rate = sum(prev_confidence_scores) / len(prev_confidence_scores) if prev_confidence_scores else 0.0
        
        # Calculate percentage changes
        quotes_change = ((quotes_generated - prev_quotes_generated) / prev_quotes_generated * 100) if prev_quotes_generated > 0 else 0.0
        revenue_change = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0.0
        processing_time_change = ((avg_processing_time - prev_avg_processing_time) / prev_avg_processing_time * 100) if prev_avg_processing_time > 0 else 0.0
        accuracy_change = ((accuracy_rate - prev_accuracy_rate) / prev_accuracy_rate * 100) if prev_accuracy_rate > 0 else 0.0
        
        # New clients in current period
        new_clients = db.query(models.Client).filter(
            and_(
                models.Client.created_at >= start_date,
                models.Client.created_at <= end_date
            )
        ).count()
        
        return schemas.DashboardMetrics(
            quotes_generated=quotes_generated,
            quotes_generated_change=quotes_change,
            total_revenue=total_revenue,
            total_revenue_change=revenue_change,
            avg_processing_time=avg_processing_time,
            avg_processing_time_change=processing_time_change,
            accuracy_rate=accuracy_rate,
            accuracy_rate_change=accuracy_change,
            quotes_pending=quotes_pending,
            quotes_approved=quotes_approved,
            quotes_rejected=quotes_rejected,
            new_clients_this_month=new_clients
        )
        
    except Exception as e:
        # Return default metrics if there's an error
        return schemas.DashboardMetrics(
            quotes_generated=0,
            quotes_generated_change=0.0,
            total_revenue=0.0,
            total_revenue_change=0.0,
            avg_processing_time=0.0,
            avg_processing_time_change=0.0,
            accuracy_rate=0.0,
            accuracy_rate_change=0.0,
            quotes_pending=0,
            quotes_approved=0,
            quotes_rejected=0,
            new_clients_this_month=0
        )

@router.get("/quote-status-distribution", response_model=schemas.QuoteStatusDistribution)
async def get_quote_status_distribution(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get distribution of quotes by status"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get quotes in the time period
        quotes = db.query(models.Quote).filter(
            and_(
                models.Quote.created_at >= start_date,
                models.Quote.created_at <= end_date
            )
        ).all()
        
        # Count by status
        status_counts = {
            'pending': 0,
            'analyzing': 0,
            'quoted': 0,
            'approved': 0,
            'rejected': 0
        }
        
        for quote in quotes:
            status = quote.status
            if status in status_counts:
                status_counts[status] += 1
        
        return schemas.QuoteStatusDistribution(**status_counts)
        
    except Exception as e:
        return schemas.QuoteStatusDistribution(
            pending=0, analyzing=0, quoted=0, approved=0, rejected=0
        )

@router.get("/revenue-by-month", response_model=List[schemas.RevenueByMonth])
async def get_revenue_by_month(
    months: int = Query(12, description="Number of months to analyze"),
    db: Session = Depends(get_db)
):
    """Get revenue data by month"""
    try:
        revenue_data = []
        current_date = datetime.utcnow()
        
        for i in range(months):
            # Calculate month boundaries
            if i == 0:
                month_end = current_date
                month_start = month_end.replace(day=1)
            else:
                # Go back i months
                if current_date.month > i:
                    month = current_date.month - i
                    year = current_date.year
                else:
                    month = 12 - (i - current_date.month)
                    year = current_date.year - 1
                
                month_start = datetime(year, month, 1)
                # Get last day of month
                last_day = calendar.monthrange(year, month)[1]
                month_end = datetime(year, month, last_day, 23, 59, 59)
            
            # Get approved quotes for this month
            month_quotes = db.query(models.Quote).filter(
                and_(
                    models.Quote.approved_at >= month_start,
                    models.Quote.approved_at <= month_end,
                    models.Quote.status == 'approved'
                )
            ).all()
            
            # Calculate revenue and count
            month_revenue = sum([q.client_price for q in month_quotes if q.client_price])
            quotes_count = len(month_quotes)
            
            month_name = month_start.strftime("%Y-%m")
            
            revenue_data.insert(0, schemas.RevenueByMonth(
                month=month_name,
                revenue=month_revenue,
                quotes_count=quotes_count
            ))
        
        return revenue_data
        
    except Exception as e:
        return []

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, description="Number of recent activities to return"),
    db: Session = Depends(get_db)
):
    """Get recent system activity"""
    try:
        # Get recent quotes
        recent_quotes = db.query(models.Quote).order_by(
            models.Quote.updated_at.desc()
        ).limit(limit).all()
        
        activities = []
        for quote in recent_quotes:
            activity = {
                "id": quote.id,
                "type": "quote",
                "action": f"Quote {quote.status}",
                "description": f"Quote {quote.quote_number} - {quote.project_name or 'Untitled'}",
                "timestamp": quote.updated_at.isoformat(),
                "status": quote.status,
                "value": quote.client_price
            }
            activities.append(activity)
        
        return {"activities": activities}
        
    except Exception as e:
        return {"activities": []}

@router.get("/top-clients")
async def get_top_clients(
    limit: int = Query(5, description="Number of top clients to return"),
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get top clients by revenue"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query to get clients with their total revenue
        client_revenue = db.query(
            models.Client.id,
            models.Client.name,
            models.Client.company,
            func.sum(models.Quote.client_price).label('total_revenue'),
            func.count(models.Quote.id).label('quote_count')
        ).join(
            models.Quote, models.Client.id == models.Quote.client_id
        ).filter(
            and_(
                models.Quote.created_at >= start_date,
                models.Quote.created_at <= end_date,
                models.Quote.status == 'approved'
            )
        ).group_by(
            models.Client.id, models.Client.name, models.Client.company
        ).order_by(
            func.sum(models.Quote.client_price).desc()
        ).limit(limit).all()
        
        top_clients = []
        for client in client_revenue:
            top_clients.append({
                "client_id": client.id,
                "name": client.name,
                "company": client.company,
                "total_revenue": float(client.total_revenue or 0),
                "quote_count": client.quote_count
            })
        
        return {"top_clients": top_clients}
        
    except Exception as e:
        return {"top_clients": []}

@router.get("/processing-performance")
async def get_processing_performance(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get AI processing performance metrics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get processed files in the time period
        processed_files = db.query(models.QuoteFile).filter(
            and_(
                models.QuoteFile.processed_at >= start_date,
                models.QuoteFile.processed_at <= end_date,
                models.QuoteFile.is_processed == True
            )
        ).all()
        
        # Calculate metrics
        total_files = len(processed_files)
        successful_files = len([f for f in processed_files if f.processing_status == 'completed'])
        failed_files = len([f for f in processed_files if f.processing_status == 'failed'])
        
        success_rate = (successful_files / total_files * 100) if total_files > 0 else 0.0
        
        # File type breakdown
        file_types = {}
        for file in processed_files:
            file_type = file.file_type
            if file_type not in file_types:
                file_types[file_type] = {"total": 0, "successful": 0}
            file_types[file_type]["total"] += 1
            if file.processing_status == 'completed':
                file_types[file_type]["successful"] += 1
        
        # Add success rates
        for file_type in file_types:
            total = file_types[file_type]["total"]
            successful = file_types[file_type]["successful"]
            file_types[file_type]["success_rate"] = (successful / total * 100) if total > 0 else 0.0
        
        return {
            "total_files_processed": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "overall_success_rate": success_rate,
            "file_type_breakdown": file_types
        }
        
    except Exception as e:
        return {
            "total_files_processed": 0,
            "successful_files": 0,
            "failed_files": 0,
            "overall_success_rate": 0.0,
            "file_type_breakdown": {}
        }

@router.get("/analytics/export")
async def export_analytics_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Export analytics data for the specified date range"""
    try:
        # Parse dates
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Get quotes in date range
        quotes = db.query(models.Quote).filter(
            and_(
                models.Quote.created_at >= start,
                models.Quote.created_at <= end
            )
        ).all()
        
        # Prepare export data
        export_data = []
        for quote in quotes:
            quote_data = {
                "quote_number": quote.quote_number,
                "client_name": quote.client.name if quote.client else "Unknown",
                "project_name": quote.project_name,
                "status": quote.status,
                "total_cost": quote.total_cost,
                "client_price": quote.client_price,
                "margin": quote.margin,
                "created_at": quote.created_at.isoformat(),
                "complexity_level": quote.complexity_level,
                "ai_confidence_score": quote.ai_confidence_score,
                "processing_time_minutes": quote.processing_time_minutes,
                "estimated_delivery_days": quote.estimated_delivery_days
            }
            export_data.append(quote_data)
        
        return {
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "total_quotes": len(export_data),
            "data": export_data
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "data": []
        }