import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, require_admin
from app.config import get_settings

router = APIRouter(prefix="/transactions", tags=["Transactions"])
settings = get_settings()
ALLOWED_SORT_FIELDS = {
    "id": models.Transaction.id,
    "date": models.Transaction.date,
    "amount": models.Transaction.amount,
    "category": models.Transaction.category,
    "type": models.Transaction.type,
}


def build_transaction_query(
    db: Session,
    current_user,
    type: Optional[models.TransactionType] = None,
    category: Optional[str] = None,
    categories: Optional[str] = None,
    search: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    query = db.query(models.Transaction)

    if current_user.role != models.UserRole.admin:
        query = query.filter(models.Transaction.user_id == current_user.id)

    if type:
        query = query.filter(models.Transaction.type == type)
    if category:
        query = query.filter(models.Transaction.category == category.strip().lower())
    if categories:
        normalized_categories = [c.strip().lower() for c in categories.split(",") if c.strip()]
        if normalized_categories:
            query = query.filter(models.Transaction.category.in_(normalized_categories))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Transaction.category.ilike(pattern),
                models.Transaction.notes.ilike(pattern),
            )
        )
    if amount_min is not None:
        query = query.filter(models.Transaction.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(models.Transaction.amount <= amount_max)
    if from_date:
        query = query.filter(models.Transaction.date >= from_date)
    if to_date:
        query = query.filter(models.Transaction.date <= to_date)

    return query

@router.post("/", response_model=schemas.TransactionOut)
def create(
    t: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    record = models.Transaction(**t.model_dump(), user_id=current_user.id)
    if not record.date:
        record.date = datetime.now(timezone.utc)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/", response_model=schemas.TransactionListResponse)
def get_all(
    type: Optional[models.TransactionType] = None,
    category: Optional[str] = None,
    categories: Optional[str] = None,
    search: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = settings["default_page_size"],
    sort_by: str = "date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if skip < 0:
        raise HTTPException(status_code=422, detail="skip must be 0 or greater")
    if limit < 1 or limit > settings["max_page_size"]:
        raise HTTPException(
            status_code=422,
            detail=f"limit must be between 1 and {settings['max_page_size']}"
        )
    if amount_min is not None and amount_min <= 0:
        raise HTTPException(status_code=422, detail="amount_min must be greater than 0")
    if amount_max is not None and amount_max <= 0:
        raise HTTPException(status_code=422, detail="amount_max must be greater than 0")
    if amount_min is not None and amount_max is not None and amount_min > amount_max:
        raise HTTPException(status_code=422, detail="amount_min cannot be greater than amount_max")
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=422, detail="invalid sort_by field")
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="sort_order must be either 'asc' or 'desc'")

    schemas.TransactionFilters(from_date=from_date, to_date=to_date)

    query = build_transaction_query(
        db=db,
        current_user=current_user,
        type=type,
        category=category,
        categories=categories,
        search=search,
        amount_min=amount_min,
        amount_max=amount_max,
        from_date=from_date,
        to_date=to_date,
    )

    total = query.count()
    sort_column = ALLOWED_SORT_FIELDS[sort_by]
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    items = query.offset(skip).limit(limit).all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/export")
def export_transactions(
    type: Optional[models.TransactionType] = None,
    category: Optional[str] = None,
    categories: Optional[str] = None,
    search: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = build_transaction_query(
        db=db,
        current_user=current_user,
        type=type,
        category=category,
        categories=categories,
        search=search,
        amount_min=amount_min,
        amount_max=amount_max,
        from_date=from_date,
        to_date=to_date,
    ).order_by(models.Transaction.date.desc())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "amount", "type", "category", "date", "notes", "user_id"])
    for record in query.all():
        writer.writerow([
            record.id,
            record.amount,
            record.type.value,
            record.category,
            record.date.isoformat() if record.date else "",
            record.notes or "",
            record.user_id,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )

@router.get("/{id}", response_model=schemas.TransactionOut)
def get_one(id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    record = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if current_user.role != models.UserRole.admin and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this transaction")
    return record

@router.put("/{id}", response_model=schemas.TransactionOut)
def update(
    id: int,
    data: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    record = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    record = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(record)
    db.commit()
    return {"message": "Transaction deleted"}


@router.post("/import")
def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    records_to_create = []

    try:
        for index, row in enumerate(reader, start=2):
            payload = {
                "amount": float(row["amount"]),
                "type": row["type"],
                "category": row["category"],
                "date": row.get("date") or None,
                "notes": row.get("notes") or None,
            }
            validated = schemas.TransactionCreate(**payload)
            records_to_create.append(models.Transaction(**validated.model_dump(), user_id=current_user.id))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid CSV data: {exc}")

    if not records_to_create:
        raise HTTPException(status_code=422, detail="No valid transactions found in file")

    try:
        for record in records_to_create:
            db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to import transactions")

    return {"message": "Transactions imported successfully", "count": len(records_to_create)}