# fluxara/reports/auto_generator.py
"""
Pre-generates ALL PDF reports and saves to disk.
Runs on API startup (background) and every night at midnight.

Directory structure:
  reports/
    facilities/   -> Facility_1.pdf, Facility_2.pdf, ...
    regions/      -> USA.pdf, CAN.pdf, Global.pdf, ...
    companies/    -> OrgName_1.pdf, OrgName_2.pdf, ...
    manifest.json -> index of all generated files + metadata
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from fluxara.database.connection import AsyncSessionLocal
from fluxara.database.models import Facility, Inversion, Alert, Organisation
from fluxara.utils.pdf_generator import (
    generate_facility_pdf,
    generate_company_pdf,
    generate_summary_pdf,
    generate_full_pdf,
    generate_compliance_pdf,
)

logger = logging.getLogger("fluxara.reports")

# Root directory for pre-generated reports
REPORTS_DIR = Path(os.getenv("FLUXARA_REPORTS_DIR", "reports"))
FACILITIES_DIR = REPORTS_DIR / "facilities"
REGIONS_DIR = REPORTS_DIR / "regions"
COMPANIES_DIR = REPORTS_DIR / "companies"
MANIFEST_PATH = REPORTS_DIR / "manifest.json"


def _ensure_dirs():
    """Create report directories if they don't exist."""
    for d in [FACILITIES_DIR, REGIONS_DIR, COMPANIES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Convert a name into a filesystem-safe filename."""
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    return safe.strip().replace(' ', '_')[:80]


async def generate_all_reports():
    """
    Master function: generates every PDF and writes manifest.
    Called on startup and by the nightly scheduler.
    """
    _ensure_dirs()
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "facilities": [],
        "regions": [],
        "companies": [],
        "global": None,
    }

    async with AsyncSessionLocal() as db:
        try:
            # ── Load all data once ──────────────────────────────────────
            fac_result = await db.execute(select(Facility).order_by(Facility.name))
            all_facilities = fac_result.scalars().all()

            inv_result = await db.execute(
                select(Inversion).order_by(Inversion.date.desc())
            )
            all_inversions = inv_result.scalars().all()

            alert_result = await db.execute(
                select(Alert).where(Alert.resolved == False).order_by(Alert.created_at.desc())
            )
            all_alerts = alert_result.scalars().all()

            org_result = await db.execute(select(Organisation).where(Organisation.active == True))
            all_orgs = org_result.scalars().all()

            if not all_facilities:
                logger.warning("No facilities in database - skipping PDF generation")
                return manifest

            logger.info(f"Starting PDF generation: {len(all_facilities)} facilities, "
                        f"{len(all_orgs)} orgs, {len(all_inversions)} inversions")

            # ── 1. Per-Facility PDFs ────────────────────────────────────
            inv_by_fac = {}
            for inv in all_inversions:
                inv_by_fac.setdefault(inv.facility_id, []).append(inv)

            alert_by_fac = {}
            for alert in all_alerts:
                alert_by_fac.setdefault(alert.facility_id, []).append(alert)

            for facility in all_facilities:
                try:
                    f_dict = {
                        "name": facility.name,
                        "country": facility.country,
                        "sector": facility.sector,
                        "lat": facility.lat,
                        "lon": facility.lon,
                        "fluxara_latest": facility.fluxara_latest,
                        "risk_level": facility.risk_level or "low",
                        "epa_reported": facility.epa_reported,
                    }
                    inv_list = [
                        {"date": str(i.date), "emission_rate": i.emission_rate or 0, "confidence": i.confidence or 0}
                        for i in inv_by_fac.get(facility.id, [])[:10]
                    ]
                    alert_list = [
                        {"severity": a.severity or "medium", "message": a.message or "", "created_at": a.created_at.isoformat() if a.created_at else ""}
                        for a in alert_by_fac.get(facility.id, [])[:5]
                    ]

                    pdf_bytes = generate_facility_pdf(f_dict, inv_list, alert_list)
                    filename = f"Facility_{facility.id}_{_safe_filename(facility.name)}.pdf"
                    filepath = FACILITIES_DIR / filename
                    filepath.write_bytes(pdf_bytes)

                    manifest["facilities"].append({
                        "id": facility.id,
                        "name": facility.name,
                        "country": facility.country,
                        "sector": facility.sector,
                        "org_id": facility.org_id,
                        "filename": filename,
                        "file_size": len(pdf_bytes),
                        "risk_level": facility.risk_level,
                    })
                except Exception as e:
                    logger.error(f"Failed to generate PDF for facility {facility.id}: {e}")

            logger.info(f"Generated {len(manifest['facilities'])} facility PDFs")

            # ── 2. Per-Region (Country) PDFs ────────────────────────────
            countries = set(f.country for f in all_facilities if f.country)
            for country in countries:
                try:
                    country_facs = [f for f in all_facilities if f.country == country]
                    fac_dicts = [
                        {
                            "name": f.name, "country": f.country, "sector": f.sector,
                            "fluxara_latest": f.fluxara_latest, "epa_reported": f.epa_reported,
                            "risk_level": f.risk_level or "low",
                        }
                        for f in country_facs
                    ]

                    total_emissions = sum(f.get("fluxara_latest", 0) or 0 for f in fac_dicts)
                    total_epa = sum(f.get("epa_reported", 0) or 0 for f in fac_dicts)
                    high_risk = sum(1 for f in fac_dicts if (f.get("risk_level") or "").lower() == "high")
                    underreporting = [
                        f for f in fac_dicts
                        if (f.get("epa_reported") or 0) > 0 and (f.get("fluxara_latest") or 0) > 0
                        and ((f["fluxara_latest"] - f["epa_reported"]) / f["epa_reported"]) > 0.20
                    ]
                    ur_pct = round(len(underreporting) / len(fac_dicts) * 100, 1) if fac_dicts else 0

                    stats = {
                        "total_facilities": len(fac_dicts),
                        "total_emissions": total_emissions,
                        "total_epa": total_epa,
                        "high_risk": high_risk,
                        "underreporting_pct": ur_pct,
                        "region": country,
                        "date_from": "All time",
                        "date_to": datetime.utcnow().strftime("%Y-%m-%d"),
                    }

                    title = f"Fluxara Regional Summary - {country} - {datetime.utcnow().strftime('%B %Y')}"
                    pdf_bytes = generate_summary_pdf(title, fac_dicts, stats)

                    filename = f"Region_{_safe_filename(country)}.pdf"
                    filepath = REGIONS_DIR / filename
                    filepath.write_bytes(pdf_bytes)

                    manifest["regions"].append({
                        "country": country,
                        "filename": filename,
                        "file_size": len(pdf_bytes),
                        "total_facilities": len(fac_dicts),
                        "total_emissions": round(total_emissions, 2),
                    })
                except Exception as e:
                    logger.error(f"Failed to generate region PDF for {country}: {e}")

            logger.info(f"Generated {len(manifest['regions'])} region PDFs")

            # ── 3. Per-Company (Organisation) PDFs ──────────────────────
            for org in all_orgs:
                try:
                    org_facs = [f for f in all_facilities if f.org_id == org.id]
                    if not org_facs:
                        continue

                    org_dict = {"name": org.name}
                    fac_list = [
                        {
                            "name": f.name,
                            "fluxara_latest": f.fluxara_latest or 0,
                            "risk_level": (f.risk_level or "low"),
                            "country": f.country or "N/A",
                        }
                        for f in org_facs
                    ]
                    total_emissions = sum(f["fluxara_latest"] for f in fac_list)

                    org_alert_count = sum(
                        len(alert_by_fac.get(f.id, []))
                        for f in org_facs
                    )

                    pdf_bytes = generate_company_pdf(org_dict, fac_list, total_emissions, org_alert_count)

                    filename = f"Company_{org.id}_{_safe_filename(org.name)}.pdf"
                    filepath = COMPANIES_DIR / filename
                    filepath.write_bytes(pdf_bytes)

                    manifest["companies"].append({
                        "id": org.id,
                        "name": org.name,
                        "filename": filename,
                        "file_size": len(pdf_bytes),
                        "total_facilities": len(fac_list),
                        "total_emissions": round(total_emissions, 2),
                    })
                except Exception as e:
                    logger.error(f"Failed to generate company PDF for org {org.id}: {e}")

            logger.info(f"Generated {len(manifest['companies'])} company PDFs")

            # ── 4. Global Summary PDF ───────────────────────────────────
            try:
                all_fac_dicts = [
                    {
                        "name": f.name, "country": f.country, "sector": f.sector,
                        "fluxara_latest": f.fluxara_latest, "epa_reported": f.epa_reported,
                        "risk_level": f.risk_level or "low",
                    }
                    for f in all_facilities
                ]
                total_emissions = sum(f.get("fluxara_latest", 0) or 0 for f in all_fac_dicts)
                total_epa = sum(f.get("epa_reported", 0) or 0 for f in all_fac_dicts)
                high_risk = sum(1 for f in all_fac_dicts if (f.get("risk_level") or "").lower() == "high")
                underreporting = [
                    f for f in all_fac_dicts
                    if (f.get("epa_reported") or 0) > 0 and (f.get("fluxara_latest") or 0) > 0
                    and ((f["fluxara_latest"] - f["epa_reported"]) / f["epa_reported"]) > 0.20
                ]
                ur_pct = round(len(underreporting) / len(all_fac_dicts) * 100, 1) if all_fac_dicts else 0

                stats = {
                    "total_facilities": len(all_fac_dicts),
                    "total_emissions": total_emissions,
                    "total_epa": total_epa,
                    "high_risk": high_risk,
                    "underreporting_pct": ur_pct,
                    "region": "Global",
                    "date_from": "All time",
                    "date_to": datetime.utcnow().strftime("%Y-%m-%d"),
                }

                title = f"Fluxara Global Intelligence Report - {datetime.utcnow().strftime('%B %Y')}"
                pdf_bytes = generate_summary_pdf(title, all_fac_dicts, stats)

                filename = "Global_Summary.pdf"
                filepath = REGIONS_DIR / filename
                filepath.write_bytes(pdf_bytes)

                manifest["global"] = {
                    "filename": filename,
                    "file_size": len(pdf_bytes),
                    "total_facilities": len(all_fac_dicts),
                    "total_emissions": round(total_emissions, 2),
                }
            except Exception as e:
                logger.error(f"Failed to generate global PDF: {e}")

            # ── Write manifest ──────────────────────────────────────────
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, default=str))

            total = (
                len(manifest["facilities"])
                + len(manifest["regions"])
                + len(manifest["companies"])
                + (1 if manifest["global"] else 0)
            )
            logger.info(
                f"PDF generation complete: {total} reports "
                f"({len(manifest['facilities'])} facilities, "
                f"{len(manifest['regions'])} regions, "
                f"{len(manifest['companies'])} companies, "
                f"1 global)"
            )

        except Exception as e:
            logger.error(f"Fatal error during PDF generation: {e}", exc_info=True)

    return manifest


def get_manifest():
    """Read the current manifest from disk."""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return None


def get_facility_pdf_path(facility_id: int) -> Path | None:
    """Look up a pre-generated facility PDF by ID."""
    manifest = get_manifest()
    if not manifest:
        return None
    for entry in manifest.get("facilities", []):
        if entry["id"] == facility_id:
            path = FACILITIES_DIR / entry["filename"]
            return path if path.exists() else None
    return None


def get_region_pdf_path(country: str) -> Path | None:
    """Look up a pre-generated region PDF by country code."""
    manifest = get_manifest()
    if not manifest:
        return None
    for entry in manifest.get("regions", []):
        if entry["country"] == country:
            path = REGIONS_DIR / entry["filename"]
            return path if path.exists() else None
    return None


def get_company_pdf_path(org_id: int) -> Path | None:
    """Look up a pre-generated company PDF by org ID."""
    manifest = get_manifest()
    if not manifest:
        return None
    for entry in manifest.get("companies", []):
        if entry["id"] == org_id:
            path = COMPANIES_DIR / entry["filename"]
            return path if path.exists() else None
    return None


def get_global_pdf_path() -> Path | None:
    """Get the pre-generated global summary PDF."""
    manifest = get_manifest()
    if not manifest or not manifest.get("global"):
        return None
    path = REGIONS_DIR / manifest["global"]["filename"]
    return path if path.exists() else None
