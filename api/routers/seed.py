from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from api.core.database import get_db
from api.core.config import settings
from api.models import Category

router = APIRouter(prefix="/seed", tags=["Seed"])


@router.post("/categories")
def seed_categories(db: Session = Depends(get_db)):
    if not settings.DEBUG and not settings.ENABLE_SEED:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Seed endpoint is disabled in production")

    names = [
        'Salary', 'Freelance', 'Investment', 'Housing',
        'Food', 'Transport', 'Utilities', 'Shopping',
        'Entertainment', 'Savings', 'Healthcare', 'Education'
    ]

    created = []
    skipped = []

    for name in names:
        exists = db.query(Category).filter(Category.name == name).first()
        if not exists:
            db.add(Category(name=name, created_at=datetime.utcnow()))
            created.append(name)
        else:
            skipped.append(name)

    db.commit()

    return {
        "status": "done",
        "created": created,
        "skipped": skipped,
    }