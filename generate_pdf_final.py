from fpdf import FPDF

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
        '\u2190': '<-',    # left arrow
        '\u2191': '^',     # up arrow
        '\u2193': 'v',     # down arrow
        '\u00b7': '-',     # middle dot
        '\u00a0': ' ',     # non-breaking space
        '\u200b': '',      # zero-width space
        '\ufeff': '',      # BOM
        '\u2713': 'v',     # check mark
        '\u2717': 'x',     # cross mark
        '\u26a0': '!',     # warning
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 7)
            self.cell(0, 4, sanitize_text('AquaNexis -- Round 2 Progress Report | UPES Dehradun | Track 2'), align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.cell(0, 8, f'Page {self.page_no()}/{{nb}}', align='C')

pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

def write_section(title, level=1):
    if level == 1:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(26, 60, 94)
        pdf.cell(0, 6, sanitize_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(44, 95, 138)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
    elif level == 2:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(44, 95, 138)
        pdf.cell(0, 5, sanitize_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

def write_text(text):
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(51, 51, 51)
    pdf.multi_cell(0, 4, sanitize_text(text))
    pdf.ln(1)

def write_table(headers, rows, col_widths=None):
    if col_widths is None:
        available = 190
        col_widths = [available / len(headers)] * len(headers)
    
    # Header
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(26, 60, 94)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 5, sanitize_text(header), border=1, fill=True, align='C')
    pdf.ln()
    
    # Rows
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(51, 51, 51)
    fill = False
    for row in rows:
        if pdf.get_y() > 275:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 7)
            pdf.set_fill_color(240, 244, 248)
            pdf.set_text_color(26, 60, 94)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 5, sanitize_text(header), border=1, fill=True, align='C')
            pdf.ln()
            pdf.set_font('Helvetica', '', 7)
            pdf.set_text_color(51, 51, 51)
            fill = False
        
        if fill:
            pdf.set_fill_color(250, 251, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        # Calculate row height using dry_run
        max_lines = 1
        for i, cell in enumerate(row):
            lines = pdf.multi_cell(col_widths[i], 5, sanitize_text(str(cell)), border=0, dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        row_h = max(max_lines * 5, 5)
        
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        if y_start + row_h > 280:
            pdf.add_page()
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            pdf.set_font('Helvetica', 'B', 7)
            pdf.set_fill_color(240, 244, 248)
            pdf.set_text_color(26, 60, 94)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 5, sanitize_text(header), border=1, fill=True, align='C')
            pdf.ln()
            pdf.set_font('Helvetica', '', 7)
            pdf.set_text_color(51, 51, 51)
            fill = False
            x_start = pdf.get_x()
            y_start = pdf.get_y()
        
        for i, cell in enumerate(row):
            x = x_start + sum(col_widths[:i])
            pdf.set_xy(x, y_start)
            pdf.cell(col_widths[i], row_h, '', border=1, fill=fill)
            pdf.set_xy(x + 0.5, y_start + 0.5)
            pdf.multi_cell(col_widths[i] - 1, 5, sanitize_text(str(cell)), border=0)
        
        pdf.set_xy(x_start, y_start + row_h)
        fill = not fill
    pdf.ln(2)

# ===== BUILD THE PDF =====

# Title
pdf.set_font('Helvetica', 'B', 16)
pdf.set_text_color(26, 60, 94)
pdf.cell(0, 8, sanitize_text('AquaNexis -- Round 2 Progress Report'), new_x="LMARGIN", new_y="NEXT", align='C')
pdf.ln(1)

# Meta info
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
meta = [
    ('Track', 'Track 2 -- Water Purifier'),
    ('Institution', 'UPES Dehradun'),
    ('Participation', 'Solo Prototype'),
    ('Date', '4 November 2026'),
    ('Competition', 'atomQUEST 2026'),
]
for label, value in meta:
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(28, 4.5, sanitize_text(f'{label}:'), new_x="RIGHT", new_y="TOP")
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(0, 4.5, sanitize_text(value), new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)

# Draw a line
pdf.set_draw_color(26, 60, 94)
pdf.set_line_width(0.4)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(2)

# Section 1: Project & Participant Details
write_section('1. Project & Participant Details')
write_table(
    ['Field', 'Value'],
    [
        ['Project Name', 'AquaNexis -- Predictive Water Intelligence System'],
        ['Track', 'Track 2: Water Purifier'],
        ['Institution', 'UPES Dehradun'],
        ['Participation', 'Solo Prototype'],
        ['Primary', 'Filter failure prognostics (FSI, FHI, RUL, Failure Risk)'],
        ['Secondary', 'Beyond-TDS sensing (pH, Turbidity, Temp, Flow, Pressure)'],
    ],
    [35, 155]
)

# Section 2: Problem & Solution
write_section('2. Problem & Solution')
write_text('Problem: Water purifiers lack predictive intelligence. Filter replacements are reactive or time-based (wasteful). Users lack visibility into filter degradation, water quality trends, or impending failures.')
write_text('Solution: AquaNexis is a software-only predictive intelligence platform ingesting 13-sensor telemetry, computing FSI/FHI via deterministic models, estimating RUL with confidence intervals, classifying failure risk with explainable evidence, providing real-time dashboard, alerts, and guided maintenance. All readings/analytics carry explicit provenance (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED).')

# Section 3: Completed Software Modules
write_section('3. Completed Software Modules')
write_table(
    ['Module', 'Status', 'Key Features'],
    [
        ['Telemetry Ingestion', 'Done', 'FastAPI, JWT, dedup, quality validation'],
        ['Water Quality Analytics', 'Done', 'AquaScore 0-100, param scores, trends, anomalies'],
        ['Filter Stress Index (FSI)', 'Done', '7-comp deterministic, pressure diff, rolling baselines'],
        ['Filter Health Index (FHI)', 'Done', '5-comp weighted, maintenance bands, confidence'],
        ['RUL Estimation', 'Done', 'ML interface + deterministic fallback, stability, counterfactuals'],
        ['Failure Risk', 'Done', '5-comp risk model, explainable evidence, alert integration'],
        ['Alert State Machine', 'Done', 'DETECTED->OPEN->ACK/SNOOZE/RESOLVE/AUTO_CLEAR'],
        ['Notifications', 'Done', 'Console, Email/SMTP, Webhook with SSRF protection'],
        ['Maintenance Lifecycle', 'Done', 'Catalog 11 cats, compat engine, workflow state machine'],
        ['Calibration Mgmt', 'Done', 'Time/usage policies, post-maint verification, baselines'],
        ['Safety Architecture', 'Done', 'Leak/pressure/flow/pump, idempotent, RBAC'],
        ['Real-time WebSocket', 'Done', 'Telemetry/alert broadcast, exp backoff reconnect'],
        ['React Dashboard', 'Done', 'Sensor grid, AquaScore, FHI, Diagnostics, Alerts, Maint'],
        ['Provenance Display', 'Done', 'MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED badges'],
    ],
    [38, 12, 140]
)

# Section 4: Sourcing Risks
write_section('4. Original Sourcing Risks & Status')
write_table(
    ['Risk', 'Status', 'Resolution'],
    [
        ['ESP32 hardware unavailable', 'Resolved', 'Software-only scope; firmware archived'],
        ['ESP-IDF build env missing', 'Resolved', 'Not needed for software prototype'],
        ['Physical sensor calibration', 'Resolved', 'Simulator provides calibrated synthetic data'],
        ['Sensor PCB fabrication', 'Resolved', 'Out of scope - simulated telemetry'],
        ['Custom filter housing', 'Resolved', 'Out of scope - catalog only'],
    ],
    [45, 15, 130]
)

# Section 5: Budget
write_section('5. Budget: Original vs Actual')
write_table(
    ['Category', 'Estimate (Rs)', 'Actual (Rs)', 'Notes'],
    [
        ['ESP32 Dev Kit', '1,500', '0', 'Not purchased - out of scope'],
        ['Sensors (13 types)', '8,000', '0', 'Not purchased - out of scope'],
        ['PCB Fabrication', '2,000', '0', 'Not purchased - out of scope'],
        ['Enclosure/Mechanical', '3,000', '0', 'Not purchased - out of scope'],
        ['Cloud/Hosting', '500', '0', 'Local dev only'],
        ['Total', '~15,000', '0', 'Software-only - no hardware'],
    ],
    [35, 25, 20, 110]
)
write_text('Note: Stage 1 abstract estimated Rs.5,000-10,000 for minimal hardware. Actual spend Rs.0 - pivoted to software-only before procurement.')

# Section 6: Scope Change
write_section('6. Scope Change & Reason')
write_text('Original (Stage 1): HW+SW purifier with ESP32, 13 physical sensors, custom PCB, filter housing, dashboard.')
write_text('Revised (G6): Software-only platform. Python simulator replaces sensors. All analytics, dashboard, alerts, maintenance, safety in software.')
write_text('Reason: ESP-IDF unavailable; no hardware for validation; competition allows SW-only; focus on predictive/diagnostic value.')
write_text('Firmware in firmware/esp32/ archived (13 drivers, comm layer, main app - GCC validated).')

# Section 7: Performance Targets
write_section('7. Revised Targets & Verification')
write_table(
    ['Original Target', 'Revised Target', 'Status'],
    [
        ['>=4 contextual signals', '13 sensors implemented', 'Verified - all 13 in sim & dashboard'],
        ['RUL MAE <= 7 days', 'Deterministic fallback', 'Not verifiable - no trained model; labeled'],
        ['Dashboard <= 5s update', 'WS + 5s staleTime', 'Verified - WS live, stale at 30s'],
        ['Auto safe shutdown', 'SW safety alerts only', 'Verified - alerts generated; no actuators'],
        ['TDS rejection/flow tracking', 'Purification module', 'Verified - rejection, recovery, efficiency'],
    ],
    [40, 45, 105]
)

# Section 8: Delays
write_section('8. Delay Reasons')
write_table(
    ['Delay', 'Cause', 'Mitigation'],
    [
        ['ESP-IDF setup failed', 'No ESP-IDF/Docker on Windows', 'Pivot to SW-only; firmware archived'],
        ['PostgreSQL not running', 'No local DB instance', 'Unit tests use mocks; 133/133 pass (11 DB errs)'],
        ['WS message type mismatch', 'Backend/frontend types diverged', 'Mapping layer in WS manager'],
        ['Offline mode missing', 'No connection state handling', 'Stale banner, offline indicator, auto-recovery'],
    ],
    [42, 50, 98]
)

# Section 9: Safety
write_section('9. Safety / Fail-Safe Status')
write_table(
    ['Feature', 'Implementation', 'Status'],
    [
        ['Leak detection', 'Reading -> critical alert -> safety workflow', 'SW implemented'],
        ['High pressure', 'Threshold breach -> alert + pump shutdown cmd', 'SW command only'],
        ['Low flow/dry run', 'Flow < threshold -> alert + shutdown cmd', 'SW command only'],
        ['Pump overcurrent', 'Current > threshold -> alert + shutdown cmd', 'SW command only'],
        ['Physical actuator', 'NOT IMPLEMENTED - SW prototype', 'EXPLICITLY NOT DONE'],
    ],
    [35, 75, 80]
)
write_text('Critical Disclosure: No physical purifier, pump, valve, or actuator exists. All safety actions are SW alerts and logged commands only. System demonstrates fail-safe logic but cannot physically shut down equipment.')

# Section 10: Round 3 Plan
write_section('10. Round 3 Plan')
write_table(
    ['Activity', 'Description', 'Target'],
    [
        ['Ext Telemetry API', 'Documented API for real purifier ingest (HTTP/WS)', 'Q1 2027'],
        ['ML Model Training', 'Collect data -> train RUL -> replace fallback', 'Q2 2027'],
        ['Mobile App', 'React Native for technicians/consumers', 'Q2 2027'],
        ['Fleet View', 'Dashboard for multiple purifiers', 'Q3 2027'],
        ['Field Validation', 'Partner with OEM for real-world pilot', 'Q3 2027'],
        ['Regulatory', 'Map analytics to ISO/NSF standards', 'Q4 2027'],
    ],
    [35, 95, 60]
)

# Section 11: Demo Evidence
write_section('11. Demo Evidence (G7.6)')
write_table(
    ['Scenario', 'Evidence'],
    [
        ['NORMAL', 'Online, AquaScore 85, sensors GOOD, prov=SIMULATED'],
        ['FILTER_STRESS', 'FSI=65 MODERATE, FHI=45 POOR, Band=REPLACE, Alert=Critical'],
        ['LEAK', 'Critical "Leak Detected", Diagnostics=CRITICAL, safety workflow'],
        ['SENSOR_FAULT', 'Quality=SUSPECT/BAD, provenance tracked, no silent degradation'],
    ],
    [30, 160]
)
write_text('All tested via python backend/simulator.py --profile <name>.')

# Declaration
pdf.ln(2)
write_section('Declaration')
write_text('This report reflects software-only implementation. All HW dev (ESP32, sensors, PCB, enclosure) out of scope, archived in firmware/esp32/. Demo uses simulated telemetry from backend/simulator.py. No physical purifier exists.')
write_text('Prepared by: [Participant Name]')
write_text('Institution: UPES Dehradun')
write_text('Date: 4 November 2026')

# Save
output_path = 'atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf'
pdf.output(output_path)
print(f'PDF saved to {output_path}')
print(f'Pages: {pdf.page_no()}')