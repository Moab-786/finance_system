from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from app.dependencies import require_analyst_or_admin

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_analyst_or_admin)
):
    transactions = db.query(models.Transaction).all()
    total_income = sum(t.amount for t in transactions if t.type == models.TransactionType.income)
    total_expenses = sum(t.amount for t in transactions if t.type == models.TransactionType.expense)
    
    # Category breakdown
    categories = {}
    for t in transactions:
        categories[t.category] = categories.get(t.category, 0) + t.amount

    # Monthly totals
    monthly = {}
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + t.amount

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "category_breakdown": categories,
        "monthly_totals": monthly,
        "recent_activity": [
            {"id": t.id, "amount": t.amount, "type": t.type, "date": t.date}
            for t in sorted(transactions, key=lambda x: x.date, reverse=True)[:5]
        ]
    }