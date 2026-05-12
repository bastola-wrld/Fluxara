# fluxara/utils/pdf_generator.py
from fpdf import FPDF
from datetime import datetime
import io

class FluxaraReport(FPDF):
    def header(self):
        # Branding
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(26, 44, 39) # #1A2C27
        self.cell(0, 10, 'FLUXARA', ln=True, align='L')
        
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Source-Attributed Satellite Intelligence Portal', ln=True, align='L')
        
        self.ln(5)
        self.set_draw_color(26, 44, 39)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.cell(0, 10, f'Page {self.page_no()} | Generated at {timestamp} | Fluxara Earth Analytics', align='C')

    def chapter_title(self, label):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(26, 44, 39)
        self.cell(0, 10, label, ln=True, align='L')
        self.ln(4)

    def add_metric(self, label, value, unit=""):
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.write(10, f"{label}: ")
        self.set_font('helvetica', '', 11)
        self.write(10, f"{value} {unit}\n")

def generate_facility_pdf(facility_data, inversions, alerts):
    pdf = FluxaraReport()
    pdf.add_page()
    
    # Title
    pdf.chapter_title(f"Facility Audit Report: {facility_data['name']}")
    
    # Overview
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, "Summary Metrics", ln=True)
    pdf.ln(2)
    
    pdf.add_metric("Country", facility_data.get('country', 'N/A'))
    pdf.add_metric("Sector", facility_data.get('sector', 'N/A'))
    pdf.add_metric("Location", f"{facility_data['lat']}, {facility_data['lon']}")
    pdf.add_metric("Latest Emission Rate", facility_data.get('fluxara_latest', 0.0), "kg/hr")
    pdf.add_metric("Risk Level", facility_data.get('risk_level', 'Low').upper())
    
    pdf.ln(10)
    
    # Inversions Table
    pdf.chapter_title("Recent Satellite Inversions")
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    
    # Table Header
    pdf.cell(40, 10, "Date", 1, 0, 'C', True)
    pdf.cell(60, 10, "Emission Rate (kg/hr)", 1, 0, 'C', True)
    pdf.cell(40, 10, "Confidence", 1, 0, 'C', True)
    pdf.cell(50, 10, "Status", 1, 1, 'C', True)
    
    pdf.set_font('helvetica', '', 10)
    for inv in inversions[:10]: # Top 10
        pdf.cell(40, 10, str(inv['date']), 1)
        pdf.cell(60, 10, f"{inv['emission_rate']:.2f}", 1, 0, 'R')
        pdf.cell(40, 10, f"{inv['confidence']*100:.1f}%", 1, 0, 'C')
        status = "CRITICAL" if inv['emission_rate'] > 100 else "NORMAL"
        pdf.cell(50, 10, status, 1, 1, 'C')

    pdf.ln(10)
    
    # Active Alerts
    if alerts:
        pdf.chapter_title("Active System Alerts")
        for alert in alerts[:5]:
            pdf.set_font('helvetica', 'B', 10)
            color = (200, 0, 0) if alert['severity'] == 'high' else (200, 100, 0)
            pdf.set_text_color(*color)
            pdf.cell(0, 8, f"[{alert['severity'].upper()}] {alert['created_at'].split('T')[0]}", ln=True)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(0, 6, alert['message'])
            pdf.ln(2)

    return pdf.output()

def generate_company_pdf(org_data, facilities, total_emissions, total_alerts):
    pdf = FluxaraReport()
    pdf.add_page()
    
    pdf.chapter_title(f"Corporate ESG Portfolio: {org_data['name']}")
    
    pdf.add_metric("Total Facilities", len(facilities))
    pdf.add_metric("Aggregate Emissions", f"{total_emissions:.2f}", "kg/hr")
    pdf.add_metric("Active Alerts", total_alerts)
    pdf.ln(10)
    
    pdf.chapter_title("Asset Performance Table")
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 8, "Facility Name", 1, 0, 'L', True)
    pdf.cell(40, 8, "Latest (kg/hr)", 1, 0, 'C', True)
    pdf.cell(40, 8, "Risk", 1, 0, 'C', True)
    pdf.cell(30, 8, "Country", 1, 1, 'C', True)
    
    pdf.set_font('helvetica', '', 9)
    for f in facilities:
        pdf.cell(80, 8, f['name'], 1)
        pdf.cell(40, 8, f"{f.get('fluxara_latest', 0.0):.1f}", 1, 0, 'R')
        pdf.cell(40, 8, f.get('risk_level', 'Low').upper(), 1, 0, 'C')
        pdf.cell(30, 8, f.get('country', 'N/A'), 1, 1, 'C')

    return pdf.output()


