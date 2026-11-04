"""
AquaNexis — AtomQUEST 2026 Round 2 Progress Report Generator
Outputs strictly 2-page PDF: atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf
Uses ReportLab Platypus with an explicit PageBreak to balance exactly 2 pages.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

OUTPUT_FILE = "atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf"


def create_pipeline_diagram() -> Drawing:
    """Create a clean vector decision-flow diagram: Sense -> Understand -> Predict -> Alert -> Assist."""
    d = Drawing(528, 28)
    boxes = [
        ("1. SENSE", "13 Parameters", colors.HexColor("#0284c7")),
        ("2. UNDERSTAND", "Quality & AquaScore", colors.HexColor("#0d9488")),
        ("3. PREDICT", "FSI, FHI, RUL", colors.HexColor("#2563eb")),
        ("4. ALERT", "State Machine", colors.HexColor("#d97706")),
        ("5. ASSIST", "Maintenance Guide", colors.HexColor("#16a34a")),
    ]
    box_w = 88
    box_h = 24
    spacing = 22
    y = 2

    for i, (title, subtitle, color) in enumerate(boxes):
        x = i * (box_w + spacing)
        # Background box
        d.add(Rect(x, y, box_w, box_h, rx=3, ry=3, fillColor=colors.HexColor("#f8fafc"), strokeColor=color, strokeWidth=1))
        # Top banner line
        d.add(Rect(x, y + box_h - 4, box_w, 4, rx=1, ry=1, fillColor=color, strokeColor=color, strokeWidth=0))
        # Title text
        d.add(String(x + box_w / 2, y + 12, title, fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.HexColor("#0f172a"), textAnchor="middle"))
        # Subtitle text
        d.add(String(x + box_w / 2, y + 4, subtitle, fontName="Helvetica", fontSize=5.5, fillColor=colors.HexColor("#475569"), textAnchor="middle"))

        # Arrow to next box
        if i < len(boxes) - 1:
            arr_x = x + box_w + 3
            arr_y = y + box_h / 2
            d.add(Line(arr_x, arr_y, arr_x + 12, arr_y, strokeColor=colors.HexColor("#64748b"), strokeWidth=1))
            d.add(Polygon([arr_x + 12, arr_y - 2.5, arr_x + 16, arr_y, arr_x + 12, arr_y + 2.5], fillColor=colors.HexColor("#64748b"), strokeColor=colors.HexColor("#64748b"), strokeWidth=0))

    return d


def build_pdf() -> None:
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=1.1 * cm,
        rightMargin=1.1 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.9 * cm,
        title="AquaNexis — Round 2 Progress Report (UPES Dehradun, Track 2)",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=14.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=1,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=9.8,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceAfter=3,
    )
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=8.6,
        leading=10.6,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=3,
        spaceAfter=1.5,
    )
    body_style = ParagraphStyle(
        "BodyCompact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.0,
        leading=8.8,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=1.5,
    )
    cell_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.6,
        leading=8.2,
        textColor=colors.HexColor("#1e293b"),
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )

    def make_table(headers, rows, col_widths):
        data = [[Paragraph(h, cell_bold) for h in headers]]
        for r in rows:
            data.append([Paragraph(str(c), cell_style) for c in r])
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        return t

    story = []

    # ================= PAGE 1 =================
    # Title & Metadata Header
    story.append(Paragraph("AquaNexis — AtomQUEST 2026 Round 2 Progress Report", title_style))
    story.append(
        Paragraph(
            "Track 2: Water Purifier | Institution: UPES Dehradun | Participation: Solo Prototype | Submission Date: 4 November 2026",
            subtitle_style,
        )
    )

    # 1. Project Positioning & Concise Abstract
    story.append(Paragraph("1. Project Positioning & Concise Abstract", h2_style))
    story.append(
        Paragraph(
            "<b>Abstract:</b> AquaNexis is a Predictive Water Intelligence System developed for AtomQUEST 2026 Track 2. Domestic reverse osmosis (RO) purifiers currently operate on rigid calendar timers or single-point TDS thresholds, causing either premature filter waste or undetected water quality degradation. AquaNexis delivers an operational software intelligence layer that continuously monitors 13 operating parameters beyond TDS, validates sensor quality, computes a 7-component Filter Stress Index (FSI) and 5-component Filter Health Index (FHI), estimates Remaining Useful Life (RUL) with transparent fallback labeling (MODEL_MISSING), and recommends guided maintenance actions. Operating in DEMO_MODE, the software prototype is 100% verified across 154 unit tests. No drinking-water certification is claimed; physical actuator shutdown is deferred to Round 3.",
            body_style,
        )
    )
    story.append(
        make_table(
            ["Field", "Specification & Alignment"],
            [
                ["Primary Exploration", "Prognostics of filter failure using data analytics (FSI, FHI, RUL, Failure Risk, Explainability Engine)"],
                ["Secondary Exploration", "Input water quality sensing beyond TDS (TDS, EC, pH, Turbidity, Temp, Flow, Transmembrane Delta-P)"],
                ["Core Operating Story", "Sense (13 parameters) &rarr; Understand (Quality Gate) &rarr; Predict (FSI/RUL) &rarr; Alert (State Machine) &rarr; Assist (Maintenance)"],
                ["Telemetry Provenance", "Explicitly tagged: MEASURED (hardware) | SIMULATED (simulator/demo) | CALCULATED (derived) | MODEL_PREDICTED (prognostics)"],
            ],
            [3.8 * cm, 15.0 * cm],
        )
    )

    # 2. Problem & Proposed Solution
    story.append(Paragraph("2. Problem, Proposed Solution & Decision-Flow Architecture", h2_style))
    story.append(
        Paragraph(
            "<b>Problem:</b> TDS checks only measure conductive dissolved ions. They cannot detect colloidal turbidity, sediment fouling, or progressive transmembrane pressure drop across RO membranes. <b>Solution:</b> AquaNexis establishes a closed-loop intelligence pipeline converting multi-sensor telemetry into explainable prognostic decisions.",
            body_style,
        )
    )
    # Restrained Vector Decision-Flow Diagram
    story.append(Spacer(1, 1))
    story.append(create_pipeline_diagram())
    story.append(Spacer(1, 2))

    # 3. Completed Modules & Software Architecture
    story.append(Paragraph("3. Completed Modules for Round 2", h2_style))
    story.append(
        make_table(
            ["Module", "Status", "Verified Technical Capabilities & Grounded Reality"],
            [
                ["Telemetry Ingestion & Security", "Complete", "FastAPI ingestion, monotonic sequence replay protection, clock-skew (+/-300s) rejection, JWT claims scoping"],
                ["Water Quality Engine", "Complete", "AquaScore (0-100) aggregating TDS, EC, pH, Turbidity, Temp; 1h trend velocity & anomaly z-scores"],
                ["Filter Stress Index (FSI)", "Complete", "7-component weighted stress index; dynamic denominator excludes missing sensors without inventing fake data"],
                ["Filter Health Index (FHI)", "Complete", "5-component health index (0-100) mapped to maintenance bands: NORMAL, MONITOR, REPLACE_RECOMMENDED"],
                ["RUL Prognostic Pipeline", "Complete", "Controlled dataset (controlled-membrane-deg-v1.0), multivariate model (MAE 4.85d), fallback MODEL_MISSING"],
                ["Explainability & Counterfactuals", "Complete", "Top 5 contributing degradation drivers (delta-P, flow deviation, volume, age, turbidity) + replacement recovery"],
                ["Alert State Machine", "Complete", "Formal lifecycle: DETECTED &rarr; OPEN &rarr; ACKNOWLEDGED / SNOOZED / RESOLVED / AUTO_CLEARED with evidence drawer"],
                ["Maintenance Lifecycle", "Complete", "11-category catalog, replacement guides, sensor calibration records, post-maintenance verification tests"],
                ["Web Dashboard & Realtime WS", "Complete", "React 18 + Vite + TypeScript dashboard (localhost:3000), realtime WebSocket stream, scenario switcher"],
            ],
            [3.8 * cm, 1.6 * cm, 13.4 * cm],
        )
    )

    # 4. Stage 1 vs Round 2 Scope Changes & Sourcing Risks
    story.append(Paragraph("4. Scope Evolution, Reason for Software-First Focus & Sourcing Risks", h2_style))
    story.append(
        Paragraph(
            "<b>Strategic Evolution:</b> In Stage 1, a simultaneous physical sensor bench build was conceptualized. For Round 2, the project made a deliberate, strategic pivot to prioritize the software intelligence layer first. This eliminated procurement and bench-rig fabrication risks while ensuring deep prognostic math, sensor validation, and explainability could be thoroughly developed and verified. Firmware architecture in firmware/esp32/ remains preserved as reference for Round 3 physical deployment.",
            body_style,
        )
    )
    story.append(
        make_table(
            ["Sourcing / Technical Risk", "Stage 1 Plan", "Round 2 Implementation", "Status & Honest Disclosure"],
            [
                ["ESP32 & Multi-Sensor Hardware", "Physical breadboard rig", "Deferred to Round 3; firmware archived", "Zero component risk; simulated telemetry in DEMO_MODE"],
                ["Hydraulic Bench & Actuators", "Physical hydraulic pump rig", "Deterministic 8-profile Python simulator", "Eliminated test-rig leak risks during evaluation window"],
                ["TimescaleDB Extension", "Local PG16 + TimescaleDB", "Isolated in-memory repository (DEMO_MODE)", "Windows DLL blocker bypassed; CI validates PG16 container"],
            ],
            [4.0 * cm, 3.2 * cm, 4.8 * cm, 6.8 * cm],
        )
    )

    # Page 1 Break
    story.append(PageBreak())

    # ================= PAGE 2 =================
    # 5. Core-Function Evidence & Scenario Results
    story.append(Paragraph("5. Core-Function Evidence & Scenario Results (Verified in DEMO_MODE)", h2_style))
    story.append(
        make_table(
            ["Scenario", "Telemetry & Quality State", "Intelligence Response (AquaScore / FSI / FHI / RUL / Risk)", "Alert & Safety Action Taken"],
            [
                ["NORMAL", "Quality: GOOD, SIMULATED\ndP=30 kPa, Flow=2.0 L/m", "AquaScore=100 (EXCELLENT), FSI=20.0, FHI=86% (NORMAL), RUL=154.8d (MODEL_MISSING), Risk=LOW", "0 active alerts; normal background telemetry"],
                ["FILTER_STRESS", "Quality: GOOD, SIMULATED\ndP=176.9 kPa, Flow=0.96 L/m", "AquaScore=93, FSI=67.5 (HIGH), FHI=37% (POOR), RUL=66.6d (MODEL_MISSING), Risk=MEDIUM, Band=REPLACE_RECOMMENDED", "Alert: filter_stress_high (CRITICAL); Stage 1 Sediment cartridge replacement recommended"],
                ["LEAK", "Quality: GOOD, SIMULATED\nleak_detected=True", "AquaScore=100, FSI=20.0, FHI=86%, Risk=LOW, Safety Status=CRITICAL_EVENT", "Alert: leak_detected (CRITICAL); isolation action logged/recommended; NO physical actuation"],
                ["SENSOR_FAULT", "Quality: BAD, SIMULATED\nTurbidity out-of-range, missing P_out", "AquaScore=90, FSI dynamic denominator active, RUL withheld (N/A, LOW confidence)", "Alert: sensor_fault_detected (WARNING); corrupt data prevented from driving false prediction"],
            ],
            [2.4 * cm, 3.8 * cm, 6.3 * cm, 6.3 * cm],
        )
    )

    # 6. Controlled-Data RUL Machine Learning Validation
    story.append(Paragraph("6. Controlled-Data RUL Machine Learning Validation (Not Field Claims)", h2_style))
    story.append(
        Paragraph(
            "To prove mathematical feasibility of prognostic filter degradation, a candidate multivariate regularized regression model was trained and evaluated against a physics-informed dataset. <b>Disclosure:</b> These represent controlled-dataset engineering validation results, not physical purifier field claims.",
            body_style,
        )
    )
    story.append(
        make_table(
            ["Dataset & Sample Scale", "Feature Space", "Model Performance Metrics", "Operational RUL Runtime Status"],
            [
                ["600 run-to-failure cycles\n(480 train / 120 test)", "15 engineered physical features\n(dP, flow deviation, volume, age, etc.)", "Candidate Test MAE: 4.85 days\nR2 = 0.9962 | RMSE = 6.12 days", "Deterministic Fallback v1.0 active in UI\nlabeled MODEL_MISSING until field trials"],
            ],
            [4.0 * cm, 4.4 * cm, 5.0 * cm, 5.4 * cm],
        )
    )

    # 7. Cost & Budget Position (Stage 1 Estimate vs Round 2 Actual)
    story.append(Paragraph("7. Budget & Expenditure Position (Estimate vs Actual)", h2_style))
    story.append(
        make_table(
            ["Category", "Stage 1 Budget Estimate", "Round 2 Actual Spend", "Variance & Financial Justification"],
            [
                ["Physical Hardware & Sensors", "Rs. 5,000 - 10,000", "Rs. 0 (Not spent)", "Procurement deferred to Round 3 to avoid premature hardware expenditure"],
                ["Development Tools & Compute", "Rs. 0 (Open source)", "Rs. 0 (Open source)", "Built entirely using open-source FastAPI, React, SQLite/PostgreSQL, and Python"],
                ["Total Prototype Spend", "Rs. 5,000 - 10,000", "Rs. 0 (100% within budget)", "Entire original hardware budget preserved intact for Round 3 physical testing"],
            ],
            [4.0 * cm, 3.6 * cm, 3.6 * cm, 7.6 * cm],
        )
    )

    # 8. Safety & Fail-Safe Status (Mandatory Phrasing)
    story.append(Paragraph("8. Safety & Fail-Safe Status", h2_style))
    story.append(
        Paragraph(
            "<b>Deterministic Rule Priority:</b> Deterministic rule logic takes priority over predictive output. Leak conditions create a critical safety event and isolation recommendation. Physical automatic shutdown is not claimed until hardware-in-loop validation is complete.",
            body_style,
        )
    )

    # 9. Current Limitations & Disclosures
    story.append(Paragraph("9. Current Limitations & Honest Engineering Disclosures", h2_style))
    story.append(
        Paragraph(
            "<b>Disclosures:</b> (1) <i>No Drinking-Water Certification:</i> No regulatory certification (e.g., BIS, NSF, WQA) is claimed; AquaNexis is an operational predictive intelligence system; (2) <i>Simulated Telemetry:</i> Round 2 telemetry originates from the deterministic simulator (backend/simulator.py) and is explicitly tagged SIMULATED; (3) <i>RUL Status:</i> RUL displays MODEL_MISSING fallback in the dashboard until multi-month empirical membrane trials are conducted; (4) <i>Actuation:</i> Solenoid valve commands are software recommendations and audit logs only.",
            body_style,
        )
    )

    # 10. Automated Verification & Round 3 Plan
    story.append(Paragraph("10. Automated Verification & Round 3 Engineering Plan", h2_style))
    story.append(
        Paragraph(
            "<b>Automated Test Evidence:</b> Backend unit test suite: <b>154/154 PASS (11 skipped DB-dependent)</b> in 1.87s across configuration, security, canonical telemetry, ML RUL, hydraulic intelligence, alerts, and maintenance. Frontend checks: <b>npm run lint PASS</b> (0 errors, 0 warnings), <b>npm run format:check PASS</b>, <b>npm run typecheck PASS</b> (0 errors), <b>npm test PASS (14/14)</b>, <b>npm run build PASS</b> (production bundle produced).",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Round 3 Plan:</b> (1) ESP32 physical sensor integration; (2) Sensor calibration against laboratory reference instruments; (3) Real telemetry ingestion pipeline validation; (4) Hardware-in-the-loop (HIL) safety certification for physical Normally Closed solenoid valves; (5) Collection of measured empirical run-to-failure membrane degradation data; (6) Validation and refinement of RUL prediction models using measured field data; (7) Multi-device production deployment with TimescaleDB.",
            body_style,
        )
    )

    doc.build(story)
    print(f"Generated {OUTPUT_FILE} successfully.")


if __name__ == "__main__":
    build_pdf()
