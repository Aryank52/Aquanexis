"""
Generate the 2-page Round 2 Progress Report PDF:
atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf
Uses ReportLab Platypus so it runs natively on Windows without external GTK dependencies.
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
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="AquaNexis — Round 2 Progress Report (UPES Dehradun, Track 2)",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=5,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "BodyCompact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=3,
    )
    cell_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
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
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        return t

    story = []

    # Header
    story.append(Paragraph("AquaNexis — Round 2 Progress Report", title_style))
    story.append(
        Paragraph(
            "Track 2: Water Purifier | Institution: UPES Dehradun | Participation: Solo Prototype (Software-Only) | Date: 4 Nov 2026 | atomQUEST 2026",
            subtitle_style,
        )
    )

    # 1. Project & Participant Details
    story.append(Paragraph("1. Project & Participant Details", h2_style))
    story.append(
        make_table(
            ["Field", "Value"],
            [
                ["Project Name", "AquaNexis — Predictive Water Intelligence System (Software-Only Prototype)"],
                ["Track & Institution", "Track 2: Water Purifier | UPES Dehradun | Solo Prototype"],
                ["Primary Exploration", "Prognostics of filter failure using data analytics (FSI, FHI, RUL, Failure Risk, Explainability)"],
                ["Secondary Exploration", "Input water quality sensing beyond TDS (TDS, EC, pH, Turbidity, Temperature, Flow, Inlet/Outlet Pressure)"],
            ],
            [4.2 * cm, 14.0 * cm],
        )
    )

    # 2. Problem & Proposed Solution
    story.append(Paragraph("2. Problem & Proposed Solution", h2_style))
    story.append(
        Paragraph(
            "<b>Problem:</b> Conventional water purifiers rely on fixed calendar timers or basic TDS checks, resulting in either premature filter replacement or unexpected membrane clogging and unmonitored water quality degradation.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Solution:</b> AquaNexis is a software-only predictive intelligence platform that ingests 13-sensor purifier telemetry, validates sensor quality, computes a normalized 7-component Filter Stress Index (FSI) and 5-component Filter Health Index (FHI), estimates Remaining Useful Life (RUL) via an explicitly disclosed deterministic fallback (<b>MODEL_MISSING</b>), classifies failure risk with feature-level evidence, and drives stateful alerts and guided maintenance workflows. All values carry explicit provenance (<b>SIMULATED / CALCULATED / MODEL_PREDICTED / MEASURED</b>).",
            body_style,
        )
    )

    # 3. Completed Software Modules
    story.append(Paragraph("3. Completed Software Modules", h2_style))
    story.append(
        make_table(
            ["Module", "Status", "Verified Implementation Details"],
            [
                ["Telemetry & Quality Gate", "Complete", "FastAPI ingestion, JWT/API-key auth, range/rate/cross-sensor validation (GOOD/SUSPECT/BAD)"],
                ["Water Quality (Beyond TDS)", "Complete", "AquaScore (0-100), TDS, EC, pH, Turbidity, Temperature sub-scores, 1h trends, anomalies"],
                ["Filter Stress Index (FSI)", "Complete", "7-component normalized weights (sum=1.00); excludes missing sensors from weight denominator"],
                ["Filter Health Index (FHI)", "Complete", "5-component composite health score (0-100) + maintenance bands (NORMAL/MONITOR/REPLACE)"],
                ["RUL & Risk Prognostics", "Complete", "Deterministic fallback labeled MODEL_MISSING; withheld (N/A, LOW confidence) on SENSOR_FAULT"],
                ["Explainability Engine", "Complete", "Top 5 feature contributors (delta-P, flow deviation, volume, age, turbidity) + counterfactuals"],
                ["Alert State Machine", "Complete", "DETECTED -> OPEN -> ACKNOWLEDGED / SNOOZED / RESOLVED / AUTO_CLEARED + evidence drawer"],
                ["Maintenance Lifecycle", "Complete", "11-category filter catalog, compatibility engine, replacement/calibration/verification workflows"],
                ["WebSocket & React UI", "Complete", "React 18 + TypeScript dashboard (localhost:3000), live WebSocket (/ws/realtime/{id}), DEMO_MODE switcher"],
            ],
            [4.0 * cm, 1.8 * cm, 12.4 * cm],
        )
    )

    # 4. Sourcing Risks, Scope Reset & Budget
    story.append(Paragraph("4. Original Sourcing Risks, Scope Reset & Budget (Estimate vs Actual)", h2_style))
    story.append(
        make_table(
            ["Item / Risk", "Stage 1 Estimate", "Actual Spend / Status", "Resolution & Honest Disclosure"],
            [
                ["ESP32 + 13 Sensors + PCB", "Rs. 5,000 - 15,000", "Rs. 0 (Not purchased)", "Descoped in G6 to software-only prototype; firmware/esp32/ archived as reference"],
                ["Physical Calibration & Rig", "Bench loop planned", "Rs. 0 (Simulated)", "Replaced by deterministic 8-profile Python simulator (backend/simulator.py)"],
                ["TimescaleDB Extension", "Local PG16 + Timescale", "Rs. 0 (DEMO_MODE)", "Local Windows PG16 lacked timescaledb DLL; isolated DEMO_MODE runs full analytics in-memory"],
            ],
            [3.8 * cm, 2.8 * cm, 3.0 * cm, 8.6 * cm],
        )
    )

    # 5. Revised Performance Targets & Verification Status
    story.append(Paragraph("5. Revised Performance Targets & Verification Status", h2_style))
    story.append(
        make_table(
            ["Original Target", "Revised Software Target", "Verification Status & Disclosure"],
            [
                [">=4 contextual signals beyond TDS", "13 simulated sensor channels", "Verified: TDS, EC, pH, Turbidity, Temp, Flow, Inlet/Outlet Pressure, Tank, Leak, Current, Power, UV"],
                ["RUL MAE <= 7 days", "Deterministic RUL fallback + CI", "Disclosed: No trained .pkl ML model yet; explicitly labeled MODEL_MISSING (Deterministic Fallback v1.0)"],
                ["Dashboard update <= 5 seconds", "Live WebSocket + 5s staleTime", "Verified: Real-time WebSocket broadcast (/ws/realtime/{id}) + stale banner at >30s"],
                ["Automatic safe shutdown", "Software safety alert + audit log", "Disclosed: Software alert (leak_detected) & safety log only; NO physical solenoid valve or relay exists"],
                ["Bad sensor fault resilience", "Quality gate + confidence guard", "Verified: SENSOR_FAULT flags Quality=BAD, excludes missing sensors, and withholds RUL (Confidence=LOW)"],
            ],
            [4.2 * cm, 4.2 * cm, 9.8 * cm],
        )
    )

    # 6. End-to-End Scenario Demonstration Evidence
    story.append(Paragraph("6. End-to-End Scenario Demonstration Evidence (Verified in DEMO_MODE)", h2_style))
    story.append(
        make_table(
            ["Scenario", "Telemetry & Quality", "Analytics Response (AquaScore / FSI / FHI / RUL / Risk)", "Alert & Maintenance Action"],
            [
                ["NORMAL", "Quality=GOOD, SIMULATED (dP=30 kPa, Flow=2.0 L/m)", "AquaScore=100, FSI=20.0, FHI=83%, RUL=149.4d (MODEL_MISSING), Risk=LOW (13.4%)", "0 active alerts; routine monitoring"],
                ["FILTER_STRESS", "Quality=GOOD, SIMULATED (dP=280 kPa, Flow=0.85 L/m)", "AquaScore=93, FSI=67.5, FHI=40%, RUL=72.0d (MODEL_MISSING), Risk=MEDIUM (49.3%), Band=REPLACE_RECOMMENDED", "Alert filter_stress_high (OPEN -> ACKNOWLEDGED); Stage 1 Sediment replacement recommended"],
                ["LEAK", "Quality=GOOD, SIMULATED (leak_detected=true)", "AquaScore=100, FSI=22.3, FHI=83%, Risk=LOW", "Critical manual-only alert leak_detected + SAFETY_SHUTDOWN_RECOMMENDED software audit log"],
                ["SENSOR_FAULT", "Quality=BAD, SIMULATED (Turb>150 NTU, flow/P_out=null)", "AquaScore=59, FSI=0 (missing excluded), RUL=None (N/A withheld), Confidence=LOW", "Alert sensor_fault_detected; prevents false confident RUL prediction"],
            ],
            [2.5 * cm, 4.0 * cm, 6.2 * cm, 5.5 * cm],
        )
    )

    # 7. Test Suite Verification & Round 3 Plan
    story.append(Paragraph("7. Automated Verification & Round 3 Roadmap", h2_style))
    story.append(
        Paragraph(
            "<b>Automated Verification:</b> Backend unit tests: <b>133/133 PASS</b> (pytest: config, security, Phase D analytics, alert state machine, auto-clear, notifications, maintenance). Frontend checks: <b>npm run typecheck PASS</b> (0 errors), <b>npm test PASS (14/14)</b>, <b>npm run build PASS</b>.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Round 3 Plan:</b> (1) Train Random Forest / XGBoost RUL regression models on labeled run-to-failure membrane datasets to replace the deterministic fallback; (2) Deploy containerized PostgreSQL + TimescaleDB stack for multi-device fleet persistence; (3) Validate external HTTP/WebSocket telemetry ingestion with physical RO test-bench data.",
            body_style,
        )
    )
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "<b>Declaration:</b> This report accurately reflects the software-only prototype. All hardware work in firmware/esp32/ is archived out of scope. All demo telemetry is simulated (backend/simulator.py), RUL uses a deterministic fallback (MODEL_MISSING), and safety actions are software alerts/logs only.",
            body_style,
        )
    )

    doc.build(story)
    print(f"Generated {OUTPUT_FILE} successfully.")


if __name__ == "__main__":
    build_pdf()
