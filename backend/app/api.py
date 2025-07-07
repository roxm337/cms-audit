from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from .database import get_db
from . import crud, models
from .tasks import scan_laravel, scan_wordpress

router = APIRouter()

# ----------- Schemas ----------------------------------------
from pydantic import BaseModel, HttpUrl

class TargetOut(BaseModel):
    id: UUID
    url_or_name: str
    type: models.TargetType
    last_scan_at: str | None
    class Config:
        orm_mode = True

class FindingOut(BaseModel):
    component: str
    detected_version: str
    fixed_version: str | None
    cve: str | None
    title: str | None
    severity: models.Severity
    first_seen: str
    last_seen: str

# ----------- Routes -----------------------------------------

@router.post("/targets/laravel", response_model=TargetOut)
async def add_laravel_target(file: UploadFile = File(...), db: Session = Depends(get_db)):
    lock_bytes = await file.read()
    target = crud.create_target(db, file.filename, models.TargetType.LARAVEL)
    scan_laravel.delay(lock_bytes, str(target.id))
    return target

@router.post("/targets/wordpress", response_model=TargetOut)
async def add_wordpress_target(payload: dict, db: Session = Depends(get_db)):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing url")
    target = crud.create_target(db, url, models.TargetType.WORDPRESS)
    scan_wordpress.delay(url, str(target.id))
    return target

@router.get("/targets", response_model=List[TargetOut])
async def list_targets(db: Session = Depends(get_db)):
    return db.query(models.Target).all()

@router.get("/targets/{target_id}/findings", response_model=List[FindingOut])
async def list_findings(target_id: UUID, db: Session = Depends(get_db)):
    items = (
        db.query(models.Finding)
        .filter(models.Finding.target_id == target_id)
        .order_by(models.Finding.severity.desc())
        .all()
    )
    return items
