from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.database import Quote, Part, Feedback
from app.models.schemas import FeedbackSubmission, ActualProductionData, BaseResponse

router = APIRouter()

@router.post("/submit/{quote_id}", response_model=BaseResponse)
async def submit_feedback(
    quote_id: str,
    feedback_data: FeedbackSubmission,
    db: Session = Depends(get_db)
):
    """Submit actual production data for model improvement"""
    
    # Verify quote exists
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    try:
        # Calculate estimation accuracy for each part
        accuracy_metrics = []
        
        for actual_data in feedback_data.production_data:
            # Get the original part analysis
            part = db.query(Part).filter(Part.id == actual_data.part_id).first()
            if not part:
                continue
            
            # Calculate accuracy metrics
            time_accuracy = calculate_accuracy(part.total_cycle_time, actual_data.actual_cycle_time)
            
            # Estimate material cost accuracy (simplified)
            estimated_material_cost = estimate_original_material_cost(part)
            cost_accuracy = calculate_accuracy(estimated_material_cost, actual_data.actual_material_cost)
            
            accuracy_metrics.append({
                "part_id": actual_data.part_id,
                "time_accuracy": time_accuracy,
                "cost_accuracy": cost_accuracy,
                "overall_accuracy": (time_accuracy + cost_accuracy) / 2
            })
        
        # Calculate overall estimation accuracy
        overall_accuracy = sum(metric["overall_accuracy"] for metric in accuracy_metrics) / len(accuracy_metrics) if accuracy_metrics else 0
        
        # Create feedback record
        feedback_record = Feedback(
            quote_id=quote_id,
            actual_data=feedback_data.dict(),
            overall_feedback=feedback_data.overall_feedback,
            estimation_accuracy=overall_accuracy,
            lessons_learned=generate_lessons_learned(accuracy_metrics, feedback_data)
        )
        
        db.add(feedback_record)
        db.commit()
        
        # Trigger model retraining process (would be async in production)
        await process_feedback_for_training(feedback_record, db)
        
        return BaseResponse(
            success=True,
            message=f"Feedback submitted successfully. Overall accuracy: {overall_accuracy:.1%}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/quote/{quote_id}")
