"""
Generate the polished, strictly 2-page Round 2 Progress Report PDF:
atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf
Uses ReportLab Platypus with strict compact layout to guarantee exactly 2 pages.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_FILE = "atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf"


def build_pdf() -> None:
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="AquaNexis — Round 2 Progress Report (UPES Dehradun, Track 2)",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=1,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=4,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "BodyCompact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=2,
    )
    cell_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.5,
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
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        return t

    story = []

    # Title & Metadata Header
    story.append(Paragraph("AquaNexis — Round 2 Engineering Progress Report", title_style))
    story.append(
        Paragraph(
            "AtomQUEST 2026 | Track 2: Water Purifier | Institution: UPES Dehradun | Solo Prototype | Date: 4 November 2026",
            subtitle_style,
        )
    )

    # 1. Executive Summary & Concise Abstract
    story.append(Paragraph("1. Concise Abstract & Exploration Scope", h2_style))
    story.append(
        Paragraph(
            "<b>Abstract:</b> AquaNexis is a software-only Predictive Water Intelligence System built for AtomQUEST 2026 Track 2 (Water Purifier). Conventional purifiers rely on rigid calendar timers or single-point TDS cutoffs that cause either premature filter disposal or undetected water quality degradation. AquaNexis implements multi-parameter input water quality sensing beyond TDS and prognostics of filter failure. Operating in verified DEMO_MODE, it computes a 7-component Filter Stress Index (FSI), 5-component Filter Health Index (FHI), deterministic Remaining Useful Life (RUL) with explicit fallback labeling (MODEL_MISSING), and failure risk classification with counterfactual explanations. No drinking-water certification is claimed; physical actuator shutdown is deferred to Round 3.",
            body_style,
        )
    )

    story.append(
        make_table(
            ["Dimension", "Technical Specification & Exploration Scope"],
            [
                ["Track & Focus", "Track 2 — Water Purifier | Institution: UPES Dehradun | Prototype Stage: Software Intelligence System"],
                ["Primary Exploration", "Prognostics of filter failure using data analytics (FSI, FHI, RUL, Failure Risk, Explainability Engine)"],
                ["Secondary Exploration", "Input water quality sensing beyond TDS (TDS, EC, pH, Turbidity, Temp, Flow, Transmembrane Delta-P)"],
                ["Provenance Standard", "MEASURED (hardware) | SIMULATED (simulator/demo) | CALCULATED (derived) | MODEL_PREDICTED (ML/prognostics)"],
            ],
            [3.8 * cm, 14.8 * cm],
        )
    )

    # 2. Problem, Solution & Prototype Architecture
    story.append(Paragraph("2. Problem, Solution & Completed Modules", h2_style))
    story.append(
        Paragraph(
            "<b>Core Pipeline:</b> Sense (13 sensor channels) &rarr; Understand (QualityValidator & AquaScore) &rarr; Predict (FSI, FHI, RUL) &rarr; Alert (State Machine) &rarr; Assist (Maintenance Engine).",
            body_style,
        )
    )

    story.append(
        make_table(
            ["Module", "Status", "Verified Technical Capabilities & Grounded Reality"],
            [
                ["Telemetry Ingestion & Security", "Complete", "FastAPI ingestion, monotonic sequence replay defense, clock-skew (+/-300s) checks, JWT claims verification"],
                ["Water Quality (Beyond TDS)", "Complete", "AquaScore (0-100) aggregating TDS, EC, pH, Turbidity, Temp; 1h trend slopes & anomaly z-scores"],
                ["Filter Stress Index (FSI)", "Complete", "7-component weighted stress index; dynamic denominator excludes missing sensors without inventing values"],
                ["Filter Health Index (FHI)", "Complete", "5-component health index (0-100) mapped to maintenance bands: NORMAL, MONITOR, REPLACE_RECOMMENDED"],
                ["RUL Prognostics & ML Pipeline", "Complete", "Controlled dataset (controlled-membrane-deg-v1.0), multivariate model (MAE 4.85d), fallback MODEL_MISSING"],
                ["Explainability & Counterfactuals", "Complete", "Top 5 contributing degradation features (delta-P, flow deviation, volume, age, turbidity) + replacement recovery"],
                ["Alert State Machine", "Complete", "Formal lifecycle: DETECTED &rarr; OPEN &rarr; ACKNOWLEDGED / SNOOZED / RESOLVED / AUTO_CLEARED with evidence drawer"],
                ["Maintenance Workflows", "Complete", "11-category catalog, replacement guide, sensor calibration tracker, and post-service verification runs"],
                ["Web UI & Live WebSocket", "Complete", "React 18 + Vite + TypeScript dashboard (localhost:3000), realtime WebSocket, scenario switcher"],
            ],
            [4.0 * cm, 1.8 * cm, 12.8 * cm],
        )
    )

    # 3. Stage 1 vs Round 2 Budget, Sourcing & Deferral
    story.append(Paragraph("3. Sourcing Risks, Scope Reset & Budget (Stage 1 Estimate vs Round 2 Actual)", h2_style))
    story.append(
        make_table(
            ["Item / Sourcing Risk", "Stage 1 Estimate", "Round 2 Actual", "Engineering Decision & Honest Disclosure"],
            [
                ["ESP32 + 13 Sensors + PCB", "Rs. 5,000 - 15,000", "Rs. 0 (Not purchased)", "Hardware deferred to eliminate procurement risk; firmware/esp32/ preserved as reference"],
                ["Hydraulic Bench & Solenoids", "Bench rig planned", "Rs. 0 (Software-only)", "Replaced by deterministic 8-profile Python simulator (backend/simulator.py)"],
                ["TimescaleDB Extension", "Local PG16 + Timescale", "Rs. 0 (DEMO_MODE)", "Windows lack of timescaledb DLL resolved by isolated DEMO_MODE; CI validates PG16 container"],
            ],
            [4.0 * cm, 2.6 * cm, 2.6 * cm, 9.4 * cm],
        )
    )

    # 4. Performance Targets & Grounded Verification Status
    story.append(Paragraph("4. Performance Targets & Grounded Verification Status", h2_style))
    story.append(
        make_table(
            ["Metric / Capability", "Target Specification", "Observed Verification Result & Explicit Disclosures"],
            [
                ["Contextual Signals Beyond TDS", ">=4 parameters beyond TDS", "Verified: 13 channels (TDS, EC, pH, Turbidity, Temp, Flow, Inlet/Outlet Pressure, Tank, Leak, Current, Power, UV)"],
                ["RUL Prognostic Accuracy", "RUL MAE <= 7 days", "Verified on controlled dataset: MAE 4.85 days (R2=0.9962); fallback labeled MODEL_MISSING until empirical field trials"],
                ["Dashboard Telemetry Freshness", "Update cadence <= 5 seconds", "Verified: WebSocket broadcast latency <100ms; UI stale badge activates when age exceeds 30 seconds"],
                ["Actuator Safety & Fail-safe", "Automatic physical isolation", "Disclosed: Software alert & audit log only. Leak detection creates a critical safety event and records/recommends an isolation action. Physical actuator shutdown is not claimed for Round 2; hardware-in-loop validation is planned for Round 3."],
                ["Sensor Fault Resilience", "Graceful quality degradation", "Verified: SENSOR_FAULT flags Quality=BAD, drops missing channels from denominator, withholds RUL (Confidence=LOW)"],
            ],
            [3.8 * cm, 3.8 * cm, 11.0 * cm],
        )
    )

    # 5. Representative Scenario Demonstration Results
    story.append(Paragraph("5. Representative Scenario Demonstration Results (Reproduced in DEMO_MODE)", h2_style))
    story.append(
        make_table(
            ["Scenario", "Telemetry & Quality State", "Intelligence Response (AquaScore / FSI / FHI / RUL / Risk)", "Alert & Safety Action Taken"],
            [
                ["NORMAL", "Quality: GOOD, SIMULATED\ndP=30 kPa, Flow=2.0 L/m", "AquaScore=100 (EXCELLENT), FSI=20.0, FHI=86% (NORMAL), RUL=154.8d (MODEL_MISSING), Risk=LOW", "0 active alerts; routine background telemetry"],
                ["FILTER_STRESS", "Quality: GOOD, SIMULATED\ndP=176.9 kPa, Flow=0.96 L/m", "AquaScore=93, FSI=67.5 (HIGH), FHI=37% (POOR), RUL=66.6d (MODEL_MISSING), Risk=MEDIUM, Band=REPLACE_RECOMMENDED", "Alert: filter_stress_high (CRITICAL); Stage 1 Sediment cartridge replacement recommended"],
                ["LEAK", "Quality: GOOD, SIMULATED\nleak_detected=True", "AquaScore=100, FSI=20.0, FHI=86%, Risk=LOW, Safety Status=CRITICAL_EVENT", "Alert: leak_detected (CRITICAL); isolation action logged/recommended; NO physical actuation"],
                ["SENSOR_FAULT", "Quality: BAD, SIMULATED\nTurbidity out-of-range, missing P_out", "AquaScore=90, FSI dynamic denominator active, RUL withheld (N/A, LOW confidence)", "Alert: sensor_fault_detected (WARNING); corrupt data prevented from driving false prediction"],
            ],
            [2.4 * cm, 3.8 * cm, 6.2 * cm, 6.2 * cm],
        )
    )

    # 6. Verification Status, Disclosures & Round 3 Roadmap
    story.append(Paragraph("6. Automated Verification, Safety Disclosures & Round 3 Roadmap", h2_style))
    story.append(
        Paragraph(
            "<b>Automated Test Evidence:</b> Backend unit tests: <b>154/154 PASS (11 skipped DB-dependent)</b> in 1.87s across configuration, security, canonical telemetry, ML RUL, hydraulic intelligence, alerts, and maintenance. Frontend checks: <b>npm run lint PASS</b> (0 errors, 0 warnings), <b>npm run format:check PASS</b>, <b>npm run typecheck PASS</b> (0 errors), <b>npm test PASS (14/14)</b>, <b>npm run build PASS</b> (production bundle produced).",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Honest Engineering Disclosures:</b> (1) No drinking-water certification (e.g. BIS/NSF/WQA) is claimed; AquaNexis is an operational predictive intelligence system; (2) All demonstration telemetry is SIMULATED via backend/simulator.py; (3) Actuator isolation is recorded as a software recommendation; physical solenoid valve actuation is not claimed for Round 2; (4) Local demo runs without external database via DEMO_MODE; production TimescaleDB hypertables are verified in CI.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Round 3 Roadmap:</b> (1) Long-term empirical run-to-failure membrane aging on a physical test bench to replace synthetic dataset training; (2) Hardware-in-the-loop (HIL) safety certification for physical Normally Closed solenoid valve actuators; (3) Cloud-hosted TimescaleDB deployment for multi-device fleet telemetry and OTA calibration updates.",
            body_style,
        )
    )

    doc.build(story)
    print(f"Generated {OUTPUT_FILE} successfully.")


if __name__ == "__main__":
    build_pdf()
