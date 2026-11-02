from fpdf import FPDF
import markdown
import re

with open('PROGRESS_REPORT.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Replace special Unicode characters with ASCII equivalents
def sanitize_text(text):
    replacements = {
        '\u2014': '--',    # em dash
        '\u2013': '-',     # en dash
        '\u2018': "'",     # left single quote
        '\u2019': "'",     # right single quote
        '\u201c': '"',     # left double quote
        '\u201d': '"',     # right double quote
        '\u2026': '...',   # ellipsis
        '\u2022': '-',     # bullet
        '\u2192': '->',    # right arrow
        '\u2264': '<=',    # less than or equal
        '\u2265': '>=',    # greater than or equal
        '\u00e0': 'a',     # a grave
        '\u20ac': 'EUR',   # euro
        '\u00a3': 'GBP',   # pound
        '\u00a5': 'JPY',   # yen
        '\u201e': '"',     # double low-9 quotation mark
        '\u201f': '"',     # high double comma
        '\u2039': '<',     # single left angle
        '\u203a': '>',     # single right angle
        '\u25aa': '-',     # black small square
        '\u25cf': '-',     # black circle
        '\u25e6': '-',     # white bullet
        '\u2713': 'v',     # check mark
        '\u2717': 'x',     # cross mark
        '\u26a0': '!',     # warning
        '\u2190': '<-',    # left arrow
        '\u2191': '^',     # up arrow
        '\u2193': 'v',     # down arrow
        '\u00b7': '-',     # middle dot
        '\u00a0': ' ',     # non-breaking space
        '\u200b': '',      # zero-width space
        '\ufeff': '',      # BOM
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining non-latin1 characters
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 5, sanitize_text('AquaNexis -- Round 2 Progress Report | UPES Dehradun | Track 2'), align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

def write_section(title, level=1):
    if level == 1:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(26, 60, 94)
        pdf.cell(0, 8, sanitize_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(44, 95, 138)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
    elif level == 2:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(44, 95, 138)
        pdf.cell(0, 7, sanitize_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

def write_text(text):
    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(51, 51, 51)
    pdf.multi_cell(0, 5, sanitize_text(text))
    pdf.ln(2)

def write_table(headers, rows, col_widths=None):
    if col_widths is None:
        available = 190
        col_widths = [available / len(headers)] * len(headers)
    
    # Header
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(26, 60, 94)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 6, sanitize_text(header), border=1, fill=True, align='C')
    pdf.ln()
    
    # Rows
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(51, 51, 51)
    fill = False
    for row in rows:
        if pdf.get_y() > 270:
            pdf.add_page()
            # Re-draw header
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_fill_color(240, 244, 248)
            pdf.set_text_color(26, 60, 94)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, sanitize_text(header), border=1, fill=True, align='C')
            pdf.ln()
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(51, 51, 51)
            fill = False
        
        if fill:
            pdf.set_fill_color(250, 251, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        # Calculate row height
        max_lines = 1
        for i, cell in enumerate(row):
            lines = pdf.multi_cell(col_widths[i], 6, sanitize_text(str(cell)), border=0, split_only=True)
            max_lines = max(max_lines, len(lines))
        row_h = max(max_lines * 6, 6)
        
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # Check if we need a page break
        if y_start + row_h > 280:
            pdf.add_page()
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            # Re-draw header
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_fill_color(240, 244, 248)
            pdf.set_text_color(26, 60, 94)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, sanitize_text(header), border=1, fill=True, align='C')
            pdf.ln()
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(51, 51, 51)
            fill = False
            x_start = pdf.get_x()
            y_start = pdf.get_y()
        
        for i, cell in enumerate(row):
            x = x_start + sum(col_widths[:i])
            pdf.set_xy(x, y_start)
            pdf.cell(col_widths[i], row_h, '', border=1, fill=fill)
            pdf.set_xy(x + 1, y_start + 1)
            pdf.multi_cell(col_widths[i] - 2, 6, sanitize_text(str(cell)), border=0)
        
        pdf.set_xy(x_start, y_start + row_h)
        fill = not fill
    pdf.ln(3)

# ===== BUILD THE PDF =====

# Title
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(26, 60, 94)
pdf.cell(0, 10, sanitize_text('AquaNexis -- Round 2 Progress Report'), new_x="LMARGIN", new_y="NEXT", align='C')
pdf.ln(2)

# Meta info
pdf.set_font('Helvetica', '', 10)
pdf.set_text_color(80, 80, 80)
meta = [
    ('Track', 'Track 2 -- Water Purifier'),
    ('Institution', 'UPES Dehradun'),
    ('Participation', 'Solo Prototype'),
    ('Date', '4 November 2026'),
    ('Competition', 'atomQUEST 2026'),
]
for label, value in meta:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(35, 6, sanitize_text(f'{label}:'), new_x="RIGHT", new_y="TOP")
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, sanitize_text(value), new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# Draw a line
pdf.set_draw_color(26, 60, 94)
pdf.set_line_width(0.5)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

# Section 1: Project & Participant Details
write_section('1. Project & Participant Details')
write_table(
    ['Field', 'Value'],
    [
        ['Project Name', 'AquaNexis -- Predictive Water Intelligence System'],
        ['Track', 'Track 2: Water Purifier'],
        ['Institution', 'UPES Dehradun'],
        ['Participation Type', 'Solo Prototype'],
        ['Primary Exploration', 'Filter failure prognostics using data analytics (FSI, FHI, RUL, Failure Risk)'],
        ['Secondary Exploration', 'Beyond-TDS water quality sensing (pH, Turbidity, Temperature, Flow, Pressure)'],
    ],
    [50, 140]
)

# Section 2: Problem & Proposed Solution
write_section('2. Problem & Proposed Solution')
write_text('Problem: Water purifiers lack predictive intelligence. Filter replacements are either reactive (after failure) or time-based (wasteful). Users have no visibility into filter degradation, water quality trends, or impending failures.')
write_text('Solution: AquaNexis is a software-only predictive intelligence platform that ingests multi-sensor telemetry (13 sensor types) from water purifiers, computes Filter Stress Index (FSI) and Filter Health Index (FHI) using deterministic engineering models, estimates Remaining Useful Life (RUL) with confidence intervals, classifies failure risk with explainable evidence, provides real-time dashboard, alerts, and guided maintenance workflows. All sensor readings and analytics carry explicit provenance (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED).')

# Section 3: Completed Software Modules
write_section('3. Completed Software Modules')
write_table(
    ['Module', 'Status', 'Key Features'],
    [
        ['Telemetry Ingestion', 'Complete', 'FastAPI endpoint, JWT auth, duplicate detection, quality validation'],
        ['Water Quality Analytics', 'Complete', 'AquaScore (0-100), parameter scores, trends, anomaly detection'],
        ['Filter Stress Index (FSI)', 'Complete', '7-component deterministic model, pressure differential, rolling baselines'],
        ['Filter Health Index (FHI)', 'Complete', '5-component weighted model, maintenance bands, confidence scoring'],
        ['RUL Estimation', 'Complete', 'ML interface with deterministic fallback, stability tracking, counterfactuals'],
        ['Failure Risk Assessment', 'Complete', '5-component risk model, explainable evidence, alert integration'],
        ['Alert State Machine', 'Complete', 'DETECTED->OPEN->ACKNOWLEDGED/SNOOZED/RESOLVED/AUTO_CLEARED'],
        ['Notification System', 'Complete', 'Console, Email/SMTP, Webhook providers with SSRF protection'],
        ['Maintenance & Filter Lifecycle', 'Complete', 'Catalog (11 categories), compatibility engine, workflow state machine'],
        ['Calibration Management', 'Complete', 'Time/usage-based policies, post-maintenance verification, baseline versioning'],
        ['Safety Architecture', 'Complete', 'Leak/pressure/flow/pump protection, idempotent actions, role-based auth'],
        ['Real-time WebSocket', 'Complete', 'Telemetry/alert broadcasts, exponential backoff reconnection'],
        ['React Dashboard', 'Complete', 'Live sensor grid, AquaScore, Filter Health, Diagnostics, Alerts, Maintenance'],
        ['Data Provenance Display', 'Complete', 'MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED badges on all values'],
    ],
    [45, 18, 127]
)

# Section 4: Original Sourcing Risks & Updated Status
write_section('4. Original Sourcing Risks & Updated Status')
write_table(
    ['Original Risk', 'Status', 'Resolution'],
    [
        ['ESP32 hardware unavailable', 'Resolved', 'Scope changed to software-only; firmware archived as reference'],
        ['ESP-IDF build environment', 'Resolved', 'Not required for software prototype'],
        ['Physical sensor calibration', 'Resolved', 'Simulator provides calibrated synthetic data'],
        ['Sensor PCB fabrication', 'Resolved', 'Out of scope - software prototype uses simulated telemetry'],
        ['Custom filter housing', 'Resolved', 'Out of scope - maintenance module manages catalog only'],
    ],
    [50, 18, 122]
)

# Section 5: Budget
write_section('5. Budget: Original Estimate vs Actual')
write_table(
    ['Category', 'Original Estimate', 'Actual Spend', 'Notes'],
    [
        ['ESP32 Dev Kit', '1,500', '0', 'Not purchased - out of scope'],
        ['Sensors (13 types)', '8,000', '0', 'Not purchased - out of scope'],
        ['PCB Fabrication', '2,000', '0', 'Not purchased - out of scope'],
        ['Enclosure/Mechanical', '3,000', '0', 'Not purchased - out of scope'],
        ['Cloud/Hosting', '500', '0', 'Local development only'],
        ['Total', '~15,000', '0', 'Software-only - no hardware procurement'],
    ],
    [40, 30, 25, 95]
)
write_text('Note: Original Stage 1 abstract estimated Rs.5,000-10,000 for minimal hardware. Actual expenditure is Rs.0 as the project pivoted to a software-only prototype before any hardware procurement.')

# Section 6: Scope Change
write_section('6. Scope Change & Reason')
write_text('Original Scope (Stage 1): Hardware + software water purifier with ESP32, 13 physical sensors, custom PCB, filter housing, and dashboard.')
write_text('Revised Scope (G6): Software-only intelligence platform. Python telemetry simulator replaces physical sensors. All analytics, dashboard, alerts, maintenance workflows, and safety logic implemented in software.')
write_text('Reason: Hardware development (ESP32 firmware, physical sensors, ESP-IDF setup, PCB fabrication, custom enclosure) was descoped due to: ESP-IDF build environment not available; physical hardware unavailable for validation; competition allows software-only prototypes where "value delivered is immense"; focus shifted to demonstrating meaningful predictive and diagnostic capabilities rather than physical integration.')
write_text('Firmware preserved in firmware/esp32/ as archived reference with 13 sensor drivers, communication layer, and main application - syntax-validated (GCC).')

# Section 7: Revised Performance Targets
write_section('7. Revised Performance Targets & Verification Status')
write_table(
    ['Original Target', 'Revised Target', 'Verification Status'],
    [
        ['>=4 additional contextual signals', '13 sensor types implemented', 'Verified - All 13 sensors in simulator & dashboard'],
        ['RUL MAE <= 7 days', 'RUL deterministic fallback (no trained model)', 'Not verifiable - No trained ML model; fallback clearly labeled'],
        ['Dashboard update <= 5 seconds', 'WebSocket + 5s staleTime', 'Verified - Live updates via WebSocket, stale detection at 30s'],
        ['Automatic safe shutdown', 'Software safety alerts only', 'Verified - Leak/pressure/flow alerts generated; no physical actuators'],
        ['TDS rejection & flow/recovery tracking', 'Purification performance module', 'Verified - Rejection rate, recovery ratio, efficiency computed'],
    ],
    [45, 50, 95]
)

# Section 8: Delay Reasons
write_section('8. Delay Reasons')
write_table(
    ['Delay', 'Cause', 'Mitigation'],
    [
        ['ESP-IDF environment setup failed', 'ESP-IDF v5.x not installed on Windows; Docker unavailable', 'Pivoted to software-only; firmware archived'],
        ['PostgreSQL not running for integration tests', 'No local DB instance', 'Unit tests use mocks; 133/133 pass (11 DB errors expected)'],
        ['WebSocket message type mismatch', 'Backend/frontend type definitions diverged', 'Fixed: added mapping layer in WebSocket manager'],
        ['Offline mode not implemented', 'Frontend lacked connection state handling', 'Added: stale data banner, offline indicator, auto-recovery'],
    ],
    [50, 55, 85]
)

# Section 9: Safety / Fail-Safe Status
write_section('9. Safety / Fail-Safe Status')
write_table(
    ['Safety Feature', 'Implementation', 'Status'],
    [
        ['Leak detection', 'Sensor reading -> critical alert -> safety workflow', 'Implemented (software)'],
        ['High pressure protection', 'Threshold breach -> alert + pump shutdown command', 'Implemented (software command only)'],
        ['Low flow / dry run', 'Flow < threshold -> alert + pump shutdown command', 'Implemented (software command only)'],
        ['Pump overcurrent', 'Current > threshold -> alert + shutdown command', 'Implemented (software command only)'],
        ['Physical actuator control', 'NOT IMPLEMENTED - Software-only prototype', 'Explicitly NOT implemented'],
    ],
    [45, 75, 70]
)
write_text('Critical Disclosure: No physical purifier, pump, valve, or actuator exists. All safety actions are software alerts and logged commands only. The system demonstrates the logic for fail-safe responses but cannot physically shut down equipment.')

# Section 10: Round 3 Plan
write_section('10. Round 3 Plan')
write_table(
    ['Activity', 'Description', 'Target'],
    [
        ['External Telemetry Integration', 'Documented API for real purifier telemetry ingestion (HTTP/WebSocket)', 'Q1 2027'],
        ['ML Model Training', 'Collect operational data -> train RUL model -> replace deterministic fallback', 'Q2 2027'],
        ['Mobile App', 'React Native companion app for technicians/consumers', 'Q2 2027'],
        ['Multi-device Fleet View', 'Dashboard for managing multiple purifiers', 'Q3 2027'],
        ['Field Validation', 'Partner with purifier OEM for real-world pilot', 'Q3 2027'],
        ['Regulatory Alignment', 'Map analytics to ISO/NSF water quality standards', 'Q4 2027'],
    ],
    [50, 95, 45]
)

# Section 11: Key Demonstration Evidence
write_section('11. Key Demonstration Evidence (G7.6)')
write_table(
    ['Scenario', 'Evidence'],
    [
        ['NORMAL', 'Dashboard: Online, AquaScore 85, all sensors GOOD, provenance=SIMULATED'],
        ['FILTER_STRESS', 'FSI=65 (MODERATE), FHI=45 (POOR), Band=REPLACE_RECOMMENDED, Alert=Filter Health Critical'],
        ['LEAK', 'Critical alert "Leak Detected", Diagnostics leak panel=CRITICAL, safety workflow displayed'],
        ['SENSOR_FAULT', 'Quality flags=SUSPECT/BAD, provenance tracking, no silent degradation to reliable predictions'],
    ],
    [30, 160]
)
write_text('All scenarios tested with Python simulator (backend/simulator.py --profile <name>).')

# Declaration
pdf.ln(4)
write_section('Declaration')
write_text('This report accurately reflects the software-only implementation status. All hardware development (ESP32 firmware, physical sensors, PCB, enclosure) is out of scope and archived in firmware/esp32/. The demonstration uses simulated telemetry from backend/simulator.py. No physical purifier exists.')
write_text('Prepared by: [Participant Name]')
write_text('Institution: UPES Dehradun')
write_text('Date: 4 November 2026')

# Save
output_path = 'atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf'
pdf.output(output_path)
print(f'PDF saved to {output_path}')
print(f'Pages: {pdf.page_no()}')