async def get_quote_feedback(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """Get feedback data for a specific quote"""
    
    feedback_records = db.query(Feedback).filter(Feedback.quote_id == quote_id).all()
    
    if not feedback_records:
        raise HTTPException(status_code=404, detail="No feedback found for this quote")
    
    return {
        "quote_id": quote_id,
        "feedback_count": len(feedback_records),
        "feedback_records": [
            {
                "id": record.id,
                "submitted_at": record.created_at,
                "estimation_accuracy": record.estimation_accuracy,
                "overall_feedback": record.overall_feedback,
                "lessons_learned": record.lessons_learned,
                "actual_data": record.actual_data
            }
            for record in feedback_records
        ]
    }

@router.get("/analytics/accuracy")
async def get_accuracy_analytics(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get model accuracy analytics across all feedback"""
    
    feedback_records = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(limit).all()
    
    if not feedback_records:
        return {
            "message": "No feedback data available",
            "analytics": {}
        }
    
    # Calculate analytics
    accuracies = [record.estimation_accuracy for record in feedback_records if record.estimation_accuracy is not None]
    
    analytics = {
        "total_feedback_count": len(feedback_records),
        "average_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
        "accuracy_trend": calculate_accuracy_trend(feedback_records),
        "accuracy_by_material": calculate_accuracy_by_material(feedback_records, db),
        "accuracy_by_complexity": calculate_accuracy_by_complexity(feedback_records, db),
        "common_issues": extract_common_issues(feedback_records),
        "improvement_suggestions": generate_improvement_suggestions(feedback_records)
    }
    
    return {
        "analytics": analytics,
        "last_updated": feedback_records[0].created_at if feedback_records else None
    }

@router.get("/training-data")
async def get_training_data(
    db: Session = Depends(get_db)
):
    """Get prepared training data for model improvement"""
    
    feedback_records = db.query(Feedback).all()
    
    training_data = []
    
    for record in feedback_records:
        # Get quote and parts data
        quote = db.query(Quote).filter(Quote.id == record.quote_id).first()
        if not quote:
            continue
        
        parts = db.query(Part).filter(Part.quote_id == record.quote_id).all()
        
        # Prepare training examples
        for part_data in record.actual_data.get("production_data", []):
            part = next((p for p in parts if p.id == part_data["part_id"]), None)
            if not part:
                continue
            
            training_example = {
                "input_features": {
                    "material_type": part.material_type,
                    "material_grade": part.material_grade,
                    "length": part.length,
                    "width": part.width,
                    "height": part.height,
                    "volume": part.volume,
                    "surface_area": part.surface_area,
                    "complexity_score": part.complexity_score
                },
                "predicted_values": {
                    "cycle_time": part.total_cycle_time,
                    "estimated_material_cost": estimate_original_material_cost(part)
                },
                "actual_values": {
                    "cycle_time": part_data["actual_cycle_time"],
                    "material_cost": part_data["actual_material_cost"],
                    "labor_hours": part_data["actual_labor_hours"]
                },
                "accuracy_metrics": {
                    "time_accuracy": calculate_accuracy(part.total_cycle_time, part_data["actual_cycle_time"]),
                    "cost_accuracy": calculate_accuracy(
                        estimate_original_material_cost(part), 
                        part_data["actual_material_cost"]
                    )
                },
                "feedback_date": record.created_at.isoformat()
            }
            
            training_data.append(training_example)
    
    return {
        "training_data": training_data,
        "total_examples": len(training_data),
        "ready_for_training": len(training_data) >= 10  # Minimum examples needed
    }

@router.post("/retrain-model", response_model=BaseResponse)
async def trigger_model_retraining(
    db: Session = Depends(get_db)
):
    """Trigger model retraining with latest feedback data"""
    
    # In a production system, this would:
    # 1. Extract all feedback data
    # 2. Prepare training datasets
    # 3. Queue model retraining job
    # 4. Update model versions
    # 5. Deploy improved models
    
    feedback_count = db.query(Feedback).count()
    
    if feedback_count < 10:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient feedback data for retraining. Need at least 10 examples, have {feedback_count}"
        )
    
    try:
        # Placeholder for actual retraining process
        # This would integrate with MLOps pipeline
        
        return BaseResponse(
            success=True,
            message=f"Model retraining initiated with {feedback_count} feedback examples"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate retraining: {str(e)}")

# Helper functions

def calculate_accuracy(predicted: float, actual: float) -> float:
    """Calculate accuracy percentage between predicted and actual values"""
    if predicted == 0 and actual == 0:
        return 1.0
    if predicted == 0 or actual == 0:
        return 0.0
    
    error = abs(predicted - actual) / max(predicted, actual)
    accuracy = max(0, 1 - error)
    return accuracy

def estimate_original_material_cost(part: Part) -> float:
    """Estimate the original material cost prediction for comparison"""
    # Simplified material cost estimation based on part properties
    material_prices = {
        'aluminum': 3.50,
        'steel': 1.20,
        'brass': 6.00,
        'titanium': 35.00
    }
    
    material_densities = {
        'aluminum': 2.7,
        'steel': 7.85,
        'brass': 8.5,
        'titanium': 4.5
    }
    
    price_per_kg = material_prices.get(part.material_type, 5.0)
    density = material_densities.get(part.material_type, 3.0)
    
    volume_cm3 = (part.volume or 1000) / 1000
    mass_kg = (volume_cm3 * density) / 1000
    
    return mass_kg * price_per_kg * 1.15  # 15% waste factor

def generate_lessons_learned(accuracy_metrics: List[dict], feedback_data: FeedbackSubmission) -> str:
    """Generate lessons learned from feedback data"""
    
    lessons = []
    
    # Analyze accuracy patterns
    time_accuracies = [m["time_accuracy"] for m in accuracy_metrics]
    cost_accuracies = [m["cost_accuracy"] for m in accuracy_metrics]
    
    avg_time_accuracy = sum(time_accuracies) / len(time_accuracies) if time_accuracies else 0
    avg_cost_accuracy = sum(cost_accuracies) / len(cost_accuracies) if cost_accuracies else 0
    
    if avg_time_accuracy < 0.8:
        lessons.append("Cycle time estimation needs improvement - consider material-specific factors")
    
    if avg_cost_accuracy < 0.8:
        lessons.append("Material cost estimation needs refinement - update pricing database")
    
    if feedback_data.overall_feedback:
        lessons.append(f"Client feedback: {feedback_data.overall_feedback}")
    
    return "; ".join(lessons) if lessons else "No specific issues identified"

async def process_feedback_for_training(feedback_record: Feedback, db: Session):
    """Process feedback record for model training (placeholder)"""
    
    # In production, this would:
    # 1. Extract features from feedback
    # 2. Update training dataset
    # 3. Queue model updates
    # 4. Log training metrics
    
    print(f"Processing feedback for training: {feedback_record.id}")

def calculate_accuracy_trend(feedback_records: List[Feedback]) -> dict:
    """Calculate accuracy trend over time"""
    
    if len(feedback_records) < 2:
        return {"trend": "insufficient_data"}
    
    # Sort by date and calculate trend
    sorted_records = sorted(feedback_records, key=lambda x: x.created_at)
    recent_half = sorted_records[len(sorted_records)//2:]
    earlier_half = sorted_records[:len(sorted_records)//2]
    
    recent_avg = sum(r.estimation_accuracy for r in recent_half if r.estimation_accuracy) / len(recent_half)
    earlier_avg = sum(r.estimation_accuracy for r in earlier_half if r.estimation_accuracy) / len(earlier_half)
    
    if recent_avg > earlier_avg + 0.05:
        trend = "improving"
    elif recent_avg < earlier_avg - 0.05:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "recent_accuracy": recent_avg,
        "earlier_accuracy": earlier_avg,
        "improvement": recent_avg - earlier_avg
    }

def calculate_accuracy_by_material(feedback_records: List[Feedback], db: Session) -> dict:
    """Calculate accuracy metrics by material type"""
    
    material_accuracy = {}
    
    for record in feedback_records:
        quote = db.query(Quote).filter(Quote.id == record.quote_id).first()
        if not quote:
            continue
        
        parts = db.query(Part).filter(Part.quote_id == record.quote_id).all()
        
        for part in parts:
            material = part.material_type
            if material not in material_accuracy:
                material_accuracy[material] = []
            
            if record.estimation_accuracy is not None:
                material_accuracy[material].append(record.estimation_accuracy)
    
    # Calculate averages
    result = {}
    for material, accuracies in material_accuracy.items():
        result[material] = {
            "average_accuracy": sum(accuracies) / len(accuracies),
            "sample_count": len(accuracies)
        }
    
    return result

def calculate_accuracy_by_complexity(feedback_records: List[Feedback], db: Session) -> dict:
    """Calculate accuracy metrics by part complexity"""
    
    complexity_ranges = {
        "low": (0, 0.3),
        "medium": (0.3, 0.7),
        "high": (0.7, 1.0)
    }
    
    complexity_accuracy = {range_name: [] for range_name in complexity_ranges}
    
    for record in feedback_records:
        parts = db.query(Part).filter(Part.quote_id == record.quote_id).all()
        
        for part in parts:
            complexity = part.complexity_score or 0.5
            
            for range_name, (min_val, max_val) in complexity_ranges.items():
                if min_val <= complexity < max_val:
                    if record.estimation_accuracy is not None:
                        complexity_accuracy[range_name].append(record.estimation_accuracy)
                    break
    
    # Calculate averages
    result = {}
    for range_name, accuracies in complexity_accuracy.items():
        if accuracies:
            result[range_name] = {
                "average_accuracy": sum(accuracies) / len(accuracies),
                "sample_count": len(accuracies)
            }
        else:
            result[range_name] = {
                "average_accuracy": 0,
                "sample_count": 0
            }
    
    return result

def extract_common_issues(feedback_records: List[Feedback]) -> List[str]:
    """Extract common issues from feedback"""
    
    issues = []
    
    low_accuracy_count = sum(1 for r in feedback_records if r.estimation_accuracy and r.estimation_accuracy < 0.7)
    
    if low_accuracy_count > len(feedback_records) * 0.3:
        issues.append("High percentage of low accuracy estimates")
    
    # Analyze feedback text for common patterns
    feedback_texts = [r.overall_feedback for r in feedback_records if r.overall_feedback]
    
    common_words = ["time", "cost", "material", "complex", "difficult"]
    for word in common_words:
        mentions = sum(1 for text in feedback_texts if word.lower() in text.lower())
        if mentions > len(feedback_texts) * 0.5:
            issues.append(f"Frequent mentions of '{word}' in feedback")
    
    return issues

def generate_improvement_suggestions(feedback_records: List[Feedback]) -> List[str]:
    """Generate improvement suggestions based on feedback patterns"""
    
    suggestions = []
    
    accuracies = [r.estimation_accuracy for r in feedback_records if r.estimation_accuracy is not None]
    
    if accuracies:
        avg_accuracy = sum(accuracies) / len(accuracies)
        
        if avg_accuracy < 0.7:
            suggestions.append("Consider retraining models with more diverse training data")
            suggestions.append("Review and update material cost database")
            suggestions.append("Improve complexity scoring algorithm")
        
        elif avg_accuracy < 0.85:
            suggestions.append("Fine-tune existing models with recent feedback data")
            suggestions.append("Add more granular material categories")
        
        else:
            suggestions.append("Models performing well - maintain current training schedule")
    
    if len(feedback_records) < 50:
        suggestions.append("Collect more feedback data for better model insights")
    
    return suggestions