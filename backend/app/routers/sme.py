from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import SMEOwnership

router = APIRouter(prefix="/sme", tags=["sme"])


@router.get("/{system_name}")
def get_sme(system_name: str, db: Session = Depends(get_db)):
    record = db.query(SMEOwnership).filter(SMEOwnership.system_name.ilike(system_name)).first()
    if not record:
        raise HTTPException(status_code=404, detail="SME not found")
    return {
        "system_name": record.system_name,
        "owner_name": record.owner_name,
        "owner_team": record.owner_team,
        "owner_email": record.owner_email,
        "expertise_tags": (record.expertise_tags or "").split(",")
    }