# ── On-Demand Report Templates ─────────────────────────────────────────────

def generate_summary_pdf(title, facilities, stats):
    """2-page executive summary with key metrics, top emitters, risk breakdown."""
    pdf = FluxaraReport()
    pdf.add_page()

    # Title
    pdf.chapter_title(title)

    # Executive Summary Box
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.ln(2)

    pdf.add_metric("Total Facilities Analysed", stats.get('total_facilities', 0))
    pdf.add_metric("Aggregate Emissions", f"{stats.get('total_emissions', 0):.2f}", "kg/hr")
    pdf.add_metric("High Risk Facilities", stats.get('high_risk', 0))
    pdf.add_metric("Underreporting Rate", f"{stats.get('underreporting_pct', 0):.1f}", "%")
    pdf.add_metric("Region", stats.get('region', 'Global'))
    pdf.add_metric("Report Period", f"{stats.get('date_from', 'N/A')} to {stats.get('date_to', 'N/A')}")
    pdf.ln(10)

    # Top Emitters Table
    pdf.chapter_title("Top Emitters")
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(70, 8, "Facility", 1, 0, 'L', True)
    pdf.cell(30, 8, "Country", 1, 0, 'C', True)
    pdf.cell(30, 8, "Sector", 1, 0, 'C', True)
    pdf.cell(30, 8, "Fluxara (kg/hr)", 1, 0, 'C', True)
    pdf.cell(30, 8, "Risk", 1, 1, 'C', True)

    pdf.set_font('helvetica', '', 9)
    sorted_facs = sorted(facilities, key=lambda f: f.get('fluxara_latest', 0) or 0, reverse=True)
    for f in sorted_facs[:15]:
        pdf.cell(70, 8, (f.get('name', '')[:30]), 1)
        pdf.cell(30, 8, f.get('country', 'N/A'), 1, 0, 'C')
        pdf.cell(30, 8, (f.get('sector', 'N/A') or 'N/A')[:12], 1, 0, 'C')
        pdf.cell(30, 8, f"{f.get('fluxara_latest', 0) or 0:.1f}", 1, 0, 'R')
        risk = (f.get('risk_level', 'Low') or 'Low').upper()
        pdf.cell(30, 8, risk, 1, 1, 'C')

    # Risk Distribution
    pdf.ln(10)
    pdf.chapter_title("Risk Distribution")
    high = sum(1 for f in facilities if (f.get('risk_level') or '').lower() == 'high')
    medium = sum(1 for f in facilities if (f.get('risk_level') or '').lower() == 'medium')
    low = len(facilities) - high - medium
    pdf.add_metric("High Risk", high)
    pdf.add_metric("Medium Risk", medium)
    pdf.add_metric("Low Risk", low)

    return pdf.output()


