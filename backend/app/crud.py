from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from . import models

# ---- Target helpers ----------------------------------------

def create_target(db: Session, url_or_name: str, target_type: models.TargetType):
    target = models.Target(url_or_name=url_or_name, type=target_type)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target

# ---- Findings helpers --------------------------------------

def upsert_findings(db: Session, target: models.Target, findings: List[Dict[str, Any]]):
    """Insert new findings or update timestamp if already present."""
    for f in findings:
        existing = (
            db.query(models.Finding)
            .filter_by(target_id=target.id, component=f["component"], cve=f.get("cve"))
            .first()
        )
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.is_resolved = False
        else:
            db.add(
                models.Finding(
                    target_id=target.id,
                    component=f["component"],
                    detected_version=f["detected_version"],
                    fixed_version=f.get("fixed_version"),
                    cve=f.get("cve"),
                    title=f.get("title"),
                    severity=models.Severity(f["severity"].lower()),
                )
            )
    target.last_scan_at = datetime.utcnow()
    db.commit()
