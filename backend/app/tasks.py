import json, os, subprocess, tempfile, httpx, shlex, re
from typing import List, Dict
from pathlib import Path
from celery.utils.log import get_task_logger

from .celery_app import celery_app
from .settings import settings
from .database import SessionLocal
from . import crud, models

logger = get_task_logger(__name__)

# ---------- Helper functions --------------------------------

def _parse_osv_batch(pkgs: List[Dict[str, str]]):
    resp = httpx.post("https://api.osv.dev/v1/querybatch", json={"queries": pkgs}, timeout=30)
    resp.raise_for_status()
    vulns = []
    for res in resp.json().get("results", []):
        pkg = res["package"]
        version = res.get("version")
        for vuln in res.get("vulns", []):
            sev = vuln.get("severity", [])[0].get("type", "unknown").lower() if vuln.get("severity") else "medium"
            vulns.append(
                {
                    "component": pkg["name"],
                    "detected_version": version,
                    "fixed_version": vuln.get("fixed"),
                    "cve": (vuln.get("aliases") or [None])[0],
                    "title": vuln.get("summary"),
                    "severity": sev,
                }
            )
    return vulns

# ---------- Celery tasks ------------------------------------

@celery_app.task(name="scan_laravel", autoretry_for=(Exception,), retry_backoff=True, max_retries=3, time_limit=600)
def scan_laravel(lock_bytes: bytes, target_id: str):
    """Scan a Laravel/Composer project via composer audit + OSV."""
    db = SessionLocal()
    target = db.query(models.Target).get(target_id)
    if not target:
        logger.error("Unknown target ID %s", target_id)
        return

    lock_json = json.loads(lock_bytes)
    pkgs = [
        {
            "package": {
                "name": p["name"],
                "ecosystem": "Composer",
            },
            "version": p["version"],
        }
        for p in lock_json["packages"]
    ]

    findings = _parse_osv_batch(pkgs)

    # composer audit for extra advisories
    with tempfile.TemporaryDirectory() as tmp:
        lock_path = Path(tmp) / "composer.lock"
        lock_path.write_bytes(lock_bytes)
        try:
            audit = subprocess.run(
                ["composer", "audit", "--format=json", "--locked"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=300,
            )
            audit_json = json.loads(audit.stdout)
            for adv in audit_json.get("advisories", {}).values():
                findings.append(
                    {
                        "component": adv["package"],
                        "detected_version": adv["version"],
                        "fixed_version": adv.get("cve") and adv.get("title"),  # composer doesn't include fix version
                        "cve": adv.get("cve"),
                        "title": adv.get("title"),
                        "severity": adv.get("severity", "medium"),
                    }
                )
        except subprocess.TimeoutExpired:
            logger.warning("composer audit timed out for target %s", target_id)

    crud.upsert_findings(db, target, findings)
    db.close()

@celery_app.task(name="scan_wordpress", autoretry_for=(Exception,), retry_backoff=True, max_retries=3, time_limit=900)
def scan_wordpress(url: str, target_id: str):
    """Run WPScan CLI to enumerate core/plugins/themes and parse JSON output."""
    db = SessionLocal()
    target = db.query(models.Target).get(target_id)
    if not target:
        logger.error("Unknown target ID %s", target_id)
        return

    token = settings.wpscan_token
    cmd = [
        "wpscan",
        "--url",
        url,
        "--enumerate",
        "ap,at,cb",
        "--format",
        "json",
        "--api-token",
        token,
        "--no-update",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=800)
        report = json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        logger.error("WPScan timed out on %s", url)
        return
    except json.JSONDecodeError:
        logger.error("WPScan produced invalid JSON for %s", url)
        return

    findings: List[Dict] = []

    def _collect(vuln_entry, component, detected_version):
        for v in vuln_entry.get("vulns", []):
            sev = v.get("cvssv3" or "cvssv2", {}).get("base_score", 0)
            sev_label = (
                "critical" if sev >= 9 else "high" if sev >= 7 else "medium" if sev >= 4 else "low"
            )
            findings.append(
                {
                    "component": component,
                    "detected_version": detected_version,
                    "fixed_version": v.get("fixed_in"),
                    "cve": (v.get("references", {}).get("cve") or [None])[0],
                    "title": v.get("title"),
                    "severity": sev_label,
                }
            )

    # core
    core = report.get("version", {})
    if core and core.get("vulnerabilities"):
        _collect({"vulns": core["vulnerabilities"]}, "wordpress-core", core.get("number"))

    # plugins
    for plugin_name, data in (report.get("plugins") or {}).items():
        if data.get("vulnerabilities"):
            _collect({"vulns": data["vulnerabilities"]}, plugin_name, data.get("version"))

    # themes
    for theme_name, data in (report.get("themes") or {}).items():
        if data.get("vulnerabilities"):
            _collect({"vulns": data["vulnerabilities"]}, theme_name, data.get("version"))

    crud.upsert_findings(db, target, findings)
    db.close()