def generate_full_pdf(title, facilities, inversions, alerts):
    """Comprehensive multi-page report with per-facility data, inversions, and alerts."""
    pdf = FluxaraReport()
    pdf.add_page()

    pdf.chapter_title(title)

    # Overview Stats
    total_emissions = sum(f.get('fluxara_latest', 0) or 0 for f in facilities)
    pdf.add_metric("Total Facilities", len(facilities))
    pdf.add_metric("Aggregate Emissions", f"{total_emissions:.2f}", "kg/hr")
    pdf.add_metric("Total Inversions", len(inversions))
    pdf.add_metric("Active Alerts", len(alerts))
    pdf.ln(10)

    # Full Facility Table
    pdf.chapter_title("Complete Facility Registry")
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(55, 7, "Facility Name", 1, 0, 'L', True)
    pdf.cell(18, 7, "Country", 1, 0, 'C', True)
    pdf.cell(25, 7, "Sector", 1, 0, 'C', True)
    pdf.cell(25, 7, "EPA (kg/hr)", 1, 0, 'C', True)
    pdf.cell(28, 7, "Fluxara (kg/hr)", 1, 0, 'C', True)
    pdf.cell(20, 7, "Diff %", 1, 0, 'C', True)
    pdf.cell(20, 7, "Risk", 1, 1, 'C', True)

    pdf.set_font('helvetica', '', 8)
    for f in facilities:
        epa = f.get('epa_reported', 0) or 0
        flx = f.get('fluxara_latest', 0) or 0
        diff_pct = round(abs((flx - epa) / epa) * 100, 1) if epa > 0 else 0

        # Page break check
        if pdf.get_y() > 260:
            pdf.add_page()

        pdf.cell(55, 7, (f.get('name', '')[:25]), 1)
        pdf.cell(18, 7, f.get('country', 'N/A'), 1, 0, 'C')
        pdf.cell(25, 7, (f.get('sector', 'N/A') or 'N/A')[:10], 1, 0, 'C')
        pdf.cell(25, 7, f"{epa:.1f}", 1, 0, 'R')
        pdf.cell(28, 7, f"{flx:.1f}", 1, 0, 'R')
        pdf.cell(20, 7, f"{diff_pct}%", 1, 0, 'C')
        pdf.cell(20, 7, (f.get('risk_level', 'Low') or 'Low').upper(), 1, 1, 'C')

    # Inversions Section
    if inversions:
        pdf.add_page()
        pdf.chapter_title("Recent Satellite Inversions")
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(35, 8, "Date", 1, 0, 'C', True)
        pdf.cell(40, 8, "Facility ID", 1, 0, 'C', True)
        pdf.cell(45, 8, "Emission Rate (kg/hr)", 1, 0, 'C', True)
        pdf.cell(35, 8, "Confidence", 1, 0, 'C', True)
        pdf.cell(35, 8, "Status", 1, 1, 'C', True)

        pdf.set_font('helvetica', '', 9)
        for inv in inversions[:50]:
            if pdf.get_y() > 260:
                pdf.add_page()
            rate = inv.get('emission_rate', 0) or 0
            conf = inv.get('confidence', 0) or 0
            pdf.cell(35, 8, str(inv.get('date', '')), 1)
            pdf.cell(40, 8, str(inv.get('facility_id', '')), 1, 0, 'C')
            pdf.cell(45, 8, f"{rate:.2f}", 1, 0, 'R')
            pdf.cell(35, 8, f"{conf*100:.1f}%", 1, 0, 'C')
            status = "CRITICAL" if rate > 100 else "NORMAL"
            pdf.cell(35, 8, status, 1, 1, 'C')

    # Alerts Section
    if alerts:
        pdf.add_page()
        pdf.chapter_title("Active System Alerts")
        for alert in alerts[:30]:
            if pdf.get_y() > 260:
                pdf.add_page()
            sev = alert.get('severity', 'medium')
            color = (200, 0, 0) if sev == 'high' else (200, 100, 0)
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(*color)
            created = str(alert.get('created_at', ''))[:10]
            pdf.cell(0, 8, f"[{sev.upper()}] Facility #{alert.get('facility_id', '?')} - {created}", ln=True)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font('helvetica', '', 9)
            pdf.multi_cell(0, 6, alert.get('message', ''))
            pdf.ln(3)

    return pdf.output()


