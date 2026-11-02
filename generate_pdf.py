import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

with open('PROGRESS_REPORT.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

html_content = markdown.markdown(md_content, extensions=['tables', 'toc', 'fenced_code'])

css = CSS(string='''
@page { size: A4; margin: 2cm; }
body { font-family: 'DejaVu Sans', 'Arial', sans-serif; font-size: 10pt; line-height: 1.4; color: #333; }
h1 { color: #1a3c5e; border-bottom: 2px solid #1a3c5e; padding-bottom: 0.3em; font-size: 18pt; }
h2 { color: #2c5f8a; border-bottom: 1px solid #2c5f8a; padding-bottom: 0.2em; font-size: 14pt; margin-top: 1.5em; }
h3 { color: #3a7cb8; font-size: 12pt; margin-top: 1em; }
table { border-collapse: collapse; width: 100%; margin: 0.5em 0; font-size: 9pt; }
th, td { border: 1px solid #ddd; padding: 4px 6px; text-align: left; }
th { background-color: #f0f4f8; font-weight: bold; }
tr:nth-child(even) { background-color: #fafbfc; }
code { background-color: #f4f4f4; padding: 0.1em 0.3em; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 9pt; }
pre { background-color: #f8f8f8; padding: 0.5em; border-radius: 4px; overflow-x: auto; font-size: 8pt; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid #ddd; margin: 1em 0; }
ul, ol { margin: 0.3em 0 0.3em 1.5em; }
li { margin: 0.2em 0; }
p { margin: 0.4em 0; }
''')

font_config = FontConfiguration()
html_string = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AquaNexis Progress Report</title>
</head>
<body>
''' + html_content + '''
</body>
</html>
'''
HTML(string=html_string).write_pdf('atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf', stylesheets=[css], font_config=font_config)
print('PDF generated successfully')