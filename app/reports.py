"""Report files for /reports/summary: CSV (one metric per row) and PDF (a formatted one-page summary)."""
import csv
import io
from itertools import groupby

from . import analytics


def to_csv(report: dict) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "metric", "value"])
    writer.writerows(analytics.summary_rows(report))
    return buffer.getvalue().encode("utf-8")


def to_pdf(report: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    story = [Paragraph("SupportPilot summary report", styles["Title"]),
             Paragraph(f"Generated at {report['generated_at']} (UTC)", styles["Normal"]), Spacer(1, 12)]
    rows = analytics.summary_rows(report)[1:]  # skip the generated_at line, it is in the header
    for section, group in groupby(rows, key=lambda r: r[0]):
        story.append(Paragraph(section.replace("_", " ").title(), styles["Heading2"]))
        data = [["Metric", "Value"]] + [[str(metric), "" if value is None else str(value)]
                                        for _, metric, value in group]
        table = Table(data, colWidths=[300, 180])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story += [table, Spacer(1, 10)]
    out = io.BytesIO()
    SimpleDocTemplate(out, pagesize=A4, title="SupportPilot summary", leftMargin=40, rightMargin=40,
                      topMargin=40, bottomMargin=40).build(story)
    return out.getvalue()