def generate_compliance_pdf(title, facilities, stats):
    """Regulatory compliance report with underreporting flags and EPA vs Satellite comparison."""
    pdf = FluxaraReport()
    pdf.add_page()

    pdf.chapter_title(title)

    # Compliance Header
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(26, 44, 39)
    pdf.cell(0, 10, "Regulatory Compliance Assessment", ln=True)
    pdf.ln(2)

    pdf.add_metric("Region", stats.get('region', 'Global'))
    pdf.add_metric("Assessment Period", f"{stats.get('date_from', 'N/A')} to {stats.get('date_to', 'N/A')}")
    pdf.add_metric("Facilities Assessed", stats.get('total_facilities', 0))
    pdf.add_metric("EPA Aggregate", f"{stats.get('total_epa', 0):.2f}", "kg/hr")
    pdf.add_metric("Satellite Aggregate", f"{stats.get('total_emissions', 0):.2f}", "kg/hr")
    discrepancy = stats.get('total_emissions', 0) - stats.get('total_epa', 0)
    pdf.add_metric("National Discrepancy", f"{discrepancy:.2f}", "kg/hr")
    pdf.add_metric("Underreporting Rate", f"{stats.get('underreporting_pct', 0):.1f}", "%")
    pdf.ln(10)

    # Underreporting Flags
    flagged = [f for f in facilities if _is_underreporting(f)]
    flagged.sort(key=lambda f: _discrepancy_pct(f), reverse=True)

    if flagged:
        pdf.chapter_title(f"Flagged Facilities ({len(flagged)} underreporting >20%)")

        # Warning box
        pdf.set_fill_color(254, 226, 226)
        pdf.set_text_color(185, 28, 28)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 10, f"  WARNING: {len(flagged)} facilities exceed the 20% underreporting threshold", 1, 1, 'L', True)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(5)

        pdf.set_font('helvetica', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 7, "Facility", 1, 0, 'L', True)
        pdf.cell(20, 7, "Country", 1, 0, 'C', True)
        pdf.cell(25, 7, "Sector", 1, 0, 'C', True)
        pdf.cell(28, 7, "EPA (kg/hr)", 1, 0, 'C', True)
        pdf.cell(28, 7, "Satellite (kg/hr)", 1, 0, 'C', True)
        pdf.cell(20, 7, "Diff %", 1, 0, 'C', True)
        pdf.cell(20, 7, "Action", 1, 1, 'C', True)

        pdf.set_font('helvetica', '', 8)
        for f in flagged[:40]:
            if pdf.get_y() > 260:
                pdf.add_page()
            epa = f.get('epa_reported', 0) or 0
            flx = f.get('fluxara_latest', 0) or 0
            diff = _discrepancy_pct(f)
            pdf.cell(50, 7, (f.get('name', '')[:22]), 1)
            pdf.cell(20, 7, f.get('country', 'N/A'), 1, 0, 'C')
            pdf.cell(25, 7, (f.get('sector', 'N/A') or 'N/A')[:10], 1, 0, 'C')
            pdf.cell(28, 7, f"{epa:.1f}", 1, 0, 'R')
            pdf.cell(28, 7, f"{flx:.1f}", 1, 0, 'R')
            pdf.cell(20, 7, f"{diff:.1f}%", 1, 0, 'C')
            action = "AUDIT" if diff > 50 else "REVIEW"
            pdf.cell(20, 7, action, 1, 1, 'C')

    # Compliant Facilities Summary
    pdf.ln(10)
    compliant = [f for f in facilities if not _is_underreporting(f)]
    pdf.chapter_title(f"Compliant Facilities ({len(compliant)})")
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 8, f"{len(compliant)} of {len(facilities)} facilities are within acceptable reporting tolerance.", ln=True)

    return pdf.output()


def _is_underreporting(f):
    """Check if facility satellite reading exceeds EPA reported by >20%."""
    epa = f.get('epa_reported', 0) or 0
    flx = f.get('fluxara_latest', 0) or 0
    if epa <= 0:
        return False
    return (flx - epa) / epa > 0.20


def _discrepancy_pct(f):
    """Calculate discrepancy percentage."""
    epa = f.get('epa_reported', 0) or 0
    flx = f.get('fluxara_latest', 0) or 0
    if epa <= 0:
        return 0
    return round((flx - epa) / epa * 100, 1)
